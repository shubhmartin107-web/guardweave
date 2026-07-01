from __future__ import annotations

import gradio as gr


def create_theme() -> gr.Theme:
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="neutral",
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        body_background_fill="#0f1117",
        body_background_fill_dark="#0f1117",
        block_background_fill="#1a1d27",
        block_background_fill_dark="#1a1d27",
        block_border_width="0",
        block_shadow="*shadow_drop",
        button_primary_background_fill="#2563eb",
        button_primary_background_fill_hover="#1d4ed8",
        button_primary_text_color="white",
        button_secondary_background_fill="#2d3040",
        button_secondary_background_fill_hover="#3d4050",
        input_background_fill="#1a1d27",
        input_background_fill_dark="#1a1d27",
        input_border_color="#2d3040",
        input_border_color_focus="#2563eb",
        border_color_accent="#2563eb",
        border_color_primary="#2d3040",
        background_fill_primary="#0f1117",
        background_fill_secondary="#1a1d27",
        color_accent_soft="#1e293b",
        body_text_color="#cbd5e1",
        body_text_color_subdued="#64748b",
    )
