"""Model definitions and loaders for OrcaDolittle.

This subpackage isolates the *architectures* from the *analysis logic* in
:mod:`orcadolittle.core`. Encoders, generative heads, and policy heads are
defined here; the core modules call them through narrow interfaces so each
component can be swapped (e.g. AVES2 ↔ Perch 2.0) without touching the
pipeline.
"""
from __future__ import annotations
