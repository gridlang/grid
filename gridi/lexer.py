"""Grid lexer — regex tokenizer with a newline-continuation heuristic.

Shape borrowed from the legacy interp/host.py; token set is the new model's
(=> the match operator, no bool, etc.). A newline is a statement separator
EXCEPT after a token that obviously continues the line (an open bracket, a
binary/assign operator, `=>`, `?`, …).
"""
import re

TOKEN_SPEC = [
    ("FLOAT",    r"\d+\.\d+(?:[eE][+-]?\d+)?"),
    ("INT",      r"\d+"),
    ("STR",      r'"(?:[^"\\]|\\.)*"'),
    ("ISTR",     r"`(?:[^`\\]|\\.)*`"),
    ("COMMENT",  r"//[^\n]*"),
    ("FATARROW", r"=>"),
    ("ARROW",    r"->"),
    ("SHIFT",    r"<<|>>"),
    ("EQOP",     r"==|!="),
    ("CMP",      r"<=|>=|<|>"),
    ("OROR",     r"\|\|"),
    ("ANDAND",   r"&&"),
    ("INPLACE",  r"\+=|-=|\*=|/="),
    ("OP",       r"[+\-*/%]"),
    ("PUNCT",    r"[()\[\]{},;:=?!~#@.&|^]"),
    ("NAME",     r"[A-Za-z_][A-Za-z0-9_]*"),
    ("NEWLINE",  r"\n"),
    ("WS",       r"[ \t\r]+"),
]
_MASTER = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC))

# A newline after any of these is swallowed (the expression continues).
_CONT = {
    "=>", "->", "==", "!=", "<=", ">=", "<", ">", "||", "&&",
    "+", "-", "*", "/", "%", "**", "(", "[", "{", ",", ":", "=", "?", "|", "&", ".",
    "+=", "-=", "*=", "/=",
}


class Tok:
    __slots__ = ("kind", "val", "line")

    def __init__(self, kind, val, line):
        self.kind = kind
        self.val = val
        self.line = line

    def __repr__(self):
        return f"Tok({self.kind}, {self.val!r}, L{self.line})"


def lex(src):
    toks = []
    line = 1
    pos = 0
    for m in _MASTER.finditer(src):
        if m.start() != pos:
            bad = src[pos:m.start()]
            raise SyntaxError(f"unexpected {bad!r} on line {line}")
        pos = m.end()
        kind = m.lastgroup
        val = m.group()
        if kind in ("WS", "COMMENT"):
            continue
        if kind == "NEWLINE":
            if toks and toks[-1].val in _CONT:
                line += 1
                continue
            if toks and toks[-1].kind != "NL":   # collapse runs of blank lines
                toks.append(Tok("NL", "\n", line))
            line += 1
            continue
        if kind == "STR" or kind == "ISTR":
            val = bytes(val[1:-1], "utf-8").decode("unicode_escape")
        toks.append(Tok(kind, val, line))
    if pos != len(src):
        raise SyntaxError(f"unexpected {src[pos:]!r} on line {line}")
    toks.append(Tok("EOF", "", line))
    return toks
