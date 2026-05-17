"""Reproducible benchmarks for each OrcaDolittle component.

Each submodule exposes a ``run()`` function that prints a structured table
and returns a results dictionary. The aggregate runner is
:func:`run_all.run_all`.
"""
from __future__ import annotations
