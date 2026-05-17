"""Data loaders and reference taxonomies for OrcaDolittle.

Three concerns live here:

* Bulk corpora — DCLDE 2026 (:mod:`dclde`) and OrcaSound (:mod:`orcasound`).
* The published-playback re-analysis corpus (:mod:`playback_corpus`) —
  per-paper, per-condition response statistics extracted from the literature.
* Reference taxonomies — call-type vocabularies and call-type → context
  mappings (:mod:`context_mapping`).
"""
from __future__ import annotations
