from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from guardweave.core.models import ApprovalRequest

logger = logging.getLogger("guardweave.hitl")


class NotificationHook:
    def __init__(self):
        self._pending_hooks: list[Callable[[ApprovalRequest], Any]] = []
        self._decision_hooks: list[Callable[[ApprovalRequest], Any]] = []
        self._escalation_hooks: list[Callable[[ApprovalRequest], Any]] = []

    def on_pending(self, hook: Callable[[ApprovalRequest], Any]) -> None:
        self._pending_hooks.append(hook)

    def on_decision(self, hook: Callable[[ApprovalRequest], Any]) -> None:
        self._decision_hooks.append(hook)

    def on_escalation(self, hook: Callable[[ApprovalRequest], Any]) -> None:
        self._escalation_hooks.append(hook)

    async def notify_pending(self, req: ApprovalRequest) -> None:
        logger.info(
            "Approval pending: action=%s capability=%s agent=%s risk=%d",
            req.action, req.capability.value, req.agent_id, req.risk_score,
        )
        for hook in self._pending_hooks:
            try:
                result = hook(req)
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.error("Pending notification hook failed: %s", e)

    async def notify_decision(self, req: ApprovalRequest) -> None:
        logger.info(
            "Approval decision: id=%s status=%s by=%s feedback=%s",
            req.id, req.status.value, req.decided_by, req.feedback,
        )
        for hook in self._decision_hooks:
            try:
                result = hook(req)
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.error("Decision notification hook failed: %s", e)

    async def notify_escalation(self, req: ApprovalRequest) -> None:
        logger.warning(
            "Approval escalated: id=%s level=%d agent=%s action=%s",
            req.id, req.escalation_level, req.agent_id, req.action,
        )
        for hook in self._escalation_hooks:
            try:
                result = hook(req)
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.error("Escalation notification hook failed: %s", e)
