from __future__ import annotations

import gradio as gr

from guardweave.persistence.database import get_db_path, get_session_factory


def build_settings_tab() -> gr.Blocks:
    with gr.Blocks() as settings_tab:
        gr.Markdown("## Settings", elem_id="settings-header")

        with gr.Group():
            gr.Markdown("### Database Configuration")
            gr.Textbox(
                label="Database Path",
                value=str(get_db_path()),
                interactive=False,
            )
            gr.Markdown(
                "Set `GUARDWEAVE_DB_PATH` environment variable to change the database location."
            )

        with gr.Group():
            gr.Markdown("### About GuardWeave")
            gr.Markdown(
                """
**GuardWeave** is an open-source Safety, Guardrails & Governance Layer for AI Agents.

- **Version:** 0.1.0
- **License:** MIT
- **Documentation:** [guardweave.ai](https://guardweave.ai)
                """
            )

        with gr.Group():
            gr.Markdown("### Quick Actions")
            with gr.Row():
                verify_audit_btn = gr.Button("Verify Audit Chain Integrity", variant="secondary", size="sm")
                verify_status = gr.Textbox(label="Result", interactive=False)

            async def verify_integrity():
                from guardweave.audit.logger import AuditLogger
                factory = get_session_factory()
                async with factory() as session:
                    logger = AuditLogger()
                    ok = await logger.verify_integrity(session)
                if ok:
                    return "Chain integrity verified: ALL ENTITIES VALID"
                return "Chain integrity BROKEN: possible tampering detected!"

            verify_audit_btn.click(fn=verify_integrity, inputs=[], outputs=[verify_status])

    return settings_tab
