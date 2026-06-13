# Grid — The Model

> Built from the seed up, one layer at a time. This is the foundation the rest of the
> language derives from; we add a layer only once the one beneath it holds. It
> supersedes the older `design.md` (which crystallized a later, drifted syntax rather
> than the core model).
>
> 1. The Substrate — ownership = scope = purity  *(done)*
> 2. **The Triad** — `?` `#` `@` as the three ways scopes compose  ← *you are here*
> 3. Default-truthiness — one idea unifying flow, conditionals, typing, coercion
> 4. Literals & types — one symbol, one type
> 5. The grafts — defer, fallibles, streams

---

## 1. The Seed

Grid treats function purity not as a discipline you follow but as a fact that falls
out of a single decision: **a scope and an ownership boundary are the same thing.**

Most languages answer "what can this code reach?" (scope) and "who owns this data?"
(memory) with two separate systems. Grid answers them with one. A scope is the region
where a piece of data lives *and* the only region that can reach it. Purity is then
not a property you prove — it is the shape of the language.

Everything below is a consequence of taking that seriously.

## 2. Handles, not buckets

A label is a **handle** to data, not a bucket that contains it.

```
a = 1
```

`a` does not *hold* a `1`; it *points at* one. This is the Algol bucket turned inside
out, and it is what lets ownership and scope be one idea: you reason about who can
reach the data, never about where a value got copied to.

(An implementation is free to keep a small `int` in a register and a large structure
on the heap. That is an optimization. The model is always: a handle to data.)

## 3. The immutability hinge

The hard part of "handles to shared data" is mutation. If two handles point at one
thing and either can change it, you are back to aliasing, races, and the machinery —
borrow checkers, lifetimes — built to police them. Grid sidesteps the machinery with
a split it wants anyway: **immutable by default.**

**Immutable data is freely shared.** Because it cannot change, the difference between
"two handles to one value" and "two copies of one value" is *unobservable*. So
immutable handles are shared at will — at no cost, with nothing to track. For the
immutable majority of a program, everything is a pointer, and it is safe precisely
because nothing can write through it.

```
a = 1
b = a        // b and a are handles to the same 1 — indistinguishable from a copy
```

**Mutable data has exactly one handle.** A mutable value is marked with `&`, a symbol
chosen to *look like a handle gripping its data*. A `&` value is owned by one label at
a time. You cannot make a second handle to it; to get one you take your own owned copy.

```
c: &int = 1   // c is the single attached handle to a mutable 1
c += 1         // c now points at 2 — mutated in place, through the one handle
d: &int = c   // d is a NEW owned copy; c is untouched
```

> `&` is iconic, like the rest of Grid's symbols (`#` a grid, `@` a loop, `?` a fork):
> a little handle attached to the value, marking the one place a value may change.

The aliasing problem therefore never arises: shared things can't be written, written
things can't be shared.

## 4. Every scope is a holed block

There is one kind of scope: a **block** — a body together with its **holes**, the
handles that cross in from outside. A function is a block; the body of a `?`, `#`, or
`@` is a block; a bare `{ ... }` is a block. They differ only in *how they compose*
(next layer), never in how data enters them.

A block's holes are **inferred**, by a single rule applied everywhere — so you never
write a capture list, yet you can read any block and know exactly what crosses it,
because there is only ever one rule to run:

> For each name a block uses from outside itself —
> **read it** and the hole is a **share**: a free, read-only view;
> **write it** and the hole is a **move**: the handle moves in and moves back, and
> writing requires the name be `&`.

Reads share, writes move. That is the whole rule, identical for functions, `?`, `#`,
`@`, and bare blocks — so inference is never guesswork: there is no second case, no
context in which the same block would capture differently. Inferred *and* directly
knowable, because the rule is singular.

```
n = 4                // immutable
i: &int = 0          // mutable — the attached handle

@ i < n { i += 1 }    // i is written -> moved in/back;  n is read -> shared
                      // afterward i is 4 — the move brought it back
```

**Sited vs detached.** A `?`/`#`/`@` body or a bare block is *sited*: it sits
lexically inside an enclosing scope, so its holes are inferred from that scope. A
**function is detached**: named here and called elsewhere, with no enclosing locals at
its call sites — so it has nothing to infer from, and its inputs are its declared
parameters (its only ambient access is module constants, which are immutable, hence
shared). That is the entire function-vs-block difference: the same capture rule, but a
function has nothing to infer *from*.

```
push = (s: &Stack, v: int) -> () { s.data += v }

s: &Stack
s.push(10)           // s moves into push, is mutated, and moves back changed
```

(Grid has no closures — a function never captures enclosing locals. The job closures
usually do, carrying state between calls, is the stateful function's instead; layer 5.)

**Writes move, so parallelism is free.** A written hole is a *move*, and `#` opens many
blocks at once — one mutable cannot move into many — so a `#` body cannot write an
enclosing handle; it can only read (share) what is outside it, and independent reads
never race. `#` is parallel-safe by construction, and the racy program does not
compile. `@` opens one block at a time, so it *can* move a `&` accumulator in and
thread it through: that is reduce. Neither combinator carries a "parallel" or
"sequential" flag — it falls out of move meeting fan-out.

```
swap = (a: &int, b: &int) -> () { ... }
x: &int = 1
swap(x, x)           // error — x moves into a and is gone; it cannot also move into b
```

That last line is not a rule a checker enforces; it is simply impossible — a moved
handle is not there to be moved again.

## 5. What falls out

From "a scope is an ownership boundary," with the immutability hinge and move-in /
move-back, these are free — not features, but consequences:

- **Exclusivity without a checker.** A mutable value is reachable through one handle,
  ever. No borrows to track, no lifetimes to annotate, no checker to satisfy. The
  guarantee is structural.
- **Lifetime is scope.** Data lives exactly as long as the scope that owns it and is
  released when that scope ends. Nothing to garbage-collect, nothing to
  reference-count — the owning scope's exit *is* the free.
- **Purity by construction.** A scope can affect only what it was handed; the only way
  a call can change its caller's world is a `&` parameter, so effects are visible right
  in the signature.
- **Parallel-safe by construction.** Independent scopes that share immutable data and
  own disjoint mutable data cannot race — there is no shared writable state to race
  over. This is the property that lets one of the three combinators fan out across
  cores for free.

---

## Layer 2 — The Triad

Three combinators, three ways a block composes over an input: **`?` branches, `#` fans
out, `@` threads.** They share one shape —

```
input OP { pattern => result }
```

— where `{ … }` is a holed block (Layer 1) and the arms `pattern => result` match the
input. They differ only in how many blocks run and how those blocks relate. (*How* an
arm matches is Layer 3; here we fix what each operator does and what it yields.)

### `?` — branch

`?` matches the input and runs **one** block — the first arm that matches — yielding
that arm's result; if nothing matches, `()`.

```
x ? {
  0 => "zero"
  _ => "some"
}
```

`if`/`else`, `switch`, and guard-matching in one operator: one input, one chosen
block, one result.

### `#` — fan-out

`#` runs **one independent block per element** of the input and collects the results
into a list. A block that yields `()` contributes nothing — so the same operator
filters (an arm yields `()` to drop its element; *how* it decides is Layer 3).

```
doubled = nums # { n => n * 2 }     // map -> [2, 4, 6, …]
```

Each block is its own scope. By Layer 1 it may *read* (share) the surrounding scope but
cannot *write* it — a write is a move, and one handle cannot move into every parallel
block — so the blocks are independent and `#` runs them in parallel, safely, with no
annotation.

### `@` — thread

`@` runs **one block, in sequence, threaded over the input**, carrying state from step
to step. The state is nothing special: it is the captured `&` the block writes (Layer
1), moved in and back across the run.

```
sum: &int = 0
nums @ { n => sum += n }     // reduce — sum threads through; afterward it is the total
```

What you thread over decides the shape:

- a **collection** → the block runs once per element — **reduce**;
- a **condition** → the input is re-checked each step and the block runs while it holds
  — **loop**.

```
i: &int = 0
i < 4 @ { i += 1 }          // loop — runs while i < 4; afterward i is 4
```

Reduce and loop are not two constructs; they are `@` handed two kinds of input. Because
`@` is sequential, its block *may* write a captured `&` — which is precisely why the
accumulator needs no syntax of its own. (The bare infinite form `@ { … }` and
early-exit-with-a-value are Layer 3 — they need the truthiness machinery.)

### Why the three are one family

`#` and `@` are the *same* iteration over the *same* kind of block. The only difference
is **independent vs threaded** — and that is not a new axis; it is Layer 1's
**read-share** (safe in parallel) versus **write-move** (must run in sequence). The
substrate already drew the line; the triad just names both sides of it. `?` is the
degenerate case: zero-or-one blocks — choose one rather than repeat one.

This is the property worth keeping: behavior comes from *what you hand the operator* — a
collection or a condition, an arm that yields a value or `()`, a block that reads or
writes — never from flags or modes. Same combinators, composed.

### What each yields

| operator | runs | yields |
|---|---|---|
| `?` | one block (the matching arm) | that arm's result, or `()` |
| `#` | one block per element, in parallel | the list of non-`()` results |
| `@` | one block per step, threaded | its last block's value; accumulated state read from the moved-back `&` |

---

*Next — Layer 3: default-truthiness. One idea — a value is falsy when it equals its
type's default — driving all of this at once: how arms match, why `()` filters in `#`,
when `@` stops, and the typing / conditional / coercion questions, in a single step.*
