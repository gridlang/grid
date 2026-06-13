# Patterns

A **pattern** is the left side of [`=>`](../match.md). It is matched against the block's
**topic**: it tests shape, binds names, and on a match commits the block. A pattern is *not*
a test — relations and computed conditions are [`?` guards](../match.md#match-shape-test-conditions),
never patterns.

## The pattern forms

| Pattern | Matches | Binds |
|---|---|---|
| literal — `0`, `"GET"`, `'z'` | the topic equals it (`==`) | nothing |
| name — `x`, `code` | always | the topic, to that name |
| `_` | always | nothing |
| `()` | the topic is `()` | nothing |
| tuple — `(p, q)` | a tuple of that arity, each `pᵢ` matching | each position |
| list — `[p, q]` | a list of that **exact** length, each `pᵢ` matching | each position |
| list + rest — `[p, ...]` | a list of *at least* that length | the leads; `...` discards the tail |

A **struct** is a [named tuple](../types.md#tuples-and-structs--both--), so a positional
tuple pattern matches it by position — `(x: 1, y: 2) ? { (a, b) => … }` binds `a = 1`,
`b = 2`.

Sub-patterns nest to any depth — each position is itself one of the forms above:

```grid
(1, (2, 3))    ? { (a, (b, c)) => `{a} {b} {c}` }     // -> "1 2 3"
[1, 2]         ? { [a, b]    => `pair {a},{b}` }      // exact length: [1] does not match
[1, 2, 3]      ? { [a, b, c] => `triple` }
```

A bare name binds the **whole** topic, which is why the idiom for "match anything and name
it" is just `x =>`, and "match anything, ignore it" is `_ =>`.

## Matching is commit-on-match

The first arm whose pattern matches **commits** the block — its result is returned
immediately, *even if that result is `()`*, and no later arm runs. A non-matching arm is
transparent: it yields `()` and threads the topic through to the next statement. This is
what makes a block of arms a [dispatch](../match.md#the-topic), and it is keyed on the
*match*, not on the result's presence (see [Design Notes](../design/decisions.md#commit-on-match)).

A literal pattern dispatches on a known value; a name or `_` always matches, so a block
ending in `x =>` or `_ =>` is total. A block with no matching arm yields `()`.

## The step tuple

When a [combinator](../triad.md#the-step-value) drives a block per element, the topic is the
element paired with its position, so the pattern destructures that pair:

| source | topic per step | typical pattern |
|---|---|---|
| list | `(index, element)` | `(i, x)` or `(_, x)` |
| map | `(key, value)` | `(k, v)` |
| string | `(index, char)` | `(i, c)` |
| stream | the emitted value | `v` |

```grid
nums # { (_, n) => n * 2 }            // ignore the index
m    # { (k, v) => `{k}={v}` }        // key and value
xs   @ { (i, x) => i < k ? x }        // index and element
```

A single binding captures the *whole* pair: `# { x => x }` over `[10, 20]` yields
`[(0, 10), (1, 20)]`.

## Multi-way tests are `?:`, not patterns

Because a pattern matches *shape*, a ladder of computed conditions is a chain of
[`?:`](../try-branch.md), not a match block:

```grid
n >= 90 ? "A" : n >= 80 ? "B" : "C"      // tests -> ?: ladder
```

Reaching for `=>` here would be a category error — `n >= 90` is a test, and its value is not
a pattern. Match on shape; branch on tests.
