from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from guardweave.audit.logger import AuditLogger
from guardweave.core.enums import Capability, Decision, RiskLevel, TrustLevel
from guardweave.core.exceptions import (
    ActionDeniedError,
    ActionRequiresApprovalError,
)
from guardweave.core.models import ActionContext, PolicyEvaluationResult
from guardweave.engine.evaluator import PolicyEvaluator
from guardweave.hitl.workflow import ApprovalWorkflow
from guardweave.persistence.database import init_db
from guardweave.persistence.repositories import load_policies


class GuardWeave:
    def __init__(
        self,
        agent_id: str | None = None,
        session_id: str | None = None,
        trust_level: TrustLevel = TrustLevel.MEDIUM,
        environment: str | None = None,
    ):
        self.agent_id = agent_id or f"agent_{uuid4().hex[:8]}"
        self.session_id = session_id or f"ses_{uuid4().hex[:12]}"
        self.trust_level = trust_level
        self.environment = environment or os.environ.get("GUARDWEAVE_ENV", "development")
        self._evaluator = PolicyEvaluator()
        self._audit_logger = AuditLogger()
        self._workflow = ApprovalWorkflow()
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        await init_db()
        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            policies = await load_policies(session)
            for policy in policies:
                self._evaluator.add_policy(policy)
        self._initialized = True

    def use_plugin(self, plugin: Any) -> None:
        from guardweave.sdk.plugin import PluginManager

        if not hasattr(self, "_plugin_manager"):
            self._plugin_manager = PluginManager()
        self._plugin_manager.register(plugin)

    async def check_action(
        self,
        action: str,
        capability: Capability,
        target: str = "",
        parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyEvaluationResult:
        if not self._initialized:
            await self.initialize()

        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()

        context = ActionContext(
            agent_id=self.agent_id,
            session_id=self.session_id,
            action=action,
            capability=capability,
            target=target,
            parameters=parameters or {},
            trust_level=self.trust_level,
            environment=self.environment,
            metadata=metadata or {},
        )

        plugin_mgr = getattr(self, "_plugin_manager", None)
        if plugin_mgr:
            context = await plugin_mgr.run_before_evaluate(context)

        policy = self._evaluator.get_policy()
        result = self._evaluator.evaluate(context, policy=policy)

        if plugin_mgr:
            result = await plugin_mgr.run_after_evaluate(context, result)

        async with factory() as session:
            await self._audit_logger.log_decision(session, context, result, metadata=metadata)

            if result.requires_approval:
                req = await self._workflow.request_approval(
                    session, context, result,
                    timeout_seconds=result.risk_score * 10 if result.risk_score > 0 else 300,
                )
                result.approval_request_id = req.id
                raise ActionRequiresApprovalError(
                    f"Action '{action}' requires approval. Request ID: {req.id}"
                )

            if result.decision == Decision.DENY:
                raise ActionDeniedError(
                    f"Action '{action}' denied by policy. Reason: {result.reason}"
                )

        return result

    async def log_action(
        self,
        action: str,
        capability: Capability,
        target: str = "",
        decision: Decision = Decision.ALLOW,
        risk_score: int = 0,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self._initialized:
            await self.initialize()

        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()

        context = ActionContext(
            agent_id=self.agent_id,
            session_id=self.session_id,
            action=action,
            capability=capability,
            target=target,
            trust_level=self.trust_level,
            environment=self.environment,
            metadata=metadata or {},
        )

        from guardweave.engine.risk_scorer import RiskScorer
        scorer = RiskScorer()
        score, level = scorer.calculate(context)
        if risk_score > 0:
            score = risk_score
        result = PolicyEvaluationResult(
            decision=decision if isinstance(decision, Decision) else Decision(decision),
            risk_score=score,
            risk_level=level,
            policy_id="manual",
            reason=reason,
            context=context,
        )

        async with factory() as session:
            await self._audit_logger.log_decision(session, context, result, metadata=metadata)

    async def request_approval(
        self,
        action: str,
        capability: Capability,
        target: str = "",
        risk_score: int = 50,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if not self._initialized:
            await self.initialize()

        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()

        ctx = ActionContext(
            agent_id=self.agent_id,
            session_id=self.session_id,
            action=action,
            capability=capability,
            target=target,
            trust_level=self.trust_level,
            environment=self.environment,
            metadata=metadata or {},
        )

        result = PolicyEvaluationResult(
            decision=Decision.ASK,
            risk_score=risk_score,
            risk_level=RiskLevel.LOW,
            policy_id="manual",
            reason="Manual approval request",
            context=ctx,
        )

        async with factory() as session:
            req = await self._workflow.request_approval(session, ctx, result)
            return req.id

    async def check_approval_status(self, approval_id: str) -> str | None:
        from guardweave.persistence.database import get_session_factory
        factory = get_session_factory()
        async with factory() as session:
            req = await self._workflow.get_by_id(session, approval_id)
            return req.status.value if req else None
