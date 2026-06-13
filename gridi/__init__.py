"""gridi — a tree-walking interpreter for Grid, the validator for MODEL.md.

Its job is to keep the design and an implementation from drifting: the doc's
code blocks and the flagship snippets become golden tests. Built keystone-first.
"""
from .interp import run, grid_str, UNIT

__all__ = ["run", "grid_str", "UNIT"]
