"""Golden/smoke tests for the example programs (grid.md model).

The tour runs end to end; the flagship's pure parts (routing + handlers) are
driven directly — net.* needs real I/O, so serve/handle aren't exercised here.
"""
import io
import os
import contextlib

from gridi import run

_HERE = os.path.dirname(__file__)


def _read(name):
    return open(os.path.join(_HERE, "..", "..", "examples", name)).read()


TOUR = _read("tour.grid")
FLAGSHIP = _read("http-server.grid")


def test_tour_runs_and_prints():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run(TOUR)
    out = buf.getvalue()
    for needle in [
        "1 < 2 < 3  => 3",
        "map        => [2, 4, 6, 8, 10, 12]",
        "filter     => [2, 4, 6]",
        "reduce     => 21",
        "find       => 7",
        "keyed      => [0:a, 1:b, 2:c]",
        "grade      => A B C",
        "twice      => 18",
        "half(7)    => () / 7 odd",
        "stream     => 10 20 ()",
        "bits       => 8 ()",
        "done",
    ]:
        assert needle in out, needle


def _call(extra):
    return run(FLAGSHIP + "\n" + extra)


def test_flagship_defines():
    assert _call('ok("hi").status') == 200


def test_route_hello_named():
    r = _call('route((method: "GET", path: "/hello", body: "Ada"))')
    assert r["status"] == 200
    assert r["body"] == "hello, Ada!"


def test_route_hello_default():
    assert _call('route((method: "GET", path: "/hello", body: "")).body') == "hello, world!"


def test_route_echo():
    assert _call('route((method: "GET", path: "/echo", body: "ping")).body') == "ping"


def test_route_lines_numbered():
    r = _call('route((method: "POST", path: "/lines", body: "a\nb\nc"))')
    assert r["body"] == "1: a\n2: b\n3: c"


def test_route_not_found():
    assert _call('route((method: "DELETE", path: "/nope", body: "")).status') == 404
