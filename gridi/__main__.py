import sys
import threading

from .cli import main


def _run():
    # gridc.grid has deeply nested ?: ladders; the tree-walker recurses deep
    # while parsing/evaluating them. Run on a big stack with a high recursion
    # limit so a self-host compile doesn't blow Python's default cap / C stack.
    sys.setrecursionlimit(2_000_000)
    _run.rc = main(sys.argv)


_run.rc = 1
threading.stack_size(1024 * 1024 * 1024)   # 1 GB thread stack
t = threading.Thread(target=_run)
t.start()
t.join()
sys.exit(_run.rc)
