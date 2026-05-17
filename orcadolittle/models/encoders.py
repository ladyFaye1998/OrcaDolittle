"""Self-supervised audio-encoder loaders.

We default to AVES2 (:data:`orcadolittle.config.ENCODER_REPOS["aves2-bio"]`),
which Earth Species Project ships as a BEATs-backbone supervised-finetuned
checkpoint specialised for bioacoustics. Perch 2.0 is supported as an
alternative — see Hamer et al. 2025 for the marine-transfer evidence.

The encode function returns a *time-mean* embedding by default; callers that
need frame-level features should call :func:`encode_frames`.
"""
from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

import numpy as np

from orcadolittle.config import ENCODER_REPOS, RuntimeConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray


EMBEDDING_DIM: dict[str, int] = {
    "aves2-bio": 768,
    "aves2-all": 768,
    "aves": 768,
    "perch-2.0": 1280,
}


@functools.lru_cache(maxsize=4)
def _load_encoder(repo_id: str, device: str) -> Any:
    """Load and cache the encoder; deferred so import is cheap."""
    try:
        import torch
        from transformers import AutoModel
    except ImportError as exc:
        msg = (
            "Encoder loading requires torch and transformers. "
            "Install via `pip install orcadolittle[all]`."
        )
        raise ImportError(msg) from exc

    model = AutoModel.from_pretrained(repo_id, trust_remote_code=True)
    target_device = _resolve_device(device, torch)
    model = model.to(target_device).eval()
    return model


def _resolve_device(spec: str, torch_module: Any) -> str:
    if spec != "auto":
        return spec
    if torch_module.cuda.is_available():
        return "cuda"
    if getattr(torch_module.backends, "mps", None) and torch_module.backends.mps.is_available():
        return "mps"
    return "cpu"


def encode(
    audio: NDArray[np.float32],
    *,
    runtime: RuntimeConfig | None = None,
) -> NDArray[np.float32]:
    """Encode a waveform to a single time-mean embedding vector.

    Falls back to a zero vector when the encoder cannot be loaded (no network,
    no weights cached, missing torch). Callers that require a real encoding
    should call :func:`encode_or_raise` instead.
    """
    runtime = runtime or RuntimeConfig()
    dim = EMBEDDING_DIM.get(runtime.encoder, 768)
    repo_id = ENCODER_REPOS.get(runtime.encoder)

    if repo_id is None:
        msg = f"Unknown encoder: {runtime.encoder!r}. Known: {list(ENCODER_REPOS)}"
        raise ValueError(msg)

    try:
        import torch
    except ImportError:
        return np.zeros((dim,), dtype=np.float32)

    try:
        model = _load_encoder(repo_id, runtime.device)
    except Exception:
        return np.zeros((dim,), dtype=np.float32)

    device = next(model.parameters()).device
    with torch.inference_mode():
        x = torch.from_numpy(audio.astype(np.float32)).to(device).unsqueeze(0)
        out = model(x)
        feats = out.last_hidden_state if hasattr(out, "last_hidden_state") else out
        embedding = feats.mean(dim=1).squeeze(0).cpu().numpy()
    return embedding.astype(np.float32)


def encode_frames(
    audio: NDArray[np.float32],
    *,
    runtime: RuntimeConfig | None = None,
) -> NDArray[np.float32]:
    """Encode a waveform to a (T, D) frame-level embedding tensor."""
    runtime = runtime or RuntimeConfig()
    dim = EMBEDDING_DIM.get(runtime.encoder, 768)
    repo_id = ENCODER_REPOS.get(runtime.encoder)

    if repo_id is None:
        msg = f"Unknown encoder: {runtime.encoder!r}"
        raise ValueError(msg)

    try:
        import torch
    except ImportError:
        return np.zeros((1, dim), dtype=np.float32)

    model = _load_encoder(repo_id, runtime.device)
    device = next(model.parameters()).device
    with torch.inference_mode():
        x = torch.from_numpy(audio.astype(np.float32)).to(device).unsqueeze(0)
        out = model(x)
        feats = out.last_hidden_state if hasattr(out, "last_hidden_state") else out
        frames = feats.squeeze(0).cpu().numpy()
    return frames.astype(np.float32)
