"""Convenience wrapper for the head-H3 pilot.

This is the script the H3-headline-pivot proposal in
``docs/h3_headline_pivot.md`` recommends running in Stage 3 to falsify
(or support) the pivot. It is a thin alias for ``orca-h3-pilot``; the
real work lives in ``orcadolittle.cli.main``.

Default configuration runs the synthetic-substrate sanity check in ~1-3
minutes on CPU. The result tells you whether the H3 pipeline can detect
sequence structure when sequence structure is present by construction.
A non-zero gap (with p < 0.05 against the shuffled-sequence baseline)
is the minimum bar before pointing the same pipeline at DCLDE 2026.
"""

from __future__ import annotations

import sys

from orcadolittle.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
