# Scope is Ownership

> **Layer 1 of the model.** This is the foundation the rest of the language derives from.
> We add a layer only once the one beneath it holds.

Grid treats function purity not as a discipline you follow but as a fact that falls out of
a single decision: **a scope and an ownership boundary are the same thing.**

Most languages answer "what can this code reach?" (scope) and "who owns this data?"
(memory) with two separate systems. Grid answers them with one. A scope is the region
where a piece of data lives *and* the only region that can reach it. Purity is then not a
property you prove — it is the shape of the language. Everything in this chapter is a
consequence of taking that seriously.

## Handles, not buckets

A label is a **handle** to data, not a bucket that contains it.

```grid
a = 1
```

`a` does not *hold* a `1`; it *points at* one. This is the Algol bucket turned inside out,
and it is what lets ownership and scope be one idea: you reason about who can reach the
data, never about where a value got copied to.

An implementation is free to keep a small `int` in a register and a large structure on the
heap — that is an optimization. The model is always: a handle to data.

## The immutability hinge

The hard part of "handles to shared data" is mutation. If two handles point at one thing
and either can change it, you are back to aliasing, races, and the machinery — borrow
checkers, lifetimes — built to police them. Grid sidesteps the machinery with a split it
wants anyway: **immutable by default.**

**Immutable data is freely shared.** Because it cannot change, the difference between "two
handles to one value" and "two copies of one value" is *unobservable*. So immutable
handles are shared at will — at no cost, with nothing to track. For the immutable majority
of a program, everything is a pointer, and it is safe precisely because nothing can write
through it.

```grid
a = 1
b = a        // b and a are handles to the same 1 — indistinguishable from a copy
```

**Mutable data has exactly one handle.** A mutable value is marked with `&`, a symbol
chosen to *look like a handle gripping its data*. A `&` value is owned by one label at a
time. You cannot make a second handle to it; to get one you take your own owned copy.

```grid
c: &int = 1   // c is the single attached handle to a mutable 1
c += 1        // c now points at 2 — mutated in place, through the one handle
d: &int = c   // d is a NEW owned copy; c is untouched
```

> `&` is iconic, like the rest of Grid's symbols (`#` a grid, `@` a loop, `?` a fork): a
> little handle attached to the value, marking the one place a value may change.

The aliasing problem therefore never arises: **shared things can't be written, written
things can't be shared.** There is nothing to alias, so there is no aliasing checker — the
guarantee is structural, not enforced. (`&` is also the type intersection operator when it
sits *between* two types; the prefix-vs-infix position keeps the two readings apart. See
[Literals and Types](types.md#unions-and-intersection).)

## What this is doing for you

The whole point of making a scope an ownership boundary is what it lets you stop doing.
The next chapter, [Holes](holes.md), shows the single rule by which data crosses into a
block — and how, from that rule plus the immutability hinge, purity, exclusivity,
lifetimes, and parallel-safety all come for free.
