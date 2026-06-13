# Operators and Precedence

The authoritative binding order. Every operator yields **a value or `()`**
([Layer 3](../present.md)) — there is no separate boolean result.

## Precedence

Tightest to loosest. Operators on the same row share a level and associate left-to-right,
except `?:` (right-associative).

| | Operators | Role |
|---|---|---|
| 1 | `.`  `[]`  `()`  postfix `!` | member · index · call · [raise/propagate](../growth.md#fallibles) |
| 2 | prefix `-` | unary minus (`-x` ≡ `0 - x`) |
| 3 | `*`  `/`  `%` | multiply · divide · modulo |
| 4 | `+`  `-` | add · subtract (`+` also concatenates `str`) |
| 5 | `&`  `\|`  `^`  `<<`  `>>` | bitwise, on `int` |
| 6 | `..` | inclusive range |
| 7 | `==`  `!=`  `<`  `<=`  `>`  `>=` | comparison — yields the **right operand** on success |
| 8 | `#`  `@` | [fan-out · thread](../triad.md) (a `{block}` binds to the combinator on its left) |
| 9 | `&&` | selector — `b` if `a` present, else `()` |
| 10 | `\|\|` | selector — first present operand |
| 11 | `=>` | [match and commit](../match.md) |
| 12 | `?:` | [branch](../try-branch.md) — **loosest, right-associative** |

Two loose **prefixes** sit at the statement edge and take the whole following expression:
`~expr` ([defer](../growth.md#defer)) and `>>expr` ([emit](../growth.md#streams)).

Worked consequences of the table:

```grid
a || b ? c : d        →  (a || b) ? c : d
cond ? xs # f : ys    →  cond ? (xs # f) : ys
a ? b : c ? d : e     →  a ? b : (c ? d : e)        // right-assoc elif ladder
1 < 2 < 3             →  (1 < 2) < 3                // -> 3, comparisons chain
err ? handle : 0      →  the if-else; || is never an else
f() ? x => g(x) : h() →  then = (x => g(x)), else = h()
```

## Value operators

- **Arithmetic** `+ - * / %` on `int` / `num` — both operands the same type, no coercion.
  Division by zero is `()`, like any [partial operator](../present.md#every-operator-is-partial).
- **String** `+` concatenates two `str`.
- **Comparison** `== != < <= > >=` — a relation yields its **right operand** on success and
  `()` on failure, so `a < b < c` and `x == y == z` chain by ordinary composition. `!=`
  yields the right operand when the two differ, `()` when they are equal.
- **Selectors** `&& ||` choose a value and short-circuit: `a && b` is `b` if `a` is present
  else `()`; `a || b` is the first present operand. `||` is a value-default, **never** an
  else — that is [`?:`](../try-branch.md#a-pure-value-selector). Note `a || b ≡ a ? a : b`.
- **Bitwise** `& | ^ << >>` operate on integers.

## Control operators

- **`?`** — [try](../try-branch.md#try): `cond ? then` runs `then` (with `cond`'s value as
  the topic) iff `cond` is present.
- **`?:`** — [branch](../try-branch.md#branch): `cond ? then : else` runs exactly one side,
  chosen on `cond`'s presence. Loosest, right-associative.
- **`=>`** — [match and commit](../match.md): `pat => result` matches the block's topic,
  binds, and on a match commits the enclosing block (even with a `()` result).
- **`#` / `@`** — [the triad](../triad.md): fan-out (parallel, collects non-`()`) and thread
  (sequential, reduce/loop/find).

## Postfix and prefix

- **`!`** (postfix) — `f()!` unwraps a fallible or propagates its error; `e!` raises `e` as
  the error. → [Fallibles](../growth.md#fallibles)
- **`-`** (prefix) — unary minus.
- **`~`** (prefix) — [defer](../growth.md#defer) to scope exit (LIFO).
- **`>>`** (prefix) — [emit](../growth.md#streams) a stream value.
- **`.` `[]` `()`** — member access (`p.x`, `p.0`), index (`xs[i]`, `m["k"]` — partial), and
  call. `x.f(a)` is `f(x, a)` ([UFCS](../growth.md#functions)).

## Positional (overloaded) symbols

A few symbols mean different things by **position**, never by guesswork:

| Symbol | prefix | infix (value) | infix (type) | after params / between ints |
|---|---|---|---|---|
| `&` | `&T` mutable handle | — | `A & B` intersection / bitwise-and | — |
| `\|` | — | — | `A \| B` union / bitwise-or | — |
| `>>` | emit a stream value | — | — | `() >> T` defines a stream · `i >> j` right-shift |
| `:` | — | — | `name: T` annotation · `k: v` keyed | — |

The position fixes the reading, so the same character never needs a type to disambiguate.
