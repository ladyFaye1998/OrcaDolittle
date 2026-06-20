#!/usr/bin/env python3
"""Generate notebooks/dtag_context_decode_colab.ipynb (Octave-decode, clip-manifest pipeline)."""
import json
from pathlib import Path

OUT = Path(__file__).parent / "dtag_context_decode_colab.ipynb"


def md(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.strip("\n").splitlines(keepends=True)}


def code(src):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": src.strip("\n").splitlines(keepends=True)}


cells = []

cells.append(md(r"""# 🐋 Decode behavioural context from killer-whale *communication*

**Goal.** Show that the *communicative calls* of individual killer whales carry
information about **what the whale is doing** (foraging vs not), where the behaviour
label is defined from **movement only** and never from the sound.

**Why this is non-circular and confound-clean** ✅
- 🏷️ **Label side** comes from the tag's *movement* sensors (dive depth + jerk-based
  prey-capture), independent of the acoustic channel we decode [@tennessen2019; @holt2024masking].
- 🎙️ **Decoder input** is the whale's *pulsed communicative calls* only — echolocation
  clicks/buzzes are excluded by band + duration, so we decode *communication*, not sonar.
- 🧍 **Validation is leave-individual-out**, so a model cannot win by recognising an
  individual or recorder instead of behaviour — the confound that inflates prior results.

**Data (all open, CC-BY).** Suction-cup DTAG deployments on fish-eating killer whales,
Salish Sea [@holt2024masking_data]:
- Movement: Zenodo `10.5281/zenodo.13308835` (`*prh50.mat`, `foraging_data.csv`).
- Audio: Zenodo `10.5281/zenodo.13333019` and `10.5281/zenodo.13328931`, raw `.dtg`.

**Fully automatic — just run every cell.** `.dtg` is the lossless **X3 archive** format.
Cell 4 decodes it **in Colab with Octave** using the reference GPL X3 toolbox (Mark
Johnson, the DTAG author) — no Wine, no Windows, no manual step. Pure-Octave decoding is
slow, so Cell 4 decodes a capped number of files per deployment and **checkpoints every
WAV to Drive**, so a crash resumes rather than restarts.

**Honest scope.** Tests whether context is *decodable* from communication above a
leave-individual-out null. Association, not "meaning"; non-invasive re-analysis of archived
tag data. References keyed in `paper/refs.bib`.

> ⚙️ Set **Runtime → Change runtime type → GPU** before running (AVES2 encoding).
"""))

cells.append(code(r"""
#@title 1. 🔧 Install deps, check GPU, mount Drive (auto-persist + resume)
!pip -q install avex librosa soundfile scikit-learn pandas matplotlib tqdm requests scipy

import os, json, torch
print("torch", torch.__version__, "| CUDA:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
else:
    print("⚠️ No GPU — encoding will be slow. Runtime -> Change runtime type -> GPU.")

try:
    from google.colab import drive
    drive.mount("/content/drive")
    OUTDIR = "/content/drive/MyDrive/OrcaDolittle_context"
except Exception as e:
    print("Drive unavailable, using ephemeral /content:", e)
    OUTDIR = "/content/OrcaDolittle_context"

# Persistent sub-folders on Drive (survive crashes; pipeline resumes from these).
DIRS = {k: os.path.join(OUTDIR, k) for k in
        ["dtg", "wav", "clips", "labels", "detections", "embeddings", "reports", "figures"]}
for d in [OUTDIR, *DIRS.values()]:
    os.makedirs(d, exist_ok=True)
print("📁 All outputs persist under:", OUTDIR)
if not OUTDIR.startswith("/content/drive"):
    print("⚠️ Drive did NOT mount — outputs are on the EPHEMERAL disk and vanish on "
          "disconnect. Re-run this cell and complete the Google auth popup.")
"""))

cells.append(code(r"""
#@title 2. ⚙️ Configuration — which deployments to process
# Start with ONE deployment to validate end-to-end fast (Octave decode is slow).
DEPLOYMENTS = ["oo09_237d"]  #@param

ZEN_MOVEMENT = "13308835"
ZEN_AUDIO = ["13333019", "13328931"]   # 2009-10, 2011-14
MAX_DTG_PER_DEP = 1  #@param {type:"integer"}  # .dtg files to decode per deployment (speed vs power)

# Behavioural-context rule (MOVEMENT ONLY — never acoustic):
DEEP_M = 30.0          #@param  dive >= this depth counts as foraging (deep pursuit)
SURFACE_M = 5.0        #@param  depth below this = at-surface (between dives)
MIN_DIVE_S = 10.0      #@param  minimum dive duration

# Communicative-call detection (exclude echolocation):
CALL_BAND = (500, 10000)   # Hz; pulsed-call energy band
CLICK_BAND_HI = 12000      # Hz; >this dominating => echolocation click
DET_MIN_S, DET_MAX_S = 0.10, 8.0
DET_SNR_DB = 8.0

TARGET_SR = 16000          # AVES2 input rate
print("Deployments:", DEPLOYMENTS, "| max .dtg/dep:", MAX_DTG_PER_DEP)
print(f"Context: foraging = dive maxdepth >= {DEEP_M} m (movement only)")
"""))

cells.append(code(r"""
#@title 3. ⬇️ Download movement + the .dtg for the selected deployments (resumable)
import requests, os, glob
from tqdm.auto import tqdm

def zenodo_files(record):
    r = requests.get(f"https://zenodo.org/api/records/{record}", timeout=60)
    r.raise_for_status()
    out = {}
    for f in r.json()["files"]:
        key = f.get("key") or f.get("filename")
        link = (f.get("links", {}) or {}).get("self") or f.get("download")
        out[key] = (link, f.get("size", 0))
    return out

def dl(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return False
    tmp = dest + ".part"
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(tmp, "wb") as fh, tqdm(total=total, unit="B", unit_scale=True,
                                         desc=os.path.basename(dest)[:28], leave=False) as bar:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk); bar.update(len(chunk))
    os.replace(tmp, dest)
    return True

# 3a. Movement deposit: foraging_data.csv (once) + the prh50 file per deployment.
mv = zenodo_files(ZEN_MOVEMENT)
if "foraging_data.csv" in mv:
    dl(mv["foraging_data.csv"][0], os.path.join(DIRS["labels"], "foraging_data.csv"))
for dep in DEPLOYMENTS:
    key = f"{dep}prh50.mat"
    if key in mv:
        dl(mv[key][0], os.path.join(DIRS["labels"], key))
    else:
        print("⚠️ no prh for", dep, "(check the deployment id)")

# 3b. Audio: the first MAX_DTG_PER_DEP .dtg per deployment (sorted = contiguous from start).
audio_index = {}
for rec in ZEN_AUDIO:
    audio_index.update(zenodo_files(rec))
want = []
for dep in DEPLOYMENTS:
    files = sorted(k for k in audio_index if k.endswith(".dtg") and k.startswith(dep))
    want += files[:MAX_DTG_PER_DEP]
gb = sum(audio_index[k][1] for k in want) / 1e9
print(f"🎧 {len(want)} .dtg to fetch (~{gb:.1f} GB): {want}")
for k in want:
    dl(audio_index[k][0], os.path.join(DIRS["dtg"], k))
print("✅ downloads complete (or already cached).")
"""))

cells.append(code(r"""
#@title 4. 🔓 Decode .dtg → wav in Colab via the Octave X3 toolbox (no Wine, no manual)
# .dtg IS an X3 lossless archive, so we decode it with the reference GPL X3 Matlab toolbox
# (Mark Johnson, the DTAG author) under Octave — fully in-code, deterministic, headless.
# Pure-Octave X3 uncompression is SLOW (several minutes per 100 MB); each wav is
# checkpointed to Drive, so re-running resumes. Files are decoded in sorted order so the
# per-deployment time offset stays contiguous from the first file.
import os, glob, io, zipfile, subprocess, shutil, requests

if not shutil.which("octave"):
    print("installing octave (one-off, ~1 min) ...")
    !apt-get -qq update >/dev/null 2>&1
    !DEBIAN_FRONTEND=noninteractive apt-get -qq install -y octave >/dev/null 2>&1

X3DIR = "/content/x3-matlab"
if not os.path.exists(os.path.join(X3DIR, "x3_to_wav.m")):
    print("fetching the GPL X3 Matlab toolbox ...")
    data = requests.get("https://github.com/psiphi75/x3-matlab/archive/refs/heads/master.zip",
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=180).content
    zipfile.ZipFile(io.BytesIO(data)).extractall("/content")
    src = [p for p in glob.glob("/content/x3-matlab-*") if os.path.isdir(p)][0]
    if os.path.abspath(src) != X3DIR:
        shutil.move(src, X3DIR)
ver = subprocess.run(["octave", "--version"], capture_output=True, text=True).stdout
print("octave:", (ver.splitlines() or ["?"])[0])

dtgs = sorted(glob.glob(os.path.join(DIRS["dtg"], "*.dtg")))
if not dtgs:
    raise SystemExit(f"No .dtg in {DIRS['dtg']} — run Cell 3 first.")

def dep_of(name):
    return next((d for d in DEPLOYMENTS if os.path.basename(name).startswith(d)), None)

WORK = "/content/x3work"
ok = 0
for d in dtgs:
    if dep_of(d) is None:
        continue
    base = os.path.splitext(os.path.basename(d))[0]
    if glob.glob(os.path.join(DIRS["wav"], base + "*.wav")):
        ok += 1; print("✓ cached", base); continue
    os.makedirs(WORK, exist_ok=True)
    for f in glob.glob(os.path.join(WORK, "*")):
        os.remove(f)
    shutil.copy(d, os.path.join(WORK, base + ".dtg"))
    cmd = (f"addpath('{X3DIR}'); addpath('{X3DIR}/XML4MATv2'); "
           f"x3_to_wav('{WORK}/{base}.dtg');")
    print(f"\n--- decoding {base} (be patient; pure-Octave X3 is slow) ---")
    r = subprocess.run(["octave", "--no-gui", "--quiet", "--eval", cmd],
                       capture_output=True, text=True, timeout=21600)
    print((r.stdout or "")[-400:])
    if r.returncode != 0 or "failure" in (r.stdout + r.stderr).lower():
        print("stderr:", (r.stderr or "")[-400:])
    produced = sorted(p for p in glob.glob(os.path.join(WORK, "*.wav")))
    if produced:
        dst = os.path.join(DIRS["wav"], os.path.basename(produced[0]))
        shutil.move(produced[0], dst); ok += 1
        print("  ✅ ->", dst)
    else:
        print("  ❌ no wav produced for", base)

print(f"\n{'✅' if ok else '❌'} {ok} wav(s) ready in {DIRS['wav']}")
if ok == 0:
    print("Octave could not parse the .dtg. Paste the output above; as a fallback decode "
          "locally with scripts/dtag_local_extract.py (--fetch-dir, then d3read.exe) and "
          "upload the clips.")
"""))

cells.append(md(r"""## 🎧 From here it is all automatic

Cell 4 wrote decoded WAVs to `wav/`. The next cell detects communicative calls and cuts
16 kHz clips into a manifest; the rest of the notebook encodes them, attaches the
movement-defined context, and runs the leave-individual-out decode. Every stage is
checkpointed to Drive, so a crash resumes rather than restarts.

(If you ever decode `.dtg` elsewhere, you can also drop decoded `*.wav` into
`MyDrive/OrcaDolittle_context/wav/` or pre-cut `clips/` + `clips_manifest.json`, and the
next cell will pick them up.)
"""))

cells.append(code(r"""
#@title 5. 🎧 Ingest audio → communicative-call clips (resumable)
import os, glob, json, numpy as np, soundfile as sf, librosa
from tqdm.auto import tqdm

CLIPDIR = DIRS["clips"]
MANIFEST = os.path.join(DIRS["detections"], "clips_manifest.json")
manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else []
done_src = {m["src"] for m in manifest}

def save_manifest():
    json.dump(manifest, open(MANIFEST, "w"))

def detect_calls_wav(path):
    # Energy detector in the pulsed-call band; rejects impulsive broadband clicks (too
    # short) and segments where >12 kHz energy dominates (echolocation). 30 s blocks
    # bound memory on long files. Mirrors scripts/dtag_local_extract.py exactly.
    info = sf.info(path); sr = info.samplerate; dsr = min(sr, 32000)
    events, pos = [], 0
    for x in sf.blocks(path, blocksize=int(30 * sr), dtype="float32", always_2d=True):
        x = x.mean(axis=1)
        if sr != dsr:
            x = librosa.resample(x, orig_sr=sr, target_sr=dsr)
        hop, nfft = 256, 1024
        S = np.abs(librosa.stft(x, n_fft=nfft, hop_length=hop)) ** 2
        f = librosa.fft_frequencies(sr=dsr, n_fft=nfft)
        band = (f >= CALL_BAND[0]) & (f <= min(CALL_BAND[1], dsr / 2))
        hi = f >= min(CLICK_BAND_HI, dsr / 2 - 1)
        be, he = S[band].sum(0), S[hi].sum(0) + 1e-12
        thr = (np.median(be) + 1e-12) * 10 ** (DET_SNR_DB / 10)
        idx = np.flatnonzero((be > thr) & (be > 3 * he))
        if len(idx):
            for s in np.split(idx, np.flatnonzero(np.diff(idx) > 4) + 1):
                t0 = pos / sr + s[0] * hop / dsr
                dur = (s[-1] - s[0] + 1) * hop / dsr
                if DET_MIN_S <= dur <= DET_MAX_S:
                    events.append((float(t0), float(dur)))
        pos += int(len(x) * sr / dsr)
    return events, info.frames / sr

def dep_of(name):
    return next((d for d in DEPLOYMENTS if name.startswith(d)), None)

wavs = sorted(glob.glob(os.path.join(DIRS["wav"], "*.wav")))
have_clips = len(manifest) > 0 and len(glob.glob(os.path.join(CLIPDIR, "*.wav"))) > 0

if wavs:
    print(f"🎧 {len(wavs)} wav(s) found — detecting communicative calls + clipping ...")
    by_dep = {}
    for w in wavs:
        d = dep_of(os.path.basename(w))
        if d:
            by_dep.setdefault(d, []).append(w)
        else:
            print("   skip (no deployment prefix):", os.path.basename(w))
    for dep, ws in by_dep.items():
        offset = sum(m.get("file_dur", 0.0) for m in manifest if dep_of(m["src"]) == dep)
        for w in sorted(ws):
            name = os.path.basename(w)
            if name in done_src:
                continue
            ev, fdur = detect_calls_wav(w)
            for t0, dur in ev:
                clip = f"{dep}__{offset + t0:.3f}.wav"
                seg, _ = librosa.load(w, sr=TARGET_SR, offset=max(t0, 0.0),
                                      duration=max(dur, 1.0), mono=True)
                sf.write(os.path.join(CLIPDIR, clip), seg, TARGET_SR)
                manifest.append({"clip": clip, "deployment": dep,
                                 "abs_t": round(offset + t0, 3), "dur": round(dur, 3),
                                 "src": name, "file_dur": round(fdur, 2)})
            offset += fdur; done_src.add(name); save_manifest()
            print(f"   {name}: {len(ev)} calls")
elif have_clips:
    print(f"✅ {len(manifest)} clips already present — nothing to decode.")
else:
    print("⚠️ No clips and no WAVs. Run Cell 4 (decode) first, or upload wavs/clips.")

save_manifest()
ndep = len({m["deployment"] for m in manifest})
print(f"\n📎 manifest: {len(manifest)} clips across {ndep} deployment(s) -> {CLIPDIR}")
"""))

cells.append(code(r"""
#@title 6. 🏷️ Movement-only behavioural context from prh50 (depth + jerk dives)
import os, json, numpy as np
from scipy.io import loadmat

def load_prh(path):
    m = loadmat(path, squeeze_me=True, struct_as_record=False)
    def find(*names):
        for n in names:
            if n in m:
                return np.asarray(m[n], dtype=float).squeeze()
        return None
    p = find("p", "P", "depth", "Depth")
    fs = find("fs", "Fs", "sampling_rate")
    A = find("A", "Aw", "acc")
    fs = float(np.atleast_1d(fs)[0]) if fs is not None else 50.0
    return p, fs, A

def dive_context(p, fs, A):
    # Dive = depth > SURFACE_M for >= MIN_DIVE_S. Foraging if it reaches DEEP_M, or a
    # jerk prey-capture spike occurs in it. Movement only — no acoustic input.
    below = p > SURFACE_M
    ctx = np.zeros(len(p), dtype=np.int8)
    jerk = None
    if A is not None and A.ndim == 2 and A.shape[0] >= A.shape[1]:
        jerk = np.linalg.norm(np.diff(A, axis=0), axis=1) * fs
        jthr = np.nanmedian(jerk) + 6 * (np.nanstd(jerk) + 1e-9)
    i, n, dives = 0, len(p), []
    while i < n:
        if below[i]:
            j = i
            while j < n and below[j]:
                j += 1
            if (j - i) / fs >= MIN_DIVE_S:
                maxd = float(np.nanmax(p[i:j]))
                forag = maxd >= DEEP_M
                if jerk is not None and not forag:
                    seg = jerk[max(i - 1, 0):max(j - 1, 1)]
                    forag = bool(np.any(seg > jthr))
                if forag:
                    ctx[i:j] = 1
                dives.append((i / fs, j / fs, maxd, int(forag)))
            i = j
        else:
            i += 1
    return ctx, dives

CTX, power = {}, {}
for dep in DEPLOYMENTS:
    prh = os.path.join(DIRS["labels"], f"{dep}prh50.mat")
    if not os.path.exists(prh):
        print("skip (no prh):", dep); continue
    p, fs, A = load_prh(prh)
    if p is None:
        print("⚠️ no depth var in", dep, "— keys may differ"); continue
    ctx, dives = dive_context(p, fs, A)
    CTX[dep] = (ctx, fs, len(p))
    nf, nn = int((ctx == 1).sum()), int((ctx == 0).sum())
    power[dep] = {"fs": fs, "minutes": round(len(p) / fs / 60, 1), "n_dives": len(dives),
                  "foraging_sec": round(nf / fs, 1), "non_foraging_sec": round(nn / fs, 1)}
    print(f"{dep}: {power[dep]['minutes']} min, {len(dives)} dives, "
          f"foraging {power[dep]['foraging_sec']}s / non {power[dep]['non_foraging_sec']}s")
json.dump(power, open(os.path.join(DIRS["reports"], "context_power.json"), "w"), indent=2)
print("🏷️ context labels built for", list(CTX))
"""))

cells.append(code(r"""
#@title 7. 🧠 Encode call clips with frozen AVES2 (resumable checkpoint)
import os, json, numpy as np, librosa, torch
from avex import load_model
from tqdm.auto import tqdm

MANIFEST = os.path.join(DIRS["detections"], "clips_manifest.json")
if not os.path.exists(MANIFEST):
    raise SystemExit("⚠️ clips_manifest.json not found — run the ingest cell (5) first.")
manifest = json.load(open(MANIFEST))
if len(manifest) == 0:
    raise SystemExit("⚠️ manifest is empty: 0 clips. Cell 4 produced no wav, so there is "
                     "nothing to encode — check Cell 4's output.")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = load_model("esp_aves2_sl_beats_all", return_features_only=True, device=DEVICE)
model.eval()

def encode(wav):
    t = torch.from_numpy(wav).unsqueeze(0).float().to(DEVICE)
    with torch.no_grad():
        f = model(t)
    return f.cpu().numpy().mean(axis=1)[0]

EMB_NPZ = os.path.join(DIRS["embeddings"], "call_embeddings.npz")
embs, meta, done = [], [], set()
if os.path.exists(EMB_NPZ):
    prev = np.load(EMB_NPZ, allow_pickle=True)
    embs = list(prev["embeddings"]); meta = list(prev["metadata"])
    done = set(m["clip"] for m in meta)
    print(f"resume: {len(embs)} clips already encoded")

CLIPDIR = DIRS["clips"]; ck = 0
for m in tqdm(manifest, desc="encode"):
    if m["clip"] in done:
        continue
    p = os.path.join(CLIPDIR, m["clip"])
    if not os.path.exists(p):
        continue
    try:
        wav, _ = librosa.load(p, sr=TARGET_SR, mono=True)
    except Exception:
        continue
    if len(wav) < TARGET_SR:
        wav = np.pad(wav, (0, TARGET_SR - len(wav)))
    try:
        e = encode(wav)
    except Exception:
        continue
    embs.append(e)
    meta.append({"clip": m["clip"], "deployment": m["deployment"],
                 "abs_t": m["abs_t"], "dur": m["dur"]})
    done.add(m["clip"]); ck += 1
    if ck % 50 == 0:
        np.savez_compressed(EMB_NPZ, embeddings=np.array(embs, np.float32),
                            metadata=np.array(meta, object))
np.savez_compressed(EMB_NPZ, embeddings=np.array(embs, np.float32),
                    metadata=np.array(meta, object))
print(f"🧠 encoded {len(embs)} clips -> {EMB_NPZ}")
"""))

cells.append(code(r"""
#@title 8. 🔗 Attach movement-context label to each call (by absolute time)
import numpy as np, pandas as pd

M = pd.DataFrame(meta)
X = np.array(embs, np.float32)
if len(M) == 0 or X.size == 0:
    raise SystemExit("⚠️ No encoded calls. The .dtg decode produced no audio, so the "
                     "pipeline is empty. Re-run Cell 4 until it prints '✅ N wav(s)', "
                     "then Cell 5 and Cell 7.")
for c in ("deployment", "abs_t"):
    if c not in M.columns:
        raise SystemExit(f"⚠️ metadata missing '{c}' — re-run Cell 7.")

def label_call(dep, abs_t):
    if dep not in CTX:
        return -1
    ctx, fs, n = CTX[dep]
    i = int(abs_t * fs)
    return int(ctx[i]) if 0 <= i < n else -1

M["context"] = [label_call(d, t) for d, t in zip(M["deployment"], M["abs_t"])]
mask = (M["context"] >= 0).to_numpy()
M = M.loc[mask].reset_index(drop=True)
X = X[mask]
M["context"] = M["context"].map({1: "foraging", 0: "non_foraging"})

print("calls with a context label:", len(M))
if len(M) == 0:
    raise SystemExit("⚠️ 0 calls fell inside any deployment's context timeline "
                     "(check abs_t alignment or that CTX was built in Cell 6).")
print("\nYield per deployment x context (the key power check):")
print(pd.crosstab(M["deployment"], M["context"]))
usable = [d for d, g in M.groupby("deployment") if g["context"].nunique() == 2]
print("\ndeployments with BOTH contexts (usable for leave-individual-out):", usable)
"""))

cells.append(code(r"""
#@title 9. 🧪 Leave-individual-out decode of context from calls + permutation null
import os, json, numpy as np, matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import balanced_accuracy_score

SEED, N_PERM = 0, 200
if len(usable) < 2:
    raise SystemExit(f"⚠️ need >=2 individuals with BOTH contexts for leave-individual-out; "
                     f"have {usable}. Add deployments in Cell 2 (and raise MAX_DTG_PER_DEP) "
                     f"and re-run (all stages resume).")

sub = M[M["deployment"].isin(usable)].copy()
Xs = X[sub.index.to_numpy()]
y = sub["context"].to_numpy()
groups = sub["deployment"].to_numpy()

def pipe(kind):
    base = (LogisticRegression(max_iter=5000, class_weight="balanced") if kind == "linear"
            else MLPClassifier(hidden_layer_sizes=(128,), max_iter=400, alpha=1e-3, random_state=SEED))
    return make_pipeline(StandardScaler(), base)

def logo_balacc(Xs, y, groups, kind):
    logo = LeaveOneGroupOut(); yt, yp = [], []
    for tr, te in logo.split(Xs, y, groups):
        if len(set(y[tr])) < 2:
            continue
        yp.append(pipe(kind).fit(Xs[tr], y[tr]).predict(Xs[te])); yt.append(y[te])
    yt, yp = np.concatenate(yt), np.concatenate(yp)
    return balanced_accuracy_score(yt, yp)

results = {"n_calls": int(len(sub)), "n_individuals": int(sub["deployment"].nunique()),
           "deployments": usable, "n_perm": N_PERM, "models": {}}
rng = np.random.default_rng(SEED)
for kind in ["linear", "mlp"]:
    obs = logo_balacc(Xs, y, groups, kind)
    null = np.array([logo_balacc(Xs, rng.permutation(y), groups, kind) for _ in range(N_PERM)])
    p = (np.sum(null >= obs) + 1) / (len(null) + 1)
    results["models"][kind] = {"balanced_accuracy": float(obs),
                               "null_mean": float(null.mean()), "pvalue": float(p)}
    print(f"{kind}: leave-individual-out bal.acc = {obs:.3f} (null {null.mean():.3f}, p={p:.2e})")

fig, ax = plt.subplots(figsize=(7, 5))
ks = list(results["models"]); vals = [results["models"][k]["balanced_accuracy"] for k in ks]
nm = [results["models"][k]["null_mean"] for k in ks]
xpos = np.arange(len(ks))
ax.bar(xpos, vals, width=0.5, color="#2a7fb8", label="leave-individual-out bal. acc")
ax.plot(xpos, nm, "r_", markersize=40, markeredgewidth=3, label="permutation null")
ax.axhline(0.5, ls="--", c="gray", lw=1, label="chance (2 contexts)")
for i, v in enumerate(vals):
    ax.text(i, v + 0.02, f"{v:.2f}\n(p={results['models'][ks[i]]['pvalue']:.1e})",
            ha="center", fontsize=9)
ax.set_xticks(xpos); ax.set_xticklabels(ks); ax.set_ylim(0, 1)
ax.set_ylabel("balanced accuracy")
ax.set_title(f"Decoding movement-defined context from communicative calls\n"
             f"{results['n_calls']} calls, {results['n_individuals']} individuals, leave-individual-out")
ax.legend(fontsize=8); plt.tight_layout()
FIG = os.path.join(DIRS["figures"], "context_decode.png")
plt.savefig(FIG, dpi=150, bbox_inches="tight"); plt.show()

results["caveats"] = [
    "Context label is movement-only (depth + jerk); decoder input is communicative calls -> non-circular.",
    "Echolocation excluded by band/duration; residual click leakage is a limitation (upgrade: ORCA-SPOT).",
    "Leave-individual-out so identity cannot stand in for behaviour.",
    "Association, not 'meaning'; non-invasive re-analysis of archived DTAG data.",
    "Absolute call time assumes contiguous audio from prh t=0 (VERIFY against .xml)."]
OUTJSON = os.path.join(DIRS["reports"], "context_decode_summary.json")
json.dump(results, open(OUTJSON, "w"), indent=2)
print("\n✅ saved to Drive:", OUTJSON, "and", FIG)
print(json.dumps(results["models"], indent=2))
"""))

cells.append(md(r"""## ✅ What this produces (confound-clean versatility evidence)

If `linear`/`mlp` **leave-individual-out balanced accuracy** sits clearly above the
**permutation null** (and 0.5), then: *a whale's communicative calls carry decodable
information about its behavioural context*, with the behaviour defined independently from
movement and validated so that **individual identity cannot explain the result**.

**Bring back into the repo and commit:**
- `reports/context_decode_summary.json` → `reports/`
- `figures/context_decode.png` → `figures/`
- `reports/context_power.json` (yield per individual × context)

**Scaling up:** the leave-individual-out test needs **≥2 individuals**, so once one
deployment runs end-to-end, add more to `DEPLOYMENTS` (Cell 2) and raise
`MAX_DTG_PER_DEP`. Every stage is checkpointed, so it resumes rather than restarts.

**Honest caveats** are written into the JSON: detector click-leakage, the contiguous-audio
timing assumption, and that this is *association*, not proof of meaning. Upgrade paths:
ORCA-SPOT call detection, `.xml`-based exact timing, and the gold-standard per-dive HMM
states via the data request in `docs/data_requests.md`.
"""))

nb = {"cells": cells,
      "metadata": {"colab": {"provenance": [], "toc_visible": True},
                   "kernelspec": {"name": "python3", "display_name": "Python 3"},
                   "language_info": {"name": "python"}, "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 0}

OUT.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", OUT, "with", len(cells), "cells")
