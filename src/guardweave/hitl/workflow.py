from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from guardweave.core.enums import ApprovalStatus
from guardweave.core.models import ActionContext, ApprovalRequest, PolicyEvaluationResult
from guardweave.hitl.escalation import EscalationHandler
from guardweave.hitl.notifications import NotificationHook
from guardweave.hitl.webhooks import WebhookNotifier
from guardweave.persistence.repositories import (
    get_approval_by_id,
    get_overdue_approvals,
    get_pending_approvals,
    query_approvals,
    save_approval_request,
    update_approval_status,
)


class ApprovalWorkflow:
    def __init__(
        self,
        escalation_handler: EscalationHandler | None = None,
        notification_hook: NotificationHook | None = None,
        webhook_urls: list[str] | None = None,
    ):
        self._escalation = escalation_handler or EscalationHandler()
        self._notifications = notification_hook or NotificationHook()  # type: ignore[no-untyped-call]
        self._webhooks = WebhookNotifier(webhook_urls)
        self._timeout_task: asyncio.Task[Any] | None = None
        self._running = False

    def add_webhook(self, url: str) -> None:
        self._webhooks.add_url(url)

    async def batch_approve(
        self,
        session: AsyncSession,
        approval_ids: list[str],
        decided_by: str = "dashboard",
        feedback: str | None = None,
    ) -> list[ApprovalRequest | None]:
        results: list[ApprovalRequest | None] = []
        for aid in approval_ids:
            req = await self.approve(session, aid, decided_by=decided_by, feedback=feedback)
            results.append(req)
        return results

    async def batch_deny(
        self,
        session: AsyncSession,
        approval_ids: list[str],
        decided_by: str = "dashboard",
        feedback: str | None = None,
    ) -> list[ApprovalRequest | None]:
        results: list[ApprovalRequest | None] = []
        for aid in approval_ids:
            req = await self.deny(session, aid, decided_by=decided_by, feedback=feedback)
            results.append(req)
        return results

    async def request_approval(
        self,
        session: AsyncSession,
        context: ActionContext,
        result: PolicyEvaluationResult,
        timeout_seconds: int = 300,
        metadata: dict[str, Any] | None = None,
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            agent_id=context.agent_id,
            session_id=context.session_id,
            action=context.action,
            capability=context.capability,
            target=context.target,
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            context=context.model_dump(exclude_none=True),
            status=ApprovalStatus.PENDING,
            requested_at=datetime.now(UTC),
            timeout_seconds=timeout_seconds,
            policy_id=result.policy_id,
        )

        await save_approval_request(session, req)
        await self._notifications.notify_pending(req)
        await self._webhooks.notify_pending(req)
        return req

    async def approve(
        self,
        session: AsyncSession,
        approval_id: str,
        decided_by: str = "dashboard",
        feedback: str | None = None,
    ) -> ApprovalRequest | None:
        req = await update_approval_status(
            session,
            approval_id,
            ApprovalStatus.APPROVED,
            decided_by=decided_by,
            feedback=feedback,
        )
        if req:
            await self._notifications.notify_decision(req)
            await self._webhooks.notify_decision(req)
        return req

    async def deny(
        self,
        session: AsyncSession,
        approval_id: str,
        decided_by: str = "dashboard",
        feedback: str | None = None,
    ) -> ApprovalRequest | None:
        req = await update_approval_status(
            session,
            approval_id,
            ApprovalStatus.DENIED,
            decided_by=decided_by,
            feedback=feedback,
        )
        if req:
            await self._notifications.notify_decision(req)
        return req

    async def get_pending(self, session: AsyncSession) -> list[ApprovalRequest]:
        return await get_pending_approvals(session)

    async def get_by_id(self, session: AsyncSession, approval_id: str) -> ApprovalRequest | None:
        return await get_approval_by_id(session, approval_id)

    async def query(
        self,
        session: AsyncSession,
        status: str | None = None,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ApprovalRequest]:
        return await query_approvals(session, status=status, agent_id=agent_id, limit=limit, offset=offset)

    async def process_timeouts(self, session: AsyncSession) -> list[ApprovalRequest | None]:
        overdue = await get_overdue_approvals(session)
        processed = []
        for req in overdue:
            decision = self._escalation.handle_timeout(req)
            if decision == ApprovalStatus.ESCALATED:
                escalated_req = await update_approval_status(
                    session, req.id, ApprovalStatus.ESCALATED,
                    decided_by="system",
                    feedback=f"Auto-escalated (level {req.escalation_level + 1})",
                )
                if escalated_req:
                    await self._notifications.notify_escalation(escalated_req)
                processed.append(escalated_req)
            else:
                timeout_status = ApprovalStatus.TIMED_OUT if decision == ApprovalStatus.TIMED_OUT else ApprovalStatus.DENIED
                timed_out_req = await update_approval_status(
                    session, req.id, timeout_status,
                    decided_by="system",
                    feedback=f"Auto-{timeout_status.value} due to timeout",
                )
                if timed_out_req:
                    await self._notifications.notify_decision(timed_out_req)
                processed.append(timed_out_req)
        return processed

    async def get_approval_count(self, session: AsyncSession) -> int:
        pending = await get_pending_approvals(session)
        return len(pending)
