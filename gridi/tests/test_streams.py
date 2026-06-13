"""Slice 4: stateful streams (>>).

A `>>` function returns a stream instance; `>> value` emits. Calling the instance
yields the next value, or () once exhausted — so a stream is `() -> T | ()` and
plugs straight into the triad. (This validator evaluates streams eagerly, so it
covers finite streams; truly infinite generators are a known limitation.)
"""
from gridi import run, UNIT

EACH = "each = (xs: [int]) >> int { xs @ { (_, x) => >> x } }\n"


def test_stream_emits_then_exhausts():
    assert run(EACH + "s = each([10, 20])\ns()") == 10
    assert run(EACH + "s = each([10, 20])\ns()\ns()") == 20
    assert run(EACH + "s = each([10, 20])\ns()\ns()\ns()") is UNIT   # exhausted -> ()


def test_stream_consumed_by_thread():
    assert run(EACH + "sum: &int = 0\neach([1, 2, 3]) @ { (_, v) => sum += v }\nsum") == 6


def test_stream_consumed_by_fanout():
    assert run(EACH + "each([1, 2, 3]) # { (_, v) => v * 10 }") == [10, 20, 30]
