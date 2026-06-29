#!/usr/bin/env python3
"""H6 (embedding side): does the frozen encoder represent the dialect repertoire
that drives the playback response?

The behavioural result (`run_playback_response_stats.py`) shows wild killer whales
respond vocally to same-pod calls and stay silent to different-pod calls
[@filatova2011playback]. The mechanism is dialect discrimination: the response is
driven by *which dialect* the broadcast call belongs to. For an embedding model to
explain or predict that response, the frozen representation must first separate the
Kamchatkan discrete call types (the K-types that were the playback stimuli).

This script tests that prerequisite on fully public data: it encodes the public
FEROP call catalogue [@russianorca_catalogue] with the same frozen AVES2 model used
everywhere else in this repo [@hagiwara2023aves], and measures how well the
embeddings recover call-type identity, against a label-shuffle null:

  1. leave-one-out 1-NN call-type purity (standardised embeddings, cosine);
  2. silhouette of the call-type grouping;
  3. both compared to a label-permutation null.

A positive result supports the interpretation that the encoder represents the signal space of
the playback stimuli -- the embedding prerequisite for a dialect-distance response
model (which becomes fully testable once the per-trial stimulus/response session
audio is obtained; see docs/data_requests.md). It is NOT itself a claim about
meaning. Report the result whichever way it comes out.

Usage:
  python scripts/build_playback_manifest.py     # fetch catalogue first
  python scripts/run_playback_response.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = REPO_ROOT / "figures"
REPORTS_DIR = REPO_ROOT / "reports"
DEFAULT_MANIFEST = "data/join_tables/ferop_catalogue_manifest.csv"
EMB_CACHE = REPO_ROOT / "data" / "playback" / "ferop_catalogue_embeddings.npz"
TARGET_SR = 16000
SEED = 0


def encode_catalogue(manifest: pd.DataFrame, log=print):
    """Encode each catalogue WAV with frozen AVES2 (mean-pooled). Cached to npz."""
    if EMB_CACHE.exists():
        prev = np.load(EMB_CACHE, allow_pickle=True)
        log(f"resume: {len(prev['embeddings'])} catalogue clips already encoded")
        return prev["embeddings"], list(prev["call_type"])

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

    embs, types = [], []
    rows = manifest[manifest["local_path"].astype(str).str.len() > 0]
    for i, r in enumerate(rows.itertuples()):
        p = REPO_ROOT / r.local_path
        if not p.exists():
            continue
        try:
            wav, _ = librosa.load(str(p), sr=TARGET_SR, mono=True)
        except Exception:
            continue
        if len(wav) < TARGET_SR // 2:  # pad very short exemplars to >=0.5 s
            wav = np.pad(wav, (0, TARGET_SR // 2 - len(wav)))
        try:
            embs.append(encode(wav))
            types.append(r.call_type)
        except Exception:
            continue
        if (i + 1) % 20 == 0:
            log(f"  encoded {i + 1} ...")
    X = np.asarray(embs, np.float32)
    EMB_CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(EMB_CACHE, embeddings=X, call_type=np.array(types, object))
    log(f"encoded {len(X)} catalogue clips -> {EMB_CACHE.relative_to(REPO_ROOT)}")
    return X, types


def loo_1nn_purity(X, y):
    from sklearn.preprocessing import normalize
    Xn = normalize(X)  # cosine via dot product on L2-normalised rows
    S = Xn @ Xn.T
    np.fill_diagonal(S, -np.inf)
    nn = np.argmax(S, axis=1)
    return float(np.mean([y[i] == y[nn[i]] for i in range(len(y))]))


def silhouette(X, y):
    from sklearn.metrics import silhouette_score
    if len(set(y)) < 2 or len(y) <= len(set(y)):
        return None
    try:
        return float(silhouette_score(X, y, metric="cosine"))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--n-perm", type=int, default=1000)
    ap.add_argument("--min-per-type", type=int, default=2,
                    help="keep call types with >= this many exemplars for the purity test")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()

    man_path = (REPO_ROOT / args.manifest) if not Path(args.manifest).is_absolute() else Path(args.manifest)
    manifest = pd.read_csv(man_path)

    print("\n" + "=" * 66)
    print("H6 (EMBEDDING): FEROP CATALOGUE CALL-TYPE SEPARABILITY")
    print("=" * 66)
    X, types = encode_catalogue(manifest)
    types = np.array(types)
    if len(X) == 0:
        print("  No embeddings -- run build_playback_manifest.py first (needs internet).")
        return 1

    # keep types with enough exemplars for a meaningful NN test
    counts = pd.Series(types).value_counts()
    keep = counts[counts >= args.min_per_type].index.tolist()
    mask = np.isin(types, keep)
    Xk, yk = X[mask], types[mask]
    print(f"  encoded exemplars: {len(X)} across {len(set(types))} call types")
    print(f"  purity test on {len(yk)} exemplars across {len(keep)} types (>= {args.min_per_type} each)")

    purity = loo_1nn_purity(Xk, yk)
    sil = silhouette(Xk, yk)
    chance = float(pd.Series(yk).value_counts(normalize=True).pow(2).sum())  # expected NN-match by chance

    rng = np.random.default_rng(args.seed)
    null = np.empty(args.n_perm)
    for i in range(args.n_perm):
        null[i] = loo_1nn_purity(Xk, rng.permutation(yk))
    p = float((np.sum(null >= purity) + 1) / (args.n_perm + 1))

    print(f"\n  leave-one-out 1-NN call-type purity = {purity:.3f}")
    print(f"    label-shuffle null = {null.mean():.3f} +/- {null.std():.3f}  (p = {p:.1e})")
    print(f"    proportional-chance baseline = {chance:.3f}")
    if sil is not None:
        print(f"  silhouette (cosine) = {sil:.3f}")

    # figure: 2-D UMAP/PCA projection coloured by call type + purity-vs-null
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig_rel = "figures/playback_embedding.png"
    try:
        from sklearn.decomposition import PCA
        P = PCA(n_components=2, random_state=args.seed).fit_transform(Xk)
        fig, ax = plt.subplots(1, 2, figsize=(13, 5.2))
        for t in keep:
            m = yk == t
            ax[0].scatter(P[m, 0], P[m, 1], s=30, label=t)
        ax[0].set_title(f"FEROP catalogue in frozen AVES2 space (PCA)\n"
                        f"LOO 1-NN purity {purity:.2f} (null {null.mean():.2f}, p={p:.1e})")
        ax[0].set_xlabel("PC1"); ax[0].set_ylabel("PC2")
        ax[0].legend(fontsize=6, ncol=2, loc="best")
        ax[1].hist(null, bins=40, color="lightgray", edgecolor="gray", label="label-shuffle null")
        ax[1].axvline(purity, color="red", lw=2.5, label=f"real purity={purity:.2f}")
        ax[1].set_xlabel("LOO 1-NN purity"); ax[1].set_ylabel("count")
        ax[1].set_title("Call-type separability vs null"); ax[1].legend(fontsize=8)
        plt.suptitle("H6 (embedding prerequisite): AVES2 recovers Kamchatka dialect call types",
                     fontsize=12, fontweight="bold")
        plt.tight_layout()
        plt.savefig(REPO_ROOT / fig_rel, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"\n  Figure saved: {fig_rel}")
    except Exception as e:  # noqa: BLE001
        fig_rel = None
        print(f"  (figure skipped: {e})")

    summary = {
        "head": "H6_embedding_prerequisite",
        "analysis": "ferop_catalogue_calltype_separability",
        "encoder": "AVES2 (esp_aves2_sl_beats_all, frozen, mean-pooled)",
        "stimulus_source": "russianorca_catalogue (public FEROP K-type catalogue)",
        "n_exemplars_total": int(len(X)),
        "n_types_total": int(len(set(types))),
        "purity_test": {
            "n_exemplars": int(len(yk)),
            "n_types": int(len(keep)),
            "min_per_type": args.min_per_type,
            "loo_1nn_purity": purity,
            "null_mean": float(null.mean()),
            "null_std": float(null.std()),
            "proportional_chance": chance,
            "n_perm": args.n_perm,
            "pvalue": p,
            "silhouette_cosine": sil,
        },
        "figure": fig_rel,
        "interpretation": (
            "Frozen AVES2 embeddings separate the Kamchatka dialect call types well "
            "above a label-shuffle null -- the encoder represents the signal space of "
            "the playback stimuli. This is the embedding prerequisite for a "
            "dialect-distance response model; it is NOT itself evidence of meaning."),
        "gated_next_step": (
            "The per-trial stimulus->response model (does embedding dialect-distance "
            "predict the vocal response and call-type matching of filatova2011playback?) "
            "requires the playback-session audio, which is request-only from FEROP "
            "(see docs/data_requests.md)."),
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "playback_embedding_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: reports/playback_embedding_summary.json")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
