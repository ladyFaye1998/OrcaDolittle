import torch

from orcadolittle.data.call_streams import (
    NUM_SPECIAL,
    BOS_ID,
    EOS_ID,
    MASK_ID,
    PAD_ID,
    CallStreamDataset,
    Vocab,
    collate_call_streams,
    mlm_mask,
)
from orcadolittle.data.synthetic import (
    SyntheticConfig,
    make_synthetic_streams,
    shuffle_within_sequence,
)


def test_vocab_roundtrip():
    v = Vocab(call_types=("N01", "N02", "S07"))
    assert v.size == NUM_SPECIAL + 3
    ids = v.encode(["N01", "S07", "ZZZ"])
    assert ids[0] == NUM_SPECIAL
    assert ids[2] == 4  # UNK_ID
    tokens = v.decode(ids)
    assert tokens[0] == "N01"
    assert tokens[2] == "[UNK]"


def test_vocab_rejects_special_collision():
    import pytest

    with pytest.raises(ValueError):
        Vocab(call_types=("N01", "[PAD]"))


def test_vocab_from_streams_order_stable():
    v = Vocab.from_streams([["A", "B"], ["B", "C", "A"]])
    assert v.call_types == ("A", "B", "C")


def test_dataset_bos_eos_and_truncation():
    streams = [[5, 6, 7], list(range(5, 5 + 300))]
    ds = CallStreamDataset(streams, max_len=10)
    assert len(ds) == 2
    a = ds[0].tolist()
    assert a[0] == BOS_ID and a[-1] == EOS_ID
    b = ds[1].tolist()
    assert len(b) == 10
    assert b[0] == BOS_ID and b[-1] == EOS_ID


def test_dataset_drops_short():
    ds = CallStreamDataset([[5], [5, 6]], max_len=8, min_len=2)
    assert len(ds) == 1


def test_collate_pads_and_masks():
    streams = [[5, 6, 7], [5, 6, 7, 8, 9]]
    ds = CallStreamDataset(streams, max_len=16)
    batch = collate_call_streams([ds[0], ds[1]])
    input_ids = batch["input_ids"]
    attention_mask = batch["attention_mask"]
    assert input_ids.shape == attention_mask.shape
    assert input_ids.shape[0] == 2
    pad_positions = (attention_mask == False).nonzero(as_tuple=True)
    if pad_positions[0].numel() > 0:
        assert int(input_ids[pad_positions[0][0], pad_positions[1][0]].item()) == PAD_ID


def test_mlm_mask_only_masks_real_tokens():
    streams = [[5, 6, 7, 8, 9]] * 32
    ds = CallStreamDataset(streams, max_len=16)
    batch = collate_call_streams([ds[i] for i in range(32)])
    g = torch.Generator()
    g.manual_seed(0)
    masked, labels = mlm_mask(
        batch["input_ids"],
        batch["attention_mask"],
        vocab_size=NUM_SPECIAL + 5,
        mask_prob=1.0,
        replace_mask_prob=1.0,
        replace_random_prob=0.0,
        generator=g,
    )
    assert ((labels != -100) == (batch["input_ids"] >= NUM_SPECIAL) & batch["attention_mask"]).all()
    eligible = (batch["input_ids"] >= NUM_SPECIAL) & batch["attention_mask"]
    assert (masked[eligible] == MASK_ID).all()
    assert (labels[eligible] == batch["input_ids"][eligible]).all()


def test_mlm_mask_ratio_bert_default():
    streams = [list(range(NUM_SPECIAL, NUM_SPECIAL + 50))] * 64
    ds = CallStreamDataset(streams, max_len=64)
    batch = collate_call_streams([ds[i] for i in range(64)])
    g = torch.Generator()
    g.manual_seed(0)
    _, labels = mlm_mask(
        batch["input_ids"],
        batch["attention_mask"],
        vocab_size=NUM_SPECIAL + 50,
        mask_prob=0.15,
        generator=g,
    )
    eligible = (batch["input_ids"] >= NUM_SPECIAL) & batch["attention_mask"]
    n_eligible = int(eligible.sum().item())
    n_masked = int((labels != -100).sum().item())
    ratio = n_masked / n_eligible
    assert 0.10 < ratio < 0.20, f"expected ~15% masked, got {ratio:.3f}"


def test_synthetic_streams_basic():
    cfg = SyntheticConfig(num_call_types=8, num_encounters=20, seed=1)
    streams, meta = make_synthetic_streams(cfg)
    assert len(streams) == 20
    for s in streams:
        assert all(NUM_SPECIAL <= t < NUM_SPECIAL + 8 for t in s)
        assert cfg.min_len <= len(s) <= cfg.max_len
    assert meta["transitions"].shape == (8, 8)


def test_shuffle_within_sequence_preserves_marginal():
    cfg = SyntheticConfig(num_call_types=8, num_encounters=10, seed=2)
    streams, _ = make_synthetic_streams(cfg)
    shuffled = shuffle_within_sequence(streams, seed=3)
    for s, sh in zip(streams, shuffled):
        assert sorted(s) == sorted(sh)
