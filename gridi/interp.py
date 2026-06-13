"""Grid evaluator — the keystone core.

The whole of control flow keys on one bit: a value is PRESENT, or it is UNIT
(`()`, the one nothing). Operators are partial — any UNIT operand makes the
result UNIT — except the selectors `||`/`&&` and `?`, which inspect presence.
`?` sets a block's *topic*; `=>` matches the topic. Relations yield their right
operand on success (so comparisons chain), `()` on failure.
"""
from .parser import (
    parse, Lit, Unit, Name, Tuple, Bind, Bin, Try, Block, Match,
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


def grid_eq(a, b):
    if a is UNIT or b is UNIT:
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
            raise SyntaxError("`_` is a pattern, not a value")
        return env.get(node.id)
    if t is Tuple:
        return tuple(eval_node(i, env, topic) for i in node.items)
    if t is Bind:
        env.define(node.name, eval_node(node.value, env, topic))
        return UNIT                                   # a binding yields () (Layer 5)
    if t is Block:
        return eval_scope_block(node, Env(env), topic)
    if t is Bin:
        return eval_bin(node, env, topic)
    if t is Try:
        subj = eval_node(node.subj, env, topic)
        if not present(subj):
            return UNIT
        if type(node.cons) is Block:
            return eval_match_block(node.cons, Env(env), subj)
        return eval_node(node.cons, env, subj)        # guard: `cond ? result`
    if t is Match:
        sub = Env(env)
        if match_pat(node.pat, topic, sub):
            return eval_node(node.res, sub, topic)
        return UNIT

    raise RuntimeError(f"cannot eval {node}")


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
    if l is UNIT or r is UNIT:                         # partial: nothing in, nothing out
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
            return UNIT                                # divide by zero -> () (no exception)
        return l // r if isinstance(l, int) and isinstance(r, int) else l / r

    # relations: yield the RIGHT operand on success, () on failure
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


def eval_scope_block(block, env, topic):
    """Plain block: evaluate in order, value is the last expression (() if empty)."""
    val = UNIT
    for item in block.items:
        val = eval_node(item, env, topic)
    return val


def eval_match_block(block, env, topic):
    """`?`-opened block: first arm that yields a present value wins, else ()."""
    for item in block.items:
        val = eval_node(item, env, topic)
        if present(val):
            return val
    return UNIT


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
        if not isinstance(topic, tuple) or len(topic) != len(pat.items):
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
    return str(v)


def run(src):
    ast = parse(src)
    return eval_scope_block(ast, Env(), UNIT)
