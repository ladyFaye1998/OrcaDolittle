import math

import torch

from orcadolittle.data.call_streams import (
    NUM_SPECIAL,
    CallStreamDataset,
    collate_call_streams,
)
from orcadolittle.models.sequence_lm import SequenceLM, SequenceLMConfig


def test_forward_shape_and_logits_dtype():
    cfg = SequenceLMConfig(
        vocab_size=NUM_SPECIAL + 16, d_model=32, n_layers=2, n_heads=4, max_len=32
    )
    model = SequenceLM(cfg)
    ds = CallStreamDataset(
        [list(range(NUM_SPECIAL, NUM_SPECIAL + 10)) for _ in range(4)], max_len=cfg.max_len
    )
    batch = collate_call_streams([ds[i] for i in range(4)])
    logits = model(batch["input_ids"], batch["attention_mask"])
    assert logits.shape == (4, batch["input_ids"].shape[1], cfg.vocab_size)
    assert logits.dtype == torch.float32


def test_weight_tying_when_enabled():
    cfg = SequenceLMConfig(
        vocab_size=NUM_SPECIAL + 16, d_model=32, n_layers=2, n_heads=4, tie_weights=True
    )
    model = SequenceLM(cfg)
    assert model.head.weight.data_ptr() == model.embed.weight.data_ptr()


def test_long_sequence_rejected():
    import pytest

    cfg = SequenceLMConfig(vocab_size=NUM_SPECIAL + 4, d_model=16, n_layers=1, n_heads=2, max_len=8)
    model = SequenceLM(cfg)
    bad = torch.zeros((1, 9), dtype=torch.long)
    mask = torch.ones((1, 9), dtype=torch.bool)
    with pytest.raises(ValueError):
        model(bad, mask)


def test_num_parameters_positive():
    cfg = SequenceLMConfig(vocab_size=NUM_SPECIAL + 4, d_model=16, n_layers=1, n_heads=2)
    model = SequenceLM(cfg)
    assert model.num_parameters() > 0
