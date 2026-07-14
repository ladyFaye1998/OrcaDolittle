import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_provider_aware_benchmark import count_matrix, simulate  # noqa: E402


def test_structural_regime_has_one_single_provider_class() -> None:
    counts = count_matrix("structural", n_providers=8, n_classes=4)
    assert np.count_nonzero(counts[:, 3]) == 1
    assert np.all(np.count_nonzero(counts[:, :3], axis=0) > 1)


def test_benchmark_is_deterministic_and_aligned() -> None:
    first = simulate("partial", provider_strength=2.0, seed=17)
    second = simulate("partial", provider_strength=2.0, seed=17)
    for a, b in zip(first, second):
        np.testing.assert_array_equal(a, b)
    X, labels, providers = first
    assert X.shape[0] == labels.shape[0] == providers.shape[0]
    assert X.shape[1] == 48
