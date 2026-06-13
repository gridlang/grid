"""The composition showcase actually runs — every chain in examples/composition.grid
is executed and its result checked, so the demo stays honest."""
import os
from gridi import run

_HERE = os.path.dirname(__file__)
COMP = open(os.path.join(_HERE, "..", "..", "examples", "composition.grid")).read()


def q(expr):
    return run(COMP + "\n" + expr)


def test_pipeline_map_filter_reduce():
    assert q("odd_sq_sum") == 165


def test_nested_fanout_table():
    assert q("table") == [[1, 2, 3], [2, 4, 6], [3, 6, 9]]


def test_transform_then_find():
    assert q("first_big_sq") == 64


def test_running_fold():
    assert q("prefix_sums") == [1, 3, 6, 10, 15]


def test_stream_filter():
    assert q("even_squares") == [4, 16, 36, 64, 100]


def test_stream_over_stream():
    assert q("first_three_evens") == [2, 4, 6]


def test_guard_and_match_block():
    assert q("labelled") == ["odd", "even", "odd", "even", "odd", "even"]
