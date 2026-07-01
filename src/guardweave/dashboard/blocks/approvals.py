from __future__ import annotations

import gradio as gr

from guardweave.dashboard.state import get_session_factory, get_workflow
from guardweave.persistence.repositories import get_pending_approvals


def build_approvals_tab() -> gr.Blocks:
    workflow = get_workflow()

    with gr.Blocks() as approvals_tab:
        gr.Markdown("## Approval Queue", elem_id="approvals-header")
        gr.Markdown("Review and respond to pending action requests from agents.")

        pending_table = gr.Dataframe(
            headers=[
                "ID", "Agent", "Action", "Capability", "Target",
                "Risk Score", "Risk Level", "Requested At", "Timeout (s)",
            ],
            label="Pending Approvals",
            interactive=False,
            row_count=10,
        )

        with gr.Row():
            approval_id_input = gr.Textbox(
                label="Approval ID",
                placeholder="Paste an approval ID to act on it...",
                scale=3,
            )
            with gr.Column(scale=1):
                approve_btn = gr.Button("Approve", variant="primary", size="sm")
                deny_btn = gr.Button("Deny", variant="stop", size="sm")

        feedback_input = gr.Textbox(
            label="Feedback (optional)",
            placeholder="Add context for your decision...",
            lines=2,
        )

        status_output = gr.Textbox(label="Status", interactive=False)

        refresh_btn = gr.Button("Refresh", variant="secondary", size="sm")

        async def refresh_pending():
            factory = get_session_factory()
            async with factory() as session:
                pending = await get_pending_approvals(session)

            rows = []
            for req in pending:
                ts = req.requested_at.strftime("%Y-%m-%d %H:%M:%S") if req.requested_at else ""
                rows.append([
                    req.id,
                    req.agent_id[:12],
                    req.action[:25],
                    req.capability.value if hasattr(req.capability, "value") else str(req.capability),
                    req.target[:30],
                    str(req.risk_score),
                    req.risk_level.value if hasattr(req.risk_level, "value") else str(req.risk_level),
                    ts,
                    str(req.timeout_seconds),
                ])
            return rows

        async def handle_approve(approval_id: str, feedback: str) -> str:
            if not approval_id:
                return "Please enter an Approval ID"
            factory = get_session_factory()
            async with factory() as session:
                req = await workflow.approve(session, approval_id, decided_by="dashboard", feedback=feedback or None)
            if req:
                return f"Approved: {req.id}"
            return f"Approval request not found: {approval_id}"

        async def handle_deny(approval_id: str, feedback: str) -> str:
            if not approval_id:
                return "Please enter an Approval ID"
            factory = get_session_factory()
            async with factory() as session:
                req = await workflow.deny(session, approval_id, decided_by="dashboard", feedback=feedback or None)
            if req:
                return f"Denied: {req.id}"
            return f"Approval request not found: {approval_id}"

        refresh_btn.click(fn=refresh_pending, inputs=[], outputs=[pending_table])
        approve_btn.click(fn=handle_approve, inputs=[approval_id_input, feedback_input], outputs=[status_output])
        deny_btn.click(fn=handle_deny, inputs=[approval_id_input, feedback_input], outputs=[status_output])
        approvals_tab.load(fn=refresh_pending, inputs=[], outputs=[pending_table])

    return approvals_tab
