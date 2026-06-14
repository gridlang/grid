# Grid — The Lambda Model (convergence)

*Status: converged decision record from the topic/lambda redesign. It supersedes the
"threaded topic / blocks-are-not-first-class" treatment in `MODEL.md` and `blocks.md`. This
is the spec the mdbook rewrite follows; once folded into the book it can be retired like the
other design docs. Open items are in §8.*

## The one idea

A **block, a function, a `=>` arm, and an `_`-expression are the same thing: a lambda over
the topic.** The triad `?` `#` `@` *applies* lambdas; a call applies a lambda; an assignment
stores one. Everything else falls out of that.

---

## 1. The topic and `_`

- Every lambda has one input — its **topic**. `_` denotes the topic.
- **`_` only *references*; binders *introduce*.** The binders are exactly two: the
  **combinators** `?`/`#`/`@` (which bind `_` for their operand) and the **`=>` arm** (which
  binds `_` to its subject, the pattern destructuring it). `_` is never a per-occurrence
  parameter, so multiple `_` in one body are the **same** topic — `_ * _` is topic², not a
  two-argument lambda.
- **`_` needs a binder.** A bare `_` with no enclosing combinator/`=>` is an error. To make a
  lambda in value position, write the binder yourself: `_ => expr` (or a named `x => expr`,
  or a function).
- **Extent** = the combinator's right operand, delimited by precedence (`?:` loosest, …).
  There is no Scala-style "how much does `_` capture" question, precisely because `_`
  references rather than introduces.
- The topic is **frozen per level**: within one block it is a single fixed value. A nested
  binder introduces a new topic for its own body; bare `_` always means the *nearest*. To
  reach an outer topic past a nested binder, **name it** (`x =>`).

## 2. Values vs sited bodies — escapability

A lambda's captures (its [holes](holes.md)) are inferred and classified:

- captures only **immutable** reads (including none) → the lambda is a **value**:
  first-class, storable, passable, returnable. Its captures are moved or copied *by value*
  — free by the immutability hinge, no GC, no tracking. (Anonymous ones use `_`/`=>`; named
  ones are functions.)
- captures a **mutable** — a write-move of a `&`, or a read-view of one → the lambda is a
  **sited body**: not a value; it can only be driven in place by the combinator that birthed
  it. This is reduce and effectful loops.

The refined identity: **Grid has closures, but only over immutable data.** Mutable closures
are forbidden; they stay sited. The holes analysis already draws this line.

## 3. The forms

| Form | Is | Notes |
|---|---|---|
| `pat => result` | a pattern-matching lambda (value) | matches the topic; on match → `result` (even `()`); else `()` |
| `{ … }` block | a lambda; body is a sequence + arms (value) | returns the first committing arm, else the last statement's value |
| `(params) -> T { }` | a named, explicit-param, zero-capture lambda | a **function**; always a value |
| bare `expr` with `_` | a combinator-operand body (sugar) | not a standalone value; reify with `_ =>` |

- **Application vs storage** is exactly `f` vs `f(x)`: a combinator (or a call) *applies* a
  lambda; an assignment *stores* it. A block's arms match the block's topic **when the block
  is applied** — `xs # { x => x*2 }` applies it per element; `g = { x => x*2 }` stores it
  (`g(5)` is `10`). No statement-vs-expression rule is needed.
- A bare `_`-expression is combinator sugar, **not** a value: `g = (_ * 2)` is an error;
  write `g = _ => _ * 2`. (This is why passing a body to a *user* combinator needs the
  explicit `_ =>`.)

## 4. Topic source per combinator

The topic is "the element," whatever that is for the source:

| source | topic (the element) | indexed / projected form |
|---|---|---|
| list | the element | `xs.enum` → `(index, element)` |
| string | the char | `s.enum` → `(index, char)` |
| map | the `(key, value)` entry | `m.keys`, `m.values` |
| stream | the emitted value | — |

A map's element *is* its entry — same rule as lists, different element type. (The
`.enum`/`.keys`/`.values` naming is pending a small revision — see §8.)

Generators are unchanged: a literal `{ … }` block as `@`'s **source** is a re-evaluated
thunk (no topic) — the loop/while form: `{ i < n } @ (i += 1)`.

## 5. Block semantics — frozen topic

A block is a function body with a fixed topic input:

- statements run in order in one scope; a non-final value is discarded; bindings are visible
  to later statements.
- a `=>` arm **commits** the block on a pattern-match — the block returns its result
  immediately (even `()`), no later statement runs. A non-matching arm yields `()` and falls
  through.
- the block's value is the first committing arm's result, or else the **last statement's
  value**.
- the topic is **frozen** = the binder's (subject / element); it does **not** thread. To
  dispatch on a *computed* value, make it the subject of a nested combinator
  (`compute(x) ? { arms }`).
- `()` as the last value continues an `@` loop (a present value exits). There is **no
  topic/return asymmetry** — the topic doesn't thread, so there is nothing to reconcile.

## 6. The idioms

```grid
// map / transform — point-free (no inner ? to rebind _)
nums  # (_ * 2)
1..10 # (_ * _)                       // squares

// filter / find — NAME the element: an inner ? rebinds _ to the predicate's result
nums   # (n => n % 2 == 0 ? n)        // evens
1..100 @ (n => n * n > 40 ? n)        // first n with n² > 40  ->  7

// reduce / loop — point-free; the mutable accumulator makes the body sited
sum: &int = 0
1..5 @ (sum += _)                     // 15
i: &int = 0
{ i < 3 } @ (i += 1)                  // loop while i < 3

// if-let — point-free (the value you want IS the subject)
m["host"] ? use(_)
m["host"] ? v => str.upper(v) : "none"

// branch ladder
n >= 90 ? "A" : n >= 80 ? "B" : "C"

// dispatch — arms match the frozen subject
status ? { 200 => "ok"  404 => "missing"  _ => `other {status}` }

// compute-then-dispatch — make the computed value the subject (no threading)
str.upper(raw) ? { "GET" => "read"  "POST" => "write"  _ => "unknown" }

// nested — name the outer topic to reach past the inner binder
1..3 # (r => 1..3 # (_ * r))          // multiplication table

// destructuring — the element is a tuple / a map entry
pts    # (_.0 + _.1)                  // pts:    [(int, int)]
prices # (_.1 * 2)                    // prices: [str: int], element = the entry

// user-defined combinator — the body is an ordinary function value
myMap = (xs: [T], body: (T) -> R) { xs # body(_) }
words.myMap(upper)                    // η
words.myMap(_ => upper(_))            // explicit lambda (arg position needs the binder)
```

The learnable rule: **point-free holds until an inner `?` rebinds `_`; then name what you
need past it.** Map / transform / reduce / loop / if-let are point-free; filter / find name
their element.

## 7. What this dissolves / changes

- **block ≠ function** → gone: one lambda. (Freezing removed the threading that made a block
  special.)
- **the topic/return asymmetry** → gone (topic frozen).
- **"blocks are not first-class"** → refined: first-class iff immutable-capture.
- **"no closures"** → refined: no *mutable* closures.
- **`xs # f` was a parse error** → now legal: `xs # f` is *constant `f`*; `xs # f(_)` is
  *map `f`*. No implicit η — `_` must appear to touch the element.
- **the `(index, element)` step pair** → gone: topic = the element; index via `.enum`.

## 8. Deferred / open

- **`.enum` / `.keys` / `.values` naming** — a small revision is pending.
- **Inline sited-body params** for user combinators (Kotlin-`inline`-style), so a user
  combinator can take an effectful/accumulating body. Later.
- **Body-typed params** (`body: _ -> R`) that auto-bind `_`, erasing the explicit `_ =>` at
  user-combinator call sites. Later.
- **Exhaustiveness** warnings on a dispatch with no matching arm and no `_`. Later.

## 9. Book impact

A substantial rewrite. Affected: `holes.md` (capture → the escape line; immutable closures),
`triad.md` (topic = element; "apply a lambda"; `# f` legal), `match.md` (drop topic-threading
and the asymmetry; `=>` is a lambda; `_`; frozen topic; filter/find name their element),
`try-branch.md` (`?` rebinds `_` — if-let; `_`), `types.md` / `growth.md` (functions are
named lambdas; `.enum` / `.keys` / `.values`), the three `ref/*` pages (the `_` / lambda
forms, the extent rule, patterns), every `examples/*` (the new surface), and
`design/decisions.md` (this document's rationale). The interpreter implements none of it yet
— spec leads, implementation follows.
