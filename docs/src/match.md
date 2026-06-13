# Match and Commit

`pattern => result` is an ordinary operator. It reads the block's **topic**, matches the
pattern, binds any names, and **on a match commits the enclosing block** — the block
returns `result` immediately. It is `==` + bind + an early return.

## The patterns

- a **literal** — `0 => r` commits with `r` exactly when the topic is `0`;
- a **name** — `n => r` always matches, **binds** the topic to `n`, and commits with `r`;
- **`_`** — `_ => r` always matches, binds nothing, commits with `r`;
- **structural** — `(a, b) => r` and `[a, b] => r` match shape and bind each position,
  recursively (each position is itself a pattern — a literal, a name, `_`, or another
  structural pattern).

```grid
status ? {
  200  => "ok"
  404  => "missing"
  code => `error {code}`     // binds the topic, commits
}
```

The complete pattern grammar — nesting, list rest patterns `[first, ...]`, the step-tuple
forms — is in [Patterns](ref/patterns.md).

## Commit on the match, not the value

The commit is keyed on **the match**, not on whether `result` is present. A matched arm may
do effects and yield `()` and still win:

```grid
status ? {
  200 => { log("ok"); () }   // commits on match; the () result is fine
  _   => { log("else"); () }
}
```

This is what makes effectful dispatch work. If commit depended on the *value*, an arm that
did its work and produced `()` would look like "didn't fire," and control would fall
through to later arms — wrong for tokenizers, routers, and state machines. Keying commit on
the match means a non-match is the only thing that's transparent. The alternatives, and why
every other language commits on the selection, are in
[Design Notes](design/decisions.md#commit-on-match).

## The topic

A `{ }` block is one scope, run as a **sequence**: it returns the result of the first `=>`
arm that commits, or else its last statement's value.

Every block has a **topic** — its implicit input, what `=>` matches against. It is set by
the combinator on the left (`subject ? …`, `xs @ …`, `xs # …`) or **inherited** by a
bare/nested block from the enclosing context. Within a block, the topic threads as **the
last *present* value**:

- a statement that produces a **present** value updates the topic to that value;
- a statement that produces `()` — an effect, or a non-matching arm — is **transparent**
  and passes the current topic through unchanged.

So several `=>` arms in a block all see the *same* subject (each non-match passes it
through), which is what makes **dispatch** work — the first arm that matches commits, later
arms never run. And a value-producing **prelude** can compute the very subject the arms
match:

```grid
// non-matching arms pass the topic through; a plain statement still sees it
status ? {
  200 => "ok"            // no match -> () -> topic passes through
  404 => "missing"
  `unknown {status}`     // a plain statement, still the same topic
}

// compute-then-dispatch: a present prelude becomes the topic the arms match
raw ? {
  str.upper(raw)         // present result -> becomes the topic
  "GET"  => "read"
  "POST" => "write"
  _      => "unknown"
}
```

### The one asymmetry

The topic is `()`-*transparent* (so arms compose on one subject), but a block's **return
value** is `()`-*opaque* (a trailing `()` is a real `()` return). Equivalently: **topic =
the last present value; return = the last value.** Two different jobs — what `=>` matches
against versus what the block hands back — and this is the minimum that keeps both true at
once. The opacity of the return is exactly what lets an [`@`](triad.md#thread) body force
"continue" with a trailing `()`.

## Usable anywhere

`=>` is a normal operator, not a special clause — it does not require a `{ }` wrapper. It
can be a bare consequent or a branch slot. So if-let is just `=>` reading the topic that
`?` handed inward:

```grid
m["key"] ? v => use(v)               // bare =>, bind the looked-up value
f() ? x => g(x) : h()                // => in the then-slot; : h() is the else
7 < limit ? bound => bound * 2       // a relation yields its right operand; => binds it
```

## Match shape, test conditions

`=>`'s left side is a **pattern** — literals, names, `_`, tuples, lists, `()`. A relation
like `n < m` is a *test*, not a pattern, so it is a `?` guard, never a `=>`:

```grid
n < m ? y           // correct: a test
n < m => y          // rejected: `n < m` is not a pattern
```

Keeping that line sharp is what stops `=>` from blurring into "equality on an expression's
value." A multi-way ladder of *tests* is therefore a chain of [`?:`](try-branch.md), not a
match block:

```grid
grade = (n: int) -> str { n >= 90 ? "A" : n >= 80 ? "B" : "C" }    // tests -> ?: ladder
```

## Break, continue, and find

The same present-vs-`()` bit, read by [`@`](triad.md#thread), gives loop control without
keywords: an `@` body that yields a **present** value exits the loop with it, a body that
yields `()` continues. So `break value` is "yield a present value," `continue` is "yield
`()`," and **find** is a body that succeeds at most once:

```grid
find = (xs: [int], t: int) -> int | () {
  xs @ { (_, x) => x == t ? x }      // match -> present x -> exit; else () -> continue
}                                    // run out -> () -> not found
```

`x == t ? x` yields `x` (present, exits) or `()` (continues). The looping is `@`'s job; the
match always commits with that value, and `@` reads it. This present-exits rule is the
goal-directed core of the language; why it, and not the alternatives, is in
[Design Notes](design/decisions.md#present-exits).

## What this dissolves

With present-vs-`()`, `?`, `?:`, and `=>` in hand, several familiar constructs turn out to
have been the one nothing all along:

- **An optional is `T | ()`** — present *is* "some," `()` *is* "none." No `Option`, no
  presence flag; a present `0` and an absent `()` are distinct because `()` inhabits no
  other type.
- **A flag fuses with its payload.** "Set a bool, branch on it later" becomes a `T | ()`
  that is present exactly when the condition holds and carries what you'd act on:
  `running: Conn | ()` — present *is* running, and it hands you the connection. The bool was
  always a lossy shadow of the data.
- **No logical `!`** — invert the predicate (`a >= b`) or take the absent branch; the
  symbol is freed for [failures](growth.md#fallibles) instead.

## The keystone

Present vs `()`. Every value is success; `()` is the only failure; every operator is
partial; `?` tries, `?:` branches, `=>` matches, and the [triad](triad.md) reads off that
single bit. That is the whole of Grid's conditional and control story — no bool, no null,
no coercion, no exceptions. It is goal-directed evaluation made typed and value-returning.

What remains is to pin down the *values* themselves — the literals and types the keystone
operates on. That is [Literals and Types](types.md).
