"""Grid evaluator — keystone core + functions + the # / @ triad.

Control keys on one bit: PRESENT vs UNIT (`()`). Operators are partial (any UNIT
operand -> UNIT) except the selectors `||`/`&&` and `?`. `?` sets a block's topic;
`=>` matches it. Relations yield their right operand on success. A function is a
detached scope (it captures the module root, never the caller's locals). `#` fans
out collecting present results; `@` threads — present body exits the loop, () continues.
"""
from .parser import (
    parse, Lit, Unit, Name, Tuple, ListLit, MapLit, StructLit, Bind, InPlace, Bin, Range,
    Try, Iter, Block, Match, Fn, Call, Member, MethodCall, Index, Bang, Interp,
    Destructure, Store, Emit, Defer, ModuleDecl, ImportDecl, KeyedMatch,
    LitPat, UnitPat, BindPat, WildPat, TuplePat,
)


class _Unit:
    _inst = None
    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst
    def __repr__(self):
        return "()"


UNIT = _Unit()


def present(v):
    return v is not UNIT


class Env:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        e = self
        while e is not None:
            if name in e.vars:
                return e.vars[name]
            e = e.parent
        raise NameError(f"unbound label: {name}")

    def define(self, name, val):
        self.vars[name] = val

    def assign(self, name, val):
        e = self
        while e is not None:
            if name in e.vars:
                e.vars[name] = val
                return
            e = e.parent
        raise NameError(f"cannot mutate unbound label: {name}")

    def root(self):
        e = self
        while e.parent is not None:
            e = e.parent
        return e


class Func:
    __slots__ = ("params", "body", "root", "fallible", "stateful")
    def __init__(self, params, body, root, fallible=False, stateful=False):
        self.params = params
        self.body = body
        self.root = root
        self.fallible = fallible
        self.stateful = stateful


class TypeTag:
    """A base type name used as a value (e.g. in `Response = (status: int, …)`).
    Types are not checked at runtime, so this is an inert placeholder."""
    __slots__ = ("name",)
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name


class Lambda:
    """A reified body — `_ => expr`, `pat => expr`, or `{ … }` — in value position.
    Captures its defining env; applied (by a call or a combinator) to one argument."""
    __slots__ = ("node", "env")
    def __init__(self, node, env):
        self.node = node
        self.env = env


class Stream:
    """An eagerly-collected stream instance: yields each value, then () forever."""
    __slots__ = ("items", "cursor")
    def __init__(self, items):
        self.items = items
        self.cursor = 0

    def advance(self):
        if self.cursor < len(self.items):
            v = self.items[self.cursor]
            self.cursor += 1
            return v
        return UNIT


_emit_stack = []        # stack of collectors; >> appends to the top (one per running stream)
_defer_stack = []       # stack of frames; ~ appends (expr, env); run LIFO at function exit
_key_stack = []         # stack of iteration keys; a keyed pattern `k: v` reads the top


# ─── a small stdlib (namespaces are just dicts of builtins) ──────────────────

def _str_lines(s):
    return s.split("\n")

def _str_words(s):
    return s.split()

def _str_join(xs, sep=""):
    return sep.join(grid_str(x) for x in xs)

def _present_if(cond, val):
    return val if cond else UNIT

def _net_unavailable(*_a):
    raise RuntimeError("net.* needs real I/O; not available in the validator")


def _fs_read(path):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return UNIT


def _fs_write(path, content):
    with open(path, "w") as f:
        f.write(content if isinstance(content, str) else grid_str(content))
    return UNIT


def _make_stdlib():
    return {
        "str": {
            "lines": _str_lines,
            "words": _str_words,
            "trim": lambda s: s.strip(),
            "join": _str_join,
            "upper": lambda s: s.upper(),
            "lower": lambda s: s.lower(),
            "len": lambda s: len(s),
            "chars": lambda s: list(s),
            "split": lambda s, sep: s.split(sep),
            "replace": lambda s, a, b: s.replace(a, b),
            "contains": lambda s, sub: _present_if(sub in s, sub),
            "starts": lambda s, pre: _present_if(s.startswith(pre), pre),
            "ends": lambda s, suf: _present_if(s.endswith(suf), suf),
        },
        "sys": {
            "print": lambda *a: (print("".join(grid_str(x) for x in a), end=""), UNIT)[1],
            "println": lambda *a: (print("".join(grid_str(x) for x in a)), UNIT)[1],
        },
        "net": {k: _net_unavailable for k in
                ("listen", "accept", "readline", "read", "write", "close")},
        # mmio.* : a mock for *T effectful cells — each handle reads/writes a Grid place
        # (the volatile/effect semantics aren't observable in a tree-walker validator).
        "mmio": {n: (lambda addr: 0) for n in
                 ("u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64")},
        # fs.* : host file I/O so a Grid program can be a CLI compiler
        "fs": {"read": _fs_read, "write": _fs_write},
    }


STDLIB = _make_stdlib()


class Fallible:
    """The result of a `-> T ! E` call: exactly one of ok / err is present."""
    __slots__ = ("ok", "err")
    def __init__(self, ok, err):
        self.ok = ok
        self.err = err


class Propagate(Exception):
    """Carries a failure raised by `!` up to the enclosing fallible function."""
    def __init__(self, err):
        self.err = err


def as_pair(v):
    if isinstance(v, Fallible):
        return (v.ok, v.err)
    if isinstance(v, (tuple, list)):
        return tuple(v)
    raise RuntimeError(f"cannot destructure {v!r}")


def grid_eq(a, b):
    if a is UNIT or b is UNIT:
        return a is b
    if isinstance(a, bool) or isinstance(b, bool):     # defensive; Grid has no bool
        return a is b
    return type(a) == type(b) and a == b


# ─── eval ────────────────────────────────────────────────────────────────────

def eval_node(node, env, topic):
    t = type(node)

    if t is Lit:
        return node.val
    if t is Unit:
        return UNIT
    if t is Name:
        if node.id == "_":
            return topic                               # `_` is the body's current argument
        return env.get(node.id)
    if t is Tuple:
        return tuple(eval_node(i, env, topic) for i in node.items)
    if t is ListLit:
        return [eval_node(i, env, topic) for i in node.items]
    if t is MapLit:
        return {eval_node(k, env, topic): eval_node(v, env, topic) for k, v in node.entries}
    if t is StructLit:
        return {n: eval_node(v, env, topic) for n, v in node.fields}
    if t is Bind:
        env.define(node.name, eval_node(node.value, env, topic) if node.value is not None else UNIT)
        return UNIT
    if t is Range:
        return eval_range(eval_node(node.lo, env, topic), eval_node(node.hi, env, topic))
    if t is InPlace:
        cur = env.get(node.name)
        rhs = eval_node(node.value, env, topic)
        env.assign(node.name, _arith(node.op, cur, rhs))
        return UNIT
    if t is Fn:
        return Func(node.params, node.body, env.root(), node.fallible, node.stateful)
    if t is Emit:
        _emit_stack[-1].append(eval_node(node.value, env, topic))
        return UNIT
    if t is Defer:
        if _defer_stack:
            _defer_stack[-1].append((node.expr, env))
        return UNIT
    if t is ModuleDecl:
        return UNIT
    if t is ImportDecl:
        env.define(node.name, STDLIB.get(node.name, {}))
        return UNIT
    if t is Call:
        return eval_call(node, env, topic)
    if t is MethodCall:
        obj = eval_node(node.obj, env, topic)
        args = [eval_node(a, env, topic) for a in node.args]
        m = eval_member(obj, node.name)               # member-call if obj HAS the member
        if m is not UNIT and (isinstance(m, (Func, Stream)) or callable(m)):
            return apply_func(m, args)
        return apply_func(env.get(node.name), [obj] + args)   # else UFCS: name(obj, args)
    if t is Bang:
        return eval_bang(eval_node(node.expr, env, topic))
    if t is Interp:
        return "".join(
            part if kind == "lit" else grid_str(eval_node(part, env, topic))
            for kind, part in node.parts
        )
    if t is Store:                                     # `place = expr` — store, never introduce
        val = eval_node(node.value, env, topic)
        if type(node.target) is Name:
            env.assign(node.target.id, val)            # raises if the place was never introduced
        else:
            return eval_store_index(node.target, val, env, topic)
        return UNIT
    if t is Destructure:
        parts = as_pair(eval_node(node.value, env, topic))
        for name, val in zip(node.names, parts):
            if name != "_":
                (env.assign if node.store else env.define)(name, val)
        return UNIT
    if t is Member:
        return eval_member(eval_node(node.obj, env, topic), node.key)
    if t is Index:
        return eval_index(eval_node(node.obj, env, topic), eval_node(node.idx, env, topic))
    if t is Block:
        return Lambda(node, env)                        # value position: reify (applied later)
    if t is Bin:
        return eval_bin(node, env, topic)
    if t is Try:
        subj = eval_node(node.subj, env, topic)
        if present(subj):                              # then-branch; topic = subject (if-let)
            return _eval_branch(node.cons, env, subj)
        if node.els is not None:                       # else-branch; cond absent -> ambient topic
            return _eval_branch(node.els, env, topic)
        return UNIT
    if t is Iter:
        return eval_iter(node, env, topic)
    if t is Match:                                      # value position: reify
        return Lambda(node, env)
    if t is KeyedMatch:
        raise RuntimeError("keyed pattern `k: v` is valid only in iteration")

    raise RuntimeError(f"cannot eval {node}")


def eval_body(body, env, value):
    """Apply a body to one argument (`_` = value): a block runs; a `=>` arm matches
    and commits; a bare expression evaluates with `_` bound. This is *application*,
    distinct from reifying a `=>`/`{ }` as a Lambda value (eval_node)."""
    tb = type(body)
    if tb is Block:
        return eval_scope_block(body, Env(env), value)
    if tb is Match:
        sub = Env(env)
        if match_pat(body.pat, value, sub):
            return eval_node(body.res, sub, value)
        return UNIT
    if tb is KeyedMatch:
        sub = Env(env)
        if (_key_stack and match_pat(body.key, _key_stack[-1], sub)
                and match_pat(body.pat, value, sub)):
            return eval_node(body.res, sub, value)
        return UNIT
    return eval_node(body, Env(env), value)


def eval_call(node, env, topic):
    f = eval_node(node.fn, env, topic)
    args = [eval_node(a, env, topic) for a in node.args]
    return apply_func(f, args)


def apply_func(f, args):
    if isinstance(f, Lambda):                          # a reified body, applied to one arg
        return eval_body(f.node, f.env, args[0] if args else UNIT)
    if isinstance(f, Stream):                          # s() : next value, or ()
        return f.advance()
    if isinstance(f, Func):
        call_env = Env(f.root)
        for name, val in zip(f.params, args):
            call_env.define(name, val)
        _defer_stack.append([])                         # ~ deferrals run on every exit
        try:
            if f.stateful:
                _emit_stack.append([])
                try:
                    eval_scope_block(f.body, call_env, UNIT)
                finally:
                    collected = _emit_stack.pop()
                return Stream(collected)
            if f.fallible:
                try:
                    return Fallible(eval_scope_block(f.body, call_env, UNIT), UNIT)
                except Propagate as p:
                    return Fallible(UNIT, p.err)
            return eval_scope_block(f.body, call_env, UNIT)
        finally:
            for expr, denv in reversed(_defer_stack.pop()):
                eval_node(expr, denv, UNIT)
    if callable(f):                                    # builtin
        return f(*args)
    raise RuntimeError(f"not callable: {f!r}")


def eval_bang(v):
    # ! on a fallible result unwraps the success or propagates the error;
    # ! on a plain value raises it (the `"msg"!` failure form).
    if isinstance(v, Fallible):
        if v.err is not UNIT:
            raise Propagate(v.err)
        return v.ok
    raise Propagate(v)


def eval_member(obj, key):
    if isinstance(key, int):                           # tuple/list index by .N
        if isinstance(obj, (tuple, list)) and -len(obj) <= key < len(obj):
            return obj[key]
        return UNIT
    if key == "len" and isinstance(obj, (list, tuple, str, dict)):
        return len(obj)
    if isinstance(obj, dict):                          # struct field / namespace member
        return obj.get(key, UNIT)
    return UNIT


def eval_range(lo, hi):
    if isinstance(lo, int) and isinstance(hi, int):
        return list(range(lo, hi + 1))
    if isinstance(lo, str) and isinstance(hi, str) and len(lo) == 1 and len(hi) == 1:
        return [chr(c) for c in range(ord(lo), ord(hi) + 1)]
    return UNIT


def eval_index(obj, idx):
    if isinstance(obj, (list, tuple, str)):
        if isinstance(idx, int) and -len(obj) <= idx < len(obj):
            return obj[idx]
        return UNIT
    if isinstance(obj, dict):
        return obj.get(idx, UNIT)
    return UNIT


def eval_store_index(target, val, env, topic):
    # `place[i] = v` / `place.field = v` — a store; success yields (), an out-of-bounds
    # index yields a Fallible error (consume with `!`). Map insert always succeeds.
    if type(target) is Index:
        obj = eval_node(target.obj, env, topic)
        idx = eval_node(target.idx, env, topic)
        if isinstance(obj, list):
            if isinstance(idx, int) and -len(obj) <= idx < len(obj):
                obj[idx] = val
                return UNIT
            return Fallible(UNIT, f"index out of bounds: {grid_str(idx)}")
        if isinstance(obj, dict):
            obj[idx] = val
            return UNIT
        return Fallible(UNIT, "not indexable")
    if type(target) is Member:
        obj = eval_node(target.obj, env, topic)
        if isinstance(obj, dict):
            obj[target.key] = val
            return UNIT
        return Fallible(UNIT, f"no such field: {target.key}")
    raise RuntimeError(f"cannot store into {target}")


def _arith(op, l, r):
    if l is UNIT or r is UNIT:
        return UNIT
    if op == "+":
        return l + r
    if op == "-":
        return l - r
    if op == "*":
        return l * r
    if op == "%":
        return UNIT if r == 0 else l % r
    if op == "/":
        if r == 0:
            return UNIT
        return l // r if isinstance(l, int) and isinstance(r, int) else l / r
    if op == "&":
        return l & r
    if op == "|":
        return l | r
    if op == "^":
        return l ^ r
    if op == "<<":
        return l << r
    if op == ">>":
        return l >> r
    raise RuntimeError(f"unknown arithmetic op {op}")


def eval_bin(node, env, topic):
    op = node.op
    if op == "||":
        l = eval_node(node.l, env, topic)
        return l if present(l) else eval_node(node.r, env, topic)
    if op == "&&":
        l = eval_node(node.l, env, topic)
        return eval_node(node.r, env, topic) if present(l) else UNIT

    l = eval_node(node.l, env, topic)
    r = eval_node(node.r, env, topic)
    if l is UNIT or r is UNIT:
        return UNIT

    if op in ("+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>"):
        return _arith(op, l, r)
    if op == "==":
        return r if grid_eq(l, r) else UNIT
    if op == "!=":
        return r if not grid_eq(l, r) else UNIT
    if op == "<":
        return r if l < r else UNIT
    if op == "<=":
        return r if l <= r else UNIT
    if op == ">":
        return r if l > r else UNIT
    if op == ">=":
        return r if l >= r else UNIT
    raise RuntimeError(f"unknown operator {op}")


def _eval_branch(node, env, topic):
    # a `?` / `?:` branch is a body applied to the subject: a block runs, a `=>` arm
    # matches and commits, a bare expression evaluates with `_` = the subject.
    return eval_body(node, env, topic)


def eval_scope_block(block, env, topic):
    # A block is one scope, run as a sequence. A matching `=>` arm commits the block —
    # it returns the arm's result immediately, even if that result is `()`; a non-matching
    # arm yields `()` and is transparent. The topic threads as the last *present* value
    # (so arms compose on one subject, and a value-producing statement can set it); the
    # block's return is its last value (here `()` is NOT transparent — a trailing `()`
    # still returns `()`, which is what lets an `@` body force "continue").
    val = UNIT
    for item in block.items:                           # topic is FROZEN — no threading
        ti = type(item)
        if ti is Match:
            sub = Env(env)
            if match_pat(item.pat, topic, sub):
                return eval_node(item.res, sub, topic)
            val = UNIT
        elif ti is KeyedMatch:
            sub = Env(env)
            if (_key_stack and match_pat(item.key, _key_stack[-1], sub)
                    and match_pat(item.pat, topic, sub)):
                return eval_node(item.res, sub, topic)
            val = UNIT
        else:
            val = eval_node(item, env, topic)
    return val


def _source_items(v):
    """A source yields (index/key, element/value) tuples — the per-step topic."""
    if isinstance(v, dict):
        return list(v.items())
    if isinstance(v, (list, tuple, str)):
        return list(enumerate(v))
    if isinstance(v, Stream):
        rem = list(enumerate(v.items[v.cursor:]))
        v.cursor = len(v.items)
        return rem
    return None


def _drive_step(body, env, key, value):
    """Run the body for one keyed step: `_` = value, the key is on _key_stack."""
    _key_stack.append(key)
    try:
        return eval_body(body, env, value)
    finally:
        _key_stack.pop()


def eval_iter(node, env, topic):
    if node.op == "#":                                 # fan-out: collect every present result
        items = _source_items(eval_node(node.subj, env, topic))
        if items is None:
            return UNIT
        out = []
        for key, value in items:
            v = _drive_step(node.block, env, key, value)
            if present(v):
                out.append(v)
        return out

    # node.op == "@" — thread the body over a source. A present body value exits
    # the loop with it (find / break); () continues. How the source is *driven* is
    # read from its form:
    if node.subj is None:                              # bare @ {}: an always-present source
        while True:
            v = eval_body(node.block, env, UNIT)
            if present(v):
                return v

    if isinstance(node.subj, Block):                   # a literal block is a generator —
        while True:                                    # re-evaluated on each pull; () = done
            step = eval_scope_block(node.subj, Env(env), topic)
            if not present(step):
                return UNIT
            v = eval_body(node.block, env, step)
            if present(v):
                return v

    first = eval_node(node.subj, env, topic)           # any other source: evaluated once
    items = _source_items(first)
    if items is not None:                              # a collection -> iterate its elements
        for key, value in items:
            v = _drive_step(node.block, env, key, value)
            if present(v):
                return v
        return UNIT
    if present(first):                                 # a single value -> thread it once
        return eval_body(node.block, env, first)
    return UNIT                                        # () -> nothing to thread


def match_pat(pat, topic, env):
    t = type(pat)
    if t is WildPat:
        return True
    if t is UnitPat:
        return topic is UNIT
    if t is LitPat:
        return grid_eq(topic, pat.val)
    if t is BindPat:
        env.define(pat.name, topic)
        return True
    if t is TuplePat:
        if not isinstance(topic, (tuple, list)) or len(topic) != len(pat.items):
            return False
        return all(match_pat(p, v, env) for p, v in zip(pat.items, topic))
    raise RuntimeError(f"unknown pattern {pat}")


def grid_str(v):
    if v is UNIT:
        return "()"
    if isinstance(v, str):
        return v
    if isinstance(v, tuple):
        return "(" + ", ".join(grid_str(x) for x in v) + ")"
    if isinstance(v, list):
        return "[" + ", ".join(grid_str(x) for x in v) + "]"
    if isinstance(v, dict):
        return "(" + ", ".join(f"{k}: {grid_str(x)}" for k, x in v.items()) + ")"
    if isinstance(v, (Func, Lambda)):
        return "<fn>"
    if isinstance(v, TypeTag):
        return v.name
    if isinstance(v, Stream):
        return "<stream>"
    if isinstance(v, Fallible):
        return grid_str(v.ok) if v.err is UNIT else f"!{grid_str(v.err)}"
    return str(v)


_SIZED = {
    "u8": (0, 255), "u16": (0, 65535), "u32": (0, 2**32 - 1), "u64": (0, 2**64 - 1),
    "i8": (-128, 127), "i16": (-32768, 32767),
    "i32": (-2**31, 2**31 - 1), "i64": (-2**63, 2**63 - 1),
}


def _checked(lo, hi):
    return lambda v: v if isinstance(v, int) and lo <= v <= hi else UNIT


def make_global_env():
    g = Env()
    for name in ("int", "num", "char"):                 # base type names as inert tags
        g.define(name, TypeTag(name))
    for name, (lo, hi) in _SIZED.items():               # sized numerics: checked conversions
        g.define(name, _checked(lo, hi))
    g.define("f32", lambda v: float(v))
    g.define("f64", lambda v: float(v))
    for name, ns in STDLIB.items():                      # str / sys / net / mmio by default
        g.define(name, ns)
    return g


class Session:
    """A persistent evaluation context — the REPL keeps one across inputs."""
    def __init__(self):
        self.env = make_global_env()

    def eval(self, src):
        try:
            return eval_scope_block(parse(src), self.env, UNIT)
        except Propagate as p:
            raise RuntimeError(f"unhandled failure: {grid_str(p.err)}")


def run(src):
    return Session().eval(src)
