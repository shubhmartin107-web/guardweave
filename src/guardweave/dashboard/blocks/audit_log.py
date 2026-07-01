from __future__ import annotations

from datetime import UTC

import gradio as gr

from guardweave.dashboard.state import get_session_factory
from guardweave.persistence.repositories import query_audit_logs


def build_audit_log_tab() -> gr.Blocks:
    with gr.Blocks() as audit_log_tab:
        gr.Markdown("## Audit Log", elem_id="audit-log-header")

        with gr.Row():
            filter_agent = gr.Textbox(label="Filter by Agent ID", placeholder="All agents...", scale=1)
            filter_capability = gr.Dropdown(
                label="Filter by Capability",
                choices=["All", "file:read", "file:write", "file:delete", "shell",
                         "code:exec", "network:http", "secrets:access", "db:read", "db:write"],
                value="All",
                scale=1,
            )
            filter_decision = gr.Dropdown(
                label="Filter by Decision",
                choices=["All", "allow", "deny", "ask"],
                value="All",
                scale=1,
            )
            limit_slider = gr.Slider(label="Entries", minimum=10, maximum=500, value=100, step=10, scale=1)

        refresh_btn = gr.Button("Search", variant="primary", size="sm")

        log_table = gr.Dataframe(
            headers=[
                "Time", "Agent", "Session", "Action", "Capability",
                "Target", "Decision", "Risk", "Policy", "Rule",
            ],
            label="Audit Entries",
            interactive=False,
            row_count=20,
            wrap=True,
        )

        row_count_display = gr.Number(label="Results", value=0, interactive=False)

        async def search_logs(agent: str, capability: str, decision: str, limit: int) -> tuple[list[list[str]], int]:
            factory = get_session_factory()
            cap = None if capability == "All" else capability
            dec = None if decision == "All" else decision
            agent_id = agent if agent.strip() else None

            async with factory() as session:
                entries = await query_audit_logs(
                    session,
                    agent_id=agent_id,
                    capability=cap,
                    decision=dec,
                    limit=limit,
                )

            rows = []
            for e in entries:
                ts = e.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
                rows.append([
                    ts.strftime("%Y-%m-%d %H:%M:%S"),
                    e.agent_id[:12],
                    e.session_id[:10],
                    e.action[:25],
                    e.capability.value if hasattr(e.capability, "value") else str(e.capability),
                    e.target[:35] if e.target else "",
                    e.decision.value.upper() if hasattr(e.decision, "value") else str(e.decision).upper(),
                    f"{e.risk_score} ({e.risk_level.value})",
                    e.policy_id[:12],
                    e.rule_id[:12] if e.rule_id else "",
                ])
            return rows, len(rows)

        refresh_btn.click(
            fn=search_logs,
            inputs=[filter_agent, filter_capability, filter_decision, limit_slider],
            outputs=[log_table, row_count_display],
        )

        audit_log_tab.load(
            fn=search_logs,
            inputs=[filter_agent, filter_capability, filter_decision, limit_slider],
            outputs=[log_table, row_count_display],
        )

    return audit_log_tab
