#!/usr/bin/env python3
"""Decode movement-defined behavioural context from killer-whale communicative calls.

Decision side of the confound-clean test (see docs/decode_context_plan.md). Reads the
locally-decoded call clips and their movement-only context labels, encodes each call
with frozen AVES2, and asks whether a model can predict context **on held-out
individuals** (leave-individual-out) above a label-permutation null. Because identity
is held out and the label never saw the audio, a positive result cannot be explained by
recognising the whale, the recorder, or the site [@tennessen2019; @holt2024masking].

Mirrors notebook Cells 7 + 9 exactly, but runs locally (no Colab) and is resumable:
embeddings checkpoint to an .npz, so a crash continues rather than restarts.

Inputs:
  --clips DIR     folder with clips_manifest.json + context_labeled_calls.csv
                  (produced by dtag_local_extract.py then dtag_context_labels.py)
Outputs:
  <clips>/call_embeddings.npz             AVES2 embeddings + metadata (checkpoint)
  reports/context_decode_summary.json     bal.acc, null mean, p-value per model
  figures/context_decode.png              bar chart vs permutation null
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
REPORT = REPO / "reports" / "context_decode_summary.json"
FIG = REPO / "figures" / "context_decode.png"
TARGET_SR = 16000
SEED, N_PERM = 0, 200


def encode_clips(clips: Path, rows, log=print):
    """Encode each clip with frozen AVES2 (mean-pooled features). Resumable via npz."""
    emb_npz = clips / "call_embeddings.npz"
    embs, meta, done = [], [], set()
    if emb_npz.exists():
        prev = np.load(emb_npz, allow_pickle=True)
        embs = list(prev["embeddings"])
        meta = list(prev["metadata"])
        done = {m["clip"] for m in meta}
        log(f"resume: {len(embs)} clips already encoded")

    # If everything is already encoded, return WITHOUT importing torch. Loading PyTorch
    # (Intel libiomp) into the same process as the sklearn decode deadlocks the MLP head
    # via the well-known dual-OpenMP-runtime hang, so we avoid the import entirely when
    # there is nothing left to encode (the common resume/decode path).
    if not [r for r in rows if r["clip"] not in done]:
        log("all clips already encoded; skipping model load")
        return np.array(embs, np.float32), meta

    import librosa
    import torch
    from avex import load_model

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log(f"AVES2 device: {device}")
    model = load_model("esp_aves2_sl_beats_all", return_features_only=True, device=device)
    model.eval()

    def encode(wav):
        t = torch.from_numpy(wav).unsqueeze(0).float().to(device)
        with torch.no_grad():
            f = model(t)
        return f.cpu().numpy().mean(axis=1)[0]

    todo = [r for r in rows if r["clip"] not in done]
    log(f"encoding {len(todo)} clips ...")
    for i, r in enumerate(todo):
        p = clips / r["clip"]
        if not p.exists():
            continue
        try:
            wav, _ = librosa.load(str(p), sr=TARGET_SR, mono=True)
        except Exception:
            continue
        if len(wav) < TARGET_SR:
            wav = np.pad(wav, (0, TARGET_SR - len(wav)))
        try:
            e = encode(wav)
        except Exception:
            continue
        embs.append(e)
        meta.append({"clip": r["clip"], "deployment": r["deployment"],
                     "abs_t": r["abs_t"], "dur": r["dur"], "context": r["context"]})
        if (i + 1) % 50 == 0:
            np.savez_compressed(emb_npz, embeddings=np.array(embs, np.float32),
                                metadata=np.array(meta, object))
            log(f"  {i + 1}/{len(todo)} encoded")
    np.savez_compressed(emb_npz, embeddings=np.array(embs, np.float32),
                        metadata=np.array(meta, object))
    log(f"encoded {len(embs)} clips -> {emb_npz}")
    return np.array(embs, np.float32), meta


def logo_balacc(X, y, groups, kind, seed=SEED):
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.model_selection import LeaveOneGroupOut
    from sklearn.metrics import balanced_accuracy_score

    def pipe():
        base = (LogisticRegression(max_iter=5000, class_weight="balanced") if kind == "linear"
                else MLPClassifier(hidden_layer_sizes=(128,), max_iter=400, alpha=1e-3,
                                   random_state=seed))
        return make_pipeline(StandardScaler(), base)

    logo = LeaveOneGroupOut()
    yt, yp = [], []
    for tr, te in logo.split(X, y, groups):
        if len(set(y[tr])) < 2:
            continue
        yp.append(pipe().fit(X[tr], y[tr]).predict(X[te]))
        yt.append(y[te])
    yt, yp = np.concatenate(yt), np.concatenate(yp)
    return balanced_accuracy_score(yt, yp)


def main() -> int:
    import pandas as pd

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clips", default=r"D:/dtag_run/clips")
    ap.add_argument("--n-perm", type=int, default=N_PERM,
                    help="permutations for the linear null (the cheap, primary probe)")
    ap.add_argument("--mlp-perm", type=int, default=50,
                    help="permutations for the MLP null (CPU-expensive; obs >20 SD above "
                         "null means even ~50 perms give a stable p well under 0.05)")
    ap.add_argument("--models", default="linear,mlp",
                    help="comma-separated decode heads to run. The linear probe is the "
                         "primary, testable head; the MLP null is O(n_samples) per refit "
                         "and becomes intractable at full scale (~11k calls x 22 folds), so "
                         "'--models linear' gives the main result without the multi-hour "
                         "MLP null.")
    args = ap.parse_args()
    model_kinds = [m.strip() for m in args.models.split(",") if m.strip()]

    clips = Path(args.clips)
    labeled = clips / "context_labeled_calls.csv"
    if not labeled.exists():
        ap.error(f"no context_labeled_calls.csv in {clips} — run dtag_context_labels.py first")
    rows = pd.read_csv(labeled).to_dict("records")
    print(f"{len(rows)} labelled calls")

    X, meta = encode_clips(clips, rows)
    M = pd.DataFrame(meta)
    if len(M) == 0:
        print("no embeddings produced")
        return 1

    usable = [d for d, g in M.groupby("deployment") if g["context"].nunique() == 2]
    print("usable individuals (both contexts):", usable)
    if len(usable) < 2:
        print("need >= 2 individuals with both contexts for leave-individual-out")
        return 1

    sub = M[M["deployment"].isin(usable)].reset_index()
    Xs = X[sub["index"].to_numpy()]
    y = sub["context"].to_numpy()
    groups = sub["deployment"].to_numpy()

    results = {"n_calls": int(len(sub)), "n_individuals": int(sub["deployment"].nunique()),
               "deployments": usable,
               "class_counts": {k: int(v) for k, v in pd.Series(y).value_counts().items()},
               "models": {}}
    rng = np.random.default_rng(SEED)
    perms = {"linear": args.n_perm, "mlp": args.mlp_perm}
    for kind in model_kinds:
        nperm = perms[kind]
        obs = logo_balacc(Xs, y, groups, kind)
        null = np.array([logo_balacc(Xs, rng.permutation(y), groups, kind)
                         for _ in range(nperm)])
        p = (np.sum(null >= obs) + 1) / (len(null) + 1)
        results["models"][kind] = {"balanced_accuracy": float(obs),
                                   "null_mean": float(null.mean()),
                                   "null_std": float(null.std()),
                                   "n_perm": int(nperm), "pvalue": float(p)}
        print(f"{kind}: leave-individual-out bal.acc = {obs:.3f} "
              f"(null {null.mean():.3f}+/-{null.std():.3f}, p={p:.2e})")

    results["caveats"] = [
        "Context label is movement-only (depth + jerk); decoder input is communicative "
        "calls -> non-circular.",
        "Echolocation excluded by band/duration; residual click leakage is a limitation.",
        "Leave-individual-out so identity cannot stand in for behaviour.",
        "Association, not 'meaning'; non-invasive re-analysis of archived DTAG data.",
        "Absolute call time assumes contiguous audio from prh t=0.",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ks = list(results["models"])
        vals = [results["models"][k]["balanced_accuracy"] for k in ks]
        nm = [results["models"][k]["null_mean"] for k in ks]
        xpos = np.arange(len(ks))
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.bar(xpos, vals, width=0.5, color="#2a7fb8", label="leave-individual-out bal. acc")
        ax.plot(xpos, nm, "r_", markersize=40, markeredgewidth=3, label="permutation null")
        ax.axhline(0.5, ls="--", c="gray", lw=1, label="chance")
        for i, v in enumerate(vals):
            ax.text(i, v + 0.02, f"{v:.2f}\n(p={results['models'][ks[i]]['pvalue']:.1e})",
                    ha="center", fontsize=9)
        ax.set_xticks(xpos); ax.set_xticklabels(ks); ax.set_ylim(0, 1)
        ax.set_ylabel("balanced accuracy")
        ax.set_title(f"Context from communicative calls\n{results['n_calls']} calls, "
                     f"{results['n_individuals']} individuals, leave-individual-out")
        ax.legend(fontsize=8); plt.tight_layout()
        FIG.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(FIG, dpi=150, bbox_inches="tight")
        print("wrote", FIG)
    except Exception as e:
        print("figure skipped:", e)

    print("wrote", REPORT)
    print(json.dumps(results["models"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
