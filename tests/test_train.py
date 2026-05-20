import math

import torch

from orcadolittle.data.call_streams import NUM_SPECIAL, CallStreamDataset
from orcadolittle.data.synthetic import SyntheticConfig, make_synthetic_streams
from orcadolittle.models.sequence_lm import SequenceLM, SequenceLMConfig
from orcadolittle.train.mlm import TrainConfig, evaluate_mlm, train_mlm


def test_training_reduces_loss_on_synthetic_streams():
    torch.manual_seed(0)
    cfg_data = SyntheticConfig(
        num_call_types=12,
        num_encounters=400,
        mean_len=24.0,
        std_len=4.0,
        min_len=12,
        max_len=32,
        transition_concentration=0.05,
        seed=0,
    )
    streams, _ = make_synthetic_streams(cfg_data)
    train_ds = CallStreamDataset(streams[:300], max_len=64)
    eval_ds = CallStreamDataset(streams[300:], max_len=64)
    model = SequenceLM(
        SequenceLMConfig(
            vocab_size=NUM_SPECIAL + cfg_data.num_call_types,
            d_model=32,
            n_layers=2,
            n_heads=4,
            max_len=64,
        )
    )
    before = evaluate_mlm(model, eval_ds, batch_size=64, seed=0)["mlm_loss"]
    train_mlm(
        model,
        train_dataset=train_ds,
        eval_dataset=None,
        cfg=TrainConfig(
            batch_size=32,
            max_steps=120,
            warmup_steps=10,
            lr_peak=5e-3,
            seed=0,
            eval_every=10_000,
            log_every=10_000,
        ),
        device="cpu",
        log_fn=lambda *_a, **_k: None,
    )
    after = evaluate_mlm(model, eval_ds, batch_size=64, seed=0)["mlm_loss"]
    assert after < before - 0.1, f"expected loss to drop materially, got {before:.3f} -> {after:.3f}"
    chance = math.log(NUM_SPECIAL + cfg_data.num_call_types)
    assert after < chance, f"trained loss {after:.3f} should be below chance {chance:.3f}"
