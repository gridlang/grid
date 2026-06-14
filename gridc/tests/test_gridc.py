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
@pytest.mark.parametrize("n", [0, 7, 42, 200])
def test_int_main_matches_interpreter(n, tmp_path):
    program = f"main := () -> int {{ {n} }}\n"
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == n
