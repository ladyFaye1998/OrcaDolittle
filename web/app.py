"""Gradio demo for OrcaDolittle.

Five tabs:

* **Perceive** — upload an orca clip, see the inferred state.
* **Generate** — synthesise candidate calls conditioned on a target state.
* **Select** — listener clip in, chosen broadcast out, with per-candidate scores.
* **Predict** — listener clip + stimulus in, predicted response distribution out.
* **Closed loop** — full Dolittle pass on a sample or live OrcaSound clip.

The Space is built on top of :mod:`orcadolittle` and inherits the same
configuration interfaces.
"""
from __future__ import annotations

import json
from pathlib import Path

import gradio as gr
import numpy as np

from orcadolittle import generate, perceive, predict, select
from orcadolittle.config import ECOTYPES, SAMPLE_RATE
from orcadolittle.core.generate import GeneratedCall
from orcadolittle.core.perceive import CONTEXTS, ListenerState
from orcadolittle.data.context_mapping import calltype_vocab
from web.theme import orcadolittle_theme

TITLE = "OrcaDolittle"
SUBTITLE = (
    "A Doctor Dolittle stack for killer whales — perceive · generate · "
    "select · anticipate."
)

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _state_to_payload(state: ListenerState) -> dict[str, object]:
    return {
        "ecotype": state.ecotype,
        "ecotype_probs": state.ecotype_probs,
        "call_type": state.call_type,
        "call_type_topk": state.call_type_topk,
        "context": state.context,
        "confidence": state.confidence,
    }


def _audio_in(audio: tuple[int, np.ndarray] | None) -> np.ndarray | None:
    if audio is None:
        return None
    sr, data = audio
    if data.dtype != np.float32:
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    if data.ndim == 2:
        data = data.mean(axis=1)
    if sr != SAMPLE_RATE:
        try:
            import librosa
        except ImportError:
            return data
        data = librosa.resample(data, orig_sr=sr, target_sr=SAMPLE_RATE)
    return data.astype(np.float32)


def perceive_handler(audio):
    waveform = _audio_in(audio)
    if waveform is None:
        return "Upload a clip first.", json.dumps({}, indent=2)
    state = perceive(waveform)
    return state.__repr__(), json.dumps(_state_to_payload(state), indent=2)


def generate_handler(ecotype, call_type, context, n, temperature):
    state = ListenerState(
        ecotype=ecotype,
        ecotype_probs={ecotype: 1.0},
        call_type=call_type,
        call_type_topk=[(call_type, 1.0)],
        context=context,
        embedding=np.zeros(768, dtype=np.float32),
        confidence="high",
    )
    candidates = generate(state, n=int(n), call_type=call_type, temperature=float(temperature))
    audios = [(SAMPLE_RATE, c.waveform) for c in candidates]
    return audios


def select_handler(audio, policy, n):
    waveform = _audio_in(audio)
    if waveform is None:
        return "Upload a clip first.", None, "{}"
    state = perceive(waveform)
    candidates = generate(state, n=int(n))
    chosen = select(state, candidates, policy=policy)
    payload = {
        "policy": chosen.policy,
        "score": chosen.score,
        "rank": chosen.rank,
        "n_candidates": len(candidates),
        "call_type": chosen.call.call_type,
        "ecotype": chosen.call.ecotype,
        "context": chosen.call.context,
    }
    return state.__repr__(), (SAMPLE_RATE, chosen.waveform), json.dumps(payload, indent=2)


def predict_handler(audio, stimulus):
    waveform = _audio_in(audio)
    stim_wave = _audio_in(stimulus)
    if waveform is None or stim_wave is None:
        return "Upload both a listener clip and a stimulus.", "{}"
    state = perceive(waveform)
    stim = GeneratedCall(
        waveform=stim_wave.astype(np.float32),
        sample_rate=SAMPLE_RATE,
        ecotype=state.ecotype,
        call_type=state.call_type,
        context=state.context,
        latent=np.zeros(64, dtype=np.float32),
        in_distribution=True,
    )
    prediction = predict(state, stim)
    payload = {
        "summary": prediction.summary(),
        "response_probs": prediction.response_probs,
        "counterfactual_shuffled": prediction.counterfactual_shuffled,
        "counterfactual_scrambled": prediction.counterfactual_scrambled,
        "counterfactual_delta": prediction.counterfactual_delta,
        "confidence": prediction.confidence,
    }
    return prediction.summary(), json.dumps(payload, indent=2)


def loop_handler(audio, policy):
    waveform = _audio_in(audio)
    if waveform is None:
        return "Upload a clip first.", None, "{}"
    from orcadolittle.core.pipeline import run_loop

    result = run_loop(waveform, policy=policy)
    payload = {
        "state": result.state.__repr__(),
        "chosen_call_type": result.chosen.call.call_type,
        "prediction": result.prediction.summary(),
        "policy": policy,
    }
    return (
        result.prediction.summary(),
        (SAMPLE_RATE, result.chosen.waveform),
        json.dumps(payload, indent=2),
    )


with gr.Blocks(
    theme=orcadolittle_theme(),
    title=TITLE,
    css="""
    .orca-header { text-align: center; padding: 1.5rem 0 0.5rem; }
    .orca-header h1 { color: #c9a84c; font-weight: 500; letter-spacing: 0.03em; margin: 0; }
    .orca-header p { color: #bcae95; font-style: italic; margin: 0.5rem 0 0; }
    """,
) as demo:
    gr.HTML(
        f"""
        <div class='orca-header'>
            <h1>{TITLE}</h1>
            <p>{SUBTITLE}</p>
        </div>
        """,
    )

    with gr.Tabs():
        with gr.Tab("Perceive"):
            with gr.Row():
                p_audio = gr.Audio(label="Orca recording", type="numpy")
                p_state = gr.Textbox(label="State", lines=2)
            p_json = gr.Code(label="Full state JSON", language="json")
            p_btn = gr.Button("Perceive", variant="primary")
            p_btn.click(perceive_handler, [p_audio], [p_state, p_json])

        with gr.Tab("Generate"):
            with gr.Row():
                g_ecotype = gr.Dropdown(list(ECOTYPES), value="resident", label="Ecotype")
                g_calltype = gr.Dropdown(calltype_vocab("resident"), value="N04", label="Call type")
                g_context = gr.Dropdown(list(CONTEXTS), value="socialising", label="Context")
            with gr.Row():
                g_n = gr.Slider(1, 16, value=4, step=1, label="Candidates")
                g_temp = gr.Slider(0.1, 2.0, value=1.0, step=0.05, label="Temperature")
            g_audios = gr.Gallery(label="Generated candidates")
            g_btn = gr.Button("Generate", variant="primary")
            g_btn.click(
                generate_handler,
                [g_ecotype, g_calltype, g_context, g_n, g_temp],
                [g_audios],
            )

        with gr.Tab("Select"):
            with gr.Row():
                s_audio = gr.Audio(label="Listener clip", type="numpy")
                s_policy = gr.Dropdown(
                    ["thompson", "greedy", "uniform", "abstain"],
                    value="thompson", label="Policy",
                )
                s_n = gr.Slider(1, 16, value=8, step=1, label="Candidates")
            s_state = gr.Textbox(label="Listener state", lines=2)
            s_chosen = gr.Audio(label="Chosen broadcast", type="numpy")
            s_payload = gr.Code(label="Selection details", language="json")
            s_btn = gr.Button("Select", variant="primary")
            s_btn.click(select_handler, [s_audio, s_policy, s_n], [s_state, s_chosen, s_payload])

        with gr.Tab("Predict"):
            with gr.Row():
                pr_audio = gr.Audio(label="Listener clip", type="numpy")
                pr_stim = gr.Audio(label="Proposed stimulus", type="numpy")
            pr_summary = gr.Textbox(label="Summary", lines=2)
            pr_payload = gr.Code(label="Full prediction JSON", language="json")
            pr_btn = gr.Button("Predict", variant="primary")
            pr_btn.click(predict_handler, [pr_audio, pr_stim], [pr_summary, pr_payload])

        with gr.Tab("Closed loop"):
            with gr.Row():
                l_audio = gr.Audio(label="Listener clip (or OrcaSound capture)", type="numpy")
                l_policy = gr.Dropdown(
                    ["thompson", "greedy", "uniform", "abstain"],
                    value="thompson", label="Policy",
                )
            l_summary = gr.Textbox(label="Summary", lines=2)
            l_audio_out = gr.Audio(label="Broadcast-ready waveform", type="numpy")
            l_payload = gr.Code(label="Loop result JSON", language="json")
            l_btn = gr.Button("Run one closed-loop pass", variant="primary")
            l_btn.click(loop_handler, [l_audio, l_policy], [l_summary, l_audio_out, l_payload])

    gr.Markdown(
        """
        ---
        OrcaDolittle is a Coller-Dolittle 2026–27 submission. The full
        repository, documentation, and Docker image are on
        [GitHub](https://github.com/ladyFaye1998/OrcaDolittle).
        """,
    )


if __name__ == "__main__":
    demo.launch()
