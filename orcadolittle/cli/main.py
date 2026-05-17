"""Command-line entry point — ``orcadolittle ...``.

The CLI mirrors the Python API. Heavy lifting is delegated to the modules
in :mod:`orcadolittle.core` and :mod:`orcadolittle.benchmarks`.
"""
from __future__ import annotations

import json
from pathlib import Path

import click

from orcadolittle import __version__


@click.group()
@click.version_option(__version__, prog_name="orcadolittle")
def cli() -> None:
    """OrcaDolittle — a Doctor Dolittle stack for killer whales."""


@cli.command()
@click.argument("audio", type=click.Path(exists=True, path_type=Path))
@click.option("--top-k", "top_k", type=int, default=5, show_default=True)
@click.option("--encoder", default="aves2-bio", show_default=True)
def perceive(audio: Path, top_k: int, encoder: str) -> None:
    """Encode an audio file and infer ecotype · call type · context."""
    from orcadolittle import load_audio
    from orcadolittle.config import RuntimeConfig
    from orcadolittle.core.perceive import perceive as _perceive

    waveform = load_audio(audio)
    state = _perceive(waveform, top_k=top_k, config=RuntimeConfig(encoder=encoder))
    click.echo(
        json.dumps(
            {
                "ecotype": state.ecotype,
                "ecotype_probs": state.ecotype_probs,
                "call_type": state.call_type,
                "call_type_topk": state.call_type_topk,
                "context": state.context,
                "confidence": state.confidence,
            },
            indent=2,
        ),
    )


@cli.command()
@click.option("--ecotype", default="resident", show_default=True,
              type=click.Choice(["resident", "biggs", "offshore"]))
@click.option("--call-type", default="N04", show_default=True)
@click.option("--context", default="socialising", show_default=True)
@click.option("--n", type=int, default=8, show_default=True)
@click.option("--temperature", type=float, default=1.0, show_default=True)
@click.option("--output-dir", type=click.Path(path_type=Path), default=Path("./out"))
def generate(
    ecotype: str,
    call_type: str,
    context: str,
    n: int,
    temperature: float,
    output_dir: Path,
) -> None:
    """Generate *n* candidate calls without first listening."""
    import numpy as np

    from orcadolittle.core.generate import generate as _generate
    from orcadolittle.core.perceive import ListenerState

    state = ListenerState(
        ecotype=ecotype,
        ecotype_probs={ecotype: 1.0},
        call_type=call_type,
        call_type_topk=[(call_type, 1.0)],
        context=context,
        embedding=np.zeros(768, dtype=np.float32),
        confidence="high",
    )
    candidates = _generate(state, n=n, call_type=call_type, temperature=temperature)
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(candidates):
        p = output_dir / f"candidate_{i:02d}.wav"
        c.save(str(p))
        click.echo(str(p))


@cli.command()
@click.argument("audio", type=click.Path(exists=True, path_type=Path))
@click.option("--policy", default="thompson", show_default=True,
              type=click.Choice(["thompson", "greedy", "uniform", "abstain"]))
@click.option("--n-candidates", type=int, default=8, show_default=True)
def select(audio: Path, policy: str, n_candidates: int) -> None:
    """Listen → generate → select. Prints the chosen candidate metadata."""
    from orcadolittle import load_audio
    from orcadolittle.core.generate import generate as _generate
    from orcadolittle.core.perceive import perceive as _perceive
    from orcadolittle.core.select import select as _select

    state = _perceive(load_audio(audio))
    candidates = _generate(state, n=n_candidates)
    chosen = _select(state, candidates, policy=policy)
    click.echo(
        json.dumps(
            {
                "policy": chosen.policy,
                "score": chosen.score,
                "rank": chosen.rank,
                "call_type": chosen.call.call_type,
                "ecotype": chosen.call.ecotype,
                "context": chosen.call.context,
                "n_candidates": len(candidates),
            },
            indent=2,
        ),
    )


@cli.command()
@click.argument("audio", type=click.Path(exists=True, path_type=Path))
@click.argument("stimulus", type=click.Path(exists=True, path_type=Path))
@click.option("--report", "report_path", type=click.Path(path_type=Path),
              default=Path("trial_report.html"))
def predict(audio: Path, stimulus: Path, report_path: Path) -> None:
    """Predict the response to a stimulus given a listener clip."""
    import numpy as np

    from orcadolittle import load_audio
    from orcadolittle.core.generate import GeneratedCall
    from orcadolittle.core.perceive import perceive as _perceive
    from orcadolittle.core.predict import predict as _predict

    state = _perceive(load_audio(audio))
    stim_audio = load_audio(stimulus)
    call = GeneratedCall(
        waveform=stim_audio.astype(np.float32),
        sample_rate=16_000,
        ecotype=state.ecotype,
        call_type=state.call_type,
        context=state.context,
        latent=np.zeros(64, dtype=np.float32),
        in_distribution=True,
    )
    prediction = _predict(state, call)
    prediction.report(str(report_path))
    click.echo(prediction.summary())
    click.echo(f"report → {report_path}")


@cli.command(name="loop")
@click.option("--hydrophone", required=True, help="Path or URL to the input stream")
@click.option("--dry-run/--live", default=True, show_default=True)
@click.option("--broadcast-path", type=click.Path(path_type=Path), default=None)
@click.option("--policy", default="thompson", show_default=True)
def loop_cmd(hydrophone: str, dry_run: bool, broadcast_path: Path | None, policy: str) -> None:
    """Run one closed-loop pass against a recording or live stream."""
    from orcadolittle import load_audio
    from orcadolittle.core.pipeline import run_loop

    audio = load_audio(hydrophone)
    result = run_loop(
        audio,
        policy=policy,
        dry_run=dry_run,
        broadcast_path=str(broadcast_path) if broadcast_path else None,
    )
    click.echo(
        json.dumps(
            {
                "state": str(result.state),
                "chosen_call_type": result.chosen.call.call_type,
                "prediction": result.prediction.summary(),
                "broadcast_path": result.broadcast_path,
            },
            indent=2,
        ),
    )


@cli.command()
@click.option("--component",
              type=click.Choice(["perceive", "generate", "select", "predict", "all"]),
              default="all", show_default=True)
def benchmark(component: str) -> None:
    """Run reproducible component benchmarks."""
    from orcadolittle.benchmarks import (
        generate_eval,
        perceive_eval,
        predict_eval,
        run_all,
        select_eval,
    )

    if component == "all":
        results = run_all.run_all()
    else:
        runner = {
            "perceive": perceive_eval.run,
            "generate": generate_eval.run,
            "select": select_eval.run,
            "predict": predict_eval.run,
        }[component]
        results = {component: runner()}
    click.echo(json.dumps(results, indent=2, default=str))


@cli.command()
def demo() -> None:
    """Launch the Gradio web demo locally."""
    try:
        from web.app import demo as _demo
    except ImportError as exc:
        msg = "Demo requires `pip install orcadolittle[web]`"
        raise click.ClickException(msg) from exc
    _demo.launch()


if __name__ == "__main__":
    cli()
