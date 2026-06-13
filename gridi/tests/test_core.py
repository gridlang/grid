"""Golden tests for the keystone core: present vs (), partial operators, ? and =>.

These pin the most novel (and riskiest) part of MODEL.md — Layer 3 — before any
of the rest is trusted. `run(src)` evaluates a program and returns its last value;
UNIT is Grid's `()`.
"""
from gridi import run, UNIT


def test_literals():
    assert run("1") == 1
    assert run('"hi"') == "hi"
    assert run("()") is UNIT


def test_arithmetic():
    assert run("1 + 2") == 3
    assert run("2 * 3 + 1") == 7


def test_relations_yield_right_operand():
    # success yields the RIGHT operand (Layer 3), failure yields ()
    assert run("3 < 5") == 5
    assert run("5 < 3") is UNIT
    assert run("1 == 1") == 1
    assert run("1 == 2") is UNIT


def test_comparison_chains_by_composition():
    assert run("1 < 2 < 3") == 3          # (1<2)->2, 2<3->3
    assert run("1 < 5 < 3") is UNIT       # 1<5->5, 5<3->()
    assert run("3 < 2 < 5") is UNIT       # 3<2->(), ()<5->()


def test_partiality_propagates_and_divzero():
    assert run("10 / 2") == 5
    assert run("10 / 0") is UNIT          # divide by zero -> () (no exception)


def test_try_is_present_not_truthy():
    # a data 0 is PRESENT, so `?` fires — the falsy-default hazard is gone
    assert run('0 ? "present"') == "present"
    assert run('"" ? "present"') == "present"
    assert run('() ? "x"') is UNIT        # only () is absent
    assert run('3 < 5 ? "yes"') == "yes"
    assert run('5 < 3 ? "yes"') is UNIT


def test_selectors():
    assert run('() || "fallback"') == "fallback"
    assert run('"a" || "b"') == "a"
    assert run('"a" && "b"') == "b"
    assert run('() && "b"') is UNIT


def test_match_block_literal_and_wildcard():
    src = '7 ? {\n  0 => "zero"\n  _ => "other"\n}'
    assert run(src) == "other"
    src0 = '0 ? {\n  0 => "zero"\n  _ => "other"\n}'
    assert run(src0) == "zero"           # matching the default value 0 works — no hazard


def test_match_binds_the_topic():
    assert run("42 ? {\n  n => n + 1\n}") == 43


def test_first_present_arm_wins():
    src = '5 ? {\n  99 => "no"\n  _ => "yes"\n}'
    assert run(src) == "yes"


def test_bindings_and_sequence():
    assert run("x = 5\nx + 1") == 6
    assert run("a = 2\nb = 3\na * b") == 6


def test_guard_and_match_compose_in_a_block():
    # an infix-? guard arm and a => match arm side by side, first present wins
    src = 'cached = ()\nstatus = 200\nstatus ? {\n  cached ? cached\n  200 => "ok"\n  code => code\n}'
    assert run(src) == "ok"
    src2 = 'cached = "hit"\nstatus = 200\nstatus ? {\n  cached ? cached\n  200 => "ok"\n  code => code\n}'
    assert run(src2) == "hit"
