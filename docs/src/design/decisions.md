# Decisions

The consequential forks in Grid's control-flow design, and why the path taken beats the
roads not. The through-line: **keep the single-`()` keystone, and resolve each tension at
the layer where it actually lives** — never by adding a second nothing.

## Commit on match

The keystone says `()` is the only nothing, and control reads off presence. But every
*effectful* statement — a binding, `+=`, `>>`, `~`, a `print` — also produces `()`. So a
control construct that decided on the chosen branch's *value* could not tell "this branch
did its job and produced nothing" from "this branch didn't fire." It would misfire two ways:

```grid
// 1. an effectful matched arm looks like "no match" and falls through to later arms
1 ? { 1 => { log("a"); () }
      _ => { log("b"); 1 } }     // both arms run

// 2. effectful if-else via ?…|| runs both sides
1 ? { a += 100 } || { b += 1 }   // a and b both change — || rescues a branch that already ran
```

Grid keys commit on the **match**, not the value: a matching `=>` arm
[commits the block](../match.md#commit-on-the-match-not-the-value) even when its result is
`()`, and `?:` gives [if-else its own form](../try-branch.md#branch) so `||` reverts to a
pure value-selector. The single nothing is untouched; selection simply moved off the value.

**This is what every other language does.** Grid is the outlier *because* it folds
failure into a value — but the dispatch decision can still be made on the selection:

| Language | A clause commits on… |
|---|---|
| Icon (Grid's ancestor) | goal-directed success of the *selector*; failure is a control signal, not a value |
| Rust, Erlang/Elixir | the matching *pattern*, full stop |
| ML / Haskell | the pattern; a failing *guard* falls through, the body's value never does |
| Scheme/Lisp `cond` | the first truthy *test* |

Two alternatives were considered and rejected:

- **A second nothing** (a "skip-`()`" distinct from an "absent-`()`"). It would resolve
  everything at the value layer — and detonate the keystone: every partial operator, `#`/`@`
  collection, and stream-exhaustion would have to ask *which* nothing, re-introducing the
  `null`/`Option`/`bool` zoo the language exists to delete. Rejected — but it correctly
  *names* the tension (`()` is overloaded), which is what points the resolution at the
  dispatch site instead of the value.
- **A pattern-kind split** (literal patterns commit on match; bind/`_` patterns commit on a
  present value). It works, but it adds a category to learn and a fuzzy `_`-vs-bind edge.
  It turned out **unnecessary**: the only idiom it protected — cross-arm guard
  fall-through — is now written with [`?:` inside the arm](../try-branch.md), and find /
  reduce survive via `@` (below), so *every* pattern commits uniformly on match. Simpler,
  and the special case dissolves.

## Present-exits

In `@`, a body that yields a **present** value exits the loop with it; a body that yields
`()` continues. That single rule gives `break value`, `continue`, and `find` with no
keywords — but it is not the only rule one could pick, and the other two fail on
inspection:

- **The flip** — `()` exits, present continues — is *incoherent*. `()` is exactly what a
  continuing body produces (a binding, a `+=`, an emit all yield `()`), so every effectful
  loop would exit on its first step.
- **Body-is-not-a-signal** — `@` runs purely to source-exhaustion and discards the body — is
  *coherent but collapses the triad*. It makes `@` and `#` the same run-to-exhaustion
  iteration, erasing `@`'s first-success / find meaning, and forces every
  computed-termination loop through the generator-block form.

Present-exits is the goal-directed reading Grid is built on (typed Icon): `#` drives a body
to **all** its successes, `@` to the **first**, and reduce is the degenerate case where the
body never succeeds (it always yields `()`, so `@` runs to exhaustion threading the `&`).
One rule; the body's value is control, by design. The cost — an effectful loop body must end
in `()` — is a [visible discipline](../growth.md#exits-without-keywords), not a hidden rule.

## Why `?:` is the loosest operator

`?:` binds looser than everything else and is right-associative. The alternative — making it
tighter than the [combinators](../triad.md) `@ # >>` — would save one paren in
`(cond ? xs : ys) # f` at the cost of forbidding a bare combinator expression in a branch
slot (`cond ? xs # f : ys`). That is a bad trade: `?:` is the outermost branch *skeleton*,
and every value operator and combinator fills its slots, so they must bind tighter. Only the
feed-the-whole-if-else-into-something case needs grouping, which is the rarer one.

`||` is deliberately **not** an else. It defaults on a *result*; `?:` decides on a
*condition*. Pressing `||` into else-duty would run both sides of an effectful if-else, so
`||` is never an else — if/else is `cond ? then : default`. The full table is in
[Operators and Precedence](../ref/operators.md).

## Block-as-source

`@`'s source is driven by its **form**, not its runtime type: a literal block `{ … }` is a
re-evaluated [generator](../triad.md#thread) (the loop/while form); anything else is
evaluated once. So `{ i < n } @ { … }` loops, while `i < n @ { … }` threads the partial
`(i < n)` a single time — and `@` never inspects what its source *is*, which keeps the
compositional reading of `a < b @ c` intact.

This pairs with a deliberate choice: **blocks are sited, not first-class.** A block is
driven where it is written and never escapes — no stored or passed generators. That is what
keeps Grid [closure-free](../holes.md#sited-vs-detached): first-class blocks would be
closures in all but name, dragging back the captured environments, lifetimes, or GC that the
[substrate](../substrate.md) removes. First-class or non-escaping blocks are a deliberate
*later* question, not part of the language today.

## Still open: exhaustiveness

A dispatch where nothing matches yields `()` (a non-matching `=>` is transparent, and the
block falls to its last value). Whether to *warn* on a match with no `_` and no total cover —
Rust/ML-style exhaustiveness checking — is a separate, later decision. For now, absence is
just the one nothing, like everything else.
