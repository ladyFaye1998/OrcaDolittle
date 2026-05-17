"""Run the off-policy selection benchmark against the published playback
corpus and print the resulting JSON.
"""
from __future__ import annotations

import json

from orcadolittle.benchmarks import select_eval


def main() -> None:
    print(json.dumps(select_eval.run(policy="thompson"), indent=2))


if __name__ == "__main__":
    main()
