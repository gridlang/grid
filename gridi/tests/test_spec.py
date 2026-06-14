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


# ── IM5: lambda values + user-defined combinators ─────────────────────────────

def test_lambda_value():
    assert run("f := _ => _ * 2\nf(5)") == 10

def test_block_lambda_value():
    assert run("g := { _ * 2 }\ng(5)") == 10

def test_user_combinator_lambda_arg():
    src = ("myMap := (xs: [int], body: (int) -> int) -> [int] { xs # body(_) }\n"
           "myMap([1, 2, 3], _ => _ * 2)")
    assert run(src) == [2, 4, 6]

def test_user_combinator_eta():
    src = ("dbl := (n: int) -> int { n * 2 }\n"
           "myMap := (xs: [int], body: (int) -> int) -> [int] { xs # body(_) }\n"
           "myMap([1, 2, 3], dbl)")
    assert run(src) == [2, 4, 6]


# ── IM6: systems surface — *T, mmio, bitwise, hex, sized conversions ──────────

def test_hex_literal():
    assert run("0x1000") == 4096

def test_star_cell_as_place():
    assert run("ctrl: *u32 := mmio.u32(0x1000)\nctrl = 5\nctrl") == 5

def test_bitwise_ops():
    assert run("6 & 3") == 2
    assert run("4 | 1") == 5
    assert run("5 ^ 1") == 4
    assert run("1 << 4") == 16
    assert run("16 >> 2") == 4

def test_bitwise_tighter_than_comparison():
    # Grid: (4 | 1) == 5  ->  5 == 5  ->  5.  (C order 4 | (1 == 5) would be () .)
    assert run("4 | 1 == 5") == 5

def test_bitwise_inplace():
    assert run("flags: &int := 0\nflags |= 4\nflags |= 1\nflags") == 5

def test_sized_checked_conversion():
    assert run("u8(200)") == 200
    assert run("u8(256)") is UNIT
    assert run("u8(-1)") is UNIT
    assert run("i8(-128)") == -128


# ── IM7: fallible indexed/member store ────────────────────────────────────────

def test_map_store():
    assert run('m := ["a": 1]\nm["b"] = 2\nm["b"]') == 2

def test_list_store_in_bounds():
    assert run("xs := [10, 20, 30]\nxs[1] = 99\nxs[1]") == 99

def test_list_store_oob_is_fallible():
    assert run("xs := [1, 2]\n_, e := (xs[9] = 5)\ne") == "index out of bounds: 9"

def test_list_store_oob_propagates_with_bang():
    src = ("f := () -> () ! str {\n"
           "  xs := [1, 2]\n"
           "  (xs[9] = 5)!\n"
           "  ()\n"
           "}\n"
           "v, e := f()\n"
           "e")
    assert run(src) == "index out of bounds: 9"


# ── IM8: §18 idioms + grafts (breadth) ────────────────────────────────────────

GRADE = 'grade := (n: int) -> str { n >= 90 ? "A" : n >= 80 ? "B" : n >= 70 ? "C" : "F" }\n'

def test_branch_ladder():
    assert run(GRADE + "grade(95)") == "A"
    assert run(GRADE + "grade(85)") == "B"
    assert run(GRADE + "grade(50)") == "F"

def test_dispatch_effectful():
    src = ("ok: &int := 0\nother: &int := 0\nstatus := 200\n"
           "status ? { 200 => ok += 1\n_ => other += 1 }\n`{ok} {other}`")
    assert run(src) == "1 0"

def test_iflet_else():
    assert run('m := ["host": "x"]\nm["host"] ? str.upper(_) : "none"') == "X"
    assert run('m := [:]\nm["host"] ? str.upper(_) : "none"') == "none"

def test_compute_then_dispatch():
    src = ('route := (raw: str) -> str {\n'
           '  str.upper(raw) ? { "GET" => "read"\n"POST" => "write"\n_ => "unknown" }\n}\n'
           '`{route("get")} {route("post")} {route("x")}`')
    assert run(src) == "read write unknown"

def test_interpolation():
    assert run("a := 3\nc := 'z'\n`a={a} c={c}`") == "a=3 c=z"

def test_ufcs():
    assert run("dbl := (n: int) -> int { n * 2 }\n5.dbl()") == 10

def test_struct_literal_and_field():
    assert run("p := (x: 1, y: 2)\np.x + p.y") == 3

def test_fallible_propagate_and_raise():
    src = ('half := (n: int) -> int ! str { n % 2 == 0 ? n / 2 : `{n} odd`! }\n'
           'v1, e1 := half(8)\nv2, e2 := half(7)\n`{v1}/{e1} {v2}/{e2}`')
    assert run(src) == "4/() ()/7 odd"

def test_stream():
    src = ('each := (xs: [int]) >> int { xs @ (x => >> x) }\n'
           's := each([10, 20, 30])\n`{s()} {s()} {s()} {s()}`')
    assert run(src) == "10 20 30 ()"

def test_defer_lifo():
    import io, contextlib
    src = ('f := () -> () {\n  ~sys.println("3")\n  sys.println("1")\n  sys.println("2")\n}\nf()')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(src)
    assert buf.getvalue() == "1\n2\n3\n"

def test_nested_fanout_table():
    assert run("1..3 # (r => 1..3 # (_ * r))") == [[1, 2, 3], [2, 4, 6], [3, 6, 9]]

def test_ordered_abort_on_error():
    src = ('process := (n: int) -> () ! str { n < 3 ? () : `too big: {n}`! }\n'
           'run := (xs: [int]) -> () ! str { xs @ (n => process(n)!) }\n'
           '_, e := run([1, 2, 5])\ne')
    assert run(src) == "too big: 5"

def test_pipeline():
    src = ("odd_sq_sum: &int := 0\n"
           "1..10 # (n => n % 2 == 1 ? n) # (_ * _) @ (s => odd_sq_sum += s)\n"
           "odd_sq_sum")
    assert run(src) == 165
