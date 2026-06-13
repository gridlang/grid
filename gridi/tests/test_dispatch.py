"""The unified control model (blocks.md): a block is one scope, run in sequence;
a matching `=>` commits the block (even with a () result); the topic threads as the
last *present* value (() transparent). This fixes dispatch.md #1 (effectful match
fall-through) and #3 (?-block scoping), and preserves find/guard/reduce.
"""
from gridi import run, UNIT


# --- #1: an effectful matched arm commits; later arms do NOT run -------------

def test_effectful_matched_arm_commits_no_fallthrough():
    src = (
        "a: &int = 0\n"
        "b: &int = 0\n"
        "7 ? { 7 => { a += 1; () }\n"
        "      _ => { b += 1; () } }\n"
        "`{a} {b}`"
    )
    assert run(src) == "1 0"           # only the 7 arm ran (was "1 1" under first-present)


# --- #3: a multi-statement ?-consequent shares one scope ---------------------

def test_multistatement_consequent_shares_scope():
    assert run("1 ? { x: &int = 1\n x += 9\n x }") == 10   # was: unbound label: x


# --- topic threads as the last present value --------------------------------

def test_value_prelude_becomes_topic():
    # the block topic starts as the subject (5); a present statement (9) updates it,
    # so the following arm matches 9, not 5.
    assert run('5 ? { 9\n 9 => "nine" }') == "nine"        # was: 9 (first-present)


def test_unmatched_arm_is_transparent():
    # 1 => ... does not match topic 2, yields () and passes the topic through, so the
    # later arm still sees 2.
    assert run('2 ? { 1 => "one"\n 2 => "two" }') == "two"


# --- regressions: dispatch + find/guard/reduce still hold -------------------

def test_dispatch_first_match_commits():
    assert run('2 ? { 1 => "one"\n 2 => "two"\n _ => "other" }') == "two"


def test_find_still_works():
    assert run("[10, 20, 30] @ { (_, x) => x == 20 ? x }") == 20


def test_find_not_found_is_unit():
    assert run("[10, 20, 30] @ { (_, x) => x == 99 ? x }") is UNIT


def test_guard_reduce_still_works():
    assert run("big: &int = 0\n1..5 @ { (_, n) => n > 2 ? big += n }\nbig") == 12
