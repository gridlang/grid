# Present and Nothing

> **Layer 3 of the model.** The keystone — the single distinction the whole language reads
> off.

All of control flow rests on one distinction, and only one: a thing is either **present** —
some value, meaning "yes / it worked / here it is" — or it is **`()`**, the one nothing,
shared by every absence the language can express: false, null, no-match, missing key, out
of bounds, empty result, end of loop. There is no `bool`, no truthiness table. There is
*present*, and there is `()`.

## No bool

`false` was only ever "the nothing of the boolean type" — and the language already has a
universal nothing, so a second one is redundant. Grid removes `bool`: **failure is `()`,
and any present value is "true."** A test does not yield `true`/`false`; it yields a value,
or it yields nothing.

That is exactly what makes the conditional clean. A *failed* test is `()` (absent), while a
*value* like `0` is present — so "if x" never confuses "x is zero" with "x is missing," the
snag that sinks every falsy-by-default scheme:

```grid
n ? doThing        // runs if n is present — and a data 0 IS present
3 >= 5 ? doThing   // skipped — the test produced ()
```

## Every operator is partial

Once `()` is the universal failure, every operation that *might not have an answer* just
returns it. Operators are partial — each yields **a value, or `()`**:

```grid
xs[i]        // the element, or () if out of bounds
m["key"]     // the value,  or () if the key is absent
a / b        // the quotient, or () if b is 0
find(s, c)   // the index,  or () if not found
```

No exceptions, no `get-or-default`, no bounds ritual: a missing map key and a failed `if`
are the *same thing*, handled the same way. The value-level logical operators are
**selectors**, not boolean algebra — they choose a value and short-circuit by construction:

```grid
a && b       // if a is present, yield b; else ()
a || b       // yield a if present, else b   (first-present value)
```

`||` is a value-default, *not* an `if`/`else` — that distinction matters and is the subject
of [Try and Branch](try-branch.md#branching-not-selecting).

## Relations chain

A relation yields **its right operand** on success, `()` on failure — so comparison
*chains* by ordinary left-to-right composition, with no special "chained comparison"
feature:

```grid
a < b < c      //  (a < b) < c :   1 < 2 < 3  -> 3 (holds) ;  1 < 5 < 3  -> () (5 < 3 fails)
x == y == z    //  equal the whole way -> z, else ()
```

A relation is just an operator with a canonical result, no more special than `1 + 2`. This
is also why a relation drops cleanly into `?` and `=>`: `7 < limit` yields `limit`, so
`7 < limit ? bound => …` binds `limit`.

## The two operators that read the bit

Everything else in this layer is two operators reading present-vs-`()`:

- **[`?` and `?:`](try-branch.md)** — *try* and *branch*. `?` runs a consequent when its
  subject is present; `?:` adds an else, choosing on the condition.
- **[`=>`](match.md)** — *match and commit*. It reads a block's topic, matches a pattern,
  binds, and commits the block on a match.

Together with the [triad](triad.md), these are the whole of Grid's conditional and control
story. Read on.
