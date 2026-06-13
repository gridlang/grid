# Grid — The Model

> Built from the seed up, one layer at a time. This is the foundation the rest of the
> language derives from; we add a layer only once the one beneath it holds. It
> supersedes the older `design.md` (which crystallized a later, drifted syntax rather
> than the core model).
>
> 1. **The Substrate** — ownership = scope = purity  ← *you are here*
> 2. The Triad — `?` `#` `@` as the three ways scopes compose
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

*Next — Layer 2: the triad `?` `#` `@`, as the three ways scopes compose — branch,
fan-out, thread. Reduce and parallel-map live here, and they fall out of this
substrate rather than being bolted onto it.*
