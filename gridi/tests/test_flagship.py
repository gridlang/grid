"""Slice 5 (capstone): the flagship's pure parts run through the interpreter.

Loads examples/http-server.grid (module/import, structs, fallibles, ~, the triad,
interpolation, the lot), then drives `route` and the handlers on synthetic
requests. The serve/accept loop and net.* need real I/O, so they aren't exercised
here — but the routing, matching, handlers, # / @, and interpolation all are.
"""
import os
from gridi import run

_HERE = os.path.dirname(__file__)
FLAGSHIP = open(os.path.join(_HERE, "..", "..", "examples", "http-server.grid")).read()


def call(extra):
    return run(FLAGSHIP + "\n" + extra)


def test_flagship_parses_and_defines():
    # running the file defines everything (handlers, serve, main) without error
    assert call("ok(\"hi\").status") == 200


def test_route_hello_named():
    r = call('route((method: "GET", path: "/hello", body: "Ada"))')
    assert r["status"] == 200
    assert r["body"] == "hello, Ada!\n"


def test_route_hello_default_when_empty():
    r = call('route((method: "GET", path: "/hello", body: ""))')
    assert r["body"] == "hello, world!\n"


def test_route_echo():
    r = call('route((method: "GET", path: "/echo", body: "ping"))')
    assert r["body"] == "ping"


def test_route_lines_numbered():
    r = call('route((method: "POST", path: "/lines", body: "a\nb\nc"))')
    assert r["body"] == "1: a\n2: b\n3: c\n"


def test_route_not_found():
    r = call('route((method: "DELETE", path: "/nope", body: ""))')
    assert r["status"] == 404
