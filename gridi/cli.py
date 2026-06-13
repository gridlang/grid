"""gridi command line — a file runner and a REPL.

    python -m gridi              # start the REPL
    python -m gridi file.grid    # run a file, print its last value
"""
import sys

from .interp import Session, grid_str, UNIT


BANNER = "Grid · gridi REPL — Ctrl-D to exit, blank line to force-evaluate"


def _incomplete(err):
    # the parser ran out of input (open bracket / mid-expression) rather than
    # hitting a genuine error — keep reading more lines in the REPL
    return "EOF" in str(err)


def repl():
    print(BANNER)
    session = Session()
    buf = []
    while True:
        prompt = "» " if not buf else "… "
        try:
            line = input(prompt)
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            print("^C")
            buf = []
            continue

        buf.append(line)
        src = "\n".join(buf)

        try:
            value = session.eval(src)
        except SyntaxError as e:
            if _incomplete(e) and line.strip() != "":
                continue                       # incomplete input — read another line
            print(f"  parse error: {e}")
            buf = []
            continue
        except Exception as e:                 # runtime error (NameError, failure, …)
            print(f"  error: {e}")
            buf = []
            continue

        buf = []
        if value is not UNIT:
            print(grid_str(value))


def run_file(path):
    try:
        src = open(path).read()
    except OSError as e:
        print(f"gridi: {e}", file=sys.stderr)
        return 1
    try:
        value = Session().eval(src)
    except SyntaxError as e:
        print(f"parse error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if value is not UNIT:
        print(grid_str(value))
    return 0


def main(argv):
    if len(argv) > 1:
        return run_file(argv[1])
    repl()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
