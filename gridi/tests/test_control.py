"""Smoke test for examples/control-converged.grid — the converged control model
(effectful dispatch, bare `=>` if-let, compute-then-dispatch topic threading,
chained `?:` guard ladder, if-let on a relation)."""
import io
import os
import contextlib

from gridi import run

_HERE = os.path.dirname(__file__)
SRC = open(os.path.join(_HERE, "..", "..", "examples", "control-converged.grid")).read()


def test_converged_control_runs_and_prints():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(SRC)
    out = buf.getvalue()
    for needle in [
        "=== converged control model ===",
        'm["host"] -> GRID.DEV',                       # bare => if-let binds + transforms
        'm["port"] -> none',                           # ?: fallback on a missing key
        "hit 200 -> ok=1 other=0",                     # effectful arm commits, no fall-through
        "get post put -> read write unknown",          # topic-shifting prelude then dispatch
        "95 85 75 65 -> A B C F",                       # chained ?: guard ladder
        "7 < limit binds 10 -> 20",                    # if-let on a relation's right operand
    ]:
        assert needle in out, needle
