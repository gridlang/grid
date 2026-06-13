"""Stdlib + REPL-session extensions: ranges, .len, more str.*, a persistent Session.

Namespaces (str/sys/net) are available by default in the global env, so live
exploration needs no `import`. A Session keeps bindings across evals (the REPL).
"""
from gridi import run, UNIT
from gridi.interp import Session


def test_len_member():
    assert run("[1, 2, 3].len") == 3
    assert run('"hello".len') == 5
    assert run("(1, 2, 3).len") == 3
    assert run("(x: 1, y: 2).len") == 2


def test_range():
    assert run("1..5") == [1, 2, 3, 4, 5]
    assert run("[1..5]") == [1, 2, 3, 4, 5]
    assert run("1..5 # { (_, n) => n * n }") == [1, 4, 9, 16, 25]
    assert run("sum: &int = 0\n1..10 @ { (_, n) => sum += n }\nsum") == 55


def test_str_builtins():
    assert run('str.split("a,b,c", ",")') == ["a", "b", "c"]
    assert run('str.contains("hello", "ell")') == "ell"
    assert run('str.contains("hello", "xyz")') is UNIT
    assert run('str.starts("hello", "he")') == "he"
    assert run('str.ends("hello", "lo")') == "lo"
    assert run('str.replace("a-b-c", "-", "+")') == "a+b+c"
    assert run('str.upper("hi")') == "HI"
    assert run('str.chars("abc")') == ["a", "b", "c"]


def test_namespaces_available_without_import():
    assert run('str.trim("  hi  ")') == "hi"


def test_session_persists_bindings():
    s = Session()
    assert s.eval("x = 5") is UNIT
    assert s.eval("x + 1") == 6
    assert s.eval("double = (n: int) -> int { n * 2 }\ndouble(x)") == 10
