#!/usr/bin/env python3
"""H3: Sequence language model over per-encounter call-type streams.

Trains a small BERT-style masked language model on per-encounter call-type
sequences and tests whether call ORDER carries learnable structure (real vs
order-shuffled sequences), in the spirit of the sperm-whale coda work
[@sharma2024].

Two methodological fixes over the naive version:

  1. BALANCED VOCABULARY. The previous tokeniser used HDBSCAN, which on these
     embeddings collapsed to ~4 call types with >95% of calls in one token --
     a degenerate alphabet that makes any sequence test meaningless. We instead
     quantise the embeddings with k-means into a fixed vocabulary of K call
     types (default 40), giving a well-populated, balanced alphabet. Token
     entropy is reported to confirm balance.

  2. HELD-OUT EVALUATION. Encounters are split into train/val. The MLM is
     trained only on train encounters; the real-vs-shuffled comparison and the
     permutation test are computed on held-out val encounters. A unigram
     baseline (predicting the marginal token distribution) is reported as an
     absolute reference for the loss scale.

Usage:
  python scripts/run_h3_sequence_lm.py --embeddings data/embeddings/aves2_full_labeled.npz \
      --epochs 30 --vocab-size 40 --device cuda
"""

import argparse
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message=".*enable_nested_tensor.*")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from torch.utils.data import DataLoader, Dataset

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"
SEED = 0

N_LAYERS = 6
N_HEADS = 8
D_MODEL = 512
D_FF = 2048
DROPOUT = 0.1
MAX_SEQ_LEN = 256
MASK_PROB = 0.15

DEFAULT_EPOCHS = 30
DEFAULT_LR = 1e-4
DEFAULT_BATCH_SIZE = 32
DEFAULT_VOCAB = 40
PCA_COMPONENTS = 32
VAL_FRACTION = 0.2


def quantize_embeddings(embeddings, vocab_size=DEFAULT_VOCAB, seed=SEED):
    """Assign each call a discrete call-type ID via PCA + balanced k-means."""
    n_comp = min(PCA_COMPONENTS, embeddings.shape[1], embeddings.shape[0] - 1)
    reduced = PCA(n_components=n_comp, random_state=seed).fit_transform(embeddings)
    km = MiniBatchKMeans(
        n_clusters=vocab_size,
        random_state=seed,
        n_init=10,
        batch_size=4096,
        max_iter=300,
    )
    return km.fit_predict(reduced).astype(int)


def token_entropy_bits(ids: np.ndarray, k: int) -> float:
    counts = np.bincount(ids, minlength=k).astype(float)
    p = counts / counts.sum()
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def load_metadata(npz_path: Path):
    data = np.load(npz_path, allow_pickle=True)
    if "metadata" in data:
        meta = data["metadata"]
        if isinstance(meta, np.ndarray) and meta.dtype == object:
            return list(meta)
    return None


def _metadata_start_seconds(item, fallback_index: int) -> float:
    """Return a stable time key for chronological sequence construction."""
    if isinstance(item, dict):
        for field in ("begin_sec", "start_time_s", "FileBeginSec"):
            if field in item:
                try:
                    return float(item[field])
                except (TypeError, ValueError):
                    pass
    return float(fallback_index)


def build_encounter_sequences(call_ids, metadata, min_len=3):
    """Group calls by provider/source file and sort each sequence by start time."""
    n = len(call_ids)
    if metadata is not None and len(metadata) == n:
        enc = {}
        for i, m in enumerate(metadata):
            sf = m.get("soundfile", "") if isinstance(m, dict) else ""
            prov = m.get("provider", "") if isinstance(m, dict) else ""
            enc.setdefault(f"{prov}::{sf}", []).append((_metadata_start_seconds(m, i), i))
    else:
        enc = {"all": [(float(i), i) for i in range(n)]}

    seqs = []
    for rows in enc.values():
        ordered = [i for _, i in sorted(rows, key=lambda item: (item[0], item[1]))]
        if len(ordered) >= min_len:
            seqs.append([int(call_ids[i]) for i in ordered])
    return seqs


class CallVocab:
    PAD, MASK, BOS, EOS = 0, 1, 2, 3
    SPECIAL_OFFSET = 4

    def __init__(self, n_call_types):
        self.n_call_types = n_call_types
        self.vocab_size = n_call_types + self.SPECIAL_OFFSET

    def encode_sequence(self, call_ids, max_len=MAX_SEQ_LEN):
        tokens = [self.BOS]
        for cid in call_ids[: max_len - 2]:
            tokens.append(cid + self.SPECIAL_OFFSET)
        tokens.append(self.EOS)
        return tokens


class MLMDataset(Dataset):
    def __init__(self, sequences, vocab, max_len=MAX_SEQ_LEN, mask_prob=MASK_PROB, seed=SEED):
        self.vocab = vocab
        self.max_len = max_len
        self.mask_prob = mask_prob
        self.rng = np.random.default_rng(seed)
        self.encoded = [vocab.encode_sequence(s, max_len) for s in sequences]

    def __len__(self):
        return len(self.encoded)

    def __getitem__(self, idx):
        tokens = self.encoded[idx]
        input_ids = list(tokens)
        labels = [-100] * len(tokens)
        for i in range(1, len(tokens) - 1):
            if self.rng.random() < self.mask_prob:
                labels[i] = input_ids[i]
                r = self.rng.random()
                if r < 0.8:
                    input_ids[i] = self.vocab.MASK
                elif r < 0.9:
                    input_ids[i] = int(
                        self.rng.integers(self.vocab.SPECIAL_OFFSET, self.vocab.vocab_size)
                    )
        pad = self.max_len - len(input_ids)
        input_ids += [self.vocab.PAD] * pad
        labels += [-100] * pad
        attn = [1] * len(tokens) + [0] * pad
        return {
            "input_ids": torch.tensor(input_ids),
            "labels": torch.tensor(labels),
            "attention_mask": torch.tensor(attn),
        }


class CallSequenceBERT(nn.Module):
    def __init__(self, vocab_size, max_len=MAX_SEQ_LEN):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, D_MODEL, padding_idx=CallVocab.PAD)
        self.position_embedding = nn.Embedding(max_len, D_MODEL)
        self.layer_norm = nn.LayerNorm(D_MODEL)
        self.dropout = nn.Dropout(DROPOUT)
        layer = nn.TransformerEncoderLayer(
            d_model=D_MODEL,
            nhead=N_HEADS,
            dim_feedforward=D_FF,
            dropout=DROPOUT,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=N_LAYERS)
        self.mlm_head = nn.Sequential(
            nn.Linear(D_MODEL, D_MODEL),
            nn.GELU(),
            nn.LayerNorm(D_MODEL),
            nn.Linear(D_MODEL, vocab_size),
        )
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0.0, 0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, 0.0, 0.02)
                if m.padding_idx is not None:
                    nn.init.zeros_(m.weight[m.padding_idx])

    def forward(self, input_ids, attention_mask):
        batch, length = input_ids.shape
        del batch
        pos = torch.arange(length, device=input_ids.device).unsqueeze(0).expand_as(input_ids)
        x = self.token_embedding(input_ids) + self.position_embedding(pos)
        x = self.dropout(self.layer_norm(x))
        x = self.encoder(x, src_key_padding_mask=attention_mask == 0)
        return self.mlm_head(x)

    @property
    def num_parameters(self):
        return sum(p.numel() for p in self.parameters())


def train_mlm(model, loader, epochs, lr, device):
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    model.train()
    losses = []
    for ep in range(epochs):
        tot, nb = 0.0, 0
        for b in loader:
            logits = model(b["input_ids"].to(device), b["attention_mask"].to(device))
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                b["labels"].to(device).view(-1),
                ignore_index=-100,
            )
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tot += loss.item()
            nb += 1
        sched.step()
        losses.append(tot / max(nb, 1))
        if (ep + 1) % 5 == 0 or ep == 0:
            print(f"    epoch {ep + 1:3d}/{epochs}: loss={losses[-1]:.4f}")
    return losses


@torch.no_grad()
def evaluate_mlm(model, loader, device):
    model.eval()
    tot, nb = 0.0, 0
    for b in loader:
        logits = model(b["input_ids"].to(device), b["attention_mask"].to(device))
        loss = F.cross_entropy(
            logits.view(-1, logits.size(-1)),
            b["labels"].to(device).view(-1),
            ignore_index=-100,
        )
        tot += loss.item()
        nb += 1
    return tot / max(nb, 1)


def permutation_test_loss(model, sequences, vocab, device, n_perm, batch_size, seed):
    """Shuffle within-encounter call order; recompute held-out MLM loss."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n_perm):
        shuffled = []
        for s in sequences:
            t = list(s)
            rng.shuffle(t)
            shuffled.append(t)
        ds = MLMDataset(shuffled, vocab, seed=seed + i + 1000)
        out.append(evaluate_mlm(model, DataLoader(ds, batch_size=batch_size), device))
    return np.array(out)


def unigram_baseline_loss(sequences, vocab):
    """Cross-entropy of predicting the marginal token distribution."""
    counts = np.zeros(vocab.vocab_size)
    for s in sequences:
        for cid in s:
            counts[cid + vocab.SPECIAL_OFFSET] += 1
    p = counts / counts.sum()
    p = np.clip(p, 1e-12, None)
    return float(-np.sum((counts / counts.sum()) * np.log(p)))


def make_figure(losses, real_loss, shuffled, unigram, k, n_enc, n_train, n_val,
                entropy_bits, encoder_name, pvalue):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    axes[0].plot(range(1, len(losses) + 1), losses)
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("MLM loss")
    axes[0].set_title("Training loss")
    axes[0].grid(alpha=0.3)

    axes[1].hist(shuffled, bins=30, label="Order-shuffled (held-out)")
    axes[1].axvline(real_loss, lw=2.5, label=f"Real order={real_loss:.3f}")
    axes[1].axvline(unigram, lw=1.5, ls=":", label=f"Unigram={unigram:.3f}")
    axes[1].set_xlabel("MLM loss (held-out)")
    axes[1].set_ylabel("Count")
    axes[1].set_title(f"Order test (p={pvalue:.2e})")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.3)

    axes[2].axis("off")
    txt = (
        f"H3: Sequence MLM\n{'-' * 32}\n\n"
        f"Vocabulary (k-means): {k} call types\n"
        f"Token entropy: {entropy_bits:.2f} bits (max {np.log2(k):.2f})\n"
        f"Encounters: {n_enc}  (train {n_train} / val {n_val})\n\n"
        f"Held-out real-order loss: {real_loss:.4f}\n"
        f"Held-out shuffled loss:   {shuffled.mean():.4f} ± {shuffled.std():.4f}\n"
        f"Unigram baseline:         {unigram:.4f}\n"
        f"Delta (shuffled - real):  {shuffled.mean() - real_loss:.4f}\n"
        f"p-value: {pvalue:.2e}\n"
        f"Verdict: {'ORDER MATTERS' if pvalue < 0.05 else 'no order effect'}"
    )
    axes[2].text(0.03, 0.97, txt, transform=axes[2].transAxes, fontsize=10,
                 fontfamily="monospace", va="top")

    plt.suptitle(f"H3: Call-sequence MLM -- {encoder_name.upper()} "
                 f"({k} call types, held-out order test)", fontsize=12, fontweight="bold")
    plt.tight_layout()
    path = FIGURES_DIR / f"h3_sequence_lm_{encoder_name}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    return path


def main():
    parser = argparse.ArgumentParser(description="H3: sequence MLM (balanced vocab, held-out)")
    parser.add_argument("--embeddings", required=True)
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--lr", type=float, default=DEFAULT_LR)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--n-perm", type=int, default=100)
    parser.add_argument("--vocab-size", type=int, default=DEFAULT_VOCAB)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    emb_path = Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: {emb_path} not found.")
        return 1
    device = torch.device(args.device if args.device else
                          ("cuda" if torch.cuda.is_available() else "cpu"))

    data = np.load(emb_path, allow_pickle=True)
    embeddings = data["embeddings"]
    encoder_name = emb_path.stem.replace("_embeddings", "")

    print(f"\n{'=' * 64}")
    print(f"HEAD H3: SEQUENCE LANGUAGE MODEL ({encoder_name.upper()})")
    print(f"{'=' * 64}")
    print(f"  Device: {device}  Embeddings: {embeddings.shape}")

    print(f"\n--- Step 1: balanced k-means tokenisation (K={args.vocab_size}) ---")
    call_ids = quantize_embeddings(embeddings, vocab_size=args.vocab_size, seed=args.seed)
    k = int(call_ids.max()) + 1
    ent = token_entropy_bits(call_ids, k)
    counts = np.bincount(call_ids, minlength=k)
    print(f"  Call types: {k}  token entropy: {ent:.2f} / {np.log2(k):.2f} bits")
    print(f"  Token counts: min={counts.min()}, max={counts.max()}, median={int(np.median(counts))}")

    print("\n--- Step 2: per-encounter sequences ---")
    metadata = load_metadata(emb_path)
    sequences = build_encounter_sequences(call_ids, metadata, min_len=3)
    if not sequences:
        print("  ERROR: no encounter sequences.")
        return 1
    rng = np.random.default_rng(args.seed)
    perm = rng.permutation(len(sequences))
    n_val = max(1, int(len(sequences) * VAL_FRACTION))
    val_idx = set(perm[:n_val].tolist())
    train_seqs = [s for i, s in enumerate(sequences) if i not in val_idx]
    val_seqs = [s for i, s in enumerate(sequences) if i in val_idx]
    print(f"  Encounters: {len(sequences)} (train {len(train_seqs)} / val {len(val_seqs)})")
    lens = [len(s) for s in sequences]
    print(f"  Seq length: min={min(lens)} max={max(lens)} mean={np.mean(lens):.1f}")

    print("\n--- Step 3: train MLM on TRAIN encounters ---")
    vocab = CallVocab(k)
    train_ds = MLMDataset(train_seqs, vocab, seed=args.seed)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              drop_last=len(train_ds) > args.batch_size)
    model = CallSequenceBERT(vocab.vocab_size).to(device)
    print(f"  Params: {model.num_parameters / 1e6:.1f}M  vocab: {vocab.vocab_size}")
    losses = train_mlm(model, train_loader, args.epochs, args.lr, device)

    print("\n--- Step 4: held-out evaluation (VAL encounters) ---")
    val_real = MLMDataset(val_seqs, vocab, seed=args.seed + 42)
    real_loss = evaluate_mlm(model, DataLoader(val_real, batch_size=args.batch_size), device)
    unigram = unigram_baseline_loss(val_seqs, vocab)
    print(f"  Held-out real-order loss: {real_loss:.4f}")
    print(f"  Unigram baseline loss:    {unigram:.4f}")

    print(f"  Permutation test (n={args.n_perm}, held-out order shuffle)...")
    shuffled = permutation_test_loss(model, val_seqs, vocab, device,
                                     args.n_perm, args.batch_size, args.seed)
    pvalue = (np.sum(shuffled <= real_loss) + 1) / (args.n_perm + 1)
    print(f"  Held-out shuffled loss: {shuffled.mean():.4f} ± {shuffled.std():.4f}")
    print(f"  Delta (shuffled-real): {shuffled.mean() - real_loss:.4f}  p={pvalue:.2e}")

    fig_path = make_figure(losses, real_loss, shuffled, unigram, k, len(sequences),
                           len(train_seqs), len(val_seqs), ent, encoder_name, pvalue)
    print(f"  Figure saved: {fig_path}")

    beats_unigram = real_loss < unigram
    print(f"\n{'=' * 64}\nH3 SUMMARY\n{'=' * 64}")
    print(f"  Vocabulary: {k} balanced call types (entropy {ent:.2f}/{np.log2(k):.2f} bits)")
    print(f"  Held-out real-order loss {real_loss:.4f} vs shuffled {shuffled.mean():.4f} "
          f"vs unigram {unigram:.4f}")
    print(f"  Beats unigram baseline: {beats_unigram}")
    print(f"  Order effect p-value: {pvalue:.2e}")
    print(f"  Verdict: {'ORDER carries structure' if pvalue < 0.05 else 'no detectable order effect'}")
    print(f"{'=' * 64}")

    results = {
        "encoder": encoder_name,
        "vocab_size": k,
        "token_entropy_bits": ent,
        "max_entropy_bits": float(np.log2(k)),
        "n_encounters": len(sequences),
        "n_train": len(train_seqs),
        "n_val": len(val_seqs),
        "heldout_real_loss": float(real_loss),
        "heldout_shuffled_loss_mean": float(shuffled.mean()),
        "heldout_shuffled_loss_std": float(shuffled.std()),
        "unigram_baseline_loss": float(unigram),
        "beats_unigram": bool(beats_unigram),
        "order_pvalue": float(pvalue),
        "figure": f"figures/{fig_path.name}",
    }
    (FIGURES_DIR / f"h3_metrics_{encoder_name}.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    print(f"  Metrics JSON: {FIGURES_DIR / f'h3_metrics_{encoder_name}.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
