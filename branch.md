# Branching and the `?:` Operator

*Status: design proposal, converged. Companion to `dispatch.md`. Closes `dispatch.md`
problem #2 (effectful if-else); problems #1 (effectful match fall-through) and #3 (`?`-block
scoping) are separate threads.*

## TL;DR

Grid lacks a way to express **mutually-exclusive effectful branching**: "if condition then
A else B, exactly one of which runs." `||` can't do it, because `||` defaults on the
*result* of the left side, not on the *condition* that chose it — and effectful branches
produce `()`, so `||` "rescues" a branch that already ran.

Add one construct:

```grid
cond ? then : else
```

- `then` runs iff `cond` is present; `else` runs iff `cond` is `()`. The choice is made
  **once, on `cond`** — `else` is skipped when `cond` is present, even if `then` yields `()`.
- Both branches are full expression slots (block, literal, call, combinator chain, …).
- **`?:` is the loosest operator, right-associative.** Every value operator (`||`, `&&`,
  comparison, arithmetic) and every combinator (`@ # >>`) binds tighter, so all three
  slots accept full expressions without parens.
- `||` keeps its single job — **first-present value selector** — and is **not** an else.
  The old `cond ? then || default` idiom is retired (it was a workaround for the missing
  else; see §4).

This is designed from the best vision, not for backward compatibility: existing
`? … ||`-as-else code changes meaning under this precedence and should be rewritten as
`? … : …`. That is intentional.

---

## 1. The branch family

`?:` is not an imported C ternary bolted on — it is the missing member of a family that
present-vs-`()` already implies:

| Form | Arity | Meaning |
|---|---|---|
| `cond ? then` | 1-outcome **gate** | run `then` if `cond` present, else `()` |
| `cond ? then : else` | 2-outcome **branch** | run exactly one, chosen by `cond`'s presence |
| `topic ? { pat => … }` | n-outcome **dispatch** | match (only reachable when `topic` present) |

And `||` is the **degenerate branch where the test is the payload**:

```grid
a || b   ≡   a ? a : b      // (single-eval: a is evaluated once)
```

This is why the family factors cleanly and why the precedence (§3) *falls out*
structurally rather than being chosen: `?:` is the branch skeleton; `||`, `&&`, and the
rest are ordinary value-expressions that fill its slots, so they must bind tighter.

---

## 2. The gap it fills

Grid's control flow is built on **present vs `()`**. The value-level operators are
selectors, not booleans:

| Operator | Meaning | Short-circuit |
|---|---|---|
| `a ? b` | if `a` present, yield `b`; else `()` | yes |
| `a && b` | if `a` present, yield `b`; else `()` | yes |
| `a \|\| b` | if `a` present, yield `a`; else yield `b` | yes |

These choose *values*, and most code needs nothing more:

```grid
config_file || env_config || default_config     // first present source
1 < 2 < 3                                        // chained comparison
```

The gap appears when the branch you take is **effectful** and therefore yields `()`:

```grid
a: &int = 0
b: &int = 0
1 ? { a += 100 } || { b += 1 }
```
```
a=100 b=1        ← both branches ran
```

`1 ? { a += 100 }` does the effect and yields `()`; `||` sees `()` and "helpfully" runs the
right side too. `||` cannot tell "the condition was absent" from "the then-branch ran and
produced nothing." Grid has no `bool` and no `is-this-()` test, so you cannot build if-else
from `?` + negation. The gap is real: the language cannot directly say "do A or B, not both."

---

## 3. Proposal: `cond ? then : else`

### Semantics

1. Evaluate `cond`.
2. If `cond` is **present**: evaluate `then`, yield its value. `else` is not evaluated.
3. If `cond` is **`()`**: evaluate `else`, yield its value. `then` is not evaluated.

The decision is on `cond` alone — `else` is skipped when `cond` is present even if `then`
evaluates to `()`. That is the whole point.

```grid
// effectful if-else: exactly one runs
1 ? { a += 100 } : { b += 1 }

// value if-else
n % 2 == 0 ? n / 2 : `{n} is odd`!

// mixed
m["key"] ? { use(it) } : { log("missing"); () }
```

### Why this is not `||`

`?:` branches on the **condition**; `||` defaults on the **result**:

| Expression | cond present, then=`100` | cond present, then=`()` | cond=`()` |
|---|---|---|---|
| `cond ? then : else` | `100` | `()` (else skipped) | else |
| `cond ? then \|\| else` | `100` | else (**wrong** for if-else) | `()` |

### Precedence: `?:` is the loosest operator, right-associative

One rule: **`?:` binds looser than everything else (value operators *and* combinators),
and is right-associative.** All three slots therefore accept full expressions without
parens:

```grid
a || b ? c : d        →  (a || b) ? c : d        // condition is a presence-chain
cond ? xs # f : ys    →  cond ? (xs # f) : ys     // then is a combinator expression
cond ? a : b || c     →  cond ? a : (b || c)      // else is a presence-chain
a ? b : c ? d : e     →  a ? b : (c ? d : e)      // right-assoc: an elif chain
n % 2 == 0 ? n / 2 : `{n} is odd`!
                      →  (n % 2 == 0) ? (n / 2) : (`{n} is odd`!)
```

The cost is symmetric and visible: when you want the **result** of an if-else to feed a
tighter operator, you parenthesize:

```grid
(cond ? xs : ys) # f
(cond ? src1 : src2) @ { x => x * 2 }
(cond ? a : b) || default                 // default the whole if-else
```

This is the correct cost distribution: `?:` is the outermost branch skeleton, everything
else fills its slots, and only the fan-out-of-result case needs grouping. Making `?:`
tighter than `@ # >>` would remove that one paren at the cost of forbidding bare combinator
expressions in the then/else slots — a bad trade.

Note `cond ? xs : ys # f` parses as `cond ? xs : (ys # f)` ("if cond, xs; else fan-out ys"),
asymmetric with `(cond ? xs : ys) # f` but fully predictable from the one rule.

`=>` is an ordinary operator (see `blocks.md`), sitting **just under `?:`**: its pattern
binds on the left and its result extends right as a full expression, stopping at an
enclosing `?:`'s `:`. So `200 => x ? a : b` is `200 => (x ? a : b)`, and in
`f() ? x => g(x) : h()` the then-branch is `x => g(x)` while the `:` is the branch's else.

---

## 4. `||` reverts to a pure value-selector

Once `?:` exists, `||` has exactly one job: **yield the first present value in a chain.**
The `cond ? then || default` idiom — `||` standing in for an else — was only ever a
workaround for the missing else. It is a category error: a result-selector faking a
conditional. It is retired.

```grid
// retired (was "else" via ||)
n % 2 == 0 ? n / 2 || `{n} is odd`!

// best vision
n % 2 == 0 ? n / 2 : `{n} is odd`!

// || stays, for value-defaulting only
config || default_config
input  || fallback
```

This is a deliberate, non-additive change: under the §3 precedence, any surviving
`cond ? then || default` reparses as `cond ? (then || default)` and changes meaning. Such
sites are rewritten to `?:`; we are designing the language we want, not preserving the
idiom.

### Polarity control (a small bonus)

Because `?:` chooses on the condition, it can also flip the presence signal — a poor-man's
`not` with an explicit marker, no `bool` required:

```grid
a || default        // preserves polarity: a if present, else default
a ? () : default     // inverts: () if present, else default
a ? marker : ()      // present -> marker, absent -> ()
```

---

## 5. `:` does not generalize beyond `?`

Tempting question: should `: default` mean "else / default on `()`" after `@`, `#`, `>>`,
or as a bare infix? No — and the reason is structural, not cautious:

**Only `?` separates a *test* from a *payload*.** The left operand of `?:` is the
condition, not the value you want. That is not true elsewhere:

- `a @ b` / `a # b` — the left side is the **source**, not a test.
- `a || b` — the left side is the **value** you want if present.

So a bare infix `a : b` would either duplicate `||` (redundant) or mean something subtly
different from `a || b` (confusing). `:` stays bound to `?` as the `?:` pair.

The one form that reads well is find-with-fallback after `@`:

```grid
xs @ { x => x > 10 ? x } : -1        // = (xs @ { … }) || -1
```

But that is **pure sugar** for `|| -1`, and adding sugar later is free — so defer it until
it earns its place.

(`:` is otherwise used in `(x: 1)` structs, `["k": v]` maps, `x: int` annotations, and `[:]`
the empty map. None collide: those colons are bracketed or positional, and `:` here is
bound to `?:`, never a free infix — so `cond ? (x: 1) : (y: 2)` parses cleanly.)

---

## 6. Interaction with match (see `blocks.md`)

Per `blocks.md`, a block is always one single-scope **sequence** — there is no "dispatch
block" vs "sequence block." `=>` is an ordinary operator within it that commits the block on
a pattern-match. `?:` composes cleanly on top: the condition supplies the topic, and any
`=>` arms inside a branch match and commit against it. A `:` after the branch is the else:

```grid
// then-branch with no => — a plain sequence
n >= 0 ? { setup(); compute(n) } : { log("negative"); () }

// then-branch with => arms — each commits on match
status ? {
  200 => "ok"
  404 => "missing"
} : "no status"
```

**The `: else` catches topic-*absence*, not topic-*non-match*.** In the dispatch example,
`: "no status"` fires only when `status` is `()`. A present-but-unmatched topic (e.g. `500`)
is *not* caught by `:` — it falls through the dispatch to `()`. To catch it, add a `_ =>`
arm:

```grid
status ? {
  200 => "ok"
  404 => "missing"
  _   => `other {status}`     // present-but-unmatched
} : "no status"               // absent
```

That is a feature: topic-absence and topic-non-match are different events, and the syntax
lets you handle each explicitly. (Effectful dispatch arms commit on match per `blocks.md`;
`?:` does not address that.)

---

## 7. Recommendations

1. **Adopt `cond ? then : else`** as the if-then-else form — mutual-exclusion branching
   with no `bool`, `null`, or negation operator.
2. **`?:` is the loosest operator, right-associative.** One rule; all slots take full
   expressions; parenthesize only to feed an if-else *result* into a tighter operator.
3. **`:` is the separator** — no `else` keyword. Grid is symbol-driven (two keywords
   total), `? :` is universally read, and there is no real `:` collision.
4. **`||` becomes a pure value-selector.** Retire `cond ? then || default`-as-else; rewrite
   such sites to `?:`.
5. **Do not generalize `:` beyond `?`.** Only `?` separates test from payload; the `@`
   find-with-fallback is deferrable sugar for `|| default`.

---

## 8. Open questions

1. **Migration sweep.** Rewriting every `? … ||`-as-else to `? … :` across `MODEL.md` and
   the examples is mechanical but worth doing in one pass so nothing silently reparses.
2. **Precedence vs postfix `!`.** In `cond ? a : error!`, `!` binds to `error` inside the
   else. Expected to be fine (postfix is tightest); needs a test case.
3. **Exhaustiveness.** Orthogonal to `?:`, but related: should a dispatch with no matching
   arm and no `_` warn, or stay `()` (current)? A separate decision.
