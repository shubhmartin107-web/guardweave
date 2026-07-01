from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from guardweave.engine.evaluator import PolicyEvaluator
from guardweave.hitl.workflow import ApprovalWorkflow

_evaluator: PolicyEvaluator | None = None
_workflow: ApprovalWorkflow | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    from guardweave.persistence.database import get_session_factory as _get_factory
    return _get_factory()


def get_evaluator() -> PolicyEvaluator:
    global _evaluator
    if _evaluator is None:
        _evaluator = PolicyEvaluator()
    return _evaluator


def get_workflow() -> ApprovalWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = ApprovalWorkflow()
    return _workflow


def set_evaluator(evaluator: PolicyEvaluator) -> None:
    global _evaluator
    _evaluator = evaluator


def set_workflow(workflow: ApprovalWorkflow) -> None:
    global _workflow
    _workflow = workflow
