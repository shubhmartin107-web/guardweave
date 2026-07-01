from __future__ import annotations

import logging
from typing import Any

import gradio as gr

from guardweave.dashboard.blocks.approvals import build_approvals_tab
from guardweave.dashboard.blocks.audit_log import build_audit_log_tab
from guardweave.dashboard.blocks.monitor import build_monitor_tab
from guardweave.dashboard.blocks.policies import build_policies_tab
from guardweave.dashboard.blocks.settings import build_settings_tab
from guardweave.dashboard.theme import create_theme

logger = logging.getLogger("guardweave.dashboard")


def create_dashboard(theme: Any = None) -> gr.Blocks:
    if theme is None:
        theme = create_theme()

    with gr.Blocks(
        title="GuardWeave Dashboard",
    ) as dashboard:
        gr.HTML(HEADER_HTML)

        with gr.Tabs(elem_id="gw-tabs"):
            with gr.Tab("Monitor", elem_id="tab-monitor"):
                monitor = build_monitor_tab()
                monitor.render()

            with gr.Tab("Approvals", elem_id="tab-approvals"):
                approvals = build_approvals_tab()
                approvals.render()

            with gr.Tab("Policies", elem_id="tab-policies"):
                policies = build_policies_tab()
                policies.render()

            with gr.Tab("Audit Log", elem_id="tab-audit"):
                audit = build_audit_log_tab()
                audit.render()

            with gr.Tab("Settings", elem_id="tab-settings"):
                settings = build_settings_tab()
                settings.render()

    return dashboard


CSS = """
#gw-tabs { border: none; }
#gw-tabs .tab-nav button {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: #64748b;
    font-weight: 500;
    padding: 8px 16px;
    margin-right: 4px;
    transition: all 0.2s;
}
#gw-tabs .tab-nav button:hover {
    color: #e2e8f0;
    border-bottom-color: #475569;
}
#gw-tabs .tab-nav button.selected {
    color: #60a5fa;
    border-bottom-color: #2563eb;
}
.gw-header {
    padding: 16px 24px;
    border-bottom: 1px solid #1e293b;
}
.gw-header h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.gw-header p {
    margin: 4px 0 0 0;
    color: #64748b;
    font-size: 13px;
}
"""

HEADER_HTML = """
<div class="gw-header">
    <h1>GuardWeave</h1>
    <p>Safety, Guardrails &amp; Governance Layer for AI Agents</p>
</div>
"""
