import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_workflow_error_propagation import (  # noqa: E402
    corrupt_labels,
    corrupt_providers,
    run,
)


def test_corruption_preserves_shapes_and_changes_requested_fraction():
    import numpy as np

    rng = np.random.default_rng(3)
    y = np.tile(np.arange(4), 25)
    providers = np.tile(np.arange(5), 20)
    changed_y = corrupt_labels(y, 0.1, rng)
    changed_p = corrupt_providers(providers, 0.2, rng)
    assert changed_y.shape == y.shape
    assert changed_p.shape == providers.shape
    assert int((changed_y != y).sum()) == 10
    assert int((changed_p != providers).sum()) == 20


def test_error_propagation_output_is_deterministic_and_complete():
    first = run(repeats=1, seed=7)
    second = run(repeats=1, seed=7)
    assert first["cumulative_stages"] == second["cumulative_stages"]
    assert set(first["one_factor_sweeps"]) == {
        "feature_noise",
        "target_label_error",
        "provider_metadata_error",
    }
    assert first["cumulative_stages"]["clean"]["random_cv"]["mean"] > 0.25
