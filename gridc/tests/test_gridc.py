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


@clang
@pytest.mark.parametrize("program,val", [
    # one-armed `?` (try): present yields the value, absent yields ()
    ("main := () -> int { 5 > 3 ? 42 }", 42),
    ("main := () -> int { 5 < 3 ? 42 }", 0),
    # a one-armed try bound and used later (absent -> () -> 0 at the exit boundary)
    ("main := () -> int {\n  x := 7 > 2 ? 9\n  x + 1\n}", 10),
    # @ first-success (find): first element whose arm is present, exit early
    ("main := () -> int {\n  1..10 @ (n => n * n > 30 ? n)\n}", 6),
    # find that matches nothing -> ()
    ("main := () -> int {\n  1..3 @ (n => n > 99 ? n)\n}", 0),
    # the arm's present payload can be a computed value
    ("main := () -> int {\n  hit := 1..10 @ (n => n * n > 30 ? n * n)\n  hit\n}", 36),
    # reduce and find compose: sum 1..5, then find first > 2
    ("main := () -> int {\n  s: &int := 0\n  1..5 @ (n => s += n)\n  f := 1..10 @ (n => n > 2 ? n)\n  s + f\n}", 18),
])
def test_present_unit_value_model(program, val, tmp_path):
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == val


@clang
@pytest.mark.parametrize("program,val", [
    # string literals are fat values {len, ptr}; .len reads the length field
    ('main := () -> int { "hello".len }', 5),
    ('main := () -> int { "".len }', 0),
    # a string bound by := infers str type; .len works through the slot
    ('main := () -> int {\n  s := "grid"\n  s.len\n}', 4),
    # .len yields i64, so it composes with integer arithmetic
    ('main := () -> int {\n  a := "foo"\n  b := "barbar"\n  a.len + b.len\n}', 9),
    ('main := () -> int {\n  s := "abcdefg"\n  s.len - 2\n}', 5),
])
def test_string_literals_and_len(program, val, tmp_path):
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == val


@clang
@pytest.mark.parametrize("program,val", [
    # concat allocates in the arena and copies both halves; .len of the result
    ('main := () -> int {\n  s := "ab" + "cde"\n  s.len\n}', 5),
    ('main := () -> int { ("ab" + "cd").len }', 4),
    # chained concat
    ('main := () -> int {\n  s := "a" + "bc" + "def"\n  s.len\n}', 6),
    # concat with an empty operand
    ('main := () -> int {\n  s := "" + "grid"\n  s.len\n}', 4),
    # mutable str accumulator via store (= s + ...), the way gridc builds output
    ('main := () -> int {\n  s: &str := "ab"\n  s = s + "cd"\n  s.len\n}', 4),
    # mutable str accumulator via += concat in a loop (1..4 is 4 iterations)
    ('main := () -> int {\n  s: &str := ""\n  1..4 @ (n => s += "xy")\n  s.len\n}', 8),
])
def test_string_concat(program, val, tmp_path):
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == val


@clang
@pytest.mark.parametrize("program,val", [
    # tuple construction + numeric field access
    ('main := () -> int {\n  t := (3, 4)\n  t.0 * 10 + t.1\n}', 34),
    ('main := () -> int {\n  t := (7, 9)\n  t.1 - t.0\n}', 2),
    # multi-name destructure of a tuple literal
    ('main := () -> int {\n  a, b := (5, 6)\n  a * b\n}', 30),
    ('main := () -> int {\n  a, b, c := (1, 2, 3)\n  a + b * c\n}', 7),
    # destructure from a tuple-valued local
    ('main := () -> int {\n  t := (4, 9)\n  a, b := t\n  a + b\n}', 13),
    # heterogeneous tuple: a str field and an int field, chained .0.len
    ('main := () -> int {\n  t := ("hi", 5)\n  t.0.len + t.1\n}', 7),
    # tuple fields feeding a mutable accumulator
    ('main := () -> int {\n  t := (2, 3)\n  s: &int := 0\n  s += t.0\n  s += t.1\n  s\n}', 5),
])
def test_tuples_and_destructure(program, val, tmp_path):
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == val


@clang
@pytest.mark.parametrize("program,val", [
    # function returning a tuple, destructured at the call site
    ('pair := () -> (int, int) { (8, 3) }\nmain := () -> int {\n  a, b := pair()\n  a - b\n}', 5),
    # str parameter, .len through the typed param slot
    ('slen := (s: str) -> int { s.len }\nmain := () -> int { slen("hello") }', 5),
    # str param in, str out (concat), consumed by .len
    ('greet := (s: str) -> str { "hi " + s }\nmain := () -> int { greet("bob").len }', 6),
    # tuple parameter, field access
    ('fst := (t: (int, int)) -> int { t.0 }\nmain := () -> int { fst((9, 2)) }', 9),
    # function returns a tuple, bound and field-accessed
    ('mk := (x: int) -> (int, int) { (x, x * 2) }\nmain := () -> int {\n  p := mk(7)\n  p.1 - p.0\n}', 7),
    # two str params concatenated
    ('cat := (a: str, b: str) -> str { a + b }\nmain := () -> int { cat("ab", "cde").len }', 5),
])
def test_typed_function_abi(program, val, tmp_path):
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == val


@clang
@pytest.mark.parametrize("body,val", [
    # string equality / inequality (length + bytes via __strcmp)
    ('"abc" == "abc" ? 5 : 0', 5),
    ('"abc" == "abd" ? 5 : 0', 0),
    ('"ab" != "abc" ? 7 : 0', 7),
    # lexicographic ordering
    ('"a" < "b" ? 7 : 0', 7),
    ('"abc" < "abd" ? 7 : 0', 7),
    ('"b" >= "a" ? 7 : 0', 7),
    ('"z" <= "a" ? 7 : 0', 0),
    # && / || over relations (the lexer's char predicates)
    ('c := "5"\n  c >= "0" && c <= "9" ? 1 : 0', 1),
    ('c := "x"\n  c >= "0" && c <= "9" ? 1 : 0', 0),
    ('c := "\\n"\n  (c == "\\n" || c == ";") ? 9 : 0', 9),
    ('c := "a"\n  (c == "\\n" || c == ";") ? 9 : 0', 0),
    # string indexing s[i] -> a 1-char string, compared
    ('s := "hello"\n  s[1] == "e" ? 42 : 0', 42),
    ('s := "abc"\n  s[0] == "a" && s[2] == "c" ? 8 : 0', 8),
])
def test_string_compare_and_index(body, val, tmp_path):
    program = "main := () -> int {\n  " + body + "\n}\n"
    assert compile_exit(program, tmp_path) == interp_exit(program, tmp_path) == val
