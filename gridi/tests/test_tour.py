"""Newly-filled features (char/map literals, unary minus) and a smoke test that
the feature tour runs and prints the expected results."""
import io
import os
import contextlib

from gridi import run

_HERE = os.path.dirname(__file__)
TOUR = open(os.path.join(_HERE, "..", "..", "examples", "tour-features.grid")).read()


def test_char_and_char_range():
    assert run("'z'") == "z"
    assert run("'a'..'d'") == ["a", "b", "c", "d"]


def test_map_literal():
    assert run('m = ["a": 1, "b": 2]\nm["b"]') == 2
    assert run('["a": 1, "b": 2].len') == 2
    assert run("[:].len") == 0                       # empty map


def test_unary_minus():
    assert run("-5") == -5
    assert run("3 - -2") == 5
    assert run("x = 4\n-x") == -4


def test_string_escapes_preserve_utf8():
    assert run(r'"a\tb — é"') == "a\tb — é"


def test_tour_runs_and_prints():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(TOUR)
    out = buf.getvalue()
    for needle in [
        "=== Grid feature tour ===",
        "1 < 2 < 3     => 3",
        "find first n with n*n>40 : 7",
        "half(7) -> value (), error 7 is odd",
        "pull 4 times: 10 20 30 ()",
        "sum of squares over 25 in 1..10 = 330",
        "fan-out — map",                              # em-dash survives
    ]:
        assert needle in out, needle
    assert out.index("[1] opened") < out.index("[2] using") < out.index("[3] deferred")
