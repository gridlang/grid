# A Tour of Grid

A fast pass over the whole language, each piece runnable. For the reasoning behind any of
it, follow the links into [The Language](../substrate.md).

## Present, or nothing

Every value is a success; `()` is the only failure. A data `0` is present; only `()` is
absent. `||` selects the first present value.

```grid
0 ? "y"        // "y"   — a data 0 is present
() ? "y"       // ()    — only () is absent
"a" || "b"     // "a"
```

Every operator is [partial](../present.md#every-operator-is-partial) — a value or `()` —
and relations yield their right operand, so comparisons chain:

```grid
10 / 0         // ()    — no divide-by-zero crash
[1, 2, 3][9]   // ()    — out of bounds
1 < 2 < 3      // 3     — (1 < 2) -> 2, then (2 < 3) -> 3
```

## Bindings and functions

`=` defines an immutable handle; `&` marks a mutable one; `+=` mutates it in place.
Functions are values, and `x.f(a)` is `f(x, a)`:

```grid
counter: &int = 0
counter += 5              // counter is 5

inc = (n: int) -> int { n + 1 }
5.inc()                   // 6  — UFCS: inc(5)
```

## Matching the topic

`?` opens a block with its subject as the [topic](../match.md#the-topic); `=>` matches that
topic. Patterns can be literals, binds, `_`, or structural:

```grid
quadrant = (p: (int, int)) -> str {
  p ? {
    (0, 0) => "origin"
    (x, 0) => "on x-axis"
    (0, y) => "on y-axis"
    (x, y) => "in the plane"
  }
}
quadrant((0, 0))   // "origin"
quadrant((4, 0))   // "on x-axis"
quadrant((3, 2))   // "in the plane"
```

A ladder of *tests* (not shapes) is a chain of [`?:`](../try-branch.md), right-associative:

```grid
grade = (n: int) -> str { n >= 90 ? "A" : n >= 80 ? "B" : n >= 70 ? "C" : "F" }
grade(95)   // "A"
grade(83)   // "B"
grade(71)   // "C"
grade(50)   // "F"
```

## The triad

`#` **fans out** — map, and filter by yielding `()`:

```grid
1..6  # { (_, n) => n * n }            // [1, 4, 9, 16, 25, 36]   — map
1..10 # { (_, n) => n % 2 == 0 ? n }   // [2, 4, 6, 8, 10]        — filter
1..3  # { (_, r) => 1..3 # { (_, c) => r * c } }   // nested # = a table:
                                       // [[1,2,3],[2,4,6],[3,6,9]]
```

`@` **threads** — reduce (an `&` accumulator), loop (a `{ }` generator source), and find (a
present body value exits):

```grid
total: &int = 0
1..5 @ { (_, n) => total += n }        // total is 15            — reduce

i: &int = 0
{ i < 3 } @ { i += 1 }                 // i is 3                 — loop

1..100 @ { (_, n) => n * n > 40 ? n }  // 7                      — find
```

## Fallibles and streams

`-> T ! E` carries a reason for failure; `!` raises or propagates it:

```grid
half = (n: int) -> int ! str { n % 2 == 0 ? n / 2 : `{n} is odd`! }
half(8)   // value 4,  error ()
half(7)   // value (), error "7 is odd"
```

A `>>` function is a stream; calling it returns a fresh instance, and exhaustion is `()`:

```grid
each = (xs: [int]) >> int { xs @ { (_, x) => >> x } }
s = each([10, 20, 30])
s()   // 10
s()   // 20
s()   // 30
s()   // ()   — exhausted
```

## It composes

Because the triad shares one shape, a map → filter → reduce pipeline is one breath — sum of
the squares of the odd numbers in `1..10`:

```grid
odd_sq_sum: &int = 0
1..10 # { (_, n) => n % 2 == 1 ? n } # { (_, n) => n * n } @ { (_, s) => odd_sq_sum += s }
// odds [1, 3, 5, 7, 9] -> squares [1, 9, 25, 49, 81] -> sum 165
```

Next: a complete program — the [HTTP Server](http-server.md) — and the
[control-flow patterns](control.md) in depth.
