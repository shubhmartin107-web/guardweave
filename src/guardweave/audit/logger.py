from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from guardweave.audit.hashing import HashChain
from guardweave.core.models import ActionContext, AuditEntry, PolicyEvaluationResult
from guardweave.persistence.repositories import (
    get_latest_audit_hash,
    save_audit_entry,
)


class AuditLogger:
    def __init__(self, hasher: HashChain | None = None):
        self._hasher = hasher or HashChain()

    async def log_decision(
        self,
        session: AsyncSession,
        context: ActionContext,
        result: PolicyEvaluationResult,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        previous_hash = await get_latest_audit_hash(session) or ""

        entry_data = self._hasher.build_entry_data(
            entry_id=result.id,
            timestamp=datetime.now(UTC),
            agent_id=context.agent_id,
            session_id=context.session_id,
            action=context.action,
            capability=context.capability.value,
            target=context.target,
            decision=result.decision.value,
            risk_score=result.risk_score,
            risk_level=result.risk_level.value,
            policy_id=result.policy_id,
            rule_id=result.matched_rule.id if result.matched_rule else None,
            reason=result.reason,
            context=context.model_dump(exclude_none=True),
            previous_hash=previous_hash,
        )

        chain_hash = self._hasher.compute_hash(entry_data)

        entry = AuditEntry(
            id=result.id,
            timestamp=entry_data["timestamp"],
            agent_id=context.agent_id,
            session_id=context.session_id,
            action=context.action,
            capability=context.capability,
            target=context.target,
            decision=result.decision,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            policy_id=result.policy_id,
            rule_id=result.matched_rule.id if result.matched_rule else None,
            reason=result.reason,
            context=context.model_dump(exclude_none=True),
            chain_hash=chain_hash,
            previous_hash=previous_hash,
            metadata=metadata or {},
        )

        await save_audit_entry(session, entry)
        return entry

    async def verify_integrity(self, session: AsyncSession) -> bool:
        from guardweave.persistence.repositories import query_audit_logs

        entries = await query_audit_logs(session, limit=10000, ascending=True)
        if not entries:
            return True

        entry_dicts = []
        for e in entries:
            entry_dicts.append({
                "id": e.id,
                "timestamp": e.timestamp.isoformat() if hasattr(e.timestamp, 'isoformat') else str(e.timestamp),
                "agent_id": e.agent_id,
                "session_id": e.session_id,
                "action": e.action,
                "capability": e.capability.value if hasattr(e.capability, 'value') else str(e.capability),
                "target": e.target,
                "decision": e.decision.value if hasattr(e.decision, 'value') else str(e.decision),
                "risk_score": e.risk_score,
                "risk_level": e.risk_level.value if hasattr(e.risk_level, 'value') else str(e.risk_level),
                "policy_id": e.policy_id,
                "rule_id": e.rule_id,
                "reason": e.reason,
                "context": e.context,
                "previous_hash": e.previous_hash,
                "chain_hash": e.chain_hash,
            })

        return self._hasher.verify_chain(entry_dicts)
