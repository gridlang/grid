# Dispatch and the overloaded `()`

*Status: resolved. Written to be read cold — no prior context assumed. **Resolution:**
problem #2 (effectful if-else) → `branch.md` (`?:`); problems #1 (effectful match
fall-through) and #3 (`?`-block scoping) → `blocks.md` (the topic + `=>`-commits model,
which **supersedes Option A** below — the pattern-kind split is no longer needed).*

## TL;DR

Grid's keystone is that `()` is the **only** "nothing": there is no `bool`, no `null`,
no `Option`. Every other value is "present" = "yes / it worked / here it is", and all
of control flow reads off that one distinction. This is beautiful and it mostly pays off.

But control-flow constructs decide **on the value's presence**, while every *effectful*
statement (a binding, `+=`, `>>`, `~`, `sys.println`) **produces `()`**. So a branch that
*did its job* yields `()` and is read as *"didn't fire"* — and control falls through and
runs **later** branches too. Effectful dispatch (tokenizers, routers, state machines) and
effectful if/else silently do the wrong thing.

The root cause is that `()` is overloaded to mean both **"no value / no match / failed
test"** and **"a branch ran and produced nothing"**. This doc lays out the problem, the
constraints any fix must respect, four options (with the one we should reject and why),
what other languages do, and a recommendation.

---

## Background: the keystone (for readers new to Grid)

- `()` is the sole nothing. A value is either **present** (anything else) or `()`.
- Every operator is **partial**: it yields a value on success or `()` on failure.
  Relations yield their **right operand** on success, so `a < b < c` chains
  (`(a<b)` → `b`, then `b<c` → `c`).
- `subject ? consequent` is the one conditional: run `consequent` iff `subject` is present.
- `=>` is match: `== + ? + bind`. A `{ pat => res ; … }` block tries arms.
- `#` fan-out collects the present results; `@` threads/reduces/loops; `||` selects the
  first present operand.
- **Continuing/effectful forms yield `()` by design** — this is load-bearing: it's what
  lets a loop body "keep going" (`@`'s body continues on `()`, exits on a present value).

That last point is the crux: `()` is *simultaneously* the universal "nothing" signal **and**
the natural output of doing work. Dispatch wants the first meaning; effects produce the second.

---

## The problem

All three reproduce on the current interpreter (`python -m gridi`); outputs are real.

### 1. A matched arm that does effects falls through to later arms

```grid
1 ? { 1 => { sys.println("a"); () }
      _ => { sys.println("b"); 1 } }
```
```
a
b      ← the _ arm ran too
1
```

The `1 =>` arm **matched** (`1 == 1`) and did its work, but its body ended in `()`. The
match evaluator (`eval_match_block`) returns the first arm whose *value* is present, so a
`()`-valued arm is treated as "no match" and it **continues to the `_` arm**. Both fire.
This is exactly the shape you want for a tokenizer ("classify the char → do the effect"),
and it silently runs multiple arms — advancing an index twice, double-emitting, etc.

The only workaround today is to end every effectful arm in a present sentinel (`… ; 1`),
which is non-obvious, easy to forget, and **collides head-on with the `@` loop rule**: an
`@` body must end in `()` to *continue*, but a match arm must end *present* to *win* — so a
loop whose body is a dispatch needs the inner arms to end present and the outer body to end
`()`, in the same block. That inversion is real cognitive load.

### 2. Effectful "if / else" via `?` … `||` runs both branches

```grid
a: &int = 0
b: &int = 0
1 ? { a += 100 } || { b += 1 }
```
```
a=100 b=1      ← the else ran too
```

`||` is "first present operand". The `then` block's value is `a += 100` → `()`. So `||`
sees `()` on the left and **runs the `else`** as well. `?` … `||` is not an if/else; it's
a present-selector, and it can't tell "the then-branch ran and produced nothing" from "the
condition was false".

### 3. (Related) A multi-statement `?`-block doesn't share scope

```grid
n >= 0 ? { x: &int = 1
           x += 9
           x }
```
```
error: unbound label: x
```

A `?`-consequent that is a `{ … }` block is routed through the **match** evaluator, which
runs *each statement in its own fresh scope* (treating them as independent arms). So a
binding in statement 1 is invisible to statement 2. The identical block as a function body
or a bare `{ }` works fine (it goes through the sequential-scope evaluator). Same syntax,
two different scopings, decided by position — and the failure is a confusing "unbound
label", not a clear error.

### Why it happens (one sentence)

`eval_match_block` returns the **first arm whose value is present**, and `Try` routes a
block consequent through it — so a matched-but-`()`-valued arm is indistinguishable from a
non-matching arm, and a multi-statement block is mistaken for a set of arms.

---

## Constraints: what any fix must preserve

These all work today and must keep working (verified on the current interpreter):

| # | Case | Result |
|---|---|---|
| R1 | value match `2 ? { 1 => "one"  2 => "two"  _ => "other" }` | `two` |
| R2 | find `[10, 20, 30] @ { (_, x) => x == 20 ? x }` | `20` |
| R3 | guard reduce `1..5 @ { (_, n) => n > 2 ? big += n }` (big starts `&0`) | `big = 12` |
| R4 | tuple arm `p = (1,2)`; `p ? { (a, b) => a + b }` | `3` |
| R5 | the `@`-body rule: a body yielding `()` **continues** the loop; a present body value **exits** it (find / break) | load-bearing |

R2/R3/R5 are the trap for any fix: the find/guard idiom is a *single bind/wildcard arm*
whose `cond ? x` body yields `()` to mean "keep looking". If a fix makes every matched arm
"commit" regardless of value, naively it would break find. The good fixes thread this needle.

---

## Options

### Option A — Dispatch on pattern-match, not value-presence

> **Superseded by `blocks.md`.** The commit-on-match idea was kept, but its *pattern-kind
> split* (literal commits / bind-wildcard falls through) proved unnecessary — `?:` absorbs
> the guard-fall-through case, so every pattern commits uniformly. Kept here as the path to
> that conclusion.

A match arm commits when its **pattern matches**, regardless of whether its value is
present. Mechanism: a non-matching arm returns a distinct `NoMatch` sentinel (not `()`);
the evaluator returns the first **non-`NoMatch`** arm, whatever its value (including `()`).

- **Fixes:** #1 (the `1 =>` arm commits on match; the `_` never runs).
- **The R2/R3 needle:** the find/guard arm is a `_`/bind pattern that *always* matches, so
  "first match wins" would commit to it and return its (possibly `()`) value — which is
  exactly what find/`@` already consume. The trap appears only with a **multi-arm
  wildcard/guard ladder** (`{ _ => g1 ? r1   _ => g2 ? r2 }`), which today relies on
  `()`-fall-through. Resolve by keying commit-vs-fall-through to **pattern kind**:
  - a **literal / structural** pattern (`"d"`, `2`, `(a, b)`) commits on match — this is
    *dispatch*, and effectful arms work;
  - a **bind / wildcard** pattern (`x`, `_`) keeps present-wins / fall-through — this is
    *filter / find / guard*.
  This split is well-motivated: a literal pattern says "I'm dispatching on a known shape"
  (commit); a bind says "I'm capturing/testing" (fall through). It fixes the tokenizer
  (literal patterns) and preserves R2/R3 (bind/`_`).
- **MODEL.md rule change:** "a match block returns the first arm whose **value** is
  present" → "returns the first arm whose **pattern matches**; for bind/wildcard arms,
  whose **value** is present" (or: structural ⇒ commit-on-match, bind ⇒ commit-on-present).
- **Risk:** the rule now depends on pattern *kind*, a subtlety users must learn. A
  multi-arm ladder of literal patterns where you *wanted* `()`-fall-through is no longer
  possible — but there's no sane reason to want that, so the cost is near-zero.
- **Verdict:** the principled, mainstream answer (see Prior Art). Recommended core.

### Option B — Two kinds of nothing (skip-`()` vs absent-`()`)

Name the disease directly: introduce a distinction between an **intentional skip / empty
result** and an **absence / failed test**, so dispatch treats "handled, produced nothing"
as commit-and-stop and "no match" as try-next.

- **Fixes:** all of them, at the value layer.
- **Cost:** it breaks the keystone monism. Every operator's partiality, `#`/`@` collecting
  non-`()`, streams' exhaustion-`()`, and `?` short-circuit all now have to answer "*which*
  nothing?". The whole identity of the language is *one* `()`; a second nothing
  metastasizes across every layer and re-introduces exactly the `null`-vs-`Option`-vs-bool
  zoo the language exists to delete.
- **Verdict:** **reject as a cure**, but keep as the *diagnosis*. B correctly identifies
  that `()` is overloaded — and that insight is what tells us to disambiguate **at the
  dispatch site** (Option A/D), not in the value domain. Right disease, wrong layer.

### Option C — Scoped fix to `?` / `||` only (leave match alone)

Two narrow, pragmatic changes:

1. **Give `?` a real two-branch if/else** (e.g. `cond ? then : else` or `cond ? {…} {…}`)
   that commits to `then` when `cond` is present, regardless of `then`'s value, and runs
   `else` only when `cond` is absent. This decouples if/else from `||`'s present-selection
   so #2 stops misfiring. (`||` stays a pure present-selector — which is all it ever was.)
2. **Make a `?`-block with no `=>` arms a sequence** (run all, yield last) — fixes #3, the
   scoping bug.

- **Fixes:** #2 and #3. **Does not fix #1** (multi-arm effectful match still falls through).
- **Verdict:** viable and cheap, but **partial** — it addresses if/else and block scope
  without touching dispatch. Best seen as a *subset* of D, not a standalone answer.

### Option D — Disambiguate the three uses of `{}`

> **Superseded by `blocks.md`.** This kept the two-kinded-block framing (a `{}` is a
> *dispatch* if it has `=>`, else a *sequence*). `blocks.md` goes further: there is only
> *one* kind of block (a sequence); `=>` is an ordinary operator that commits on match. So
> the distinction this option draws no longer exists. Kept here as the path to that.

Today a `?`/match `{ }` is overloaded across three jobs. Make the distinction **syntactic**:

- a `?`/match block **with `=>` arms** is a **dispatch** — commit on pattern-match
  (Option A's semantics);
- a `?`/match block **without `=>`** is a **sequence** — run all statements in one scope,
  yield the last (fixes #3);
- guard/filter behaviour (present-wins / fall-through) is the bind/wildcard case inside a
  dispatch (Option A's split), plus a guarded arm `pat => g ? r` may fall through when the
  guard fails.

Combined with a dedicated `?`-if/else (C-1) so `||` is never pressed into else-duty.

- **Fixes:** all three — #1 via commit-on-match, #2 via real if/else, #3 via no-`=>` =
  sequence.
- **MODEL.md rule change:** "`?`'s block consequent is a match" → "`?`'s block is a
  **sequence** unless it contains `=>` arms, in which case it is a **dispatch** (commit on
  pattern-match)". The `@` *body* stays a sequence as it is today (so R5 is untouched).
- **Risk:** one more syntactic rule to learn ("`=>` means you're dispatching"). But it's a
  *visible* rule keyed to a token the reader can see, not a runtime-type guess.
- **Verdict:** **recommended.** It's the unifying principle: A's semantics for dispatch +
  C's sequence/if-else fixes, organized under one legible rule (the presence of `=>`).

---

## Prior art

Every mainstream pattern/clause construct commits on **the selection (pattern/test)**, not
on the body's value. Grid is the outlier *because* it folded failure into a value.

| Language | How a clause commits | Side-effect-only / empty body |
|---|---|---|
| **Icon** (Grid's ancestor) | goal-directed: an expr *succeeds* (a result) or **fails** — and failure is **not a value**, it's a separate signal that drives control. `if`/`case` commit on the selection. | a body that produces nothing is fine; failure ≠ a null result. |
| **Rust** | `match` commits on the first matching pattern, full stop. | normal — `=> { do(); }` yields `()`; the value never affects dispatch. |
| **ML / Haskell** | `case` commits on pattern match; **guards** (`\| cond ->`) fall through to the next pattern only when the guard is false. | `()`/unit is an ordinary value; no conflation. |
| **Scheme/Lisp `cond`** | commits on the first **test** that is truthy; the `(test => recv)` form passes the test's value. | a body returning `nil`/`#f` does **not** fall through — commit is on the test. |
| **Erlang/Elixir `case`** | pattern + guard; commit on match. | body value irrelevant to dispatch. |

**The lesson is unanimous: dispatch on the pattern/test; the body's value (including
"nothing") must not control selection.** Icon is the sharpest mirror — Grid is "typed
Icon", but Icon kept *failure* out of the value domain, whereas Grid merged failure into
`()`. That merge is the source of this exact problem, and the fix (Option A/D) restores the
distinction *at the dispatch site* without giving up the single-`()` value model.

---

## Recommendation

**Resolved — see `blocks.md` and `branch.md`.** The converged design keeps the single-`()`
keystone and decides selection by the pattern/match rather than by the chosen branch's value
— but it does so *more simply* than Options A and D, **both of which are superseded**:

1. **One kind of block (supersedes Option D).** A block is always a single-scope
   **sequence**; there is no "dispatch block" vs "sequence block." A matching `=>` arm
   commits the block. This fixes the `?`-scoping bug (#3). [`blocks.md`]
2. **Uniform commit-on-match (supersedes Option A's pattern-kind split).** *Every* pattern —
   literal, tuple, bind, `_` — commits on match, even with a `()` result. No
   literal-vs-bind carve-out is needed: find / guard / reduce are preserved by the **`@`
   combinator** (present-exit / `()`-continue) and the **`?`-if-let topic**, not by match
   fall-through. This fixes effectful dispatch (#1). [`blocks.md`]
3. **`=>` is an ordinary operator** (usable outside `{}`), and the **topic is explicit**,
   threading as the last present value. [`blocks.md`]
4. **A dedicated `?:` if/else** (`cond ? then : else`, the loosest operator) fixes effectful
   if-else (#2); `||` reverts to a pure value-selector. [`branch.md`]
5. **Reject Option B**, but credit it: it correctly names the `()` overload, which is *why*
   the fix belongs at the dispatch site (the match / topic), not in the value system.

The one idiom Option A's split existed to protect — cross-arm guard fall-through — is instead
expressed with `?:` in-arm, so the split is unnecessary.

Net: the single-`()` keystone stays intact; selection is decided by the pattern/match, not by
whether the chosen branch produced a value — what every other language in the table does.

---

## Open questions

Most are now resolved by `blocks.md` / `branch.md`:

- **Pattern-kind split vs. always-commit** — *decided: always-commit.* Every pattern
  commits on match; no literal-vs-bind split. find / guard / reduce survive via the `@`
  combinator (present-exit / `()`-continue) and the `?`-if-let topic, not match
  fall-through. [`blocks.md`]
- **If/else surface syntax** — *decided: `cond ? then : else`* (`:` separator, no keyword;
  no real collision since `:` is bound to `?:`). [`branch.md`]
- **Guards as first-class** — *moot.* Cross-arm guard fall-through is retired; a guarded
  result is written in-arm with `?:`. [`blocks.md` §3, `branch.md`]
- **`@`-body interaction** — *resolved.* A block's value drives `@` (present = exit, `()` =
  continue — R5); the `=>`-commit rule computes that value and never overrides the
  combinator. [`blocks.md`]

Still open:

- **Exhaustiveness:** a match with no matching arm and no `_` currently yields `()`. Whether
  to add Rust/ML-style exhaustiveness warnings is a later question. [`blocks.md` §8]
