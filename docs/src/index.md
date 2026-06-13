# Grid

Grid is a small systems language built on a single idea: **present, or nothing.**

Every value Grid can produce is a success — "yes, here it is." There is exactly one
failure, written `()`, and it stands for *every* absence the language can express: false,
null, no match, missing key, out of bounds, empty result, end of a loop. There is no
`bool`, no `null`, no `Option`, no exceptions. A test does not return true or false; it
returns a value, or it returns nothing.

```grid
n ? doThing          // run doThing if n is present — and a data 0 IS present
3 >= 5 ? doThing     // skipped — the comparison produced ()
m["key"] ? v => use(v)   // if the key is there, bind its value and use it
```

This is goal-directed evaluation — the spine of the language [Icon](https://www2.cs.arizona.edu/icon/) —
made typed and value-returning. Once `()` is the only nothing, the conditional, the
optional, iteration, loop-exit, and error handling stop being five separate mechanisms and
become one.

## The whole model, in one breath

Grid is built from the seed up, each layer falling out of the one beneath it:

1. **A scope is an ownership boundary.** A label is a *handle* to data, not a bucket that
   holds it. Immutable data is shared freely; mutable data (marked `&`) has exactly one
   handle. Holes — the names a block uses from outside — are inferred by one rule:
   *reads share, writes move.* So purity, exclusivity, and lifetimes are structural — no
   garbage collector, no borrow checker, no closures. → [Scope is Ownership](substrate.md)

2. **The triad `?` `#` `@`** is the three ways a scope composes over an input: `?`
   **branches**, `#` **fans out** (map/filter, in parallel), `@` **threads** (reduce, loop,
   find). Parallel-vs-sequential is not a flag — it falls out of read-share meeting
   write-move. → [The Triad](triad.md)

3. **Present vs `()`** is the keystone. `()` is the only nothing; every operator is partial
   (a value, or `()`); relations chain because they yield their right operand. `?` tries,
   `?:` branches, `=>` matches. → [Present and Nothing](present.md)

4. **One symbol, one type.** The bracket tells you the container's shape and `:` tells you
   it is keyed: `()` fixed → tuple/struct, `[]` variable → list/map. `{ }` is freed
   entirely — it is only ever a block. → [Literals and Types](types.md)

5. **What grows from the seed** — functions, defer (`~`), fallibles (`! E`), streams
   (`>>`) — are mostly not new machinery but consequences of the four layers below. →
   [From the Seed](growth.md)

No `bool`, no `null`, no exceptions, no garbage collector, no borrow checker, and — save
`module` and `import` — no keywords.

## How to read this book

- **[Why Grid?](why.md)** — what the language reacts against, and the one decision it is
  built on. Start here if you want the *why*.
- **The Language** — the model derived layer by layer (the five chapters above). This is
  the heart: explanation and justification together, because in Grid each piece is forced
  by the one below it.
- **[Reference](ref/grammar.md)** — the precise lookup: grammar, the operator
  [precedence table](ref/operators.md), the full [pattern grammar](ref/patterns.md).
- **[In Practice](examples/tour.md)** — worked programs: a [tour](examples/tour.md), the
  [HTTP-server flagship](examples/http-server.md), and the
  [control-flow patterns](examples/control.md).
- **[Design Notes](design/decisions.md)** — the roads not taken, and why.

> Grid is a language in design. This book is its specification; the implementation follows
> it, not the other way around.
