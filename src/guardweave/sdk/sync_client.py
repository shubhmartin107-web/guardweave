from __future__ import annotations

import asyncio
from typing import Any

from guardweave.core.enums import Capability, Decision, TrustLevel
from guardweave.core.models import PolicyEvaluationResult
from guardweave.sdk.guardweave import GuardWeave as AsyncGuardWeave


class GuardWeave:
    def __init__(
        self,
        agent_id: str | None = None,
        trust_level: TrustLevel = TrustLevel.MEDIUM,
        environment: str | None = None,
    ):
        self._async = AsyncGuardWeave(
            agent_id=agent_id,
            trust_level=trust_level,
            environment=environment,
        )
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def _run(self, coro: Any) -> Any:
        loop = self._get_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
        return loop.run_until_complete(coro)

    def initialize(self) -> None:
        self._run(self._async.initialize())

    def check_action(
        self,
        action: str,
        capability: Capability,
        target: str = "",
        parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyEvaluationResult:
        return self._run(  # type: ignore[no-any-return]
            self._async.check_action(
                action=action,
                capability=capability,
                target=target,
                parameters=parameters,
                metadata=metadata,
            )
        )

    def log_action(
        self,
        action: str,
        capability: Capability,
        target: str = "",
        decision: Decision | str = Decision.ALLOW,
        risk_score: int = 0,
        reason: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        resolved_decision = Decision(decision) if isinstance(decision, str) else decision
        self._run(
            self._async.log_action(
                action=action,
                capability=capability,
                target=target,
                decision=resolved_decision,
                risk_score=risk_score,
                reason=reason,
                metadata=metadata,
            )
        )

    def request_approval(
        self,
        action: str,
        capability: Capability,
        target: str = "",
        risk_score: int = 50,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        return self._run(  # type: ignore[no-any-return]
            self._async.request_approval(
                action=action,
                capability=capability,
                target=target,
                risk_score=risk_score,
                metadata=metadata,
            )
        )

    def check_approval_status(self, approval_id: str) -> str | None:
        return self._run(self._async.check_approval_status(approval_id))  # type: ignore[no-any-return]

    def close(self) -> None:
        if self._loop and not self._loop.is_closed():
            self._loop.close()
