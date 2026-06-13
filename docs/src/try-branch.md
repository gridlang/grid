# Try and Branch

`?` and `?:` are how Grid reads presence into control. `?` *tries*; `?:` *branches*.

## Try

`subject ? consequent` is the one conditional. If `subject` is **present**, it yields
`consequent` — evaluated with `subject`'s value as the block's **topic** — otherwise `()`.

```grid
cond ? result               // result if cond succeeded, else ()
m["k"] ? v => use(v)        // if-let: v binds the value if the key was there, else ()
```

`?` is the `if`, the optional-unwrap of a `T | ()`, and the success-check over any partial
operator — all one operator, because they are all one question: *is the subject present?*
That its consequent sees the subject's value as the topic is what gives Grid **if-let** for
free; the [topic](match.md#the-topic) is developed in the next section.

## Branch

For an explicit **else**, `?:` is the two-outcome **branch**: `subject ? then : else` runs
exactly one side, chosen by `subject`'s presence. The decision is made **once, on the
condition** — `else` is skipped when `subject` is present, *even if `then` evaluates to
`()`*:

```grid
m["k"] ? v => use(v) : fallback()        // present -> use it; absent -> fallback
n % 2 == 0 ? n / 2 : `{n} is odd`!       // value if / else
n > 99 ? "big" : n > 9 ? "med" : "small" // right-associative -> an elif ladder
```

That "decide on the condition, not on `then`'s value" is the entire point, and it is what a
value-selector cannot do.

## The branch family

`?:` is not a C ternary bolted on — it is the middle member of a family that
present-vs-`()` already implies, one step apart in arity:

| Form | Arity | Meaning |
|---|---|---|
| `cond ? then` | 1-outcome **gate** | run `then` if `cond` present, else `()` |
| `cond ? then : else` | 2-outcome **branch** | run exactly one, chosen by `cond`'s presence |
| `topic ? { pat => … }` | n-outcome **dispatch** | [match](match.md) (reachable only when the topic is present) |

And `||` is the **degenerate branch where the test is the payload**:

```grid
a || b   ≡   a ? a : b      // (a is evaluated once)
```

This is why the family factors cleanly, and why the precedence below *falls out*
structurally rather than being chosen.

## Branching, not selecting

`?:` branches on the **condition**; `||` defaults on the **result**. When the chosen branch
is effectful — and so yields `()` — they diverge, and only `?:` is an if/else:

| Expression | cond present, then = `100` | cond present, then = `()` | cond = `()` |
|---|---|---|---|
| `cond ? then : else` | `100` | `()` (else skipped) | else |
| `cond ? then \|\| else` | `100` | else (**wrong** for if-else) | `()` |

`||` cannot tell "the condition was absent" from "the then-branch ran and produced
nothing," so pressing it into else-duty runs both branches of an effectful if/else. That is
exactly why an if/else is `?:` and never `||`; the trade-off is examined in
[Design Notes](design/decisions.md#commit-on-match).

## Precedence: the loosest operator

One rule: **`?:` binds looser than everything else** — every value operator (`||`, `&&`,
comparison, arithmetic) and every combinator (`@` `#` `>>`) — **and is
right-associative.** All three slots therefore accept full expressions without parens:

```grid
a || b ? c : d        →  (a || b) ? c : d        // condition is a presence-chain
cond ? xs # f : ys    →  cond ? (xs # f) : ys     // then is a combinator expression
cond ? a : b || c     →  cond ? a : (b || c)      // else is a presence-chain
a ? b : c ? d : e     →  a ? b : (c ? d : e)      // right-assoc: an elif ladder
```

The cost is symmetric and visible: when you want the *result* of an if/else to feed a
tighter operator, you parenthesize.

```grid
(cond ? xs : ys) # f
(cond ? a : b) || default                 // default the whole if-else
```

This is the right cost distribution — `?:` is the outermost branch skeleton, everything
else fills its slots, and only the feed-the-result case needs grouping. [`=>`](match.md) is
an ordinary operator sitting **just under `?:`**, so `f() ? x => g(x) : h()` reads as
then = `x => g(x)`, else = `h()`. The full table is in
[Operators and Precedence](ref/operators.md).

## A pure value-selector

`||` has exactly one job: **yield the first present value in a chain.** It is not an else —
`cond ? then || default` defaults on `then`'s *result*, which is a different thing from
branching on a condition, so an if/else is always `?:`, never `||`.

```grid
config || default_config         // value-defaulting: first present source
input  || fallback
```

Because `?:` chooses on the condition, it also gives you polarity control — a `not` written
with an explicit marker, no `bool` required:

```grid
a || default        // preserves polarity: a if present, else default
a ? () : default    // inverts: () if present, else default
a ? marker : ()     // present -> marker, absent -> ()
```

The companion to `?` is `=>`, which matches the topic that `?` hands inward. That is
[Match and Commit](match.md).
