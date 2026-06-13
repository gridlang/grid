# Control-Flow Patterns

Grid's control model, by example. Five patterns that together cover Grid's whole
conditional surface — and show why it needs no `if`, `switch`, `break`, or `return`. The
operators in play:

- `?` — [try / if-let](../try-branch.md#try); the consequent's topic is the subject's value
- `?:` — [two-outcome branch](../try-branch.md#branch); the loosest operator,
  right-associative
- `=>` — [match and commit](../match.md); on a match, return the result immediately, even if
  it is `()`

## if-let with a fallback

`?` hands the subject's value inward as the topic; a bare `=>` binds it. A `:` adds the
absent-case fallback. So "look it up, transform it, or fall back" is one line:

```grid
m = ["host": "grid.dev"]
m["host"] ? v => str.upper(v) : "none"   // "GRID.DEV"  — present: bind and transform
m["port"] ? v => str.upper(v) : "none"   // "none"      — absent: fallback
```

## Effectful dispatch

A matched arm [commits on the match, not on its value](../match.md#commit-on-the-match-not-the-value),
so an arm can do effects and yield `()` and still win, and no later arm runs:

```grid
ok: &int = 0
other: &int = 0
status = 200
status ? {
  200 => { ok += 1; () }
  _   => { other += 1; () }
}
// ok = 1, other = 0   — the _ arm never runs
```

This is the pattern behind tokenizers, routers, and state machines: classify, do the
effect, stop.

## Compute, then dispatch

The [topic threads](../match.md#the-topic) as the last present value, so a value-producing
prelude sets the very subject the arms match:

```grid
route = (raw: str) -> str {
  raw ? {
    str.upper(raw)            // present result -> becomes the topic the arms match
    "GET"  => "read"
    "POST" => "write"
    _      => "unknown"
  }
}
route("get")    // "read"
route("post")   // "write"
route("put")    // "unknown"
```

## A guard ladder

A ladder of *tests* is a chain of `?:`. Because `?:` is right-associative, it reads as a
clean if / elif / else — and there is no cross-arm fall-through to reason about:

```grid
grade = (n: int) -> str {
  n >= 90 ? "A" : n >= 80 ? "B" : n >= 70 ? "C" : "F"
}
grade(95)   // "A"
grade(85)   // "B"
grade(75)   // "C"
grade(65)   // "F"
```

(Match on *shape* with `=>`; branch on *tests* with `?:`. A relation like `n >= 90` is a
test, never a pattern — see [Match and Commit](../match.md#match-shape-test-conditions).)

## if-let on a relation

A relation [yields its right operand](../present.md#relations-chain), so `=>` can bind that
operand directly — `7 < limit` succeeds with `limit`, and `bound` captures it:

```grid
limit = 10
7 < limit ? bound => bound * 2 : -1     // 20  — 7 < 10 yields 10, bound binds it
```

Five patterns, three operators, one bit — present or `()`. That is the whole of Grid's
control flow. The roads not taken on the way here are in [Design Notes](../design/decisions.md).
