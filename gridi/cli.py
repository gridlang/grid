"""gridi command line — a file runner and a REPL.

    python -m gridi              # start the REPL
    python -m gridi file.grid    # run a file, print its last value
"""
import sys

from .interp import Session, grid_str, UNIT, Func, apply_func, Propagate


BANNER = "Grid · gridi REPL — Ctrl-D to exit, blank line to force-evaluate"


def _incomplete(err):
    # the parser ran out of input (open bracket / mid-expression) rather than
    # hitting a genuine error — keep reading more lines in the REPL
    return "EOF" in str(err)


def _lookup(env, name):
    e = env
    while e is not None:
        if name in e.vars:
            return e.vars[name]
        e = e.parent
    return None


def complete(env, text):
    """Tab-completion candidates for `text` against a live environment.

    After a dot, complete a namespace's / struct's members; otherwise complete
    visible bindings (and the two declaration words).
    """
    if "." in text:
        obj, _, prefix = text.rpartition(".")
        target = _lookup(env, obj)
        if isinstance(target, dict):
            return sorted(f"{obj}.{k}" for k in target if k.startswith(prefix))
        return []
    names = set(("module", "import"))
    e = env
    while e is not None:
        names.update(e.vars.keys())
        e = e.parent
    return sorted(n for n in names if n.startswith(text))


def _install_readline(session):
    try:
        import readline
    except ImportError:
        return
    # keep '.' and identifier chars OUT of the delimiters so a dotted path
    # (str.li) is treated as one completion token
    readline.set_completer_delims(" \t\n`~!@#$%^&*()-=+[{]}\\|;:'\",<>/?")

    def completer(text, state):
        if state == 0:
            completer.matches = complete(session.env, text)
        return completer.matches[state] if state < len(completer.matches) else None

    readline.set_completer(completer)
    if "libedit" in (getattr(readline, "__doc__", "") or ""):
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")


def repl():
    print(BANNER)
    session = Session()
    _install_readline(session)              # tab-completion, history, line editing
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


def run_file(path, args=None):
    try:
        src = open(path).read()
    except OSError as e:
        print(f"gridi: {e}", file=sys.stderr)
        return 1
    session = Session()
    try:
        value = session.eval(src)
        main_fn = session.env.vars.get("main")
        if isinstance(main_fn, Func):                  # CLI entry: main(args) -> exit code
            result = apply_func(main_fn, [list(args or [])])
            return result if isinstance(result, int) else 0
    except SyntaxError as e:
        print(f"parse error: {e}", file=sys.stderr)
        return 1
    except Propagate as p:
        print(f"unhandled failure: {grid_str(p.err)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if value is not UNIT:
        print(grid_str(value))
    return 0


def main(argv):
    if len(argv) > 1:
        return run_file(argv[1], argv[2:])
    repl()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
