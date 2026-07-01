from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from guardweave.core.enums import ApprovalStatus, Decision
from guardweave.core.models import (
    ApprovalRequest,
    AuditEntry,
    Policy,
    Rule,
)
from guardweave.persistence.models import (
    ApprovalRequestModel,
    AuditEntryModel,
    PolicyModel,
    RuleModel,
)

# -- Policy Repository --


async def load_policies(session: AsyncSession) -> list[Policy]:
    result = await session.execute(
        select(PolicyModel).options(selectinload(PolicyModel.rules)).where(PolicyModel.active)
    )
    rows = result.scalars().all()
    return [_policy_from_model(m) for m in rows]


async def load_policy_by_id(session: AsyncSession, policy_id: str) -> Policy | None:
    result = await session.execute(
        select(PolicyModel).options(selectinload(PolicyModel.rules)).where(PolicyModel.id == policy_id)
    )
    model = result.scalar_one_or_none()
    return _policy_from_model(model) if model else None


async def load_policy_by_name(session: AsyncSession, name: str) -> Policy | None:
    result = await session.execute(
        select(PolicyModel).options(selectinload(PolicyModel.rules)).where(PolicyModel.name == name).limit(1)
    )
    model = result.scalar_one_or_none()
    return _policy_from_model(model) if model else None


async def save_policy(session: AsyncSession, policy: Policy) -> Policy:
    model = PolicyModel(
        id=policy.id,
        name=policy.name,
        version=policy.version,
        description=policy.description,
        trust_level=policy.trust_level.value,
        environment=policy.environment,
        default_decision=policy.default_decision.value,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
        active=policy.active,
    )
    session.add(model)
    for rule in policy.rules:
        rm = RuleModel(
            id=rule.id,
            policy_id=policy.id,
            description=rule.description,
            match_json=rule.match.model_dump(),
            decision=rule.decision.value,
            risk_score_modifier=rule.risk_score_modifier,
            reason=rule.reason,
        )
        session.add(rm)
    await session.commit()
    return policy


async def delete_policy(session: AsyncSession, policy_id: str) -> bool:
    await session.execute(delete(RuleModel).where(RuleModel.policy_id == policy_id))
    result = await session.execute(delete(PolicyModel).where(PolicyModel.id == policy_id))
    await session.commit()
    return bool(result.rowcount > 0)


async def list_policies(session: AsyncSession) -> list[Policy]:
    result = await session.execute(
        select(PolicyModel).options(selectinload(PolicyModel.rules)).order_by(PolicyModel.created_at.desc())
    )
    rows = result.scalars().all()
    return [_policy_from_model(m) for m in rows]


# -- Audit Repository --


async def save_audit_entry(session: AsyncSession, entry: AuditEntry) -> AuditEntry:
    model = AuditEntryModel(
        id=entry.id,
        timestamp=entry.timestamp,
        agent_id=entry.agent_id,
        session_id=entry.session_id,
        action=entry.action,
        capability=entry.capability.value,
        target=entry.target,
        decision=entry.decision.value,
        risk_score=entry.risk_score,
        risk_level=entry.risk_level.value,
        policy_id=entry.policy_id,
        rule_id=entry.rule_id,
        reason=entry.reason,
        context=entry.context,
        chain_hash=entry.chain_hash,
        previous_hash=entry.previous_hash,
        metadata_json=entry.metadata,
    )
    session.add(model)
    await session.commit()
    return entry


async def query_audit_logs(
    session: AsyncSession,
    agent_id: str | None = None,
    capability: str | None = None,
    decision: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
    ascending: bool = False,
) -> list[AuditEntry]:
    order = AuditEntryModel.timestamp.asc() if ascending else AuditEntryModel.timestamp.desc()
    query = select(AuditEntryModel).order_by(order)
    if agent_id:
        query = query.where(AuditEntryModel.agent_id == agent_id)
    if capability:
        query = query.where(AuditEntryModel.capability == capability)
    if decision:
        query = query.where(AuditEntryModel.decision == decision)
    if action:
        query = query.where(AuditEntryModel.action == action)
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    rows = result.scalars().all()
    return [_audit_from_model(m) for m in rows]


async def get_latest_audit_hash(session: AsyncSession) -> str | None:
    result = await session.execute(
        select(AuditEntryModel.chain_hash)
        .order_by(AuditEntryModel.timestamp.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return str(row) if row else None


# -- Approval Repository --


async def save_approval_request(session: AsyncSession, req: ApprovalRequest) -> ApprovalRequest:
    model = ApprovalRequestModel(
        id=req.id,
        agent_id=req.agent_id,
        session_id=req.session_id,
        action=req.action,
        capability=req.capability.value,
        target=req.target,
        risk_score=req.risk_score,
        risk_level=req.risk_level.value,
        context=req.context,
        status=req.status.value,
        requested_at=req.requested_at,
        decided_at=req.decided_at,
        decided_by=req.decided_by,
        feedback=req.feedback,
        escalation_level=req.escalation_level,
        timeout_seconds=req.timeout_seconds,
        policy_id=req.policy_id,
    )
    session.add(model)
    await session.commit()
    return req


async def update_approval_status(
    session: AsyncSession,
    approval_id: str,
    status: ApprovalStatus,
    decided_by: str | None = None,
    feedback: str | None = None,
) -> ApprovalRequest | None:
    values = {
        "status": status.value,
        "decided_at": datetime.now(UTC),
    }
    if decided_by is not None:
        values["decided_by"] = decided_by
    if feedback is not None:
        values["feedback"] = feedback

    await session.execute(
        update(ApprovalRequestModel)
        .where(ApprovalRequestModel.id == approval_id)
        .values(**values)
    )
    await session.commit()

    result = await session.execute(
        select(ApprovalRequestModel).where(ApprovalRequestModel.id == approval_id)
    )
    model = result.scalar_one_or_none()
    return _approval_from_model(model) if model else None


async def get_pending_approvals(session: AsyncSession) -> list[ApprovalRequest]:
    result = await session.execute(
        select(ApprovalRequestModel)
        .where(ApprovalRequestModel.status == ApprovalStatus.PENDING.value)
        .order_by(ApprovalRequestModel.requested_at.desc())
    )
    rows = result.scalars().all()
    return [_approval_from_model(m) for m in rows]


async def get_approval_by_id(session: AsyncSession, approval_id: str) -> ApprovalRequest | None:
    result = await session.execute(
        select(ApprovalRequestModel).where(ApprovalRequestModel.id == approval_id)
    )
    model = result.scalar_one_or_none()
    return _approval_from_model(model) if model else None


async def query_approvals(
    session: AsyncSession,
    status: str | None = None,
    agent_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ApprovalRequest]:
    query = select(ApprovalRequestModel).order_by(ApprovalRequestModel.requested_at.desc())
    if status:
        query = query.where(ApprovalRequestModel.status == status)
    if agent_id:
        query = query.where(ApprovalRequestModel.agent_id == agent_id)
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    rows = result.scalars().all()
    return [_approval_from_model(m) for m in rows]


async def get_overdue_approvals(session: AsyncSession) -> list[ApprovalRequest]:
    now = datetime.now(UTC)
    result = await session.execute(
        select(ApprovalRequestModel)
        .where(ApprovalRequestModel.status == ApprovalStatus.PENDING.value)
        .where(
            ApprovalRequestModel.requested_at
            + timedelta(seconds=ApprovalRequestModel.timeout_seconds)
            < now
        )
    )
    rows = result.scalars().all()
    return [_approval_from_model(m) for m in rows]


async def get_agent_count(session: AsyncSession) -> int:
    result = await session.execute(
        select(AuditEntryModel.agent_id).distinct()
    )
    return len(result.scalars().all())


async def get_recent_audit_entries(session: AsyncSession, limit: int = 50) -> list[AuditEntry]:
    return await query_audit_logs(session, limit=limit)


# -- Model converters --


def _policy_from_model(m: PolicyModel) -> Policy:
    return Policy(
        id=m.id,
        name=m.name,
        version=m.version,
        description=m.description,
        trust_level=m.trust_level,
        environment=m.environment,
        default_decision=Decision(m.default_decision),
        rules=[_rule_from_model(r) for r in m.rules],
        created_at=m.created_at,
        updated_at=m.updated_at,
        active=m.active,
    )


def _rule_from_model(m: RuleModel) -> Rule:
    from guardweave.core.models import RuleMatch
    return Rule(
        id=m.id,
        description=m.description,
        match=RuleMatch(**m.match_json) if m.match_json else RuleMatch(),
        decision=Decision(m.decision),
        risk_score_modifier=m.risk_score_modifier,
        reason=m.reason,
    )


def _audit_from_model(m: AuditEntryModel) -> AuditEntry:
    from guardweave.core.enums import Capability, Decision, RiskLevel
    return AuditEntry(
        id=m.id,
        timestamp=m.timestamp,
        agent_id=m.agent_id,
        session_id=m.session_id,
        action=m.action,
        capability=Capability(m.capability),
        target=m.target,
        decision=Decision(m.decision),
        risk_score=m.risk_score,
        risk_level=RiskLevel(m.risk_level),
        policy_id=m.policy_id,
        rule_id=m.rule_id,
        reason=m.reason,
        context=m.context,
        chain_hash=m.chain_hash,
        previous_hash=m.previous_hash,
        metadata=m.metadata_json,
    )


def _approval_from_model(m: ApprovalRequestModel) -> ApprovalRequest:
    from guardweave.core.enums import Capability, RiskLevel
    return ApprovalRequest(
        id=m.id,
        agent_id=m.agent_id,
        session_id=m.session_id,
        action=m.action,
        capability=Capability(m.capability),
        target=m.target,
        risk_score=m.risk_score,
        risk_level=RiskLevel(m.risk_level),
        context=m.context,
        status=ApprovalStatus(m.status),
        requested_at=m.requested_at,
        decided_at=m.decided_at,
        decided_by=m.decided_by,
        feedback=m.feedback,
        escalation_level=m.escalation_level,
        timeout_seconds=m.timeout_seconds,
        policy_id=m.policy_id,
    )
