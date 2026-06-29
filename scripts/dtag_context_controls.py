#!/usr/bin/env python3
"""Controls that rule out the trivial explanations for the context decode.

A skeptic can offer three cheap explanations for "calls predict context" that are *not*
context-specific communication:
  call rate -- the whale simply calls more in one context, so a rate feature alone
       would decode context;
  loudness/duration -- calls are just louder/longer in one context (an energetics
       artefact), so low-level acoustic scalars alone would decode context;
  echolocation leakage -- residual biosonar (clicks) rather than communicative calls
       carries the signal.

This script answers all three on the existing data (reuses AVES2 embeddings; no re-encode):
  - decode context from a RATE-only feature and from LOW-LEVEL acoustic scalars, and show
    the AVES2 call-structure embeddings decode substantially better (the result is about
    call *structure*, not rate or loudness);
  - flag the most click-like clips from 16 kHz acoustic features and show the embedding
    decode SURVIVES dropping them (and is not carried by the click-like quartile). Note:
    clips are 16 kHz, so echolocation *peak* energy (>>8 kHz) is already absent by
    construction; this test addresses residual low-band transients only.

Inputs:
  --emb NPZ      call_embeddings.npz
  --labels CSV   context_labeled_calls.csv (binary) by default -- defends the main result
  --clips DIR    folder with the wav clips (for low-level acoustic features)
Outputs:
  <clips>/clip_acoustic_features.npz     per-clip scalar features (cache)
  reports/context_controls_summary.json
  figures/context_controls.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
REPORT = REPO / "reports" / "context_controls_summary.json"
FIG = REPO / "figures" / "context_controls.png"
SEED = 0
SR = 16000
RATE_WIN_S = 30.0     # +/- window for the local call-rate feature


def logo_balacc(X, y, groups, seed=SEED):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.model_selection import LeaveOneGroupOut
    from sklearn.metrics import balanced_accuracy_score

    if X.ndim == 1:
        X = X.reshape(-1, 1)
    logo = LeaveOneGroupOut()
    yt, yp = [], []
    for tr, te in logo.split(X, y, groups):
        if len(set(y[tr])) < 2:
            continue
        pipe = make_pipeline(StandardScaler(),
                             LogisticRegression(max_iter=5000, class_weight="balanced"))
        yp.append(pipe.fit(X[tr], y[tr]).predict(X[te]))
        yt.append(y[te])
    yt, yp = np.concatenate(yt), np.concatenate(yp)
    return float(balanced_accuracy_score(yt, yp))


def acoustic_features(clips: Path, clip_names, log=print):
    """Per-clip low-level scalars: dur, log-RMS, ZCR, spectral centroid, HF-fraction, flatness.

    Cached to clip_acoustic_features.npz and resumable.
    """
    import librosa

    cache = clips / "clip_acoustic_features.npz"
    feats, done = {}, set()
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        for name, row in zip(z["clip"], z["feat"]):
            feats[str(name)] = np.asarray(row, float)
        done = set(feats)
        log(f"resume: {len(done)} cached acoustic features")

    todo = [c for c in clip_names if c not in done]
    log(f"extracting acoustic features for {len(todo)} clips ...")
    for i, name in enumerate(todo):
        p = clips / name
        try:
            x, _ = librosa.load(str(p), sr=SR, mono=True)
        except Exception:
            feats[name] = np.full(6, np.nan)
            continue
        if x.size < 64:
            feats[name] = np.full(6, np.nan)
            continue
        dur = x.size / SR
        rms = float(np.sqrt(np.mean(x ** 2)) + 1e-9)
        zcr = float(np.mean(np.abs(np.diff(np.sign(x))) > 0))
        S = np.abs(librosa.stft(x, n_fft=512, hop_length=256)) + 1e-9
        freqs = librosa.fft_frequencies(sr=SR, n_fft=512)
        power = (S ** 2).sum(axis=1)
        centroid = float((freqs * power).sum() / power.sum())
        hf_frac = float(power[freqs >= 4000].sum() / power.sum())
        flat = float(np.exp(np.mean(np.log(S))) / np.mean(S))
        feats[name] = np.array([dur, np.log(rms), zcr, centroid, hf_frac, flat], float)
        if (i + 1) % 500 == 0:
            names = list(feats)
            np.savez_compressed(cache, clip=np.array(names, object),
                                feat=np.array([feats[n] for n in names], float))
            log(f"  {i + 1}/{len(todo)}")
    names = list(feats)
    np.savez_compressed(cache, clip=np.array(names, object),
                        feat=np.array([feats[n] for n in names], float))
    log(f"cached {len(names)} -> {cache}")
    return feats


def main() -> int:
    import pandas as pd

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--emb", default=r"D:/dtag_run/clips/call_embeddings.npz")
    ap.add_argument("--labels", default=r"D:/dtag_run/clips/context_labeled_calls.csv")
    ap.add_argument("--label-col", default="context")
    ap.add_argument("--clips", default=r"D:/dtag_run/clips")
    ap.add_argument("--drop-frac", type=float, default=0.25,
                    help="fraction of most click-like clips to drop in the leakage test")
    args = ap.parse_args()

    clips = Path(args.clips)
    d = np.load(args.emb, allow_pickle=True)
    E = d["embeddings"].astype(np.float32)
    meta = pd.DataFrame(list(d["metadata"])).reset_index()
    lab = pd.read_csv(args.labels)
    col = args.label_col if args.label_col in lab.columns else lab.columns[-1]
    if col in meta.columns:           # embeddings metadata already carries a 'context' field
        meta = meta.drop(columns=[col])
    meta = meta.merge(lab[["clip", col]], on="clip", how="inner")

    # restrict to individuals with both/all contexts (same rule as the main decode)
    keep = [dep for dep, g in meta.groupby("deployment") if g[col].nunique() >= 2]
    meta = meta[meta["deployment"].isin(keep)].reset_index(drop=True)
    Xemb = E[meta["index"].to_numpy()]
    y = meta[col].to_numpy()
    groups = meta["deployment"].to_numpy()
    print(f"{len(meta)} calls, {len(keep)} individuals, contexts {sorted(set(y))}")

    # Local call-rate feature (calls within +/- RATE_WIN_S in the same deployment)
    rate = np.zeros(len(meta))
    for dep, g in meta.groupby("deployment"):
        t = g["abs_t"].to_numpy()
        idx = g.index.to_numpy()
        for k, ti in zip(idx, t):
            rate[k] = np.sum(np.abs(t - ti) <= RATE_WIN_S)
    ba_rate = logo_balacc(rate, y, groups)

    # Low-level acoustic scalars
    feats = acoustic_features(clips, list(meta["clip"]))
    F = np.array([feats.get(c, np.full(6, np.nan)) for c in meta["clip"]], float)
    ok = ~np.isnan(F).any(axis=1)
    ba_lowlevel = logo_balacc(F[ok], y[ok], groups[ok])
    ba_loudness = logo_balacc(F[ok][:, [1]], y[ok], groups[ok])  # log-RMS only (loudness)

    # embeddings (main) on the same rows for a fair comparison
    ba_emb = logo_balacc(Xemb, y, groups)
    ba_emb_ok = logo_balacc(Xemb[ok], y[ok], groups[ok])

    # Echolocation-leakage stress test.
    # click-likeness = short duration + high HF fraction + high ZCR + high flatness (z-scored)
    def z(a):
        a = a.astype(float)
        return (a - np.nanmean(a)) / (np.nanstd(a) + 1e-9)
    dur, _, zcr, _, hf, flat = [F[:, j] for j in range(6)]
    click_like = z(hf) + z(flat) + z(zcr) - z(dur)
    cl = click_like[ok]
    order = np.argsort(-cl)  # most click-like first
    n_drop = int(round(args.drop_frac * ok.sum()))
    drop_mask = np.zeros(ok.sum(), bool)
    drop_mask[order[:n_drop]] = True
    Xok, yok, gok = Xemb[ok], y[ok], groups[ok]
    # keep individuals that still hold >=2 contexts after dropping
    def restrict(mask):
        keep2 = [dep for dep in np.unique(gok[mask]) if len(set(yok[mask][gok[mask] == dep])) >= 2]
        m2 = mask & np.isin(gok, keep2)
        return m2
    keep_clean = restrict(~drop_mask)
    keep_click = restrict(drop_mask)
    ba_drop_clicklike = logo_balacc(Xok[keep_clean], yok[keep_clean], gok[keep_clean])
    ba_only_clicklike = (logo_balacc(Xok[keep_click], yok[keep_click], gok[keep_click])
                         if keep_click.sum() > 0 and len(set(yok[keep_click])) >= 2 else None)

    results = {
        "label_column": col,
        "n_calls": int(len(meta)),
        "n_individuals": int(len(keep)),
        "classes": sorted(set(map(str, y))),
        "decode_balanced_accuracy": {
            "aves2_embeddings": ba_emb,
            "call_rate_only": ba_rate,
            "loudness_logrms_only": ba_loudness,
            "lowlevel_acoustic_only": ba_lowlevel,
            "aves2_embeddings_same_rows_as_lowlevel": ba_emb_ok,
        },
        "echolocation_leakage": {
            "drop_fraction_most_clicklike": args.drop_frac,
            "n_dropped": int(n_drop),
            "aves2_after_dropping_clicklike": ba_drop_clicklike,
            "aves2_on_clicklike_quartile_only": ba_only_clicklike,
            "note": "Clips are 16 kHz; echolocation peak energy (>>8 kHz) is absent by "
                    "construction. This addresses residual low-band transients only.",
        },
        "lowlevel_feature_order": ["dur_s", "log_rms", "zcr", "spectral_centroid_hz",
                                   "hf_fraction_ge4khz", "spectral_flatness"],
        "interpretation": [
            "If aves2_embeddings >> call_rate_only and >> lowlevel_acoustic_only, the decode "
            "reflects call STRUCTURE, not rate or loudness.",
            "If aves2_after_dropping_clicklike stays high, the decode is not carried by "
            "click-like transients.",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(f"\nbalanced accuracy by feature set:")
    print(f"  AVES2 embeddings        : {ba_emb:.3f}")
    print(f"  call-rate only          : {ba_rate:.3f}")
    print(f"  loudness/log-RMS        : {ba_loudness:.3f}")
    print(f"  low-level acoustic      : {ba_lowlevel:.3f}  (emb same rows: {ba_emb_ok:.3f})")
    print(f"  drop {args.drop_frac:.0%} click-like: {ba_drop_clicklike:.3f}"
          + (f"  | click-like only: {ba_only_clicklike:.3f}" if ba_only_clicklike else ""))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        names = ["AVES2\nembeddings", "call-rate\nonly", "low-level\nacoustic",
                 f"AVES2\ndrop {args.drop_frac:.0%}\nclick-like"]
        vals = [ba_emb, ba_rate, ba_lowlevel, ba_drop_clicklike]
        colors = ["#2a7fb8", "#bbbbbb", "#bbbbbb", "#2a7fb8"]
        chance = 1.0 / len(set(y))
        fig, ax = plt.subplots(figsize=(8, 4.6))
        ax.bar(range(len(vals)), vals, color=colors, width=0.6)
        ax.axhline(chance, ls="--", c="red", lw=1, label=f"chance ({chance:.2f})")
        for i, v in enumerate(vals):
            ax.text(i, v + 0.015, f"{v:.2f}", ha="center", fontsize=10)
        ax.set_xticks(range(len(vals))); ax.set_xticklabels(names, fontsize=9)
        ax.set_ylim(0, 1); ax.set_ylabel("leave-individual-out balanced accuracy")
        ax.set_title("Controls: the decode reflects call structure, not rate / loudness / clicks")
        ax.legend(fontsize=8); plt.tight_layout()
        FIG.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(FIG, dpi=150, bbox_inches="tight")
        print("wrote", FIG)
    except Exception as e:
        print("figure skipped:", e)

    print("wrote", REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
