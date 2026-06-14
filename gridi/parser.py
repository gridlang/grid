"""Grid parser — recursive descent producing the AST.

Precedence, tight -> loose: postfix (call / member / index) , * / % , + - ,
comparison , the combinators ? # @ , && , || . A `{block}` binds to the
combinator on its immediate left, so `err ? {…} || 0` is `(err ? {…}) || 0`.

A block is one node; the evaluator picks its mode from context — `?`'s block is a
match (first present arm), a `#`/`@` body and a bare block are scopes (last value).
"""
from dataclasses import dataclass, field
from .lexer import lex


# ─── AST ────────────────────────────────────────────────────────────────────

@dataclass
class Lit:       val: object
@dataclass
class Unit:      pass
@dataclass
class Name:      id: str
@dataclass
class Tuple:     items: list
@dataclass
class ListLit:   items: list
@dataclass
class MapLit:    entries: list                         # list of (key_node, value_node)
@dataclass
class StructLit: fields: list           # list of (name, value_node)
@dataclass
class Bind:      name: str; value: object; mutable: bool = False
@dataclass
class InPlace:   name: str; op: str; value: object
@dataclass
class Bin:       op: str; l: object; r: object
@dataclass
class Range:     lo: object; hi: object               # a .. b (inclusive)
@dataclass
class Try:       subj: object; cons: object; els: object = None   # cond ? cons [: els]
@dataclass
class Iter:      op: str; subj: object; block: object   # op in {"#", "@"}; subj may be None
@dataclass
class Block:     items: list
@dataclass
class Match:     pat: object; res: object
@dataclass
class KeyedMatch: key: object; pat: object; res: object   # iteration arm: kpat: vpat => res
@dataclass
class Fn:        params: list; body: object; fallible: bool = False; stateful: bool = False
@dataclass
class Emit:      value: object                          # prefix >> (yield from a stream)
@dataclass
class Defer:     expr: object                           # prefix ~ (run at scope exit)
@dataclass
class ModuleDecl: name: str
@dataclass
class ImportDecl: name: str
@dataclass
class Call:      fn: object; args: list
@dataclass
class Bang:      expr: object                           # postfix ! (raise / unwrap-or-propagate)
@dataclass
class Interp:    parts: list                            # list of ("lit", str) | ("expr", node)
@dataclass
class Destructure: names: list; value: object; store: bool = False
@dataclass
class Store:      target: object; value: object         # `place = expr` / `place[i] = expr`
@dataclass
class Member:    obj: object; key: object               # str field or int index
@dataclass
class MethodCall: obj: object; name: str; args: list    # obj.name(args): member-call, else UFCS
@dataclass
class Index:     obj: object; idx: object

# patterns
@dataclass
class LitPat:    val: object
@dataclass
class UnitPat:   pass
@dataclass
class BindPat:   name: str
@dataclass
class WildPat:   pass
@dataclass
class TuplePat:  items: list


# ─── Parser ─────────────────────────────────────────────────────────────────

class Parser:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def cur(self):
        return self.toks[self.i]

    def peek(self, n=1):
        return self.toks[min(self.i + n, len(self.toks) - 1)]

    def at(self, kind, val=None):
        t = self.cur()
        return t.kind == kind and (val is None or t.val == val)

    def eat(self, kind, val=None):
        t = self.cur()
        if t.kind != kind or (val is not None and t.val != val):
            want = val if val is not None else kind
            raise SyntaxError(f"expected {want!r}, got {t}")
        self.i += 1
        return t

    def nl(self):
        while self.at("NL"):
            self.i += 1

    def seps(self):
        while self.at("NL") or self.at("PUNCT", ";"):
            self.i += 1

    # program / blocks ---------------------------------------------------------

    def parse_program(self):
        items = self.parse_items("EOF", None)
        self.eat("EOF")
        return Block(items)

    def parse_block(self):
        self.eat("PUNCT", "{")
        items = self.parse_items("PUNCT", "}")
        self.eat("PUNCT", "}")
        return Block(items)

    def _end(self, ek, ev):
        return self.at("EOF") or self.at(ek, ev)

    def parse_items(self, ek, ev):
        items = []
        self.seps()
        while not self._end(ek, ev):
            before = self.i
            items.append(self.parse_item())
            if self.at("NL") or self.at("PUNCT", ";"):
                self.seps()
            else:
                break
            if self.i == before:
                raise SyntaxError(f"stuck at {self.cur()}")
        return items

    def parse_item(self):
        if self.at("NAME", "module"):
            self.eat("NAME")
            return ModuleDecl(self.eat("NAME").val)
        if self.at("NAME", "import"):
            self.eat("NAME")
            name = self.eat("NAME").val
            while self.at("OP", "/") or self.at("PUNCT", "."):
                self.i += 1
                name = self.eat("NAME").val
            return ImportDecl(name)
        d = self.try_destructure()
        if d is not None:
            return d
        if self.at("NAME"):
            nxt = self.peek()
            if nxt.kind == "INPLACE":                          # place += expr  (store)
                name = self.eat("NAME").val
                op = self.eat("INPLACE").val[:-1]              # strip trailing '='
                self.nl()
                return InPlace(name, op, self.parse_expr())
            if nxt.kind == "DEFINE":                           # name := expr  (introduce)
                name = self.eat("NAME").val
                self.eat("DEFINE"); self.nl()
                return Bind(name, self.parse_expr())
            if nxt.kind == "PUNCT" and nxt.val == ":":         # name: [&|*]T [:=|= expr]  (introduce)
                name = self.eat("NAME").val
                self.eat("PUNCT", ":")
                mutable = False
                if self.at("PUNCT", "&") or self.at("OP", "*"):
                    self.i += 1
                    mutable = True
                self.parse_type()                 # parsed for shape, ignored at runtime
                value = None
                if self.at("DEFINE") or self.at("PUNCT", "="):
                    self.i += 1
                    self.nl()
                    value = self.parse_expr()
                return Bind(name, value, mutable)
            if nxt.kind == "PUNCT" and nxt.val == "=":         # place = expr  (store, must exist)
                name = self.eat("NAME").val
                self.eat("PUNCT", "=")
                self.nl()
                return Store(Name(name), self.parse_expr())
        e = self.parse_expr()
        if self.at("FATARROW"):
            self.eat("FATARROW")
            self.nl()
            return Match(self.to_pattern(e), self.parse_arm_result())
        return e

    def try_destructure(self):
        # `a, b, ... = expr` (>= 2 names) -> Destructure
        if not self.at("NAME"):
            return None
        names = [self.cur().val]
        j = self.i + 1
        while self.toks[j].kind == "PUNCT" and self.toks[j].val == ",":
            j += 1
            if self.toks[j].kind != "NAME":
                return None
            names.append(self.toks[j].val)
            j += 1
        if len(names) < 2:
            return None
        tj = self.toks[j]
        if tj.kind == "DEFINE":                            # a, b := expr  (introduce)
            store = False
        elif tj.kind == "PUNCT" and tj.val == "=":         # a, b = expr   (store)
            store = True
        else:
            return None
        self.i = j + 1
        self.nl()
        return Destructure(names, self.parse_expr(), store)

    def parse_arm_result(self):
        # an arm's right-hand side may be an in-place op (e.g. `=> sum += n`)
        if self.at("NAME") and self.peek().kind == "INPLACE":
            name = self.eat("NAME").val
            op = self.eat("INPLACE").val[0]
            self.nl()
            return InPlace(name, op, self.parse_expr())
        return self.parse_expr()

    def parse_consequent(self):
        # the (non-block) right-hand side of `?` may be an emit, a defer, or an
        # in-place op, as well as an ordinary expression
        if self.at("SHIFT", ">>"):
            self.eat("SHIFT", ">>"); self.nl()
            return Emit(self.parse_consequent())
        if self.at("PUNCT", "~"):
            self.eat("PUNCT", "~"); self.nl()
            return Defer(self.parse_consequent())
        if self.at("NAME") and self.peek().kind == "INPLACE":
            name = self.eat("NAME").val
            op = self.eat("INPLACE").val[0]
            self.nl()
            return InPlace(name, op, self.parse_comb())
        return self.parse_ternary()

    def parse_type(self):
        # types are not checked at runtime — skip a type expression by tokens,
        # stopping at the punctuation that ends it (=, comma, closing, !, {, …)
        depth = 0
        while True:
            t = self.cur()
            if t.kind in ("EOF", "NL", "DEFINE"):
                return
            if t.kind == "PUNCT" and t.val in ("(", "["):
                depth += 1
                self.i += 1
                continue
            if t.kind == "PUNCT" and t.val in (")", "]"):
                if depth == 0:
                    return
                depth -= 1
                self.i += 1
                continue
            if depth == 0 and t.kind == "PUNCT" and t.val in ("=", ",", ";", "!", "{"):
                return
            self.i += 1

    # expressions --------------------------------------------------------------

    def parse_expr(self):
        if self.at("SHIFT", ">>"):                  # prefix >> : emit a stream value
            self.eat("SHIFT", ">>"); self.nl()
            return Emit(self.parse_expr())
        if self.at("PUNCT", "~"):                   # prefix ~ : defer to scope exit
            self.eat("PUNCT", "~"); self.nl()
            return Defer(self.parse_expr())
        return self.parse_ternary()

    def parse_ternary(self):
        # `?:` is the loosest operator, right-associative. The condition and both
        # branches accept full expressions (=> / || / && / combinators all bind tighter).
        cond = self.parse_match()
        if not self.at("PUNCT", "?"):
            return cond
        self.eat("PUNCT", "?"); self.nl()
        cons = self.parse_block() if self.at("PUNCT", "{") else self.parse_consequent()
        els = None
        if self.at("PUNCT", ":"):
            self.eat("PUNCT", ":"); self.nl()
            els = self.parse_block() if self.at("PUNCT", "{") else self.parse_consequent()
        return Try(cond, cons, els)

    def parse_match(self):
        # `=>` is an ordinary operator just under `?:`: a pattern on the left, and a full
        # expression on the right (arm-result form — allows `+=` / `>>` / `~`). So a bare
        # `pat => result` works anywhere an expression does, e.g. `f() ? x => g(x) : h()`.
        left = self.parse_or()
        if self.at("PUNCT", ":"):                  # maybe a keyed pattern  kpat: vpat => res
            save = self.i
            self.eat("PUNCT", ":"); self.nl()
            val = self.parse_or()
            if self.at("FATARROW"):
                self.eat("FATARROW"); self.nl()
                return KeyedMatch(self.to_pattern(left), self.to_pattern(val),
                                  self.parse_arm_result())
            self.i = save                          # not keyed (e.g. a ?: else) — back out
        if self.at("FATARROW"):
            self.eat("FATARROW"); self.nl()
            return Match(self.to_pattern(left), self.parse_arm_result())
        return left

    def parse_or(self):
        l = self.parse_and()
        while self.at("OROR"):
            self.eat("OROR"); self.nl()
            l = Bin("||", l, self.parse_and())
        return l

    def parse_and(self):
        l = self.parse_comb()
        while self.at("ANDAND"):
            self.eat("ANDAND"); self.nl()
            l = Bin("&&", l, self.parse_comb())
        return l

    def parse_comb(self):
        left = self.parse_cmp()
        while True:
            if self.at("PUNCT", "#") or self.at("PUNCT", "@"):
                op = self.eat("PUNCT").val
                self.nl()
                left = Iter(op, left, self.parse_cmp())   # body: bare expr, or a ({}/()) group
            else:
                return left

    def parse_cmp(self):
        l = self.parse_range()
        while self.cur().kind in ("EQOP", "CMP"):
            op = self.eat(self.cur().kind).val
            self.nl()
            l = Bin(op, l, self.parse_range())
        return l

    def parse_range(self):
        l = self.parse_add()
        while self.at("RANGE"):
            self.eat("RANGE"); self.nl()
            l = Range(l, self.parse_add())
        return l

    def parse_add(self):
        l = self.parse_mul()
        while self.at("OP", "+") or self.at("OP", "-"):
            op = self.eat("OP").val; self.nl()
            l = Bin(op, l, self.parse_mul())
        return l

    def parse_mul(self):
        l = self.parse_unary()
        while self.at("OP", "*") or self.at("OP", "/") or self.at("OP", "%"):
            op = self.eat("OP").val; self.nl()
            l = Bin(op, l, self.parse_unary())
        return l

    def parse_unary(self):
        if self.at("OP", "-"):                       # prefix minus: -x  ==  0 - x
            self.eat("OP", "-"); self.nl()
            return Bin("-", Lit(0), self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        if self.at("PUNCT", "(") and self._paren_is_params():
            return self.parse_fn_rest(self.parse_params())
        node = self.parse_atom()
        while True:
            if self.at("PUNCT", "("):
                node = Call(node, self.parse_args())
            elif self.at("PUNCT", "."):
                self.eat("PUNCT", ".")
                if self.at("INT"):
                    node = Member(node, int(self.eat("INT").val))
                else:
                    name = self.eat("NAME").val
                    if self.at("PUNCT", "("):       # obj.name(args): member-call or UFCS
                        node = MethodCall(node, name, self.parse_args())
                    else:
                        node = Member(node, name)
            elif self.at("PUNCT", "["):
                self.eat("PUNCT", "["); self.nl()
                idx = self.parse_expr(); self.nl()
                self.eat("PUNCT", "]")
                node = Index(node, idx)
            elif self.at("PUNCT", "!"):
                self.eat("PUNCT", "!")
                node = Bang(node)
            else:
                return node

    def parse_args(self):
        self.eat("PUNCT", "("); self.nl()
        args = []
        if not self.at("PUNCT", ")"):
            args.append(self.parse_expr()); self.nl()
            while self.at("PUNCT", ","):
                self.eat("PUNCT", ","); self.nl()
                args.append(self.parse_expr()); self.nl()
        self.eat("PUNCT", ")")
        return args

    def _paren_is_params(self):
        # a `(...)` that is immediately followed by `->` or `>>` is a parameter list
        depth = 0
        j = self.i
        n = len(self.toks)
        while j < n:
            t = self.toks[j]
            if t.kind == "EOF":
                return False
            if t.kind == "PUNCT" and t.val in ("(", "[", "{"):
                depth += 1
            elif t.kind == "PUNCT" and t.val in (")", "]", "}"):
                depth -= 1
                if depth == 0:
                    break
            j += 1
        k = j + 1
        while k < n and self.toks[k].kind == "NL":
            k += 1
        t = self.toks[k]
        return t.kind == "ARROW" or (t.kind == "SHIFT" and t.val == ">>")

    def parse_params(self):
        self.eat("PUNCT", "("); self.nl()
        names = []
        if self.at("PUNCT", ")"):
            self.eat("PUNCT", ")")
            return names
        while True:
            names.append(self.eat("NAME").val)
            if self.at("PUNCT", ":"):
                self.eat("PUNCT", ":")
                if self.at("PUNCT", "&"):
                    self.eat("PUNCT", "&")
                self.parse_type()                   # parameter type, ignored at runtime
            if self.at("PUNCT", ","):
                self.eat("PUNCT", ","); self.nl()
                if self.at("PUNCT", ")"):
                    break
                continue
            break
        self.eat("PUNCT", ")")
        return names

    def parse_fn_rest(self, params):
        fallible = stateful = False
        if self.at("SHIFT", ">>"):                  # stateful stream: `(params) >> T { ... }`
            self.eat("SHIFT", ">>"); self.nl()
            self.parse_type()
            stateful = True
        else:
            self.eat("ARROW"); self.nl()
            self.parse_type()                       # return type T, ignored at runtime
            if self.at("PUNCT", "!"):               # `-> T ! E`
                self.eat("PUNCT", "!")
                self.parse_type()                   # error type E, ignored at runtime
                fallible = True
        body = self.parse_block()
        return Fn(params, body, fallible, stateful)

    def parse_atom(self):
        t = self.cur()
        if t.kind == "INT":
            self.i += 1; return Lit(int(t.val))
        if t.kind == "FLOAT":
            self.i += 1; return Lit(float(t.val))
        if t.kind == "STR" or t.kind == "CHAR":
            self.i += 1; return Lit(t.val)
        if t.kind == "ISTR":
            self.i += 1; return self.parse_interp(t.val)
        if t.kind == "NAME":
            self.i += 1; return Name(t.val)
        if self.at("PUNCT", "@"):                   # bare @ { } : an infinite loop
            self.eat("PUNCT", "@"); self.nl()
            return Iter("@", None, self.parse_block())
        if self.at("PUNCT", "{"):
            return self.parse_block()
        if self.at("PUNCT", "("):
            return self.parse_paren()
        if self.at("PUNCT", "["):
            return self.parse_list()
        raise SyntaxError(f"unexpected {t}")

    def _paren_has_arrow(self):
        # is there a top-level `=>` before this paren group closes? (keyed pattern vs struct)
        depth = 0
        j = self.i
        n = len(self.toks)
        while j < n:
            t = self.toks[j]
            if t.kind == "EOF":
                return False
            if t.kind == "PUNCT" and t.val in ("(", "[", "{"):
                depth += 1
            elif t.kind == "PUNCT" and t.val in (")", "]", "}"):
                if depth == 0:
                    return False
                depth -= 1
            elif t.kind == "FATARROW" and depth == 0:
                return True
            j += 1
        return False

    def parse_paren(self):
        self.eat("PUNCT", "("); self.nl()
        if self.at("PUNCT", ")"):
            self.eat("PUNCT", ")"); return Unit()
        if self.at("NAME"):                                # a parenthesized body-statement
            nxt = self.peek()
            if nxt.kind == "INPLACE":
                name = self.eat("NAME").val; op = self.eat("INPLACE").val[:-1]; self.nl()
                v = self.parse_expr(); self.nl(); self.eat("PUNCT", ")")
                return InPlace(name, op, v)
            if nxt.kind == "DEFINE":
                name = self.eat("NAME").val; self.eat("DEFINE"); self.nl()
                v = self.parse_expr(); self.nl(); self.eat("PUNCT", ")")
                return Bind(name, v)
            if nxt.kind == "PUNCT" and nxt.val == "=":
                name = self.eat("NAME").val; self.eat("PUNCT", "="); self.nl()
                v = self.parse_expr(); self.nl(); self.eat("PUNCT", ")")
                return Store(Name(name), v)
        if (self.at("NAME") and self.peek().kind == "PUNCT" and self.peek().val == ":"
                and not self._paren_has_arrow()):          # struct (x: 1), not a keyed pattern
            return self.parse_struct_rest()
        first = self.parse_expr(); self.nl()
        if self.at("PUNCT", ","):
            items = [first]
            while self.at("PUNCT", ","):
                self.eat("PUNCT", ","); self.nl()
                if self.at("PUNCT", ")"):
                    break
                items.append(self.parse_expr()); self.nl()
            self.eat("PUNCT", ")")
            return Tuple(items)
        self.eat("PUNCT", ")")
        return first

    def parse_struct_rest(self):
        fields = []
        while True:
            name = self.eat("NAME").val
            self.eat("PUNCT", ":"); self.nl()
            fields.append((name, self.parse_expr()))
            self.nl()
            if self.at("PUNCT", ","):
                self.eat("PUNCT", ","); self.nl()
                if self.at("PUNCT", ")"):
                    break
                continue
            break
        self.eat("PUNCT", ")")
        return StructLit(fields)

    def parse_list(self):
        self.eat("PUNCT", "["); self.nl()
        if self.at("PUNCT", "]"):
            self.eat("PUNCT", "]"); return ListLit([])
        if self.at("PUNCT", ":"):                              # [:] is the empty map
            self.eat("PUNCT", ":"); self.nl(); self.eat("PUNCT", "]")
            return MapLit([])
        first = self.parse_expr(); self.nl()
        if self.at("PUNCT", ":"):                              # ["k": v, …] is a map
            self.eat("PUNCT", ":"); self.nl()
            entries = [(first, self.parse_expr())]; self.nl()
            while self.at("PUNCT", ","):
                self.eat("PUNCT", ","); self.nl()
                if self.at("PUNCT", "]"):
                    break
                k = self.parse_expr(); self.nl()
                self.eat("PUNCT", ":"); self.nl()
                entries.append((k, self.parse_expr())); self.nl()
            self.eat("PUNCT", "]")
            return MapLit(entries)
        items = [first]
        while self.at("PUNCT", ","):
            self.eat("PUNCT", ","); self.nl()
            if self.at("PUNCT", "]"):
                break
            items.append(self.parse_expr()); self.nl()
        self.eat("PUNCT", "]")
        if len(items) == 1 and isinstance(items[0], Range):   # [1..5] is the range itself
            return items[0]
        return ListLit(items)

    def parse_interp(self, raw):
        parts = []
        buf = ""
        i = 0
        n = len(raw)
        while i < n:
            c = raw[i]
            if c == "{":
                depth = 1                            # find the matching }, allowing nesting
                j = i + 1
                while j < n and depth > 0:
                    if raw[j] == "{":
                        depth += 1
                    elif raw[j] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                if buf:
                    parts.append(("lit", buf)); buf = ""
                parts.append(("expr", Parser(lex(raw[i + 1:j])).parse_expr()))
                i = j + 1
            else:
                buf += c
                i += 1
        if buf:
            parts.append(("lit", buf))
        return Interp(parts)

    # pattern conversion -------------------------------------------------------

    def to_pattern(self, node):
        if isinstance(node, Lit):
            return LitPat(node.val)
        if isinstance(node, Unit):
            return UnitPat()
        if isinstance(node, Name):
            return WildPat() if node.id == "_" else BindPat(node.id)
        if isinstance(node, Tuple):
            return TuplePat([self.to_pattern(i) for i in node.items])
        if isinstance(node, ListLit):
            return TuplePat([self.to_pattern(i) for i in node.items])
        raise SyntaxError(f"not a pattern: {node}")


def parse(src):
    return Parser(lex(src)).parse_program()
