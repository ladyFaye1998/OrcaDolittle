"""Run every component benchmark and print a summary table.

Invoked from the CLI as ``orcadolittle benchmark`` or directly:

    python -m orcadolittle.benchmarks.run_all
"""
from __future__ import annotations

import json
from typing import Any

from orcadolittle.benchmarks import (
    generate_eval,
    perceive_eval,
    predict_eval,
    select_eval,
)


def run_all() -> dict[str, dict[str, Any]]:
    """Run all component benchmarks and return their result dictionaries."""
    return {
        "perceive": perceive_eval.run(),
        "generate": generate_eval.run(),
        "select": select_eval.run(),
        "predict": predict_eval.run(),
    }


if __name__ == "__main__":
    results = run_all()
    print(json.dumps(results, indent=2, default=str))
