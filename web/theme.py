"""A dark editorial Gradio theme matching the OrcaDolittle palette."""
from __future__ import annotations

import gradio as gr


def orcadolittle_theme() -> gr.themes.Base:
    """Return the OrcaDolittle Gradio theme."""
    return gr.themes.Base(
        primary_hue=gr.themes.Color(
            c50="#fef9ec", c100="#fbeec5", c200="#f5dc94",
            c300="#eec869", c400="#e3b346", c500="#c9a84c",
            c600="#a98935", c700="#876c25", c800="#5b481a",
            c900="#3a2f12", c950="#1a1714",
        ),
        secondary_hue="amber",
        neutral_hue=gr.themes.Color(
            c50="#e8e0d4", c100="#d9cfbe", c200="#bcae95",
            c300="#9b8d72", c400="#7a6e57", c500="#5a4f3e",
            c600="#3d342a", c700="#28221b", c800="#1a1714",
            c900="#0d0b0a", c950="#070605",
        ),
        font=[gr.themes.GoogleFont("Lora"), "ui-serif", "Georgia", "serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
    ).set(
        body_background_fill="#0d1117",
        body_text_color="#e8e0d4",
        block_background_fill="#1a1714",
        block_border_color="#3d342a",
        block_label_text_color="#c9a84c",
        button_primary_background_fill="#c9a84c",
        button_primary_background_fill_hover="#e3b346",
        button_primary_text_color="#1a1714",
        button_secondary_background_fill="#28221b",
        button_secondary_background_fill_hover="#3d342a",
        button_secondary_text_color="#e8e0d4",
    )
