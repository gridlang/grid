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
class StructLit: fields: list           # list of (name, value_node)
@dataclass
class Bind:      name: str; value: object; mutable: bool = False
@dataclass
class InPlace:   name: str; op: str; value: object
@dataclass
class Bin:       op: str; l: object; r: object
@dataclass
class Try:       subj: object; cons: object
@dataclass
class Iter:      op: str; subj: object; block: object   # op in {"#", "@"}; subj may be None
@dataclass
class Block:     items: list
@dataclass
class Match:     pat: object; res: object
@dataclass
class Fn:        params: list; body: object             # params: list of names
@dataclass
class Call:      fn: object; args: list
@dataclass
class Member:    obj: object; key: object               # str field or int index
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
        if self.at("NAME"):
            nxt = self.peek()
            if nxt.kind == "INPLACE":
                name = self.eat("NAME").val
                op = self.eat("INPLACE").val[0]
                self.nl()
                return InPlace(name, op, self.parse_expr())
            if nxt.kind == "PUNCT" and nxt.val == ":":
                name = self.eat("NAME").val
                self.eat("PUNCT", ":")
                mutable = False
                if self.at("PUNCT", "&"):
                    self.eat("PUNCT", "&")
                    mutable = True
                self.parse_type()                 # parsed for shape, ignored at runtime
                value = None
                if self.at("PUNCT", "="):
                    self.eat("PUNCT", "=")
                    self.nl()
                    value = self.parse_expr()
                return Bind(name, value, mutable)
            if nxt.kind == "PUNCT" and nxt.val == "=":
                name = self.eat("NAME").val
                self.eat("PUNCT", "=")
                self.nl()
                return Bind(name, self.parse_expr())
        e = self.parse_expr()
        if self.at("FATARROW"):
            self.eat("FATARROW")
            self.nl()
            return Match(self.to_pattern(e), self.parse_arm_result())
        return e

    def parse_arm_result(self):
        # an arm's right-hand side may be an in-place op (e.g. `=> sum += n`)
        if self.at("NAME") and self.peek().kind == "INPLACE":
            name = self.eat("NAME").val
            op = self.eat("INPLACE").val[0]
            self.nl()
            return InPlace(name, op, self.parse_expr())
        return self.parse_expr()

    def parse_type(self):
        # consume one type atom (names, [..], (..)); types are not checked at runtime
        if self.at("NAME"):
            self.i += 1
        elif self.at("PUNCT", "("):
            self.parse_paren()
        elif self.at("PUNCT", "["):
            self.parse_list()

    # expressions --------------------------------------------------------------

    def parse_expr(self):
        return self.parse_or()

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
            if self.at("PUNCT", "?"):
                self.eat("PUNCT", "?"); self.nl()
                cons = self.parse_block() if self.at("PUNCT", "{") else self.parse_comb()
                left = Try(left, cons)
            elif self.at("PUNCT", "#") or self.at("PUNCT", "@"):
                op = self.eat("PUNCT").val
                self.nl()
                left = Iter(op, left, self.parse_block())
            else:
                return left

    def parse_cmp(self):
        l = self.parse_add()
        while self.cur().kind in ("EQOP", "CMP"):
            op = self.eat(self.cur().kind).val
            self.nl()
            l = Bin(op, l, self.parse_add())
        return l

    def parse_add(self):
        l = self.parse_mul()
        while self.at("OP", "+") or self.at("OP", "-"):
            op = self.eat("OP").val; self.nl()
            l = Bin(op, l, self.parse_mul())
        return l

    def parse_mul(self):
        l = self.parse_postfix()
        while self.at("OP", "*") or self.at("OP", "/") or self.at("OP", "%"):
            op = self.eat("OP").val; self.nl()
            l = Bin(op, l, self.parse_postfix())
        return l

    def parse_postfix(self):
        node = self.parse_atom()
        if self.at("ARROW"):                       # the atom was a function's params
            return self.parse_fn_rest(node)
        while True:
            if self.at("PUNCT", "("):
                node = Call(node, self.parse_args())
            elif self.at("PUNCT", "."):
                self.eat("PUNCT", ".")
                if self.at("INT"):
                    node = Member(node, int(self.eat("INT").val))
                else:
                    name = self.eat("NAME").val
                    if self.at("PUNCT", "("):       # UFCS: x.f(a) -> f(x, a)
                        node = Call(Name(name), [node] + self.parse_args())
                    else:
                        node = Member(node, name)
            elif self.at("PUNCT", "["):
                self.eat("PUNCT", "["); self.nl()
                idx = self.parse_expr(); self.nl()
                self.eat("PUNCT", "]")
                node = Index(node, idx)
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

    def parse_fn_rest(self, params_node):
        self.eat("ARROW"); self.nl()
        self.parse_type()                           # return type, ignored at runtime
        body = self.parse_block()
        return Fn(self.extract_params(params_node), body)

    def extract_params(self, node):
        if isinstance(node, Unit):
            return []
        if isinstance(node, StructLit):
            return [n for n, _ in node.fields]
        if isinstance(node, Tuple):
            return [i.id for i in node.items]
        if isinstance(node, Name):
            return [node.id]
        raise SyntaxError(f"not a parameter list: {node}")

    def parse_atom(self):
        t = self.cur()
        if t.kind == "INT":
            self.i += 1; return Lit(int(t.val))
        if t.kind == "FLOAT":
            self.i += 1; return Lit(float(t.val))
        if t.kind == "STR":
            self.i += 1; return Lit(t.val)
        if t.kind == "NAME":
            self.i += 1; return Name(t.val)
        if self.at("PUNCT", "{"):
            return self.parse_block()
        if self.at("PUNCT", "("):
            return self.parse_paren()
        if self.at("PUNCT", "["):
            return self.parse_list()
        raise SyntaxError(f"unexpected {t}")

    def parse_paren(self):
        self.eat("PUNCT", "("); self.nl()
        if self.at("PUNCT", ")"):
            self.eat("PUNCT", ")"); return Unit()
        if self.at("NAME") and self.peek().kind == "PUNCT" and self.peek().val == ":":
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
        items = [self.parse_expr()]; self.nl()
        while self.at("PUNCT", ","):
            self.eat("PUNCT", ","); self.nl()
            if self.at("PUNCT", "]"):
                break
            items.append(self.parse_expr()); self.nl()
        self.eat("PUNCT", "]")
        return ListLit(items)

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
