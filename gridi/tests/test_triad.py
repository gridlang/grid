"""Slice 2: functions + the # / @ triad (map, filter, reduce, find, loop).

Functions are detached scopes; # fans out collecting present results; @ threads
(present body exits the loop, () continues). An expression source is evaluated
once — a collection iterates, a single value threads once; a literal block source
is a generator, re-evaluated each pull (the loop form). Topic for a list element
is (index, element).
"""
from gridi import run, UNIT


# --- functions ---------------------------------------------------------------

def test_function_call():
    assert run("add = (x: int, y: int) -> int { x + y }\nadd(2, 3)") == 5


def test_first_class_function():
    assert run("double = (n: int) -> int { n * 2 }\nf = double\nf(5)") == 10


def test_ufcs():
    assert run("inc = (n: int) -> int { n + 1 }\n5.inc()") == 6


def test_detached_scope_no_closures():
    # the function body sees module constants, never the caller's locals
    src = (
        "base = 100\n"
        "addbase = (n: int) -> int { n + base }\n"
        "caller = (n: int) -> int { local = 7\naddbase(n) }\n"
        "caller(1)"
    )
    assert run(src) == 101


# --- indexing and members are partial ---------------------------------------

def test_index_partial():
    assert run("xs = [10, 20, 30]\nxs[1]") == 20
    assert run("xs = [10, 20, 30]\nxs[5]") is UNIT      # out of bounds -> ()
    assert run("[10, 20, 30][0]") == 10


def test_tuple_and_struct_members():
    assert run("p = (1, 2)\np.0") == 1
    assert run("q = (x: 1, y: 2)\nq.x") == 1
    assert run("q = (x: 1, y: 2)\nq.z") is UNIT          # missing field -> ()


# --- # fan-out : map and filter ---------------------------------------------

def test_map():
    assert run("[1, 2, 3] # { (_, n) => n * 2 }") == [2, 4, 6]


def test_filter_via_unit():
    assert run("[1, 2, 3, 4] # { (_, n) => n % 2 == 0 ? n }") == [2, 4]


def test_index_is_available():
    assert run("[5, 6, 7] # { (i, _) => i }") == [0, 1, 2]


# --- @ thread : reduce, find, loop ------------------------------------------

def test_reduce_with_accumulator():
    src = "sum: &int = 0\n[1, 2, 3, 4] @ { (_, n) => sum += n }\nsum"
    assert run(src) == 10


def test_find_present_exits():
    assert run("[10, 20, 30] @ { (_, x) => x == 20 ? x }") == 20


def test_find_not_found_is_unit():
    assert run("[10, 20, 30] @ { (_, x) => x == 99 ? x }") is UNIT


def test_loop_over_block_generator():
    # A *literal block* source is re-evaluated on each pull: the loop runs while the
    # block yields present and stops when it yields (). This is the loop / while form.
    assert run("i: &int = 0\n{ i < 3 } @ { i += 1 }\ni") == 3


def test_block_generator_with_collection_valued_pull():
    # The generator yields its value — `!=` returns the string "" — and a present
    # value continues the loop whatever its type; () stops it. Decided by the block
    # form, never by the runtime type of the pulled value.
    src = (
        'lines = ["a", "b", "", "c"]\n'
        "i: &int = 0\n"
        '{ lines[i] != "" } @ { i += 1 }\n'
        "i"
    )
    assert run(src) == 2


def test_relation_source_threads_once_not_loops():
    # An *expression* source is evaluated ONCE — partials: `i < 3` yields 3, threaded
    # through the body a single time. Without a block source, @ does not loop.
    assert run("i: &int = 0\ni < 3 @ { i += 1 }\ni") == 1


def test_chained_fanout():
    src = "[1, 2, 3] # { (_, n) => n + 1 } # { (_, n) => n * 10 }"
    assert run(src) == [20, 30, 40]


def test_guard_consequent_inplace():
    # a `?` guard whose consequent is an in-place op: `n > 2 ? big += n`
    assert run("big: &int = 0\n1..5 @ { (_, n) => n > 2 ? big += n }\nbig") == 12
