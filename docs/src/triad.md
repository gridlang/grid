# The Triad: `?` `#` `@`

> **Layer 2 of the model.** With the substrate in place, this is how blocks *compose*.

Three combinators, three ways a block composes over an input: **`?` branches, `#` fans
out, `@` threads.** They share one shape —

```grid
input OP { pattern => result }
```

— where `{ … }` is a [holed block](holes.md) and the arms `pattern => result` match the
input. They differ only in how many blocks run and how those blocks relate. (*How* an arm
matches — the `=>` operator, the topic, binding — is [Present and Nothing](match.md); here
we fix what each operator does and what it yields.)

## The step value

When a combinator runs a block per element, the block's input — its **topic** — is the
element paired with its position:

| source | topic per step |
|---|---|
| list | `(index, element)` |
| map | `(key, value)` |
| string | `(index, char)` |
| stream | the emitted value |

You destructure it in the arm: `# { (i, x) => … }`. A single binding captures the *whole*
pair — `# { x => x }` over `[10, 20]` yields `[(0, 10), (1, 20)]` — so the idiom for
"ignore the index" is `(_, x)`.

## Branch

`?` runs a block against the input; a matching `=>` arm **commits** it — the first arm that
matches wins, yielding its result; if nothing matches, `()`.

```grid
x ? {
  0 => "zero"
  _ => "some"
}
```

This is `switch` and guard-matching. The simple one-armed form `cond ? result` is the
plain conditional, and `cond ? then : else` is the two-outcome branch — both are
[Try and Branch](try-branch.md). `?` is the degenerate member of the triad: zero or one
block runs — *choose* one rather than repeat one.

## Fan-out

`#` runs **one independent block per element** of the input and collects the results into a
list. A block that yields `()` contributes nothing — so the *same* operator filters (an
arm yields `()` to drop its element):

```grid
doubled = nums # { (_, n) => n * 2 }          // map  -> [2, 4, 6, …]
evens   = nums # { (_, n) => n % 2 == 0 ? n } // filter -> only the evens
```

Each block is its own scope. By [the capture rule](holes.md#one-rule-for-capture) it may
*read* (share) the surrounding scope but cannot *write* it — a write is a move, and one
handle cannot move into every parallel block — so the blocks are independent and **`#` runs
them in parallel, safely, with no annotation.** A `#` whose arms also `#` builds nested
results (a table); see the [tour](examples/tour.md).

## Thread

`@` runs **one block, in sequence, threaded over the input**, carrying state from step to
step. The state is nothing special: it is the captured `&` the block writes
([Layer 1](holes.md#writes-move-so-parallelism-is-free)), moved in and back across the run.

```grid
sum: &int = 0
nums @ { (_, n) => sum += n }     // reduce — sum threads through; afterward it is the total
```

What you thread over decides the shape, and **how the source is driven is read from its
form** — a literal block is re-run, anything else is run once:

- an **expression source** → evaluated once. A collection iterates element by element
  (**reduce** / **find**); a single value threads through the block one time (partials:
  `a < b` yields `b`, so `a < b @ blk` runs `blk` once on `b`); `()` threads nothing.
- a **literal block source** `{ … }` → a **generator**: re-evaluated on each pull, looping
  while it yields present and stopping when it yields `()`. This is the **loop / while**
  form.

```grid
i: &int = 0
{ i < 4 } @ { i += 1 }      // loop — the block re-tests i < 4 each pull; afterward i is 4
```

Nothing inspects the source's runtime *type*, only its *form*, so a generator whose pulled
value is itself a string — `{ line != "" }` yields the string `""` — still loops; the block
form, not the value, decides. (This is a deliberate choice; the alternatives are weighed
in [Design Notes](design/decisions.md#block-as-source).)

Reduce and loop are not two constructs; they are `@` handed two kinds of input. Because `@`
is sequential, its block *may* write a captured `&` — which is precisely why the
accumulator needs no syntax of its own.

And the third use of `@` is **find**: because an `@` body that yields a *present* value
exits the loop with it (and a `()` body continues), threading a body that succeeds at most
once gives you first-match search:

```grid
1..100 @ { (_, n) => n * n > 40 ? n }     // 7 — the first n whose square exceeds 40
```

This present-exits rule is the goal-directed heart of `@`; it is developed fully under
[Match and Commit](match.md) and [From the Seed](growth.md#exits-without-keywords), and the
roads not taken are in [Design Notes](design/decisions.md#present-exits).

## Why the three are one family

`#` and `@` are the *same* iteration over the *same* kind of block. The only difference is
**independent vs threaded** — and that is not a new axis; it is Layer 1's
[read-share](holes.md#writes-move-so-parallelism-is-free) (safe in parallel) versus
write-move (must run in sequence). The substrate already drew the line; the triad just
names both sides of it.

A **generator** source — re-evaluated, stateful, order-dependent — is therefore `@`-only;
`#` takes a materialized source it can fan out in parallel. `?` is the degenerate case:
zero-or-one blocks — choose one rather than repeat one.

This is the property worth keeping: behavior comes from *what you hand the operator* — a
value source or a generator block, an arm that yields a value or `()`, a block that reads
or writes — never from flags or modes. Same combinators, composed.

## What each yields

| operator | runs | yields |
|---|---|---|
| `?` | the block (a matching `=>` arm commits) | the committed arm's result, the block's last value, or `()` if the subject is absent |
| `#` | one block per element, in parallel | the list of non-`()` results |
| `@` | one block per step, threaded | its last block's value; accumulated state read from the moved-back `&` |

The arms above all turn on one question — did the block produce a value, or `()`? That
question is the keystone, and it is [the next chapter](present.md).
