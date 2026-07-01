from __future__ import annotations

import logging
from typing import Any

import httpx

from guardweave.core.models import ApprovalRequest

logger = logging.getLogger("guardweave.hitl.webhooks")


class WebhookNotifier:
    def __init__(self, webhook_urls: list[str] | None = None):
        self._urls: list[str] = webhook_urls or []
        self._client = httpx.AsyncClient(timeout=10.0)

    def add_url(self, url: str) -> None:
        if url not in self._urls:
            self._urls.append(url)

    def remove_url(self, url: str) -> None:
        self._urls = [u for u in self._urls if u != url]

    async def notify_pending(self, req: ApprovalRequest) -> None:
        payload = self._build_payload("approval.pending", req)
        await self._dispatch(payload)

    async def notify_decision(self, req: ApprovalRequest) -> None:
        status = "approved" if req.status.value == "approved" else "denied"
        payload = self._build_payload(f"approval.{status}", req)
        await self._dispatch(payload)

    async def notify_escalation(self, req: ApprovalRequest) -> None:
        payload = self._build_payload("approval.escalated", req)
        await self._dispatch(payload)

    async def _dispatch(self, payload: dict[str, Any]) -> None:
        for url in self._urls:
            try:
                response = await self._client.post(url, json=payload)
                response.raise_for_status()
                logger.debug("Webhook sent to %s (status=%d)", url, response.status_code)
            except Exception as e:
                logger.warning("Webhook failed for %s: %s", url, e)

    def _build_payload(self, event: str, req: ApprovalRequest) -> dict[str, Any]:
        return {
            "event": event,
            "id": req.id,
            "agent_id": req.agent_id,
            "session_id": req.session_id,
            "action": req.action,
            "capability": req.capability.value if hasattr(req.capability, "value") else str(req.capability),
            "target": req.target,
            "risk_score": req.risk_score,
            "risk_level": req.risk_level.value if hasattr(req.risk_level, "value") else str(req.risk_level),
            "status": req.status.value,
            "requested_at": req.requested_at.isoformat() if req.requested_at else None,
            "decided_at": req.decided_at.isoformat() if req.decided_at else None,
            "decided_by": req.decided_by,
            "feedback": req.feedback,
            "escalation_level": req.escalation_level,
        }

    async def close(self) -> None:
        await self._client.aclose()


class SlackWebhookFormatter:
    @staticmethod
    def format_pending(req: ApprovalRequest) -> dict[str, Any]:
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "GuardWeave: Approval Required"},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Agent:*\n{req.agent_id}"},
                        {"type": "mrkdwn", "text": f"*Action:*\n{req.action}"},
                        {"type": "mrkdwn", "text": f"*Capability:*\n{req.capability.value}"},
                        {"type": "mrkdwn", "text": f"*Risk:*\n{req.risk_score} ({req.risk_level.value})"},
                        {"type": "mrkdwn", "text": f"*Target:*\n`{req.target}`"},
                        {"type": "mrkdwn", "text": f"*ID:*\n`{req.id[:16]}`"},
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Approve"},
                            "style": "primary",
                            "url": f"http://localhost:7860/?approval_id={req.id}",
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Deny"},
                            "style": "danger",
                            "url": f"http://localhost:7860/?deny_id={req.id}",
                        },
                    ],
                },
            ],
        }
