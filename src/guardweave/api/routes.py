from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from guardweave.core.models import ActionContext
from guardweave.engine.evaluator import PolicyEvaluator
from guardweave.engine.policy_parser import load_policy_from_yaml
from guardweave.hitl.workflow import ApprovalWorkflow
from guardweave.persistence.repositories import (
    get_pending_approvals,
    list_policies,
    load_policy_by_id,
    query_audit_logs,
    save_policy,
)

router = APIRouter(prefix="/api/v1")


# -- Policy endpoints --


@router.get("/policies")
async def api_list_policies() -> list[dict[str, Any]]:
    from guardweave.persistence.database import get_session_factory
    factory = get_session_factory()
    async with factory() as session:
        policies = await list_policies(session)
    return [p.model_dump() for p in policies]


@router.get("/policies/{policy_id}")
async def api_get_policy(policy_id: str) -> dict[str, Any]:
    from guardweave.persistence.database import get_session_factory
    factory = get_session_factory()
    async with factory() as session:
        policy = await load_policy_by_id(session, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy.model_dump()


@router.post("/policies")
async def api_create_policy(data: dict[str, Any]) -> dict[str, Any]:
    policy = load_policy_from_yaml(data.get("yaml", ""))
    from guardweave.persistence.database import get_session_factory
    factory = get_session_factory()
    async with factory() as session:
        saved = await save_policy(session, policy)
    return saved.model_dump()


# -- Action evaluation --


@router.post("/evaluate")
async def api_evaluate_action(data: dict[str, Any]) -> dict[str, Any]:
    from guardweave.persistence.database import get_session_factory
    factory = get_session_factory()
    evaluator = PolicyEvaluator()

    async with factory() as session:
        policies = await list_policies(session)
        for p in policies:
            evaluator.add_policy(p)

    context = ActionContext(**data)
    policy = evaluator.get_policy()
    result = evaluator.evaluate(context, policy=policy)
    return result.model_dump()


# -- Audit logs --


@router.get("/audit")
async def api_query_audit(
    agent_id: str | None = None,
    capability: str | None = None,
    decision: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    from guardweave.persistence.database import get_session_factory
    factory = get_session_factory()
    async with factory() as session:
        entries = await query_audit_logs(
            session,
            agent_id=agent_id,
            capability=capability,
            decision=decision,
            limit=limit,
        )
    return [e.model_dump() for e in entries]


# -- Approvals --


@router.get("/approvals/pending")
async def api_pending_approvals() -> list[dict[str, Any]]:
    from guardweave.persistence.database import get_session_factory
    factory = get_session_factory()
    async with factory() as session:
        pending = await get_pending_approvals(session)
    return [r.model_dump() for r in pending]


@router.post("/approvals/{approval_id}/approve")
async def api_approve(approval_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    from guardweave.persistence.database import get_session_factory
    factory = get_session_factory()
    workflow = ApprovalWorkflow()
    feedback = (data or {}).get("feedback")
    async with factory() as session:
        req = await workflow.approve(session, approval_id, decided_by="api", feedback=feedback)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return req.model_dump()


@router.post("/approvals/{approval_id}/deny")
async def api_deny(approval_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    from guardweave.persistence.database import get_session_factory
    factory = get_session_factory()
    workflow = ApprovalWorkflow()
    feedback = (data or {}).get("feedback")
    async with factory() as session:
        req = await workflow.deny(session, approval_id, decided_by="api", feedback=feedback)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return req.model_dump()


# -- Health --


@router.get("/health")
async def api_health() -> dict[str, str]:
    return {"status": "ok", "service": "guardweave"}
