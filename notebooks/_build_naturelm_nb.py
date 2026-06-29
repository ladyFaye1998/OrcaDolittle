#!/usr/bin/env python3
"""Generate notebooks/naturelm_audio_comparison_colab.ipynb.

The notebook is intentionally self-contained for Colab: it installs NatureLM-audio,
uses the fine-tuned audio encoder inside the model, and runs the two primary
second-encoder comparison analyses.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).parent / "naturelm_audio_comparison_colab.ipynb"


def md(src: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": src.strip("\n").splitlines(keepends=True),
    }


def code(src: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": src.strip("\n").splitlines(keepends=True),
    }


cells: list[dict] = []

cells.append(md(r"""
# 🐋 NatureLM-audio second-encoder analysis

This notebook evaluates whether the primary audio-embedding findings are stable under
a second frozen audio encoder, NatureLM-audio.

## Scope

The notebook runs two bounded analyses:

1. **Catalogue call types:** site-controlled SRKW/NRKW call-type classification and
   VFPA -> SMRU transfer for shared SRKW calls.
2. **FEROP playback-dialect space:** separability of public Kamchatka K-type catalogue
   exemplars in the NatureLM-audio embedding space.

## Boundary

The outputs are evidence for representation-level structure only. They are not claims
about semantic meaning, translation, intent, syntax, or playback causality.

## Run modes

Use **Runtime -> Change runtime type -> GPU**, then run the cells top to bottom.

- 🏁 `FULL_ANALYSIS`: full data with permutation tests enabled.
- ⚡ `FULL_FAST`: full data with observed-model metrics only.
- 🧪 `SMOKE_TEST`: small setup check; not an analysis result.

Outputs are cached in Google Drive at `MyDrive/OrcaDolittle_naturelm`, so disconnects
do not erase downloaded resources, embeddings, reports, or figures.
"""))

cells.append(code(r"""
#@title 1. Install base dependencies, check GPU, mount Drive
!pip -q install -U huggingface_hub librosa soundfile scikit-learn pandas matplotlib tqdm requests

import os
import json
import platform
import sys
from pathlib import Path
from IPython.display import Markdown, display
import torch

def show_box(title, body):
    display(Markdown(f"### {title}\n{body}"))

print("torch", torch.__version__, "| CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    print("GPU:", gpu_name)
    show_box("✅ GPU detected", f"`{gpu_name}` is ready for NatureLM-audio.")
else:
    show_box("⚠️ No GPU detected", "Set **Runtime -> Change runtime type -> GPU** before running the encoder cells.")

try:
    from google.colab import drive
    drive.mount("/content/drive")
except Exception as e:
    raise RuntimeError(
        "Google Drive mount is required for this notebook so the NatureLM model cache, "
        "audio cache, embeddings, reports, and figures survive Colab disconnects."
    ) from e

OUTDIR = Path("/content/drive/MyDrive/OrcaDolittle_naturelm")

DIRS = {
    "audio": OUTDIR / "audio_cache",
    "playback": OUTDIR / "playback",
    "embeddings": OUTDIR / "embeddings",
    "reports": OUTDIR / "reports",
    "figures": OUTDIR / "figures",
    "repos": OUTDIR / "_repos",
    "hf": OUTDIR / "_hf_cache",
}
for d in [OUTDIR, *DIRS.values()]:
    d.mkdir(parents=True, exist_ok=True)

# Persist the heavy Hugging Face downloads to Drive rather than Colab's session disk.
os.environ["HF_HOME"] = str(DIRS["hf"])
os.environ["HF_HUB_CACHE"] = str(DIRS["hf"] / "hub")
os.environ["TRANSFORMERS_CACHE"] = str(DIRS["hf"] / "transformers")
os.environ["XDG_CACHE_HOME"] = str(OUTDIR / "_cache")
for key in ["HF_HOME", "HF_HUB_CACHE", "TRANSFORMERS_CACHE", "XDG_CACHE_HOME"]:
    Path(os.environ[key]).mkdir(parents=True, exist_ok=True)

print("Outputs:", OUTDIR)
print("Persistent HF cache:", os.environ["HF_HOME"])
ENV_INFO = {
    "python": sys.version,
    "platform": platform.platform(),
    "torch": torch.__version__,
    "cuda_available": bool(torch.cuda.is_available()),
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}
(DIRS["reports"] / "naturelm_environment.json").write_text(json.dumps(ENV_INFO, indent=2))
show_box("📁 Persistent cache ready", f"All large files will survive session resets under `{OUTDIR}`.")
"""))

cells.append(code(r"""
#@title 2. Authenticate if needed and install pinned NatureLM-audio code
# This notebook loads only the audio encoder weights, not the Llama text generator.
# A token is optional unless Hugging Face asks for authentication in your session.
import shutil
import subprocess
import sys
from getpass import getpass
from huggingface_hub import login, whoami

token = os.environ.get("HF_TOKEN", "").strip()
if not token:
    token = getpass("Optional Hugging Face read token (press Enter to skip): ").strip()
if token:
    os.environ["HF_TOKEN"] = token
    try:
        login(token=token, add_to_git_credential=False)
        print("HF user:", whoami(token=token).get("name"))
    except Exception as e:
        print("WARNING: Hugging Face token was not accepted; continuing without auth:", e)
        os.environ.pop("HF_TOKEN", None)
else:
    print("No Hugging Face token supplied; continuing with public model files.")

RUNTIME_PACKAGES = [
    "safetensors>=0.4.0",
]
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *RUNTIME_PACKAGES])

NATURELM_COMMIT = "c708df7a4cc294ca8d4aaf0498794b5674ce20b1"
NATURELM_DIR = DIRS["repos"] / "NatureLM-audio"

def ensure_naturelm_repo(repo_dir, commit):
    # The source repo is small. Refresh it each setup run to avoid stale/corrupt
    # Drive-backed git state; large model/audio/embedding caches remain untouched.
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    subprocess.check_call([
        "git", "clone", "--no-tags", "https://github.com/earthspecies/NatureLM-audio.git",
        str(repo_dir)
    ])
    subprocess.check_call(["git", "-C", str(repo_dir), "checkout", "--detach", commit])

ensure_naturelm_repo(NATURELM_DIR, NATURELM_COMMIT)
print("NatureLM-audio commit:", subprocess.check_output(
    ["git", "-C", str(NATURELM_DIR), "rev-parse", "HEAD"], text=True).strip())

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--no-deps", "-e", str(NATURELM_DIR)])
if str(NATURELM_DIR) not in sys.path:
    sys.path.insert(0, str(NATURELM_DIR))
import importlib
importlib.invalidate_caches()
print("NatureLM-audio installed from", NATURELM_DIR)
"""))

cells.append(code(r"""
#@title 3. Choose the run mode
RUN_MODE = "FULL_ANALYSIS"  #@param ["FULL_ANALYSIS", "FULL_FAST", "SMOKE_TEST"]
CALLTYPE_BATCH_SIZE = 2  #@param {type:"integer"}
MIN_PER_TYPE = 30        #@param {type:"integer"}
MIN_TRANSFER_TEST = 10   #@param {type:"integer"}
FORCE_CALLTYPE_PERMUTATIONS = False  #@param {type:"boolean"}
REBUILD_CACHED_EMBEDDINGS = False    #@param {type:"boolean"}
FORCE_RECOMPUTE_MODELS = False       #@param {type:"boolean"}

TARGET_SR = 16000
MIN_DURATION_S = 1.0

if RUN_MODE == "SMOKE_TEST":
    MAX_CALLTYPE_SEGMENTS = 500
    PLAYBACK_N_PERM = 100
    CALLTYPE_N_PERM = 0
    MODE_NOTE = "🧪 Setup check only; output is not a full analysis result."
elif RUN_MODE == "FULL_ANALYSIS":
    MAX_CALLTYPE_SEGMENTS = 0
    PLAYBACK_N_PERM = 1000
    CALLTYPE_N_PERM = 200
    MODE_NOTE = "🏁 Full data with permutation tests enabled; this can take hours."
else:
    MAX_CALLTYPE_SEGMENTS = 0
    PLAYBACK_N_PERM = 300
    CALLTYPE_N_PERM = 0
    MODE_NOTE = "⚡ Full data with observed-model metrics only; call-type permutations are skipped."

if FORCE_CALLTYPE_PERMUTATIONS and CALLTYPE_N_PERM == 0:
    CALLTYPE_N_PERM = 200

RUN_CALLTYPE_PERMUTATIONS = CALLTYPE_N_PERM > 0
FULL_UNCAPPED_DATA = MAX_CALLTYPE_SEGMENTS == 0

print("🐋 NatureLM run mode:", RUN_MODE)
print(MODE_NOTE)
print({
    "full_uncapped_data": FULL_UNCAPPED_DATA,
    "max_calltype_segments": MAX_CALLTYPE_SEGMENTS,
    "calltype_batch_size": CALLTYPE_BATCH_SIZE,
    "playback_permutations": PLAYBACK_N_PERM,
    "calltype_permutations": CALLTYPE_N_PERM,
    "min_per_type": MIN_PER_TYPE,
    "min_transfer_test": MIN_TRANSFER_TEST,
    "rebuild_cached_embeddings": REBUILD_CACHED_EMBEDDINGS,
    "force_recompute_models": FORCE_RECOMPUTE_MODELS,
})

if not torch.cuda.is_available():
    print("⚠️ WARNING: You are not on GPU. Switch Runtime -> Change runtime type -> GPU before encoder runs.")
if not FULL_UNCAPPED_DATA:
    print("🧪 Smoke-test mode: output is not a full analysis result.")
elif RUN_CALLTYPE_PERMUTATIONS:
    print("⏳ Call-type permutations are enabled.")
else:
    print("⚡ Call-type permutations are skipped.")
"""))

cells.append(code(r"""
#@title 4. Load NatureLM-audio audio encoder only
import contextlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import torch
import torch.nn as nn

NATURELM_COMMIT = globals().get("NATURELM_COMMIT", "c708df7a4cc294ca8d4aaf0498794b5674ce20b1")
TARGET_SR = globals().get("TARGET_SR", 16000)
MIN_DURATION_S = globals().get("MIN_DURATION_S", 1.0)
CALLTYPE_BATCH_SIZE = globals().get("CALLTYPE_BATCH_SIZE", 2)

# Self-recovery if Cell 2 was skipped or editable install did not register.
if "OUTDIR" not in globals():
    OUTDIR = Path("/content/drive/MyDrive/OrcaDolittle_naturelm")
if "DIRS" not in globals():
    DIRS = {
        "audio": OUTDIR / "audio_cache",
        "playback": OUTDIR / "playback",
        "embeddings": OUTDIR / "embeddings",
        "reports": OUTDIR / "reports",
        "figures": OUTDIR / "figures",
        "repos": OUTDIR / "_repos",
        "hf": OUTDIR / "_hf_cache",
    }
for d in [OUTDIR, *DIRS.values()]:
    d.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(DIRS["hf"]))
os.environ.setdefault("HF_HUB_CACHE", str(DIRS["hf"] / "hub"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(DIRS["hf"] / "transformers"))
os.environ.setdefault("XDG_CACHE_HOME", str(OUTDIR / "_cache"))
for key in ["HF_HOME", "HF_HUB_CACHE", "TRANSFORMERS_CACHE", "XDG_CACHE_HOME"]:
    Path(os.environ[key]).mkdir(parents=True, exist_ok=True)

NEEDED = [
    ("huggingface_hub", "huggingface_hub"),
    ("safetensors", "safetensors>=0.4.0"),
]
missing = [pkg for module, pkg in NEEDED if importlib.util.find_spec(module) is None]
if missing:
    print("Installing missing runtime packages:", missing)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *missing])

NATURELM_DIR = globals().get("NATURELM_DIR", DIRS["repos"] / "NatureLM-audio")

def ensure_naturelm_repo(repo_dir, commit):
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    subprocess.check_call([
        "git", "clone", "--no-tags", "https://github.com/earthspecies/NatureLM-audio.git",
        str(repo_dir)
    ])
    subprocess.check_call(["git", "-C", str(repo_dir), "checkout", "--detach", commit])

ensure_naturelm_repo(NATURELM_DIR, NATURELM_COMMIT)
BEATS_IMPORT_ROOT = NATURELM_DIR / "NatureLM" / "models"
if str(BEATS_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(BEATS_IMPORT_ROOT))
importlib.invalidate_caches()

try:
    from beats.BEATs import BEATs, BEATsConfig
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--no-deps", "-e", str(NATURELM_DIR)])
    if str(BEATS_IMPORT_ROOT) not in sys.path:
        sys.path.insert(0, str(BEATS_IMPORT_ROOT))
    importlib.invalidate_caches()
    from beats.BEATs import BEATs, BEATsConfig

from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
REPO_ID = "EarthSpeciesProject/NatureLM-audio"
print("🐋 Loading NatureLM-audio audio encoder on", DEVICE)
if DEVICE == "cpu":
    print("⚠️ WARNING: CPU mode is supported for recovery, but it will be very slow. GPU is strongly recommended.")

hf_token = os.environ.get("HF_TOKEN") or None
cfg_path = hf_hub_download(REPO_ID, "config.json", cache_dir=os.environ["HF_HOME"], token=hf_token)
weights_path = hf_hub_download(REPO_ID, "model.safetensors", cache_dir=os.environ["HF_HOME"], token=hf_token)
cfg = json.loads(Path(cfg_path).read_text())

beats = BEATs(cfg=BEATsConfig(cfg["beats_cfg"]))
ln_audio = nn.LayerNorm(beats.cfg.encoder_embed_dim)
state = load_file(weights_path, device="cpu")

def state_with_prefix(prefixes):
    for prefix in prefixes:
        out = {k[len(prefix):]: v for k, v in state.items() if k.startswith(prefix)}
        if out:
            return out, prefix
    return {}, None

beats_state, beats_prefix = state_with_prefix(["beats.", "model.beats.", "base_model.model.beats."])
ln_state, ln_prefix = state_with_prefix(["ln_audio.", "model.ln_audio.", "base_model.model.ln_audio."])
if not beats_state:
    raise RuntimeError("Could not find BEATs audio-encoder weights in NatureLM checkpoint.")
missing, unexpected = beats.load_state_dict(beats_state, strict=False)
if missing:
    print("WARNING: BEATs missing keys:", missing[:8], "..." if len(missing) > 8 else "")
if unexpected:
    print("WARNING: BEATs unexpected keys:", unexpected[:8], "..." if len(unexpected) > 8 else "")
if ln_state:
    ln_audio.load_state_dict(ln_state, strict=True)
else:
    print("WARNING: no ln_audio weights found; using initialized LayerNorm.")

beats.to(DEVICE).eval()
ln_audio.to(DEVICE).eval()
for p in beats.parameters():
    p.requires_grad = False
for p in ln_audio.parameters():
    p.requires_grad = False

print("✅ Loaded NatureLM audio encoder.")
print("BEATs prefix:", beats_prefix, "| LayerNorm prefix:", ln_prefix)
MODEL_MANIFEST = {
    "repo_id": REPO_ID,
    "naturelm_source_commit": NATURELM_COMMIT,
    "device": DEVICE,
    "config_path": str(cfg_path),
    "weights_path": str(weights_path),
    "weights_bytes": int(Path(weights_path).stat().st_size),
    "beats_prefix": beats_prefix,
    "layernorm_prefix": ln_prefix,
    "representation": "fine-tuned BEATs audio encoder, frozen, mean-pooled over non-padding frames",
}
(DIRS["reports"] / "naturelm_model_manifest.json").write_text(json.dumps(MODEL_MANIFEST, indent=2))

def _pad_batch(wavs, target_sr=TARGET_SR, min_duration_s=MIN_DURATION_S):
    min_len = int(target_sr * min_duration_s)
    wavs = [np.asarray(w, dtype=np.float32).reshape(-1) for w in wavs]
    wavs = [np.pad(w, (0, max(0, min_len - len(w)))) for w in wavs]
    max_len = max(len(w) for w in wavs)
    arr = np.zeros((len(wavs), max_len), dtype=np.float32)
    pad = np.ones((len(wavs), max_len), dtype=bool)
    for i, w in enumerate(wavs):
        arr[i, :len(w)] = w
        pad[i, :len(w)] = False
    return torch.from_numpy(arr).to(DEVICE), torch.from_numpy(pad).to(DEVICE)

def encode_wavs_naturelm(wavs, batch_size=CALLTYPE_BATCH_SIZE):
    # Mean-pool the fine-tuned NatureLM-audio BEATs encoder over non-padding frames.
    out = []
    autocast = torch.autocast("cuda", dtype=torch.bfloat16) if DEVICE.startswith("cuda") else contextlib.nullcontext()
    for i in range(0, len(wavs), batch_size):
        raw, padding_mask = _pad_batch(wavs[i:i + batch_size])
        with torch.inference_mode(), autocast:
            audio_embeds, audio_pad_mask = beats(raw, padding_mask=padding_mask)
            audio_embeds = ln_audio(audio_embeds)
        valid = ~audio_pad_mask.bool()
        for j in range(audio_embeds.shape[0]):
            frames = audio_embeds[j][valid[j]]
            out.append(frames.float().mean(dim=0).cpu().numpy())
    return np.asarray(out, dtype=np.float32)
"""))

cells.append(md(r"""
## Check A: FEROP playback dialect space

This is the cheaper check. It downloads the public FEROP Kamchatka K-type catalogue,
encodes each exemplar with the NatureLM-audio audio encoder, and repeats the same
leave-one-out 1-NN purity/null test used for AVES2.
"""))

cells.append(code(r"""
#@title 5. Download FEROP catalogue and run NatureLM playback-dialect separability
import csv
import json
import re
from pathlib import Path
from urllib.parse import urljoin

import librosa
import matplotlib.pyplot as plt
import pandas as pd
import requests
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize
from tqdm.auto import tqdm

CATALOG_URL = "http://russianorca.com/sounds/catalog/index.htm"
TYPE_RE = re.compile(r"(K\d+)", re.IGNORECASE)
WAV_RE = re.compile(r'href=["\']([^"\']+\.wav)["\']', re.IGNORECASE)
PLAYBACK_AUDIO = DIRS["playback"] / "ferop_catalogue"
PLAYBACK_AUDIO.mkdir(parents=True, exist_ok=True)
PLAYBACK_MANIFEST = DIRS["playback"] / "ferop_catalogue_manifest.csv"
PLAYBACK_EMB = DIRS["embeddings"] / "naturelm_ferop_catalogue_embeddings.npz"

def download_ferop_wav(url, dest):
    # Download one FEROP exemplar, tolerating stale case-sensitive catalogue links.
    candidates = [url]
    if url.lower().endswith(".wav") and not url.endswith(".wav"):
        candidates.append(url[:-4] + ".wav")
    headers = {"User-Agent": "Mozilla/5.0"}
    for candidate in dict.fromkeys(candidates):
        try:
            r = requests.get(candidate, timeout=90, headers=headers)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            if not r.content:
                continue
            tmp = dest.with_suffix(dest.suffix + ".part")
            tmp.write_bytes(r.content)
            tmp.replace(dest)
            return candidate
        except requests.RequestException as e:
            last_error = e
    print(f"WARNING: skipping missing FEROP exemplar: {url} ({last_error if 'last_error' in locals() else '404'})")
    return None

def fetch_ferop_manifest():
    html = requests.get(CATALOG_URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"}).text
    rows, seen = [], set()
    for m in WAV_RE.finditer(html):
        href = m.group(1)
        tm = TYPE_RE.search(href)
        if not tm:
            continue
        url = urljoin(CATALOG_URL, href)
        if url in seen:
            continue
        seen.add(url)
        call_type = tm.group(1).upper()
        variant = Path(href).stem
        dest = PLAYBACK_AUDIO / f"{call_type}__{variant}.wav"
        if not dest.exists() or dest.stat().st_size == 0:
            ok_url = download_ferop_wav(url, dest)
            if ok_url is None:
                continue
            url = ok_url
        rows.append({"call_type": call_type, "variant": variant, "url": url, "local_path": str(dest)})
    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError("No FEROP exemplars downloaded; public catalogue links may be unavailable.")
    pd.DataFrame(rows).to_csv(PLAYBACK_MANIFEST, index=False)
    return out

def loo_1nn_purity(X, y):
    Xn = normalize(X)
    S = Xn @ Xn.T
    np.fill_diagonal(S, -np.inf)
    nn = np.argmax(S, axis=1)
    return float(np.mean(y == y[nn]))

if REBUILD_CACHED_EMBEDDINGS and PLAYBACK_EMB.exists():
    PLAYBACK_EMB.unlink()
    print("♻️ Rebuilding cached FEROP playback embeddings.")

if PLAYBACK_EMB.exists():
    d = np.load(PLAYBACK_EMB, allow_pickle=True)
    X = d["embeddings"].astype(np.float32)
    y = d["call_type"].astype(str)
    print("✅ Loaded cached playback embeddings:", X.shape)
else:
    man = fetch_ferop_manifest()
    print(f"📥 FEROP exemplars: {len(man)} across {man['call_type'].nunique()} call types")
    if man["call_type"].nunique() < 2:
        raise RuntimeError("Too few FEROP call types downloaded for a separability test.")
    wavs, y = [], []
    for r in tqdm(list(man.itertuples()), desc="load FEROP wavs"):
        wav, _ = librosa.load(r.local_path, sr=TARGET_SR, mono=True)
        wavs.append(wav)
        y.append(r.call_type)
    print("🧠 Encoding FEROP exemplars with NatureLM-audio...")
    X = encode_wavs_naturelm(wavs, batch_size=CALLTYPE_BATCH_SIZE)
    y = np.asarray(y, dtype=object)
    np.savez_compressed(PLAYBACK_EMB, embeddings=X, call_type=y)
    print("💾 Saved", PLAYBACK_EMB, X.shape)

counts = pd.Series(y).value_counts()
keep = counts[counts >= 2].index
m = np.isin(y, keep)
Xk, yk = X[m], y[m]
purity = loo_1nn_purity(Xk, yk)
chance = float(pd.Series(yk).value_counts(normalize=True).pow(2).sum())
rng = np.random.default_rng(0)
print(f"🔁 Running FEROP label-shuffle null: {PLAYBACK_N_PERM} permutations")
null = np.array([
    loo_1nn_purity(Xk, rng.permutation(yk))
    for _ in tqdm(range(PLAYBACK_N_PERM), desc="FEROP null")
])
pval = float((np.sum(null >= purity) + 1) / (len(null) + 1)) if len(null) else None
sil = None
try:
    sil = float(silhouette_score(Xk, yk, metric="cosine"))
except Exception:
    pass

summary = {
    "analysis": "naturelm_ferop_catalogue_calltype_separability",
    "encoder": "NatureLM-audio fine-tuned BEATs audio encoder, frozen, mean-pooled",
    "run_mode": RUN_MODE,
    "full_uncapped_data": bool(FULL_UNCAPPED_DATA),
    "n_exemplars_total": int(len(X)),
    "n_types_total": int(len(set(y))),
    "purity_test": {
        "n_exemplars": int(len(yk)),
        "n_types": int(len(keep)),
        "loo_1nn_purity": float(purity),
        "null_mean": float(null.mean()) if len(null) else None,
        "null_std": float(null.std()) if len(null) else None,
        "proportional_chance": chance,
        "n_perm": int(PLAYBACK_N_PERM),
        "pvalue": pval,
        "silhouette_cosine": sil,
    },
    "boundary": "Dialect call-type separability only; not evidence of meaning.",
}
(DIRS["reports"] / "naturelm_playback_embedding_summary.json").write_text(json.dumps(summary, indent=2))

P = PCA(n_components=2, random_state=0).fit_transform(Xk)
fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
for t in sorted(keep, key=lambda z: int(z[1:])):
    mm = yk == t
    ax[0].scatter(P[mm, 0], P[mm, 1], s=30, label=t)
null_label = f"{null.mean():.2f}" if len(null) else "not run"
p_label = f"{pval:.1e}" if pval is not None else "n/a"
ax[0].set_title(f"FEROP K-types in NatureLM-audio space\nLOO purity {purity:.2f}, null {null_label}, p={p_label}")
ax[0].set_xlabel("PC1")
ax[0].set_ylabel("PC2")
ax[0].legend(fontsize=6, ncol=2)
ax[1].hist(null, bins=40, color="lightgray", edgecolor="gray")
ax[1].axvline(purity, color="red", lw=2.5)
ax[1].set_title("Purity vs label-shuffle null")
ax[1].set_xlabel("LOO 1-NN purity")
ax[1].set_ylabel("count")
fig.tight_layout()
fig_path = DIRS["figures"] / "naturelm_playback_embedding.png"
fig.savefig(fig_path, dpi=150, bbox_inches="tight")
plt.close(fig)

print(json.dumps(summary, indent=2))
print("🖼️ Figure:", fig_path)
print("✅ FEROP check complete: separability is measured, not overclaimed as meaning.")
"""))

cells.append(md(r"""
## Check B: site-controlled DCLDE catalogue call types

This rebuilds the public DCLDE call-type manifest, streams the referenced audio files,
encodes the labelled segments with NatureLM-audio, and repeats the site-controlled
call-type probes. Runtime depends on Colab GPU and network speed. For a full analysis
run, `MAX_CALLTYPE_SEGMENTS` must be `0`.
"""))

cells.append(code(r"""
#@title 6. Build public DCLDE call-type manifest and resolve audio paths
import io
import json
import re
import urllib.parse
import urllib.request
from collections import Counter

import pandas as pd

GCS_API = "https://storage.googleapis.com/storage/v1/b/noaa-passive-bioacoustic/o"
GCS_DL = "https://storage.googleapis.com/noaa-passive-bioacoustic/"
ROOT = "dclde/2027/dclde_2027_killer_whales"
PROVIDERS_WITH_CALLTYPE = ["dfo_crp", "smru", "vfpa"]
CALLTYPE_COLS = ["call_type", "Call Type", "calltype", "CallType"]
NON_CALL = {"", "unk", "unknown", "?", "n/a", "na", "none", "nothing", "nan"}
AUDIO_EXT = (".wav", ".flac", ".aif", ".aiff")

def list_keys(prefix, suffix=None):
    out, token = [], None
    while True:
        url = f"{GCS_API}?prefix={urllib.parse.quote(prefix)}&maxResults=1000"
        if token:
            url += f"&pageToken={token}"
        d = json.load(urllib.request.urlopen(url, timeout=120))
        for it in d.get("items", []):
            name = it["name"]
            if suffix is None or name.lower().endswith(suffix):
                out.append(name)
        token = d.get("nextPageToken")
        if not token:
            break
    return out

def fetch_csv(name):
    raw = urllib.request.urlopen(GCS_DL + urllib.parse.quote(name, safe="/"), timeout=180).read()
    return pd.read_csv(io.BytesIO(raw), low_memory=False)

def normalise_call_type(val):
    s = str(val).strip()
    if s.lower() in NON_CALL:
        return None
    s = re.sub(r"\s*\(.*?\)\s*", "", s).replace(" call", "").replace("call", "").strip()
    s = s.rstrip("?").strip()
    if not s or s.lower() in NON_CALL:
        return None
    m = re.fullmatch(r"([A-Za-z]+)(\d+)([a-z]*)", s)
    if m:
        pref, num, suf = m.groups()
        s = f"{pref.upper()}{int(num):02d}{suf}"
    return s

def call_family(code):
    c = code.upper()
    return ("offshore" if c.startswith("OFF") else "NRKW" if c.startswith("N")
            else "SRKW" if c.startswith("S") else "Biggs/transient" if c.startswith("T")
            else "other")

rows = []
for pv in PROVIDERS_WITH_CALLTYPE:
    csvs = list_keys(f"{ROOT}/{pv}/annotations/", suffix=".csv")
    print(f"🔎 {pv}: {len(csvs)} annotation CSVs")
    for name in csvs:
        df = fetch_csv(name)
        col = next((c for c in CALLTYPE_COLS if c in df.columns), None)
        if col is None:
            continue
        df = df[df[col].notna()].copy()
        if df.empty:
            continue
        df["call_type"] = df[col].map(normalise_call_type)
        df = df[df["call_type"].notna()]
        for _, r in df.iterrows():
            rows.append({
                "audio_path": r.get("path", r.get("filename", "")),
                "start": r.get("start", ""),
                "end": r.get("end", ""),
                "provider": pv,
                "kw_ecotype": r.get("kw_ecotype", ""),
                "clan": r.get("clan", ""),
                "subclan": r.get("subclan", ""),
                "pod": r.get("pod", ""),
                "call_type": r["call_type"],
                "call_family": call_family(r["call_type"]),
            })

man = pd.DataFrame(rows)
print("📋 manifest rows:", len(man), "| call types:", man["call_type"].nunique())
print("by provider:", man["provider"].value_counts().to_dict())

basename_to_key = {}
for pv in sorted(man["provider"].unique()):
    keys = [k for k in list_keys(f"{ROOT}/{pv}/audio/") if k.lower().endswith(AUDIO_EXT)]
    for k in keys:
        basename_to_key[k.split("/")[-1]] = k
    print(f"🎧 {pv}: {len(keys)} audio objects indexed")

man["basename"] = man["audio_path"].astype(str).apply(lambda p: p.replace("\\", "/").split("/")[-1])
man["gcs_key"] = man["basename"].map(basename_to_key)
man["start"] = pd.to_numeric(man["start"], errors="coerce")
man["end"] = pd.to_numeric(man["end"], errors="coerce")
man = man[man["gcs_key"].notna() & man["start"].notna() & man["end"].notna()].copy()
if MAX_CALLTYPE_SEGMENTS:
    man = (man.sample(n=min(MAX_CALLTYPE_SEGMENTS, len(man)), random_state=0)
           .sort_values(["provider", "gcs_key", "start"]))
else:
    man = man.sort_values(["provider", "gcs_key", "start"])

manifest_path = DIRS["reports"] / "naturelm_calltype_manifest_resolved.csv"
man.to_csv(manifest_path, index=False)
print("✅ resolved rows:", len(man), "->", manifest_path)
print(man.groupby(["provider", "call_family"]).size())
"""))

cells.append(code(r"""
#@title 7. Encode DCLDE call-type segments with NatureLM-audio (resumable)
import librosa
import requests
import time
from tqdm.auto import tqdm

CALLTYPE_EMB = DIRS["embeddings"] / "naturelm_calltype_embeddings.npz"

if REBUILD_CACHED_EMBEDDINGS and CALLTYPE_EMB.exists():
    CALLTYPE_EMB.unlink()
    print("♻️ Rebuilding cached DCLDE call-type embeddings.")

if CALLTYPE_EMB.exists():
    d = np.load(CALLTYPE_EMB, allow_pickle=True)
    embeddings = list(d["embeddings"])
    metadata = list(d["metadata"])
    done_ids = {m["segment_id"] for m in metadata}
    print("✅ Resuming cached DCLDE embeddings:", len(embeddings), "segments")
else:
    embeddings, metadata, done_ids = [], [], set()
    print("🆕 No DCLDE embedding cache found; starting fresh.")

def download_audio_key(gcs_key):
    dest = DIRS["audio"] / Path(gcs_key).name
    if not dest.exists() or dest.stat().st_size == 0:
        url = GCS_DL + urllib.parse.quote(gcs_key, safe="/")
        tmp = dest.with_suffix(dest.suffix + ".part")
        if tmp.exists():
            tmp.unlink()
        print(f"  downloading {Path(gcs_key).name}", flush=True)
        with requests.get(url, stream=True, timeout=(30, 180)) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length") or 0)
            with open(tmp, "wb") as f, tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                desc=f"download {Path(gcs_key).name[:28]}",
                leave=False,
            ) as bar:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))
        tmp.replace(dest)
    else:
        print(f"  cached audio {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)", flush=True)
    return dest

def flush_batch(wavs, metas):
    if not wavs:
        return
    t0 = time.time()
    print(f"    encoding batch: {len(wavs)} clips", flush=True)
    Xb = encode_wavs_naturelm(wavs, batch_size=CALLTYPE_BATCH_SIZE)
    for emb, meta in zip(Xb, metas):
        embeddings.append(emb)
        metadata.append(meta)
    print(f"    encoded batch in {time.time() - t0:.1f}s; total={len(embeddings)}", flush=True)

source_groups = list(man.groupby("gcs_key"))
print(
    f"🧠 Encoding {len(man)} catalogue segments from {len(source_groups)} source files; "
    f"already cached: {len(done_ids)} segments",
    flush=True,
)

for file_i, (gcs_key, group) in enumerate(tqdm(source_groups, desc="source files"), start=1):
    group = group.sort_values("start")
    pending = [
        r for r in group.itertuples()
        if f"{r.gcs_key}|{float(r.start):.3f}|{float(r.end):.3f}|{r.call_type}" not in done_ids
    ]
    print(
        f"📄 [{file_i}/{len(source_groups)}] {Path(gcs_key).name}: "
        f"{len(group)} segments, {len(pending)} pending",
        flush=True,
    )
    if not pending:
        continue
    try:
        local = download_audio_key(gcs_key)
    except Exception as e:
        print("WARN download failed:", gcs_key, e)
        continue
    wavs, metas = [], []
    for seg_i, r in enumerate(tqdm(pending, desc="segments", leave=False), start=1):
        segment_id = f"{r.gcs_key}|{float(r.start):.3f}|{float(r.end):.3f}|{r.call_type}"
        if segment_id in done_ids:
            continue
        duration = max(float(r.end) - float(r.start), 0.05)
        try:
            wav, _ = librosa.load(local, sr=TARGET_SR, mono=True, offset=float(r.start), duration=duration)
        except Exception as e:
            print("WARN segment failed:", segment_id, e)
            continue
        wavs.append(wav)
        metas.append({
            "segment_id": segment_id,
            "gcs_key": r.gcs_key,
            "basename": r.basename,
            "provider": r.provider,
            "call_type": r.call_type,
            "call_family": r.call_family,
            "start": float(r.start),
            "end": float(r.end),
        })
        done_ids.add(segment_id)
        if len(wavs) >= CALLTYPE_BATCH_SIZE:
            flush_batch(wavs, metas)
            wavs, metas = [], []
    flush_batch(wavs, metas)
    np.savez_compressed(CALLTYPE_EMB,
                        embeddings=np.asarray(embeddings, np.float32),
                        metadata=np.asarray(metadata, dtype=object))
    print("💾 checkpoint:", len(embeddings), "segments")

X_call = np.asarray(embeddings, np.float32)
meta_call = pd.DataFrame(metadata)
print("✅ DCLDE encoding done:", X_call.shape)
print(meta_call.groupby(["provider", "call_family"]).size())
"""))

cells.append(code(r"""
#@title 8. Run site-controlled call-type models and save NatureLM summary
import json
import time

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from tqdm.auto import tqdm

CALLTYPE_MODEL_CACHE = DIRS["reports"] / f"naturelm_calltype_model_summary_{RUN_MODE.lower()}.json"
CALLTYPE_MODEL_CANONICAL = DIRS["reports"] / "naturelm_calltype_model_summary.json"
CALLTYPE_PARTIAL_CACHE = DIRS["reports"] / f"naturelm_calltype_model_checkpoint_{RUN_MODE.lower()}.json"
PERM_CHECKPOINT_DIR = DIRS["reports"] / "calltype_permutation_checkpoints"
PERM_CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

model_settings = {
    "run_mode": RUN_MODE,
    "max_calltype_segments": int(MAX_CALLTYPE_SEGMENTS),
    "full_uncapped_data": bool(FULL_UNCAPPED_DATA),
    "min_per_type": int(MIN_PER_TYPE),
    "min_transfer_test": int(MIN_TRANSFER_TEST),
    "calltype_n_perm": int(CALLTYPE_N_PERM),
    "run_calltype_permutations": bool(RUN_CALLTYPE_PERMUTATIONS),
}

def cache_matches(cached):
    return (
        cached.get("n_encoded_segments") == int(len(X_call))
        and cached.get("settings", {}) == model_settings
    )

def write_json_atomic(path, payload):
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(path)

def safe_key(label):
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(label)).strip("_")

partial_state = {
    "settings": model_settings,
    "n_encoded_segments": int(len(X_call)),
    "results": {},
}
if CALLTYPE_PARTIAL_CACHE.exists() and not FORCE_RECOMPUTE_MODELS:
    try:
        cached_partial = json.loads(CALLTYPE_PARTIAL_CACHE.read_text())
        if cache_matches(cached_partial):
            partial_state = cached_partial
            print("✅ Loaded partial model checkpoint:", CALLTYPE_PARTIAL_CACHE)
        else:
            print("♻️ Partial model checkpoint exists but settings/data changed; ignoring it.")
    except Exception as e:
        print("⚠️ Could not read partial model checkpoint; ignoring it:", e)

def get_partial_result(key):
    if FORCE_RECOMPUTE_MODELS:
        return None
    return partial_state.get("results", {}).get(key)

def store_partial_result(key, result):
    partial_state.setdefault("results", {})[key] = result
    write_json_atomic(CALLTYPE_PARTIAL_CACHE, partial_state)
    print(f"💾 checkpoint saved: {key} -> {CALLTYPE_PARTIAL_CACHE}", flush=True)

def run_or_load_result(key, label, fn):
    cached = get_partial_result(key)
    if cached is not None:
        print(f"✅ Loaded checkpointed result: {label}", flush=True)
        return cached
    result = fn()
    store_partial_result(key, result)
    return result

def clf():
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0),
    )

def run_cv_predictions(Xs, y, label):
    class_counts = pd.Series(y).value_counts()
    n_splits = min(5, int(class_counts.min()))
    if n_splits < 2:
        raise ValueError(f"{label}: fewer than two examples in at least one class after filtering")
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=0)
    yt, yp = [], []
    for fold_i, (tr, te) in enumerate(skf.split(Xs, y), start=1):
        print(f"  CV fold {fold_i}/{n_splits}: train={len(tr)}, test={len(te)}", flush=True)
        model2 = clf().fit(Xs[tr], y[tr])
        yt.append(y[te])
        yp.append(model2.predict(Xs[te]))
    return skf, np.concatenate(yt), np.concatenate(yp)

def permutation_scores(Xs, y, skf, label, cache_key):
    if not RUN_CALLTYPE_PERMUTATIONS or CALLTYPE_N_PERM <= 0:
        print("  ⏭️ permutations skipped in this mode; observed CV metrics are still saved.", flush=True)
        return np.asarray([], dtype=float)
    key = safe_key(cache_key)
    scores_path = PERM_CHECKPOINT_DIR / f"{key}_scores.npy"
    meta_path = PERM_CHECKPOINT_DIR / f"{key}_meta.json"
    perm_meta = {
        "label": str(label),
        "settings": model_settings,
        "n_samples": int(len(y)),
        "classes": sorted(map(str, set(y))),
        "target_permutations": int(CALLTYPE_N_PERM),
    }
    null = []
    if not FORCE_RECOMPUTE_MODELS and scores_path.exists() and meta_path.exists():
        try:
            cached_meta = json.loads(meta_path.read_text())
            if cached_meta == perm_meta:
                null = list(np.load(scores_path).astype(float)[:CALLTYPE_N_PERM])
                if len(null):
                    print(f"  ✅ resuming permutation checkpoint: {len(null)}/{CALLTYPE_N_PERM} -> {scores_path}", flush=True)
            else:
                print("  ♻️ permutation checkpoint settings changed; starting this null from 0", flush=True)
        except Exception as e:
            print("  ⚠️ could not load permutation checkpoint; starting this null from 0:", e, flush=True)
            null = []
    if len(null) >= CALLTYPE_N_PERM:
        print(f"  ✅ permutation checkpoint complete: {len(null)}/{CALLTYPE_N_PERM}", flush=True)
        return np.asarray(null[:CALLTYPE_N_PERM], dtype=float)

    def save_perm_checkpoint():
        tmp_scores = scores_path.with_name(scores_path.name + ".part")
        tmp_meta = meta_path.with_suffix(meta_path.suffix + ".part")
        with open(tmp_scores, "wb") as f:
            np.save(f, np.asarray(null, dtype=float))
        tmp_scores.replace(scores_path)
        tmp_meta.write_text(json.dumps(perm_meta, indent=2))
        tmp_meta.replace(meta_path)

    rng = np.random.default_rng(0)
    for _ in range(len(null)):
        rng.permutation(y)
    perm_iter = tqdm(
        range(len(null), CALLTYPE_N_PERM),
        total=CALLTYPE_N_PERM,
        initial=len(null),
        desc=f"{label} permutations",
    )
    for _ in perm_iter:
        yperm = rng.permutation(y)
        yt2, yp2 = [], []
        for tr, te in skf.split(Xs, yperm):
            model2 = clf().fit(Xs[tr], yperm[tr])
            yt2.append(yperm[te])
            yp2.append(model2.predict(Xs[te]))
        score = balanced_accuracy_score(np.concatenate(yt2), np.concatenate(yp2))
        null.append(score)
        perm_iter.set_postfix(last=f"{score:.3f}")
        save_perm_checkpoint()
    return np.asarray(null, dtype=float)

def within_provider(provider, family, min_per_type=MIN_PER_TYPE):
    t0 = time.time()
    sub = meta_call[(meta_call["provider"] == provider) & (meta_call["call_family"] == family)].copy()
    label = f"{provider} {family}"
    print(f"\n🐋 Within-provider check: provider={provider}, family={family}, raw_n={len(sub)}", flush=True)
    counts = sub["call_type"].value_counts()
    print("Raw call-type counts:", counts.to_dict(), flush=True)
    keep = counts[counts >= min_per_type].index
    sub = sub[sub["call_type"].isin(keep)]
    if sub["call_type"].nunique() < 2:
        print("  🚫 skipped: fewer than two call types after min_per_type filter", flush=True)
        return {
            "status": "skipped",
            "provider": provider,
            "family": family,
            "reason": "fewer than two call types after min_per_type filter",
            "raw_n": int(len(meta_call[(meta_call["provider"] == provider) & (meta_call["call_family"] == family)])),
        }
    idx = sub.index.to_numpy()
    Xs = X_call[idx]
    y = sub["call_type"].to_numpy()
    classes = sorted(set(y))
    print(
        f"  using n={len(sub)} clips, k={len(classes)} types, "
        f"min_per_type={min_per_type}, permutations={CALLTYPE_N_PERM if RUN_CALLTYPE_PERMUTATIONS else 0}",
        flush=True,
    )
    skf, yt, yp = run_cv_predictions(Xs, y, label)
    bal = balanced_accuracy_score(yt, yp)
    macro = f1_score(yt, yp, average="macro")
    chance = float(1 / len(classes))
    print(f"  ✅ observed balanced_accuracy={bal:.3f}, macro_f1={macro:.3f}, chance={chance:.3f}", flush=True)
    null = permutation_scores(Xs, y, skf, label, cache_key=f"within_{provider}_{family}")
    if len(null):
        perm_mean = float(null.mean())
        perm_std = float(null.std())
        perm_p = float((np.sum(null >= bal) + 1) / (len(null) + 1))
    else:
        perm_mean = None
        perm_std = None
        perm_p = None
    print(f"  done in {time.time() - t0:.1f}s", flush=True)
    return {
        "status": "ok",
        "provider": provider,
        "family": family,
        "n": int(len(sub)),
        "k_types": int(len(classes)),
        "classes": classes,
        "balanced_accuracy": float(bal),
        "macro_f1": float(macro),
        "chance_1_over_k": chance,
        "majority_baseline": float(pd.Series(y).value_counts(normalize=True).iloc[0]),
        "permutations_run": bool(len(null)),
        "n_permutations": int(len(null)),
        "permutation_mean": perm_mean,
        "permutation_std": perm_std,
        "permutation_pvalue": perm_p,
        "confusion_matrix": confusion_matrix(yt, yp, labels=classes).tolist(),
    }

def cross_provider(train_pv="vfpa", test_pv="smru", min_train=MIN_PER_TYPE, min_test=MIN_TRANSFER_TEST):
    t0 = time.time()
    print(f"\n🔁 Cross-provider transfer: train={train_pv}, test={test_pv}", flush=True)
    s = meta_call[meta_call["call_family"] == "SRKW"].copy()
    tr = s[s["provider"] == train_pv]
    te = s[s["provider"] == test_pv]
    tr_counts = tr["call_type"].value_counts()
    te_counts = te["call_type"].value_counts()
    shared = [t for t in tr_counts.index if tr_counts[t] >= min_train and te_counts.get(t, 0) >= min_test]
    print(
        f"  raw train={len(tr)}, raw test={len(te)}, shared eligible types={shared}",
        flush=True,
    )
    if len(shared) < 2:
        print("  ⚠️ skipped: insufficient shared types", flush=True)
        return {"status": "skipped", "note": "insufficient shared types", "shared_types": shared}
    tr = tr[tr["call_type"].isin(shared)]
    te = te[te["call_type"].isin(shared)]
    print(f"  fitting transfer model: n_train={len(tr)}, n_test={len(te)}, k={len(shared)}", flush=True)
    model2 = clf().fit(X_call[tr.index.to_numpy()], tr["call_type"].to_numpy())
    yt = te["call_type"].to_numpy()
    yp = model2.predict(X_call[te.index.to_numpy()])
    print(f"  transfer done in {time.time() - t0:.1f}s", flush=True)
    return {
        "status": "ok",
        "train_provider": train_pv,
        "test_provider": test_pv,
        "shared_types": shared,
        "k": int(len(shared)),
        "n_train": int(len(tr)),
        "n_test": int(len(te)),
        "transfer_balanced_accuracy": float(balanced_accuracy_score(yt, yp)),
        "transfer_macro_f1": float(f1_score(yt, yp, average="macro")),
        "chance_1_over_k": float(1 / len(shared)),
    }

print("🧾 Call-type embedding matrix:", X_call.shape, flush=True)
print("Rows by provider/family:", flush=True)
print(meta_call.groupby(["provider", "call_family"]).size(), flush=True)

summary = None
if CALLTYPE_MODEL_CACHE.exists() and not FORCE_RECOMPUTE_MODELS:
    cached = json.loads(CALLTYPE_MODEL_CACHE.read_text())
    if cache_matches(cached):
        summary = cached
        print("✅ Loaded cached model summary:", CALLTYPE_MODEL_CACHE)
    else:
        print("♻️ Model cache exists but settings/data changed; recomputing.")

if summary is None:
    srkw_vfpa = run_or_load_result(
        "within_provider_vfpa_srkw",
        "VFPA/SRKW within-provider model",
        lambda: within_provider("vfpa", "SRKW"),
    )
    nrkw_dfo = run_or_load_result(
        "within_provider_dfo_crp_nrkw",
        "DFO-CRP/NRKW within-provider model",
        lambda: within_provider("dfo_crp", "NRKW"),
    )
    transfer = run_or_load_result(
        "cross_provider_vfpa_to_smru",
        "VFPA -> SMRU transfer model",
        lambda: cross_provider(),
    )

    observed_check_passed = bool(
        FULL_UNCAPPED_DATA
        and srkw_vfpa.get("status") == "ok"
        and nrkw_dfo.get("status") == "ok"
        and srkw_vfpa["balanced_accuracy"] > srkw_vfpa["chance_1_over_k"]
        and nrkw_dfo["balanced_accuracy"] > nrkw_dfo["chance_1_over_k"]
    )
    permutation_tests_complete = bool(
        observed_check_passed
        and srkw_vfpa.get("permutation_pvalue") is not None
        and nrkw_dfo.get("permutation_pvalue") is not None
    )

    summary = {
        "analysis": "naturelm_site_controlled_calltype_classification",
        "encoder": "NatureLM-audio fine-tuned BEATs audio encoder, frozen, mean-pooled",
        "settings": model_settings,
        "run_mode": RUN_MODE,
        "max_calltype_segments": int(MAX_CALLTYPE_SEGMENTS),
        "full_analysis_run": bool(MAX_CALLTYPE_SEGMENTS == 0),
        "observed_check_passed": observed_check_passed,
        "permutation_tests_complete": permutation_tests_complete,
        "n_encoded_segments": int(len(X_call)),
        "within_provider_vfpa_srkw": srkw_vfpa,
        "within_provider_dfo_crp_nrkw": nrkw_dfo,
        "cross_provider_vfpa_to_smru": transfer,
        "boundary": "Catalogue call-type discrimination, not meaning; use only if full uncapped run completes.",
    }
    write_json_atomic(CALLTYPE_MODEL_CACHE, summary)
    write_json_atomic(CALLTYPE_MODEL_CANONICAL, summary)
    print("💾 Saved:", CALLTYPE_MODEL_CACHE)
    print("💾 Saved canonical:", CALLTYPE_MODEL_CANONICAL)
else:
    srkw_vfpa = summary["within_provider_vfpa_srkw"]
    nrkw_dfo = summary["within_provider_dfo_crp_nrkw"]
    transfer = summary["cross_provider_vfpa_to_smru"]
    write_json_atomic(CALLTYPE_MODEL_CANONICAL, summary)

print(json.dumps(summary, indent=2))

labels, vals, chance = [], [], []
for name, res in [("VFPA SRKW", srkw_vfpa), ("DFO_CRP NRKW", nrkw_dfo)]:
    if res and res.get("status") == "ok":
        labels.append(f"{name}\nwithin-site")
        vals.append(res["balanced_accuracy"])
        chance.append(res["chance_1_over_k"])
if transfer and "transfer_balanced_accuracy" in transfer:
    labels.append("VFPA->SMRU\ntransfer")
    vals.append(transfer["transfer_balanced_accuracy"])
    chance.append(transfer["chance_1_over_k"])

if labels:
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    xs = np.arange(len(labels))
    ax.bar(xs, vals, color="#2a7fb8", width=0.55, label="balanced accuracy")
    ax.plot(xs, chance, "r_", markersize=34, markeredgewidth=3, label="chance")
    ax.set_xticks(xs)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    ax.set_ylabel("balanced accuracy")
    ax.set_title("NatureLM-audio headline call-type checks")
    for x, v in zip(xs, vals):
        ax.text(x, min(v + 0.03, 0.98), f"{v:.2f}", ha="center")
    ax.legend()
    fig.tight_layout()
    fig_path = DIRS["figures"] / "naturelm_calltype_model.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("🖼️ Figure:", fig_path)

if summary.get("observed_check_passed"):
    if summary.get("permutation_tests_complete"):
        print("✅ Call-type check passed on the full data with permutation tests complete.")
    else:
        print("✅ Call-type check passed on the full data with observed cross-validation metrics.")
else:
    print("⚠️ Call-type check did not pass the configured full-data criteria. See summary above.")
"""))

cells.append(md(r"""
## Analysis readout

Run this cell after the FEROP and DCLDE analyses. It produces:

- `naturelm_analysis_readout.json`
- `naturelm_analysis_readout.md`
- `naturelm_analysis_artifacts_*.zip`
- a bounded result sentence
- an explicit analysis status
"""))

cells.append(code(r"""
#@title 9. Analysis readout
import json
from pathlib import Path
from IPython.display import Markdown, display

PLAYBACK_SUMMARY_PATH = DIRS["reports"] / "naturelm_playback_embedding_summary.json"
CALLTYPE_SUMMARY_PATH = DIRS["reports"] / "naturelm_calltype_model_summary.json"
ENVIRONMENT_PATH = DIRS["reports"] / "naturelm_environment.json"
MODEL_MANIFEST_PATH = DIRS["reports"] / "naturelm_model_manifest.json"
READOUT_JSON = DIRS["reports"] / "naturelm_analysis_readout.json"
READOUT_MD = DIRS["reports"] / "naturelm_analysis_readout.md"

def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text())

def fmt(x, digits=3):
    if x is None:
        return "n/a"
    return f"{float(x):.{digits}f}"

def ok_calltype(res):
    return (
        isinstance(res, dict)
        and res.get("status") == "ok"
        and res.get("balanced_accuracy") is not None
        and res.get("chance_1_over_k") is not None
        and res["balanced_accuracy"] > res["chance_1_over_k"]
    )

playback = load_json(PLAYBACK_SUMMARY_PATH)
calltype = load_json(CALLTYPE_SUMMARY_PATH)

if playback is None:
    raise FileNotFoundError(f"Missing playback summary: {PLAYBACK_SUMMARY_PATH}")
if calltype is None:
    raise FileNotFoundError(f"Missing call-type summary: {CALLTYPE_SUMMARY_PATH}")

ferop = playback["purity_test"]
srkw = calltype["within_provider_vfpa_srkw"]
nrkw = calltype["within_provider_dfo_crp_nrkw"]
transfer = calltype.get("cross_provider_vfpa_to_smru", {})

ferop_ok = ferop["loo_1nn_purity"] > ferop["proportional_chance"]
srkw_ok = ok_calltype(srkw)
nrkw_ok = ok_calltype(nrkw)
full_data = bool(calltype.get("full_analysis_run", False)) and bool(playback.get("full_uncapped_data", True))
observed_check_passed = bool(full_data and ferop_ok and srkw_ok and nrkw_ok)
permutation_tests_complete = bool(
    observed_check_passed
    and ferop.get("pvalue") is not None
    and srkw.get("permutation_pvalue") is not None
    and nrkw.get("permutation_pvalue") is not None
)

if observed_check_passed:
    analysis_status = "PASS_OBSERVED_CHECKS"
    if permutation_tests_complete:
        analysis_status = "PASS_WITH_PERMUTATION_TESTS"
else:
    analysis_status = "INCOMPLETE_OR_CONTROL_FAILED"

result_sentence = (
    "The two primary analyses were repeated "
    "with a frozen NatureLM-audio encoder: FEROP K-type catalogue exemplars remained "
    f"separable (leave-one-out 1-NN purity={fmt(ferop['loo_1nn_purity'])}, "
    f"proportional chance={fmt(ferop['proportional_chance'])}), and site-controlled "
    f"catalogue call-type recovery remained above chance for SRKW/VFPA "
    f"(balanced accuracy={fmt(srkw.get('balanced_accuracy'))}, chance={fmt(srkw.get('chance_1_over_k'))}) "
    f"and NRKW/DFO-CRP (balanced accuracy={fmt(nrkw.get('balanced_accuracy'))}, "
    f"chance={fmt(nrkw.get('chance_1_over_k'))}). This is a cross-encoder "
    "check, not evidence of semantic meaning."
)

readout = {
    "analysis_status": analysis_status,
    "run_mode": calltype.get("run_mode", RUN_MODE),
    "full_uncapped_data": full_data,
    "observed_check_passed": observed_check_passed,
    "permutation_tests_complete": permutation_tests_complete,
    "result_sentence": result_sentence if observed_check_passed else None,
    "checks": {
        "ferop_playback_dialect_space": {
            "ok": ferop_ok,
            "loo_1nn_purity": ferop["loo_1nn_purity"],
            "chance": ferop["proportional_chance"],
            "pvalue": ferop.get("pvalue"),
        },
        "vfpa_srkw_site_controlled_calltype": {
            "ok": srkw_ok,
            "balanced_accuracy": srkw.get("balanced_accuracy"),
            "chance": srkw.get("chance_1_over_k"),
            "pvalue": srkw.get("permutation_pvalue"),
        },
        "dfo_crp_nrkw_site_controlled_calltype": {
            "ok": nrkw_ok,
            "balanced_accuracy": nrkw.get("balanced_accuracy"),
            "chance": nrkw.get("chance_1_over_k"),
            "pvalue": nrkw.get("permutation_pvalue"),
        },
        "vfpa_to_smru_transfer": transfer,
    },
    "claim_boundary": (
        "Second-encoder representation check only. Do not claim meaning, "
        "translation, syntax, intention, or playback causality from this notebook."
    ),
    "artifacts": {
        "playback_summary": str(PLAYBACK_SUMMARY_PATH),
        "calltype_summary": str(CALLTYPE_SUMMARY_PATH),
        "environment": str(ENVIRONMENT_PATH),
        "model_manifest": str(MODEL_MANIFEST_PATH),
        "playback_figure": str(DIRS["figures"] / "naturelm_playback_embedding.png"),
        "calltype_figure": str(DIRS["figures"] / "naturelm_calltype_model.png"),
    },
}

READOUT_JSON.write_text(json.dumps(readout, indent=2))

md = f'''
# NatureLM-audio analysis readout

**Analysis status:** `{analysis_status}`

**Run mode:** `{readout['run_mode']}`
**Full uncapped data:** `{full_data}`
**Permutation tests complete:** `{permutation_tests_complete}`

## Metrics

| Check | Result | Baseline | p-value |
|---|---:|---:|---:|
| FEROP K-type separability | {fmt(ferop['loo_1nn_purity'])} | {fmt(ferop['proportional_chance'])} | {fmt(ferop.get('pvalue'))} |
| VFPA/SRKW call types | {fmt(srkw.get('balanced_accuracy'))} | {fmt(srkw.get('chance_1_over_k'))} | {fmt(srkw.get('permutation_pvalue'))} |
| DFO-CRP/NRKW call types | {fmt(nrkw.get('balanced_accuracy'))} | {fmt(nrkw.get('chance_1_over_k'))} | {fmt(nrkw.get('permutation_pvalue'))} |

## Result sentence

{result_sentence if observed_check_passed else 'Analysis status did not pass the configured full-data criteria.'}

## Boundary

Second-encoder representation check only. Do not claim meaning, translation,
syntax, intention, or playback causality from this notebook.
'''
READOUT_MD.write_text(md.strip() + "\n")

badge = "✅" if observed_check_passed else "⚠️"
display(Markdown(f'''
### {badge} NatureLM-audio analysis status: `{analysis_status}`

**Full uncapped data:** `{full_data}`
**Permutation tests complete:** `{permutation_tests_complete}`

**Result sentence**

> {result_sentence if observed_check_passed else 'Analysis status did not pass the configured full-data criteria.'}

**Saved artifacts**

- `{READOUT_JSON}`
- `{READOUT_MD}`
- `{readout['artifacts']['environment']}`
- `{readout['artifacts']['model_manifest']}`
- `{readout['artifacts']['playback_figure']}`
- `{readout['artifacts']['calltype_figure']}`
'''))

print("💾 Readout JSON:", READOUT_JSON)
print("💾 Readout Markdown:", READOUT_MD)
"""))

cells.append(md(r"""
## Download package

Run this after the analysis readout. It packages the reports and figures into one ZIP, stores the ZIP
in Drive, and triggers a browser download from Colab.

By default it does **not** include generated outputs or downloaded resources, because those
files can be large and are already cached in Drive. Turn on the checkbox only if you
need the embedding matrices inside the ZIP.
"""))

cells.append(code(r"""
#@title 10. Package and download analysis artifacts
INCLUDE_EMBEDDINGS_IN_ZIP = False  #@param {type:"boolean"}

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from IPython.display import Markdown, display

PACKAGE_DIR = DIRS["reports"] / "packages"
PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
zip_path = PACKAGE_DIR / f"naturelm_analysis_artifacts_{RUN_MODE.lower()}_{stamp}.zip"

required_artifacts = [
    DIRS["reports"] / "naturelm_analysis_readout.json",
    DIRS["reports"] / "naturelm_analysis_readout.md",
    DIRS["reports"] / "naturelm_calltype_model_summary.json",
    DIRS["reports"] / "naturelm_playback_embedding_summary.json",
    DIRS["reports"] / "naturelm_environment.json",
    DIRS["reports"] / "naturelm_model_manifest.json",
    DIRS["reports"] / "naturelm_calltype_manifest_resolved.csv",
    DIRS["figures"] / "naturelm_calltype_model.png",
    DIRS["figures"] / "naturelm_playback_embedding.png",
]

extra_artifacts = sorted(DIRS["reports"].glob("naturelm_calltype_model_summary_*.json"))
if INCLUDE_EMBEDDINGS_IN_ZIP:
    extra_artifacts += sorted(DIRS["embeddings"].glob("naturelm_*.npz"))

missing_required = [p for p in required_artifacts if not p.exists()]
if missing_required:
    missing = "\n".join(f"- {p}" for p in missing_required)
    raise FileNotFoundError(
        "Run the preceding cells first. Required analysis artifacts are missing:\n" + missing
    )

all_artifacts = []
seen = set()
for path in required_artifacts + extra_artifacts:
    path = Path(path)
    if path.exists() and path not in seen:
        all_artifacts.append(path)
        seen.add(path)

package_manifest = {
    "created_utc": stamp,
    "run_mode": RUN_MODE,
    "include_embeddings": bool(INCLUDE_EMBEDDINGS_IN_ZIP),
    "output_zip": str(zip_path),
    "artifact_count": len(all_artifacts),
    "artifacts": [str(p) for p in all_artifacts],
    "note": (
        "Package contains NatureLM-audio analysis reports and figures. Large caches "
        "such as source audio, Hugging Face weights, and Drive-backed model cache "
        "are intentionally excluded."
    ),
}

def arcname(path):
    path = Path(path)
    if path.parent == DIRS["figures"]:
        return f"figures/{path.name}"
    if path.parent == DIRS["embeddings"]:
        return f"embeddings/{path.name}"
    return f"reports/{path.name}"

with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    zf.writestr("PACKAGE_MANIFEST.json", json.dumps(package_manifest, indent=2))
    for path in all_artifacts:
        zf.write(path, arcname(path))

size_mb = zip_path.stat().st_size / 1e6
display(Markdown(f'''
### 📦 Analysis artifact package ready

**ZIP:** `{zip_path}`
**Size:** `{size_mb:.1f} MB`
**Files:** `{len(all_artifacts)}`

The ZIP is saved in Drive and Colab will now try to download it to your browser.
'''))

try:
    from google.colab import files
    files.download(str(zip_path))
    print("⬇️ Browser download started:", zip_path)
except Exception as e:
    print("ZIP saved, but automatic browser download did not start.")
    print("Download manually from:", zip_path)
    print("Reason:", e)
"""))

nb = {
    "cells": cells,
    "metadata": {
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 0,
}

OUT.write_text(json.dumps(nb, indent=2), encoding="utf-8")
print(f"wrote {OUT}")
