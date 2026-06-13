"""REPL tab-completion: bindings/namespaces at top level, members after a dot."""
from gridi.interp import Session
from gridi.cli import complete


def test_complete_toplevel_bindings_and_namespaces():
    s = Session()
    s.eval("foobar = 1")
    out = complete(s.env, "foo")
    assert "foobar" in out
    assert all(x.startswith("foo") for x in out)
    assert "str" in complete(s.env, "st")


def test_complete_namespace_members():
    s = Session()
    out = complete(s.env, "str.li")
    assert out == ["str.lines"]
    assert "str.split" in complete(s.env, "str.s")
    assert "str.starts" in complete(s.env, "str.s")


def test_complete_struct_fields():
    s = Session()
    s.eval("q = (x: 1, yy: 2)")
    assert complete(s.env, "q.y") == ["q.yy"]


def test_complete_unknown_is_empty():
    s = Session()
    assert complete(s.env, "nope.") == []
    assert complete(s.env, "zzz") == []
