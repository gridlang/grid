"""Grid parser — recursive descent producing the AST.

Covers the keystone-core subset: literals, bindings, the operator ladder
(`||` `&&`, comparison, additive, multiplicative), the `?` try, `=>` match arms,
tuples/grouping/unit, and blocks. A block is one node; whether it evaluates as a
*match* (first present arm) or a *scope* (last expression) is decided by the
evaluator from context — `?`'s block consequent is a match, a bare block is a scope.
"""
from dataclasses import dataclass
from .lexer import lex


# ─── AST ────────────────────────────────────────────────────────────────────

@dataclass
class Lit:      val: object
@dataclass
class Unit:     pass
@dataclass
class Name:     id: str
@dataclass
class Tuple:    items: list
@dataclass
class Bind:     name: str; value: object
@dataclass
class Bin:      op: str; l: object; r: object
@dataclass
class Try:      subj: object; cons: object
@dataclass
class Block:    items: list
@dataclass
class Match:    pat: object; res: object

# patterns
@dataclass
class LitPat:   val: object
@dataclass
class UnitPat:  pass
@dataclass
class BindPat:  name: str
@dataclass
class WildPat:  pass
@dataclass
class TuplePat: items: list


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

    def skip_seps(self):
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

    def _at_end(self, ek, ev):
        return self.at("EOF") or self.at(ek, ev)

    def parse_items(self, ek, ev):
        items = []
        self.skip_seps()
        while not self._at_end(ek, ev):
            before = self.i
            items.append(self.parse_item())
            if self.at("NL") or self.at("PUNCT", ";"):
                self.skip_seps()
            else:
                break
            if self.i == before:
                raise SyntaxError(f"stuck at {self.cur()}")
        return items

    def parse_item(self):
        # binding: NAME "=" expr   (but not "==", which is EQOP)
        if self.at("NAME") and self.peek().kind == "PUNCT" and self.peek().val == "=":
            name = self.eat("NAME").val
            self.eat("PUNCT", "=")
            self.skip_seps_inline()
            return Bind(name, self.parse_expr())
        e = self.parse_expr()
        if self.at("FATARROW"):
            self.eat("FATARROW")
            self.skip_seps_inline()
            return Match(self.to_pattern(e), self.parse_expr())
        return e

    def skip_seps_inline(self):
        # after `=` or `=>` the lexer already swallows the newline; this is belt-and-suspenders
        while self.at("NL"):
            self.i += 1

    # expressions (precedence ladder) -----------------------------------------

    def parse_expr(self):
        return self.parse_try()

    def parse_try(self):
        left = self.parse_or()
        if self.at("PUNCT", "?"):
            self.eat("PUNCT", "?")
            self.skip_seps_inline()
            cons = self.parse_block() if self.at("PUNCT", "{") else self.parse_try()
            return Try(left, cons)
        return left

    def _binl(self, sub, kinds):
        l = sub()
        while self.cur().kind in kinds:
            op = self.eat(self.cur().kind).val
            self.skip_seps_inline()
            l = Bin(op, l, sub())
        return l

    def parse_or(self):
        return self._binl(self.parse_and, {"OROR"})

    def parse_and(self):
        return self._binl(self.parse_cmp, {"ANDAND"})

    def parse_cmp(self):
        return self._binl(self.parse_add, {"EQOP", "CMP"})

    def parse_add(self):
        l = self.parse_mul()
        while self.at("OP", "+") or self.at("OP", "-"):
            op = self.eat("OP").val
            self.skip_seps_inline()
            l = Bin(op, l, self.parse_mul())
        return l

    def parse_mul(self):
        l = self.parse_primary()
        while self.at("OP", "*") or self.at("OP", "/") or self.at("OP", "%"):
            op = self.eat("OP").val
            self.skip_seps_inline()
            l = Bin(op, l, self.parse_primary())
        return l

    def parse_primary(self):
        t = self.cur()
        if t.kind == "INT":
            self.i += 1
            return Lit(int(t.val))
        if t.kind == "FLOAT":
            self.i += 1
            return Lit(float(t.val))
        if t.kind == "STR":
            self.i += 1
            return Lit(t.val)
        if t.kind == "NAME":
            self.i += 1
            return Name(t.val)
        if self.at("PUNCT", "{"):
            return self.parse_block()
        if self.at("PUNCT", "("):
            return self.parse_paren()
        raise SyntaxError(f"unexpected {t}")

    def parse_paren(self):
        self.eat("PUNCT", "(")
        self.skip_seps_inline()
        if self.at("PUNCT", ")"):
            self.eat("PUNCT", ")")
            return Unit()
        first = self.parse_expr()
        if self.at("PUNCT", ","):
            items = [first]
            while self.at("PUNCT", ","):
                self.eat("PUNCT", ",")
                self.skip_seps_inline()
                if self.at("PUNCT", ")"):    # trailing comma (1-tuple etc.)
                    break
                items.append(self.parse_expr())
            self.eat("PUNCT", ")")
            return Tuple(items)
        self.eat("PUNCT", ")")
        return first                          # grouping

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
        raise SyntaxError(f"not a pattern: {node}")


def parse(src):
    return Parser(lex(src)).parse_program()
