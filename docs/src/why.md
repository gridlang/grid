# Why Grid?

Every language you have used carries a small zoo of *nothings*, one per type, and a
separate mechanism for each. Grid is what happens when you refuse to keep them apart.

## A second nothing for every type

Ask a program to say "there is nothing here" and watch how many different answers it has.

- A boolean's nothing is `false`.
- A reference's nothing is `null` — and a different `null` for every pointer.
- A string's nothing is `""`; a list's is `[]`; a number's is often `0`.
- A search's nothing is a sentinel: `-1`, `NaN`, `npos`, `None`.
- A map lookup's nothing is a missing key — sometimes an exception, sometimes a default.
- An iterator's nothing is `StopIteration`, or a `false` from `hasNext`, or a null
  terminator.
- A failed computation's nothing is an exception, unwound through a side channel that the
  type system cannot see.

Each of these is "the absence of a value," and each gets its own control construct:
`if` for booleans, null checks for references, `.empty()` for collections, `== -1` for
searches, `try`/`catch` for failures, `for`/`hasNext` for iteration. They do not compose.
A function that can fail *and* return nothing *and* run out has to braid three idioms
together, and the reader has to unbraid them.

Worse, the nothings lie. `0` is a real number, but it is also "falsy." `""` is a real
string, but it is also "empty." The moment a language conflates *the value zero* with
*the absence of a value*, every `if (x)` becomes a small bug waiting for the day `x` is
legitimately zero. Languages spend real complexity — `Option`, `Maybe`, nullable types,
"truthiness" tables — patching a problem they created by having more than one nothing.

## Two more taxes

On top of the nothings, systems languages charge for two things Grid declines to buy.

**Aliasing.** The hard problem in a language with pointers is that two handles can reach
one mutable thing. Everything built to police that — borrow checkers, lifetimes,
reference counting, garbage collectors — exists to make aliasing safe after the fact.
Grid removes the problem instead of policing it: immutable data is shared freely (it can't
change, so sharing is invisible), and mutable data has exactly one handle. There is
nothing to alias, so there is nothing to check. → [Scope is Ownership](substrate.md)

**Closures.** A closure quietly captures its environment, which means the environment must
outlive the closure, which drags in lifetimes or a garbage collector to decide when it is
safe to free. Grid has no closures. The one job they reliably do — carrying state between
calls — is done explicitly by a [stateful function](growth.md), and everything else a
block needs from outside is captured by one visible rule. → [Holes](holes.md)

## Icon's idea, made into a value

Grid's ancestor is [Icon](https://www2.cs.arizona.edu/icon/), a language built on
*goal-directed evaluation*: an expression either **succeeds**, producing a result, or it
**fails**. Control reads off that single distinction — `if`, `while`, `every` ask only
"did it succeed?" Icon's insight is that you do not need booleans to drive control; you
need success and failure.

But in Icon, failure is a control signal, not a value — you cannot store it, return it,
or put it in a list. Grid takes the one further step: **make failure a value.** There is a
single nothing, `()`, and it is the only one. It inhabits no other type, so a present `0`
and an absent `()` are never confused. Because it is an ordinary value, you can return it,
bind it, store it, and match on it — goal-directed evaluation, now *typed and
value-returning.*

That single move collapses the zoo:

```grid
xs[i]        // the element, or () if out of bounds
m["key"]     // the value,  or () if the key is absent
a / b        // the quotient, or () if b is 0
find(s, c)   // the index,  or () if not found
```

Every operator is **partial**: it yields a value, or `()`. A missing map key and a failed
comparison and a divide-by-zero are *the same event*, handled the same way — with `?`,
which runs its consequent only when its subject is present:

```grid
n ? doThing          // a data 0 is present, so this runs; () would not
3 >= 5 ? doThing     // the comparison failed -> () -> skipped
```

And because a relation yields its **right operand** on success, comparisons chain by
ordinary composition — no special "chained comparison" feature, just partial operators
falling into place:

```grid
1 < 2 < 3            // (1 < 2) -> 2, then (2 < 3) -> 3 ;  holds
1 < 5 < 3            // (1 < 5) -> 5, then (5 < 3) -> () ;  fails
```

## What one nothing buys

Once there is a single nothing and every operator is partial, whole categories of
language machinery evaporate — not because they were hidden, but because there is nothing
left for them to do:

- **The conditional** is `?` reading presence. No `bool`, no truthiness table. →
  [Present and Nothing](present.md)
- **The optional** is `T | ()` — present *is* "some," `()` *is* "none." No `Option` type,
  no unwrap ceremony. → [Match and Commit](match.md#what-this-dissolves)
- **Error handling** is the same `()`, and when a failure needs a *reason*, `-> T ! E`
  carries one — still over the one nothing. → [From the Seed](growth.md#fallibles)
- **Iteration** is "take the next, stop at `()`." Reaching past the end of a list is just
  an out-of-bounds index, which is already `()`. A collection and a live stream are the
  same thing: a source you pull until nothing comes back. → [From the Seed](growth.md#sources)
- **Loop exit** is the same bit read the other way: in `@`, a body that yields a present
  value *exits* with it (break / find), a body that yields `()` *continues*. So `break` and
  `continue` are not keywords — they are values; `return` dissolves too, since a block's last
  expression is its value and an early exit is the `!` operator. → [The Triad](triad.md)

The triad `?` `#` `@` then gives the three ways a block composes over an input, and the
distinction between *parallel* and *sequential* is not a flag you set — it falls out of
the memory model (reads can be shared across many blocks; a write must move into one). The
language has, save `module` and `import`, **no keywords** — control flow is operators on
values, all the way down.

## What it costs

Grid is honest about the trades. There is no logical `not`, so you invert the predicate
(`a >= b`) or take the absent branch — the `!` symbol is freed for failures instead. An
effectful loop body must end in `()` to keep looping, because a present value would exit —
a small, visible discipline rather than a hidden rule. And "everything is present or
nothing" asks you to think in success/failure where you once thought in true/false. In
exchange, you get a language with one nothing, no aliasing to police, no closures to chase,
and a control story that fits — genuinely fits — in your head.

The rest of this book derives that language one layer at a time. Each layer is forced by
the one beneath it; that is the point. Start with [Scope is Ownership](substrate.md).
