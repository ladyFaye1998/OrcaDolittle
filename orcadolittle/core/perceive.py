"""State inference: an arbitrary orca recording is encoded and classified
into ecotype · call type · inferred behavioural context.

The encoder is a frozen self-supervised foundation model (AVES2 or Perch 2.0
by default). Three small linear heads sit on top: ecotype (3-way), call type
(roughly 70-way for Northeast Pacific dialects), and a context-inference
mapping derived from the published call-type / context literature.

Calibrated uncertainty is reported per head so that the downstream
selection policy can decline to act when the listener state is poorly
identified.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from orcadolittle.config import CONFIDENCE_TIERS, ECOTYPES, RuntimeConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray

CONTEXTS: tuple[str, ...] = ("foraging", "travel", "socialising", "alarm", "unknown")


@dataclass(frozen=True)
class ListenerState:
    """A typed snapshot of what the listening side believes about the animals.

    Attributes
    ----------
    ecotype:
        Argmax ecotype prediction ("resident" / "biggs" / "offshore") with
        per-class probabilities in :attr:`ecotype_probs`.
    call_type:
        Top-1 dialect call type identifier (e.g. ``"N04"`` for the Northeast
        Pacific resident call type).
    call_type_topk:
        Top-k call-type predictions, sorted by probability descending.
    context:
        Inferred behavioural context (from the call-type → context mapping
        in :mod:`orcadolittle.data.context_mapping`).
    embedding:
        Time-mean foundation-encoder embedding for this clip; the same
        vector is consumed downstream by the selection and prediction
        components.
    confidence:
        IPCC-style confidence tier for the joint state inference.
    """

    ecotype: str
    ecotype_probs: dict[str, float]
    call_type: str
    call_type_topk: list[tuple[str, float]]
    context: str
    embedding: NDArray[np.float32]
    confidence: str = "medium"
    metadata: dict[str, object] = field(default_factory=dict)

    def __repr__(self) -> str:
        return (
            f"ListenerState(ecotype={self.ecotype!r} "
            f"({self.ecotype_probs.get(self.ecotype, 0.0):.2f}), "
            f"call_type={self.call_type!r}, context={self.context!r}, "
            f"confidence={self.confidence!r})"
        )


def perceive(
    audio: NDArray[np.float32],
    *,
    config: RuntimeConfig | None = None,
    top_k: int = 5,
) -> ListenerState:
    """Run the perception stack on a single audio clip.

    Parameters
    ----------
    audio:
        Mono waveform at :data:`orcadolittle.config.SAMPLE_RATE` (16 kHz),
        floating point in [-1.0, 1.0].
    config:
        Optional runtime configuration overriding the defaults.
    top_k:
        Number of top-call-type predictions to return alongside the argmax.

    Returns
    -------
    ListenerState
        A frozen dataclass describing the inferred state.
    """
    from orcadolittle.data.context_mapping import calltype_to_context, calltype_vocab
    from orcadolittle.models.encoders import encode

    runtime = config or RuntimeConfig()
    embedding = encode(audio, runtime=runtime)

    ecotype_probs = _ecotype_head(embedding)
    ecotype = max(ecotype_probs, key=ecotype_probs.get)

    calltype_probs = _calltype_head(embedding, vocab=calltype_vocab(ecotype))
    calltype_topk = sorted(calltype_probs.items(), key=lambda kv: -kv[1])[:top_k]
    call_type = calltype_topk[0][0]

    context = calltype_to_context(call_type, ecotype=ecotype, default="unknown")

    confidence = _confidence_tier(
        ecotype_p=ecotype_probs[ecotype],
        calltype_p=calltype_topk[0][1],
    )

    return ListenerState(
        ecotype=ecotype,
        ecotype_probs=ecotype_probs,
        call_type=call_type,
        call_type_topk=calltype_topk,
        context=context,
        embedding=embedding,
        confidence=confidence,
        metadata={"encoder": runtime.encoder},
    )


def _ecotype_head(_embedding: NDArray[np.float32]) -> dict[str, float]:
    """Linear ecotype head — trained on DCLDE 2026.

    Scaffold: returns a uniform distribution until the head is loaded from
    :data:`orcadolittle.config.WEIGHTS_ROOT`. The trained head is a logistic
    regression over the encoder embedding with class-balanced weights.
    """
    return {e: 1.0 / len(ECOTYPES) for e in ECOTYPES}


def _calltype_head(
    _embedding: NDArray[np.float32],
    vocab: list[str],
) -> dict[str, float]:
    """Linear call-type head — trained on DCLDE 2026 per ecotype.

    Scaffold: uniform over the supplied vocabulary until the head is loaded.
    """
    if not vocab:
        return {"unknown": 1.0}
    p = 1.0 / len(vocab)
    return {ct: p for ct in vocab}


def _confidence_tier(*, ecotype_p: float, calltype_p: float) -> str:
    """Map joint posterior into the five-way IPCC-style tiers."""
    joint = ecotype_p * calltype_p
    if joint >= 0.50:
        return CONFIDENCE_TIERS[0]
    if joint >= 0.25:
        return CONFIDENCE_TIERS[1]
    if joint >= 0.10:
        return CONFIDENCE_TIERS[2]
    if joint >= 0.03:
        return CONFIDENCE_TIERS[3]
    return CONFIDENCE_TIERS[4]
