#!/usr/bin/env python3
"""Generate notebooks/naturelm_audio_comparison_colab.ipynb.

The notebook is intentionally self-contained for Colab: it installs NatureLM-audio,
uses the fine-tuned audio encoder inside the model, and re-runs only the two
two primary second-encoder comparison analyses.
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
# NatureLM-audio optional comparison: two headline checks

**Goal.** Test whether the two strongest AVES2 findings also hold when the audio
representation is taken from NatureLM-audio:

1. **Catalogue call types:** site-held-constant call-type classification in SRKW and
   NRKW, plus VFPA -> SMRU cross-site transfer for shared SRKW calls.
2. **Playback dialect space:** FEROP Kamchatka K-type catalogue separability, the
   embedding prerequisite for the published same-pod vs different-pod playback response.

**Why this is optional.** NatureLM-audio is heavier than AVES2. If setup stalls, skip it;
the primary AVES2 result remains the core analysis. This notebook is for the single
sentence reviewers like to see:
"the two headline effects also hold under a second bioacoustic encoder."

**Representation used.** We use the fine-tuned BEATs audio encoder inside
NatureLM-audio, mean-pooled over non-padding frames. We do **not** use generated text
answers as labels or evidence, and we do **not** load the Llama text generator.

**Runtime.** Use Colab GPU. Outputs checkpoint to Drive under
`MyDrive/OrcaDolittle_naturelm`. The notebook refreshes the small NatureLM-audio
source clone on each setup run, while preserving the large Hugging Face, audio,
embedding, report, and figure caches.
"""))

cells.append(code(r"""
#@title 1. Install base dependencies, check GPU, mount Drive
!pip -q install -U huggingface_hub librosa soundfile scikit-learn pandas matplotlib tqdm requests

import os
from pathlib import Path
import torch

print("torch", torch.__version__, "| CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
else:
    print("WARNING: no GPU. Set Runtime -> Change runtime type -> GPU before running NatureLM.")

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
#@title 3. Configuration
# Set MAX_CALLTYPE_SEGMENTS to a small number only for a smoke test.
# Leave it at 0 for a citable headline run.
MAX_CALLTYPE_SEGMENTS = 0   #@param {type:"integer"}
CALLTYPE_BATCH_SIZE = 2     #@param {type:"integer"}
PLAYBACK_N_PERM = 1000      #@param {type:"integer"}
CALLTYPE_N_PERM = 200       #@param {type:"integer"}
MIN_PER_TYPE = 30           #@param {type:"integer"}
MIN_TRANSFER_TEST = 10      #@param {type:"integer"}
TARGET_SR = 16000
MIN_DURATION_S = 1.0

print({
    "MAX_CALLTYPE_SEGMENTS": MAX_CALLTYPE_SEGMENTS,
    "CALLTYPE_BATCH_SIZE": CALLTYPE_BATCH_SIZE,
    "PLAYBACK_N_PERM": PLAYBACK_N_PERM,
    "CALLTYPE_N_PERM": CALLTYPE_N_PERM,
})
if MAX_CALLTYPE_SEGMENTS:
    print("SMOKE MODE: do not cite call-type metrics from a capped run.")
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
print("Loading NatureLM-audio audio encoder on", DEVICE)

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

print("Loaded NatureLM audio encoder.")
print("BEATs prefix:", beats_prefix, "| LayerNorm prefix:", ln_prefix)

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

if PLAYBACK_EMB.exists():
    d = np.load(PLAYBACK_EMB, allow_pickle=True)
    X = d["embeddings"].astype(np.float32)
    y = d["call_type"].astype(str)
    print("Loaded cached playback embeddings:", X.shape)
else:
    man = fetch_ferop_manifest()
    print(f"FEROP exemplars: {len(man)} across {man['call_type'].nunique()} call types")
    if man["call_type"].nunique() < 2:
        raise RuntimeError("Too few FEROP call types downloaded for a separability test.")
    wavs, y = [], []
    for r in man.itertuples():
        wav, _ = librosa.load(r.local_path, sr=TARGET_SR, mono=True)
        wavs.append(wav)
        y.append(r.call_type)
    X = encode_wavs_naturelm(wavs, batch_size=CALLTYPE_BATCH_SIZE)
    y = np.asarray(y, dtype=object)
    np.savez_compressed(PLAYBACK_EMB, embeddings=X, call_type=y)
    print("Saved", PLAYBACK_EMB, X.shape)

counts = pd.Series(y).value_counts()
keep = counts[counts >= 2].index
m = np.isin(y, keep)
Xk, yk = X[m], y[m]
purity = loo_1nn_purity(Xk, yk)
chance = float(pd.Series(yk).value_counts(normalize=True).pow(2).sum())
rng = np.random.default_rng(0)
null = np.array([loo_1nn_purity(Xk, rng.permutation(yk)) for _ in range(PLAYBACK_N_PERM)])
pval = float((np.sum(null >= purity) + 1) / (len(null) + 1))
sil = None
try:
    sil = float(silhouette_score(Xk, yk, metric="cosine"))
except Exception:
    pass

summary = {
    "analysis": "naturelm_ferop_catalogue_calltype_separability",
    "encoder": "NatureLM-audio fine-tuned BEATs audio encoder, frozen, mean-pooled",
    "n_exemplars_total": int(len(X)),
    "n_types_total": int(len(set(y))),
    "purity_test": {
        "n_exemplars": int(len(yk)),
        "n_types": int(len(keep)),
        "loo_1nn_purity": float(purity),
        "null_mean": float(null.mean()),
        "null_std": float(null.std()),
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
ax[0].set_title(f"FEROP K-types in NatureLM-audio space\nLOO purity {purity:.2f}, null {null.mean():.2f}, p={pval:.1e}")
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
print("Figure:", fig_path)
"""))

cells.append(md(r"""
## Check B: site-controlled DCLDE catalogue call types

This rebuilds the public DCLDE call-type manifest, streams the referenced audio files,
encodes the labelled segments with NatureLM-audio, and repeats the site-controlled
call-type probes. Runtime depends on Colab GPU and network speed. For a citable result,
`MAX_CALLTYPE_SEGMENTS` must be `0`.
"""))

cells.append(code(r"""
#@title 6. Build public DCLDE call-type manifest and resolve audio paths
import io
import json
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
    print(f"{pv}: {len(csvs)} annotation CSVs")
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
print("manifest rows:", len(man), "| call types:", man["call_type"].nunique())
print("by provider:", man["provider"].value_counts().to_dict())

basename_to_key = {}
for pv in sorted(man["provider"].unique()):
    keys = [k for k in list_keys(f"{ROOT}/{pv}/audio/") if k.lower().endswith(AUDIO_EXT)]
    for k in keys:
        basename_to_key[k.split("/")[-1]] = k
    print(f"{pv}: {len(keys)} audio objects indexed")

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
print("resolved rows:", len(man), "->", manifest_path)
"""))

cells.append(code(r"""
#@title 7. Encode DCLDE call-type segments with NatureLM-audio (resumable)
import librosa
from tqdm.auto import tqdm

CALLTYPE_EMB = DIRS["embeddings"] / "naturelm_calltype_embeddings.npz"

if CALLTYPE_EMB.exists():
    d = np.load(CALLTYPE_EMB, allow_pickle=True)
    embeddings = list(d["embeddings"])
    metadata = list(d["metadata"])
    done_ids = {m["segment_id"] for m in metadata}
    print("Resuming:", len(embeddings), "segments")
else:
    embeddings, metadata, done_ids = [], [], set()

def download_audio_key(gcs_key):
    dest = DIRS["audio"] / Path(gcs_key).name
    if not dest.exists() or dest.stat().st_size == 0:
        url = GCS_DL + urllib.parse.quote(gcs_key, safe="/")
        tmp = dest.with_suffix(dest.suffix + ".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(dest)
    return dest

def flush_batch(wavs, metas):
    if not wavs:
        return
    Xb = encode_wavs_naturelm(wavs, batch_size=CALLTYPE_BATCH_SIZE)
    for emb, meta in zip(Xb, metas):
        embeddings.append(emb)
        metadata.append(meta)

for gcs_key, group in tqdm(list(man.groupby("gcs_key")), desc="source files"):
    group = group.sort_values("start")
    if all(f"{r.gcs_key}|{float(r.start):.3f}|{float(r.end):.3f}|{r.call_type}" in done_ids
           for r in group.itertuples()):
        continue
    try:
        local = download_audio_key(gcs_key)
    except Exception as e:
        print("WARN download failed:", gcs_key, e)
        continue
    wavs, metas = [], []
    for r in group.itertuples():
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
    print("checkpoint:", len(embeddings), "segments")

X_call = np.asarray(embeddings, np.float32)
meta_call = pd.DataFrame(metadata)
print("DONE:", X_call.shape)
print(meta_call.groupby(["provider", "call_family"]).size())
"""))

cells.append(code(r"""
#@title 8. Run site-controlled call-type models and save NatureLM summary
import json

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def clf():
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=5000, class_weight="balanced", C=1.0),
    )

def within_provider(provider, family, min_per_type=MIN_PER_TYPE):
    sub = meta_call[(meta_call["provider"] == provider) & (meta_call["call_family"] == family)].copy()
    counts = sub["call_type"].value_counts()
    keep = counts[counts >= min_per_type].index
    sub = sub[sub["call_type"].isin(keep)]
    if sub["call_type"].nunique() < 2:
        return None
    idx = sub.index.to_numpy()
    Xs = X_call[idx]
    y = sub["call_type"].to_numpy()
    classes = sorted(set(y))
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    yt, yp = [], []
    for tr, te in skf.split(Xs, y):
        model2 = clf().fit(Xs[tr], y[tr])
        yt.append(y[te])
        yp.append(model2.predict(Xs[te]))
    yt = np.concatenate(yt)
    yp = np.concatenate(yp)
    bal = balanced_accuracy_score(yt, yp)
    macro = f1_score(yt, yp, average="macro")
    rng = np.random.default_rng(0)
    null = []
    for _ in range(CALLTYPE_N_PERM):
        yperm = rng.permutation(y)
        yt2, yp2 = [], []
        for tr, te in skf.split(Xs, yperm):
            model2 = clf().fit(Xs[tr], yperm[tr])
            yt2.append(yperm[te])
            yp2.append(model2.predict(Xs[te]))
        null.append(balanced_accuracy_score(np.concatenate(yt2), np.concatenate(yp2)))
    null = np.asarray(null)
    return {
        "provider": provider,
        "family": family,
        "n": int(len(sub)),
        "k_types": int(len(classes)),
        "classes": classes,
        "balanced_accuracy": float(bal),
        "macro_f1": float(macro),
        "chance_1_over_k": float(1 / len(classes)),
        "majority_baseline": float(pd.Series(y).value_counts(normalize=True).iloc[0]),
        "permutation_mean": float(null.mean()),
        "permutation_std": float(null.std()),
        "permutation_pvalue": float((np.sum(null >= bal) + 1) / (len(null) + 1)),
        "confusion_matrix": confusion_matrix(yt, yp, labels=classes).tolist(),
    }

def cross_provider(train_pv="vfpa", test_pv="smru", min_train=MIN_PER_TYPE, min_test=MIN_TRANSFER_TEST):
    s = meta_call[meta_call["call_family"] == "SRKW"].copy()
    tr = s[s["provider"] == train_pv]
    te = s[s["provider"] == test_pv]
    tr_counts = tr["call_type"].value_counts()
    te_counts = te["call_type"].value_counts()
    shared = [t for t in tr_counts.index if tr_counts[t] >= min_train and te_counts.get(t, 0) >= min_test]
    if len(shared) < 2:
        return {"note": "insufficient shared types", "shared_types": shared}
    tr = tr[tr["call_type"].isin(shared)]
    te = te[te["call_type"].isin(shared)]
    model2 = clf().fit(X_call[tr.index.to_numpy()], tr["call_type"].to_numpy())
    yt = te["call_type"].to_numpy()
    yp = model2.predict(X_call[te.index.to_numpy()])
    return {
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

srkw_vfpa = within_provider("vfpa", "SRKW")
nrkw_dfo = within_provider("dfo_crp", "NRKW")
transfer = cross_provider()

summary = {
    "analysis": "naturelm_site_controlled_calltype_classification",
    "encoder": "NatureLM-audio fine-tuned BEATs audio encoder, frozen, mean-pooled",
    "max_calltype_segments": int(MAX_CALLTYPE_SEGMENTS),
    "citable": bool(MAX_CALLTYPE_SEGMENTS == 0),
    "n_encoded_segments": int(len(X_call)),
    "within_provider_vfpa_srkw": srkw_vfpa,
    "within_provider_dfo_crp_nrkw": nrkw_dfo,
    "cross_provider_vfpa_to_smru": transfer,
    "boundary": "Catalogue call-type discrimination, not meaning; use only if full uncapped run completes.",
}
out = DIRS["reports"] / "naturelm_calltype_model_summary.json"
out.write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))

labels, vals, chance = [], [], []
for name, res in [("VFPA SRKW", srkw_vfpa), ("DFO_CRP NRKW", nrkw_dfo)]:
    if res:
        labels.append(f"{name}\nwithin-site")
        vals.append(res["balanced_accuracy"])
        chance.append(res["chance_1_over_k"])
if "transfer_balanced_accuracy" in transfer:
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
    print("Figure:", fig_path)
"""))

cells.append(md(r"""
## How to use the result

If both checks are positive on an uncapped run, add one bounded sentence to the paper:

> As an optional robustness check, the two headline effects also held under the
> fine-tuned NatureLM-audio encoder: site-controlled catalogue call-type recovery
> and FEROP playback-dialect separability.

If setup fails, or if `MAX_CALLTYPE_SEGMENTS` was nonzero, do not cite the NatureLM
numbers. Report AVES2-only as the honest limitation.
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
