from __future__ import annotations

from datetime import UTC

import gradio as gr

from guardweave.dashboard.state import get_session_factory
from guardweave.persistence.repositories import (
    get_agent_count,
    get_pending_approvals,
    get_recent_audit_entries,
)


def build_monitor_tab() -> gr.Blocks:
    with gr.Blocks() as monitor:
        gr.Markdown("## Agent Monitor", elem_id="monitor-header")

        with gr.Row():
            with gr.Column(scale=1):
                agent_count_box = gr.Number(
                    label="Active Agents",
                    value=0,
                    interactive=False,
                    elem_id="agent-count",
                )
            with gr.Column(scale=1):
                pending_count_box = gr.Number(
                    label="Pending Approvals",
                    value=0,
                    interactive=False,
                    elem_id="pending-count",
                )
            with gr.Column(scale=1):
                latest_risk_box = gr.Number(
                    label="Latest Risk Score",
                    value=0,
                    interactive=False,
                    elem_id="latest-risk",
                )

        recent_logs = gr.Dataframe(
            headers=["Time", "Agent", "Action", "Capability", "Decision", "Risk"],
            label="Recent Activity",
            interactive=False,
            every=5,
        )

        refresh_btn = gr.Button("Refresh", variant="primary", size="sm")

        async def refresh_monitor():
            factory = get_session_factory()
            async with factory() as session:
                agent_count = await get_agent_count(session)
                pending = await get_pending_approvals(session)
                recent = await get_recent_audit_entries(session, limit=20)

            rows = []
            latest_risk = 0
            for entry in recent:
                ts = entry.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                rows.append([
                    ts.strftime("%H:%M:%S"),
                    entry.agent_id[:12],
                    entry.action[:30],
                    entry.capability.value if hasattr(entry.capability, "value") else str(entry.capability),
                    entry.decision.value.upper() if hasattr(entry.decision, "value") else str(entry.decision).upper(),
                    f"{entry.risk_score} ({entry.risk_level.value})",
                ])
                if entry.risk_score > latest_risk:
                    latest_risk = entry.risk_score

            return agent_count, len(pending), latest_risk, rows

        refresh_btn.click(
            fn=refresh_monitor,
            inputs=[],
            outputs=[agent_count_box, pending_count_box, latest_risk_box, recent_logs],
        )

        monitor.load(
            fn=refresh_monitor,
            inputs=[],
            outputs=[agent_count_box, pending_count_box, latest_risk_box, recent_logs],
        )

    return monitor
