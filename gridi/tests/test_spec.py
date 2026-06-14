"""Validation suite for the grid.md model (the sharpened spec).

Each slice of the interpreter migration adds tests here. These exercise the new
surface: := / = storage, _ as the frozen current argument, bare-expression
bodies, keyed-entry iteration, lambda values, the systems layer, and the §18
idioms — so the interpreter validates that grid.md is coherent.
"""
import pytest
from gridi import run
from gridi.interp import UNIT


# ── IM1: := introduces / = stores ────────────────────────────────────────────

def test_walrus_introduces():
    assert run("n := 1\nn") == 1

def test_binding_yields_unit():
    assert run("n := 5") is UNIT

def test_store_through_existing_place():
    assert run("c: &int := 0\nc = 5\nc") == 5

def test_inplace_store():
    assert run("c: &int := 0\nc += 1\nc += 1\nc") == 2

def test_equals_never_introduces():
    with pytest.raises(Exception):
        run("x = 5")                 # = on an unintroduced label is an error

def test_annotated_introduce():
    assert run("count: &int := 0\ncount += 1\ncount") == 1

def test_destructure_introduce():
    assert run("a, b := (1, 2)\na + b") == 3


# ── IM2: _ is the current argument, frozen per body level ─────────────────────

def test_underscore_is_current_arg():
    assert run("5 ? _") == 5

def test_underscore_iflet():
    assert run('m := ["k": 9]\nm["k"] ? _') == 9

def test_topic_frozen_in_block():
    # a present statement does NOT retarget _ (no threading)
    assert run("5 ? { 1\n_ }") == 5

def test_arms_see_frozen_subject():
    assert run('200 ? { 200 => "ok"\n_ => "no" }') == "ok"
    assert run('500 ? { 200 => "ok"\n_ => "other" }') == "other"


# ── IM3/IM4: bare-expression bodies + keyed-entry iteration ───────────────────

def test_map_bare_body():
    assert run("1..3 # (_ * 2)") == [2, 4, 6]

def test_square_two_underscores():
    assert run("1..3 # (_ * _)") == [1, 4, 9]

def test_filter_named():
    assert run("1..6 # (n => n % 2 == 0 ? n)") == [2, 4, 6]

def test_reduce():
    assert run("sum: &int := 0\n1..5 @ (sum += _)\nsum") == 15

def test_find():
    assert run("1..100 @ (n => n * n > 40 ? n)") == 7

def test_loop_generator():
    assert run("i: &int := 0\n{ i < 3 } @ (i += 1)\ni") == 3

def test_call_body():
    assert run("dbl := (n: int) -> int { n * 2 }\n1..3 # dbl(_)") == [2, 4, 6]

def test_keyed_index():
    assert run('["a", "b", "c"] # (i: x => `{i}:{x}`)') == ["0:a", "1:b", "2:c"]

def test_map_values_bare():
    assert run('m := ["x": 1, "y": 2]\nm # _') == [1, 2]

def test_map_keys():
    assert run('m := ["x": 1, "y": 2]\nm # (k: _ => k)') == ["x", "y"]

def test_map_entries():
    assert run('m := ["x": 1]\nm # (k: v => `{k}={v}`)') == ["x=1"]
