# Holes

There is one kind of scope in Grid: a **block** — a body together with its **holes**, the
handles that cross in from outside. A function is a block; the body of a `?`, `#`, or `@`
is a block; a bare `{ … }` is a block. They differ only in *how they compose* (that is
[the triad](triad.md)), never in how data enters them.

## One rule for capture

A block's holes are **inferred**, by a single rule applied everywhere — so you never write
a capture list, yet you can read any block and know exactly what crosses it, because there
is only ever one rule to run:

> For each name a block uses from outside itself —
> **read it** and the hole is a **share**: a free, read-only view;
> **write it** and the hole is a **move**: the handle moves in and moves back, and writing
> requires the name be `&`.

Reads share, writes move. That is the whole rule, identical for functions, `?`, `#`, `@`,
and bare blocks — so inference is never guesswork: there is no second case, no context in
which the same block would capture differently. Inferred *and* directly knowable, because
the rule is singular.

```grid
n = 4                // immutable
i: &int = 0          // mutable — the attached handle

{ i < n } @ { i += 1 }    // i is written -> moved in/back;  n is read -> shared
                          // afterward i is 4 — the move brought it back
```

A read-hole is a **view**, not a second handle — so a block may *read* an outer value, even
a `&` mutable, without breaking single-ownership: a view cannot write, and while a
[sited](#sited-vs-detached) block holds one the owner runs nothing, so a read and a write
never overlap. Only *writing* takes the move. (This is why a `#` body may read an enclosing
`&` and still never alias it for writing.)

## Sited vs detached

A `?` / `#` / `@` body or a bare block is **sited**: it sits lexically inside an enclosing
scope, so its holes are inferred from that scope.

A **function is detached**: named here and called elsewhere, with no enclosing locals at
its call sites — so it has nothing to infer *from*, and its inputs are its declared
parameters. (Its only ambient access is module constants, which are immutable, hence
shared.) That is the entire function-vs-block difference: the same capture rule, but a
function has nothing to infer from.

```grid
push = (s: &Stack, v: int) -> () { s.data += v }

s: &Stack
s.push(10)           // s moves into push, is mutated, and moves back changed
```

**Grid has no closures.** A function never captures enclosing locals. The job closures
usually do — carrying state between calls — belongs to the
[stateful function](growth.md#streams) instead, which makes that state explicit. Removing
closures removes the reason a captured environment must outlive its capturer, and with it
the lifetimes or garbage collector that decision usually drags in.

## Writes move, so parallelism is free

A written hole is a *move*, and `#` opens many blocks at once — one mutable cannot move
into many — so a `#` body cannot write an enclosing handle; it can only read (share) what
is outside it, and independent reads never race. **`#` is parallel-safe by construction,**
and the racy program does not compile.

`@` opens one block at a time, so it *can* move a `&` accumulator in and thread it through:
that is reduce. Neither combinator carries a "parallel" or "sequential" flag — it falls
out of move meeting fan-out. (This is the whole of why the triad splits the way it does;
see [The Triad](triad.md#why-the-three-are-one-family).)

```grid
swap = (a: &int, b: &int) -> () { … }
x: &int = 1
swap(x, x)           // error — x moves into a and is gone; it cannot also move into b
```

That last line is not a rule a checker enforces; it is simply impossible — a moved handle
is not there to be moved again.

## What falls out

From "a scope is an ownership boundary," with the immutability hinge and move-in /
move-back, these are free — not features, but consequences:

- **Exclusivity without a checker.** A mutable value is reachable through one handle, ever.
  No borrows to track, no lifetimes to annotate, no checker to satisfy. The guarantee is
  structural.
- **Lifetime is scope.** Data lives exactly as long as the scope that owns it and is
  released when that scope ends. Nothing to garbage-collect, nothing to reference-count —
  the owning scope's exit *is* the free. (When a non-memory effect needs to run at that
  exit — closing a handle, flushing — that is [`~` defer](growth.md#defer).)
- **Purity by construction.** A scope can affect only what it was handed; the only way a
  call can change its caller's world is a `&` parameter, so effects are visible right in
  the signature.
- **Parallel-safe by construction.** Independent scopes that share immutable data and own
  disjoint mutable data cannot race — there is no shared writable state to race over. This
  is the property that lets one of the three combinators fan out across cores for free.

With the substrate in place — handles, the immutability hinge, holes by one rule — we can
ask how blocks *compose*. That is [the triad](triad.md).
