"""branch.md: `cond ? then : else` — the 2-outcome branch. `?:` is the loosest
operator (right-associative); the decision is made on the condition, not the result.
`||` stays a pure value-selector, never an else.
"""
from gridi import run


def test_effectful_if_else_runs_exactly_one():
    assert run("a: &int = 0\nb: &int = 0\n1 ? { a += 1 } : { b += 1 }\n`{a} {b}`") == "1 0"
    assert run("a: &int = 0\nb: &int = 0\n() ? { a += 1 } : { b += 1 }\n`{a} {b}`") == "0 1"


def test_else_skipped_when_cond_present_even_if_then_is_unit():
    # the choice is on the condition; a ()-valued then does NOT trigger the else
    assert run("b: &int = 0\n1 ? () : { b += 1 }\nb") == 0


def test_value_if_else():
    assert run("1 ? 10 : 20") == 10
    assert run("() ? 10 : 20") == 20


def test_right_associative_elif_chain():
    f = 'label = (n: int) -> str { n > 99 ? "big" : n % 2 == 0 ? "even" : "odd" }\n'
    assert run(f + "label(100)") == "big"
    assert run(f + "label(4)") == "even"
    assert run(f + "label(3)") == "odd"


def test_or_in_condition_binds_tighter():
    # a || b ? c : d  ==  (a || b) ? c : d
    assert run('() || 1 ? "yes" : "no"') == "yes"
    assert run('() || () ? "yes" : "no"') == "no"


def test_or_in_else_binds_tighter():
    # cond ? a : b || c  ==  cond ? a : (b || c)
    assert run('() ? "x" : () || "fallback"') == "fallback"


def test_or_remains_pure_value_selector():
    assert run('"a" || "b"') == "a"
    assert run('() || "b"') == "b"


def test_if_let_then_binds_subject():
    assert run('m = ["k": 7]\nm["k"] ? { v => v } : -1') == 7
    assert run('m = ["k": 7]\nm["x"] ? { v => v } : -1') == -1


# --- slice 3: `=>` is a bare operator, usable without a { } wrapper ----------

def test_bare_arm_in_then_branch():
    assert run("5 ? x => x + 1 : 0") == 6
    assert run("() ? x => x + 1 : 99") == 99


def test_bare_arm_if_let():
    assert run('m = ["k": 7]\nm["k"] ? v => v : -1') == 7
    assert run('m = ["k": 7]\nm["x"] ? v => v : -1') == -1


def test_bare_arm_keeps_inplace_and_emit_results():
    # `=>` as a bare operator still allows in-place / emit results (arm-result forms)
    assert run("sum: &int = 0\n[1, 2, 3] @ { (_, n) => sum += n }\nsum") == 6
    assert run("each = (xs: [int]) >> int { xs @ { (_, x) => >> x } }\n"
               "out: &int = 0\neach([4, 5]) @ { (_, v) => out += v }\nout") == 9
