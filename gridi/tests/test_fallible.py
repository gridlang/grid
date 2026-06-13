"""Slice 3: fallibles (-> T ! E, the ! operator) and string interpolation.

A fallible function returns success or carries an error. `!` is the failure
operator: on a plain value it raises (fail with it); on a fallible result it
unwraps the success or propagates the error. `v, e = f()` destructures the pair.
"""
from gridi import run, UNIT

HALF = 'half = (n: int) -> int ! str { n % 2 == 0 ? n / 2 || "odd"! }\n'
QUARTER = HALF + "quarter = (n: int) -> int ! str { h = half(n)!\nhalf(h)! }\n"


def test_interpolation():
    assert run('name = "Ada"\n`hi {name}`') == "hi Ada"
    assert run("x = 2\n`{x} + {x} = {x + x}`") == "2 + 2 = 4"


def test_fallible_success_unwraps():
    assert run(HALF + "v, e = half(4)\nv") == 2
    assert run(HALF + "v, e = half(4)\ne") is UNIT


def test_fallible_failure_carries_error():
    assert run(HALF + "v, e = half(3)\ne") == "odd"
    assert run(HALF + "v, e = half(3)\nv") is UNIT


def test_propagation_via_bang():
    assert run(QUARTER + "v, e = quarter(8)\nv") == 2       # half(8)=4, half(4)=2
    assert run(QUARTER + "v, e = quarter(8)\ne") is UNIT
    assert run(QUARTER + "v, e = quarter(6)\ne") == "odd"   # half(6)=3, half(3) raises


def test_destructure_tuple():
    assert run("p = (1, 2)\na, b = p\na + b") == 3
