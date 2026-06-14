"""Differential tests for gridc (the Grid-in-Grid compiler).

For each Grid program we (a) interpret it with gridi and (b) compile it with
gridc -> .ll -> clang -> native, then run the binary and assert the two agree.
gridi is the correctness oracle; gridc must match it.
"""
import os
import subprocess
import sys

import pytest

_HERE = os.path.dirname(__file__)
REPO = os.path.normpath(os.path.join(_HERE, "..", ".."))
GRIDC = os.path.join(REPO, "gridc", "gridc.grid")
PY = os.path.join(REPO, ".venv", "bin", "python")
if not os.path.exists(PY):
    PY = sys.executable

clang = pytest.mark.skipif(
    subprocess.run(["which", "clang"], capture_output=True).returncode != 0,
    reason="clang not available",
)


def interp_exit(program, tmp):
    """Run a program through gridi; return main()'s exit code."""
    src = tmp / "prog.grid"
    src.write_text(program)
    r = subprocess.run([PY, "-m", "gridi", str(src)], cwd=REPO, capture_output=True, text=True)
    return r.returncode


def compile_exit(program, tmp):
    """Compile a program with gridc -> clang -> native; return the binary's exit code."""
    src = tmp / "prog.grid"
    ll = tmp / "prog.ll"
    binp = tmp / "prog.bin"
    src.write_text(program)
    c = subprocess.run([PY, "-m", "gridi", GRIDC, str(src), str(ll)],
                       cwd=REPO, capture_output=True, text=True)
    assert c.returncode == 0, f"gridc failed: {c.stderr}"
    k = subprocess.run(["clang", str(ll), "-o", str(binp)], capture_output=True, text=True)
    assert k.returncode == 0, f"clang failed: {k.stderr}\n--- IR ---\n{ll.read_text()}"
    return subprocess.run([str(binp)]).returncode


@clang
@pytest.mark.parametrize("expr,val", [
    ("0", 0), ("7", 7), ("42", 42), ("200", 200),
    ("40 + 2", 42), ("6 * 7", 42), ("100 - 58", 42), ("84 / 2", 42), ("85 % 43", 42),
    ("2 + 3 * 4", 14), ("(2 + 3) * 4", 20), ("(1 + 2) * 10 + 12", 42),
])
def test_arith_matches_interpreter(expr, val, tmp_path):
    program = f"main := () -> int {{ {expr} }}\n"
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == val


@clang
@pytest.mark.parametrize("body,val", [
    ("x := 40\n  y := 2\n  x + y", 42),
    ("a := 6\n  b := 7\n  c := a * b\n  c", 42),
    ("x := 100\n  x - 58", 42),
    ("x := 5\n  y := x * x\n  y + 17", 42),
])
def test_locals_match_interpreter(body, val, tmp_path):
    program = "main := () -> int {\n  " + body + "\n}\n"
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == val


@clang
@pytest.mark.parametrize("program,val", [
    # mutable accumulator / store
    ("main := () -> int {\n  s: &int := 0\n  s += 40\n  s += 2\n  s\n}", 42),
    ("main := () -> int {\n  x: &int := 10\n  x = 42\n  x\n}", 42),
    # functions + calls
    ("add := (a: int, b: int) -> int { a + b }\nmain := () -> int { add(40, 2) }", 42),
    ("sq := (n: int) -> int { n * n }\nmain := () -> int { sq(5) + sq(4) + 1 }", 42),
    # relations + ?:
    ("main := () -> int { 5 > 3 ? 42 : 0 }", 42),
    ("main := () -> int { 3 > 5 ? 0 : 42 }", 42),
    # nested ?: ladder
    ("g := (n: int) -> int { n >= 90 ? 4 : n >= 80 ? 3 : 0 }\n"
     "main := () -> int { g(85) + g(95) * 10 }", 43),
])
def test_functions_and_control(program, val, tmp_path):
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == val


@clang
@pytest.mark.parametrize("program,val", [
    # @ reduce over a range -> native counting loop
    ("main := () -> int {\n  sum: &int := 0\n  1..5 @ (n => sum += n)\n  sum\n}", 15),
    ("main := () -> int {\n  sum: &int := 0\n  1..10 @ (n => sum += n)\n  sum\n}", 55),
    # product accumulator
    ("main := () -> int {\n  p: &int := 1\n  1..5 @ (k => p *= k)\n  p\n}", 120),
    # range bounds from locals
    ("main := () -> int {\n  hi := 6\n  s: &int := 0\n  1..hi @ (i => s += i)\n  s\n}", 21),
    # the loop body can do real arithmetic on the element
    ("main := () -> int {\n  s: &int := 0\n  1..4 @ (n => s += n * n)\n  s\n}", 30),
    # range counting into a function call inside the body
    ("dbl := (x: int) -> int { x + x }\n"
     "main := () -> int {\n  s: &int := 0\n  1..3 @ (n => s += dbl(n))\n  s\n}", 12),
])
def test_range_reduce_matches_interpreter(program, val, tmp_path):
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == val
