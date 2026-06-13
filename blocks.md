# Blocks, Topics, and `=>`

*Status: design resolution, converged. Resolves `dispatch.md` problems #1 (effectful
match fall-through) and #3 (`?`-block scoping), and **supersedes `dispatch.md`'s Option A**
(the literal/bind/wildcard pattern-kind split — no longer needed). Pairs with `branch.md`
(`?:`). Doc-level only; no interpreter changes yet.*

## TL;DR

Three ideas, one model:

1. **A block is never "two-kinded."** It is always one lexical scope and a sequence of
   statements. There is no separate "dispatch block" vs "sequence block."
2. **`=>` is an ordinary operator, usable anywhere.** It matches the block's *topic*
   against a pattern, binds, and on a match **commits the enclosing block** with its result
   (early-return — even if that result is `()`); on no match it yields `()` and evaluation
   continues.
3. **The topic is explicit.** Every block has an input — its *topic* — supplied by the
   `lhs op { … }` on its left, or inherited. The topic threads as **the last *present*
   value**; `()` (effects, non-matching arms) is transparent and passes it through.

From these, dispatch, sequence, find, guard, reduce, if-let, and if-else all fall out of
one rule each — no modes, no pattern-kind table.

```grid
// dispatch (effectful arms commit on match — fixes #1)
status ? {
  200 => { log("ok"); () }
  404 => { log("missing"); () }
}

// sequence, one scope (fixes #3)
n >= 0 ? { x: &int = 1; x += 9; x }     // -> 10

// find: bind always matches, commits with x-or-(); @ does the looping
xs @ { x => x == t ? x }

// if-let: ?-consequent's topic is the subject's value
m["key"] ? v => use(v)

// if-else: branch.md's ?:
cond ? { a += 1 } : { b += 1 }
```

---

## 1. The problem this resolves

`dispatch.md` found that control constructs decided on **value-presence**, while every
effectful statement yields `()`. So:

- a matched arm that does effects (`()` result) was treated as "didn't fire" and fell
  through to later arms (**#1**); and
- a multi-statement `?`-consequent was routed through the match evaluator, which ran each
  statement in its own scope, so a binding in statement 1 was invisible to statement 2
  (**#3**).

`dispatch.md`'s Option A proposed fixing #1 with a *pattern-kind split* (literal patterns
commit on match; bind/wildcard commit on present value) to avoid breaking the find/guard
idiom. That works, but it adds a category to learn and a fuzzy edge (`_` vs bind). This doc
shows the split is **unnecessary** once two things are true: `=>` commits uniformly on
match, and `branch.md`'s `?:` exists to absorb the one idiom that needed fall-through.

---

## 2. The three rules in full

### Rule 1 — A block is one scope, a sequence of statements

Evaluating a block runs its statements in order, in a single shared scope. Its **return
value** is:

- the result of the first `=>` arm that **commits** (see Rule 2), or
- if nothing commits, the **last statement's** value.

For the return value, `()` is **opaque**: a trailing `()` is a real `()` return. That is
what lets an `@` body force "continue" with a trailing `()`, exactly as today.

This alone fixes **#3**: a `?`-consequent with no `=>` is just a sequence in one scope.
`eval_match_block` (and its per-statement fresh scopes) is retired.

### Rule 2 — `=>` is the match operator; a match commits the block

`pat => result` reads the block's **topic**, matches it against `pat`, and binds. Then:

- **on a match:** it **commits** the enclosing block — the block returns `result`
  immediately, *even if `result` is `()`*, and no later statements run;
- **on no match:** it yields `()`, and evaluation continues to the next statement.

Commit is keyed on **the match**, not on whether `result` is present. That is what fixes
**#1**: an effectful matched arm (`200 => { log(); () }`) commits and wins; later arms do
not run.

`=>` is a normal operator — it does not require a `{ }` wrapper. It can be a bare
consequent, a `?:` branch, etc. (`f() ? x => g(x) : h()` is just `=>` in the then-slot).

### Rule 3 — The topic is explicit and threads as the last present value

Every block has a **topic** (its input). It is supplied by the combinator on the left
(`subject ? …`, `xs @ …`, `xs # …`), or **inherited** by a bare/nested block from the
enclosing context. Within a block it threads:

- a statement that produces a **present** value updates the topic to that value;
- a statement that produces `()` — an effect, or a non-matching `=>` arm — is
  **transparent**: it passes the current topic through unchanged.

So the topic is always "the most recent present value." This is the *combining-partials*
picture: the topic is the running result and `()` is the transparent no-op. It is exactly
why several arms compose on the same subject (each non-match passes it through), and why a
value-producing prelude can set the subject the arms dispatch on:

```grid
// non-matching arms pass the topic through; a third statement still sees it
status ? {
  200 => "ok"            // no match -> () -> topic passes through
  404 => "missing"       // sees the same status
  `unknown {status}`     // a plain statement, still the same topic
}

// a value-producing prelude becomes the topic the arms match (compute-then-dispatch)
{ parse(line)            // present result -> becomes the topic
  "GET"  => handle_get
  "POST" => handle_post }
```

**The one asymmetry, stated plainly:** `()` is *transparent to the topic* (so arms compose
on one subject) but *opaque to the block's return value* (so a trailing `()` still
continues a loop). Equivalently: **topic = the last present value; return = the last
value.** Two different jobs — what `=>` matches against vs. what the block hands back —
and this is the minimum that keeps both true at once.

---

## 3. Why no pattern-kind split is needed

Option A needed the split because the find/guard idiom relies on a bind/`_` arm that yields
`()` to mean "keep going," and "commit on match" would seem to break that. It does not —
because the *looping* is the **combinator's** job, not the match's:

```grid
find = (xs: [int], t: int) -> int | () {
  xs @ { x => x == t ? x }
}
```

`x =>` (a bind) always matches, so it **commits the body** with `x == t ? x` — i.e. `x` or
`()`. The body's value is then handed to `@`, and **`@`** does present-exit / `()`-continue
(rule R5). The "continue" in find is the loop re-pulling on a `()` body; it was never the
match falling through. Single-arm bodies commit-with-a-value; the combinator interprets it.
Reduce is identical (`(_, n) => n > 2 ? big += n` commits with `()`; `@` continues).

The only thing "commit on match" actually removes is **cross-arm guard fall-through** —
`{ x => x > 100 ? "huge"   _ => "normal" }`, where a bind arm with a failing guard used to
fall through to `_`. But `branch.md`'s `?:` absorbs that **in the arm**:

```grid
n ? { x => x > 100 ? "huge" : "normal" }              // guard with its own else
n ? { x => x > 100 ? "huge" : (x > 10 ? "med" : "small") }   // ladder = nested ?:
```

So the idiom that *motivated* the split is now expressed with `?:`, and every pattern —
literal, tuple, bind, `_` — commits uniformly on match. The `_`-vs-bind question dissolves.
`branch.md` and this doc reinforce each other.

---

## 4. The `?` / `?:` / `=>` trio

Three distinct, composable operators, each doing one job against the topic:

| Operator | Job | On the topic |
|---|---|---|
| `cond ? then` | **test** (1-outcome gate) | run `then` if `cond` present; `then` sees `cond`'s value as its topic (if-let) |
| `cond ? then : else` | **branch** (2-outcome) | run exactly one, chosen by `cond`'s presence (`branch.md`) |
| `pat => result` | **match** (commit-on-match) | match the topic's shape, bind, commit the block |

- **`?` threads its subject's value inward** — confirmed: `m["key"] ? { v => v }` yields the
  looked-up value. That is if-let, and it's why a guard "shifts" the topic to its result
  (§5).
- **`?` tests; `=>` matches shape.** A computed condition is always a `?` guard, never a
  `=>` (see §5).
- **`||` stays the pure value-selector** and is the degenerate branch `a || b ≡ a ? a : b`
  (`branch.md`).

---

## 5. Boundaries and edge cases

**`=>`'s left side is a pattern, not a test.** Patterns are literals, binds, `_`, tuples,
and `()`. A relation like `n < m` is a *test*, so it is a `?` guard, not a `=>` pattern:

```grid
n < m ? y           // correct: a test
n < m => y          // rejected: `n < m` is not a pattern
```

Keeping that line sharp is what stops `=>` from blurring into "equality on an expression's
value." `?` tests; `=>` matches shape.

**Guard-then-bind shifts the topic to the guard's result.** Because `?` threads its
subject's value inward (if-let), in:

```grid
n < m ? x => y      // x binds the value of `n < m` (= m), not n
```

`x` binds `m` (the guard's result), the same mechanism that makes `m["k"] ? v => use(v)`
bind the looked-up value. For a pure guard with no capture, write `n < m ? y`. The `x =>`
form is for when you actually want the guard's result.

**Sequence-prefix before arms.** A block may mix plain statements and arms:

```grid
status ? { setup(); 200 => x  _ => y }
```

`setup()` runs first. If it is effectful (`()`), it is transparent and the arms see the
ambient `status`. If it produces a present value, that value *becomes* the topic the arms
match (§3) — the same discipline as everywhere: mind what your statements yield.

**Topic of a bare or nested block.** A block with no combinator on its left **inherits**
the ambient topic (the last present value of the enclosing context). A new topic is
introduced only by a combinator (`subject ? …`, `xs @ …`, `xs # …`).

---

## 6. Must-still-work rubric

| # | Case | Holds because |
|---|---|---|
| R1 | value match `2 ? { 1 => "one"  2 => "two"  _ => "other" }` → `two` | `2 =>` matches, commits with `"two"` |
| R2 | find `[10,20,30] @ { (_, x) => x == 20 ? x }` → `20` | bind commits with `x`-or-`()`; `@` exits on present |
| R3 | guard reduce `1..5 @ { (_, n) => n > 2 ? big += n }` → `big = 12` | bind commits with `()`; `@` continues; effect when `n>2` |
| R4 | tuple arm `p=(1,2)`; `p ? { (a,b) => a+b }` → `3` | `(a,b)` matches, commits with `a+b` |
| R5 | `@`-body: `()` continues, present exits | block return is `()`-opaque; `@` reads it |

---

## 7. Implementation consequences (for the eventual MODEL.md merge + TDD)

Doc-level today; when adopted, the work is:

1. **Lift `=>` into the expression grammar.** Today it is parsed only at statement level
   (an expression followed by `=>` becomes a `Match`), so a bare `5 ? x => x` is a parse
   error. `=>` must become an operator that slots **just under `?:`** (so
   `f() ? x => g(x) : h()` frames as then = `x => g(x)`, else = `h()`, and `x => a || b` is
   `x => (a || b)`). Its left side parses as a pattern; its right side as a full expression.
2. **Retire `eval_match_block`.** One evaluator for all blocks: run statements in one scope,
   commit on a matching `=>`, else return the last statement's value.
3. **Thread the topic as the last present value**, `()`-transparent; a matching `=>` commits.
   `?`-consequents already pass the subject's value inward (keep that — it's if-let).
4. **Precedence (firm points):** `?:` loosest, right-associative (`branch.md`); `=>` just
   under `?:`; `||`/`&&`/comparison/arithmetic tighter. The relative order of `?:`/`=>` vs
   the combinators `@ # >>` stays academic (matches and branches almost always live inside
   braced bodies) — settle it only if a concrete top-level case demands it.
5. **Rewrites:** none forced by this doc beyond what `branch.md` already implies; the find/
   guard/reduce examples are unchanged. (Cross-arm guard ladders, if any exist, move to
   in-arm `?:`.)

---

## 8. Deferred / open

- **Exhaustiveness.** A dispatch where nothing matches returns `()` (a non-matching `=>`
  is transparent, and the block falls to its last value or `()`). Whether to warn on a
  match with no `_` and no total cover is a separate, later question.
- **Bare top-level `=>`.** `=>` reads the ambient topic, which at top level is `()`. Legal
  but rarely meaningful; no special handling needed.
- **`?:` ↔ combinator precedence.** As above, deferred until a concrete need appears.
