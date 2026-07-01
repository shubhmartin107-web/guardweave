from __future__ import annotations

import gradio as gr

from guardweave.core.enums import TrustLevel
from guardweave.dashboard.state import get_session_factory
from guardweave.engine.policy_parser import load_policy_from_yaml
from guardweave.persistence.repositories import (
    delete_policy,
    list_policies,
    save_policy,
)


def build_policies_tab() -> gr.Blocks:
    with gr.Blocks() as policies_tab:
        gr.Markdown("## Policy Management", elem_id="policies-header")

        with gr.Row():
            with gr.Column(scale=2):
                policy_list = gr.Dataframe(
                    headers=["ID", "Name", "Version", "Trust Level", "Environment", "Active", "Rules"],
                    label="Policies",
                    interactive=False,
                    row_count=10,
                )
            with gr.Column(scale=1):
                refresh_list_btn = gr.Button("Refresh List", variant="secondary", size="sm")
                delete_btn = gr.Button("Delete Selected", variant="stop", size="sm")
                policy_id_to_delete = gr.Textbox(label="Policy ID to Delete", placeholder="Enter policy ID...")

        gr.Markdown("### Create / Edit Policy")
        with gr.Row():
            policy_name = gr.Textbox(label="Policy Name", placeholder="my-policy", scale=1)
            policy_version = gr.Textbox(label="Version", value="1.0", scale=1)
            trust_level = gr.Dropdown(
                label="Trust Level",
                choices=["sandbox", "low", "medium", "high", "critical"],
                value="medium",
                scale=1,
            )
            environment = gr.Dropdown(
                label="Environment",
                choices=["development", "staging", "production"],
                value="development",
                scale=1,
            )

        yaml_editor = gr.Code(
            label="Policy YAML",
            language="yaml",
            value="",
            lines=20,
        )

        with gr.Row():
            save_btn = gr.Button("Save Policy", variant="primary", size="sm")
            load_example_btn = gr.Button("Load Default Example", variant="secondary", size="sm")
            status_box = gr.Textbox(label="Status", interactive=False)

        async def refresh_policy_list():
            factory = get_session_factory()
            async with factory() as session:
                policies = await list_policies(session)
            rows = []
            for p in policies:
                rows.append([
                    p.id,
                    p.name,
                    p.version,
                    p.trust_level.value if hasattr(p.trust_level, 'value') else str(p.trust_level),
                    p.environment,
                    "Yes" if p.active else "No",
                    str(len(p.rules)),
                ])
            return rows

        async def save_new_policy(name: str, version: str, trust: str, env: str, yaml_text: str) -> str:
            if not name or not yaml_text.strip():
                return "Name and YAML content required"

            try:
                policy = load_policy_from_yaml(yaml_text)
                policy.name = name
                policy.version = version if version else "1.0"
                policy.trust_level = TrustLevel(trust)
                policy.environment = env

                factory = get_session_factory()
                async with factory() as session:
                    await save_policy(session, policy)
                return f"Policy '{name}' saved (id: {policy.id})"
            except (ValueError, OSError) as e:
                return f"Error: {e}"

        async def delete_selected(policy_id: str) -> str:
            if not policy_id:
                return "No policy ID provided"
            factory = get_session_factory()
            async with factory() as session:
                ok = await delete_policy(session, policy_id)
            return f"Deleted: {policy_id}" if ok else f"Policy not found: {policy_id}"

        async def load_example():
            try:
                from pathlib import Path
                example = Path(__file__).parents[3] / "policies" / "default.yaml"
                if example.exists():
                    return example.read_text()
            except OSError:
                pass
            return """name: example-policy
version: "1.0"
description: "An example policy"
trust_level: medium
environment: development
default_decision: ask
rules:
  - id: rule_1
    description: "Allow file reads"
    match:
      capabilities: ["file:read"]
    decision: allow
    reason: "Reads are safe"
"""

        refresh_list_btn.click(fn=refresh_policy_list, inputs=[], outputs=[policy_list])
        save_btn.click(fn=save_new_policy, inputs=[policy_name, policy_version, trust_level, environment, yaml_editor], outputs=[status_box])
        delete_btn.click(fn=delete_selected, inputs=[policy_id_to_delete], outputs=[status_box])
        load_example_btn.click(fn=load_example, inputs=[], outputs=[yaml_editor])
        policies_tab.load(fn=refresh_policy_list, inputs=[], outputs=[policy_list])

    return policies_tab
