import torch

from orcadolittle.data.call_streams import NUM_SPECIAL, CallStreamDataset
from orcadolittle.data.synthetic import SyntheticConfig, make_synthetic_streams
from orcadolittle.eval.permutation import (
    PermutationConfig,
    PermutationResult,
    run_shuffled_baseline,
)
from orcadolittle.models.sequence_lm import SequenceLMConfig
from orcadolittle.train.mlm import TrainConfig


def test_permutation_result_pvalue_math():
    r = PermutationResult(
        real_eval_loss=1.0,
        shuffled_eval_losses=[1.5, 1.4, 1.3, 1.2, 1.1],
        n_perm=5,
    )
    assert abs(r.mean_shuffled_loss - 1.3) < 1e-9
    assert r.gap > 0
    # 0 wins, so p = (1 + 0) / (1 + 5) = 1/6
    assert abs(r.p_value - (1.0 / 6.0)) < 1e-9


def test_permutation_result_pvalue_with_ties():
    r = PermutationResult(
        real_eval_loss=1.0,
        shuffled_eval_losses=[1.0, 1.0, 2.0],
        n_perm=3,
    )
    # 2 wins (<= 1.0), so p = (1 + 2) / (1 + 3) = 3/4
    assert abs(r.p_value - 0.75) < 1e-9


def test_run_shuffled_baseline_end_to_end_synthetic():
    torch.manual_seed(0)
    streams, _ = make_synthetic_streams(
        SyntheticConfig(
            num_call_types=10,
            num_encounters=300,
            mean_len=20.0,
            std_len=4.0,
            min_len=10,
            max_len=32,
            transition_concentration=0.05,
            seed=0,
        )
    )
    train_ds = CallStreamDataset(streams[:240], max_len=64)
    eval_ds = CallStreamDataset(streams[240:], max_len=64)
    result, _model = run_shuffled_baseline(
        base_model_cfg=SequenceLMConfig(
            vocab_size=NUM_SPECIAL + 10,
            d_model=32,
            n_layers=2,
            n_heads=4,
            max_len=64,
        ),
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        train_cfg=TrainConfig(
            batch_size=32,
            max_steps=120,
            warmup_steps=10,
            lr_peak=5e-3,
            seed=0,
            eval_every=10_000,
            log_every=10_000,
        ),
        perm_cfg=PermutationConfig(n_perm=2, pilot_n_perm=2, seed=0),
        device="cpu",
        use_pilot_n=True,
        log_fn=lambda *_a, **_k: None,
    )
    assert result.n_perm == 2
    assert 0.0 <= result.p_value <= 1.0
    # Per the synthetic construction, real sequences carry bigram structure
    # absent in the shuffled controls. The trained model should fit them
    # strictly better, i.e. real loss should be lower than mean shuffled loss.
    assert result.gap > 0, (
        f"expected real_loss < mean_shuffled_loss; got real={result.real_eval_loss:.3f} "
        f"mean_shuf={result.mean_shuffled_loss:.3f}"
    )
