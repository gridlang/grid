# From the Seed

> **Layer 5 of the model.** The core is complete; what remains are the features a working
> language needs — functions, defer, error handling, streams. The striking thing is how few
> are *new machinery*: most fall out of the four layers below.

## Functions

A function is the named, [**detached**](holes.md#sited-vs-detached) scope of Layer 1:
defined here, called elsewhere, declaring all its inputs (no closures). Its parameters are a
[struct](types.md#tuples-and-structs--both--); its body is a block whose last expression is
its value.

```grid
add = (x: int, y: int) -> int { x + y }
add(1, 2)                                  // 3

double = (n: int) -> int { n * 2 }         // a value; the bare name IS the function
apply  = (f: (int) -> int, n: int) -> int { f(n) }
apply(double, 5)                           // 10
```

`x.f(a)` is `f(x, a)` — **UFCS**, so free functions read as methods on their first
argument (`5.double()` is `double(5)`). A function may be **partial** like any operator
(`-> T | ()`), or fallible (below), and it composes with `?` exactly as primitives do.

## Exits without keywords

Every exit a language usually spends a keyword on is already here in present-vs-`()` and the
operators — so Grid keeps none of them.

- **return** — the body's last expression *is* the value. An early value-exit is `!`
  (below); there is no `return`.
- **break / continue** — in [`@`](triad.md#thread), a body that yields a **present** value
  exits the loop with it; a body that yields `()` continues. So a body must produce `()` to
  loop again — which a binding or an in-place `+=` does naturally — and any real value ends
  it. `break value` is "yield a present value"; `continue` is "yield `()`." A bare `@ { … }`
  is the infinite loop, ended the same way.

```grid
find = (xs: [int], t: int) -> int | () {
  xs @ { (_, x) => x == t ? x }   // match -> present x -> exit;  else () -> continue
}                                 // run out -> () -> not found
```

No `break`, no `continue`, no `return`, and `find` reports "not found" as `()` — the
[optional](match.md#what-this-dissolves), not a sentinel. (This rests on an invariant:
every continuing form — a binding, a `+=`, an emit `>>`, a defer `~` — yields `()`, so a
reduce/loop body already loops by nature. The one discipline: if an effectful body's *last*
expression would be present, end it with `()` so it doesn't exit early.)

## Defer

Memory needs no cleanup keyword: [lifetime is scope](holes.md#what-falls-out), so a value is
freed when its scope ends. `~` is for *effects* that aren't memory — closing a handle,
flushing, logging. `~expr` runs when the enclosing scope exits, however it exits, in LIFO
order.

```grid
serve = (c: Conn) -> () ! Err {
  ~c.close()                   // runs on every exit path, after the rest
  greet(c)!
  pump(c)!
}
```

## Fallibles

A no-information failure is already `-> T | ()` ([Layer 3](present.md)). When a failure must
carry a *reason*, `-> T ! E` is the shorthand. Concretely a fallible result is a **pair** —
a value `T | ()` and an error `E | ()`: on success the value is present and the error is
`()`; on failure the reverse. The postfix `!` consumes that pair:

```grid
read = (path: str)  -> str    ! Err { … }
load = (path: str)  -> Config ! Err {
  text = read(path)!           // T on success; on failure, load returns the Err
  parse(text)!
}

text, err = read(path)         // or take the pair by hand
```

`!` has two jobs, both about the error channel:

- `f()!` — **forward**: unwrap to `T` on success, or exit the enclosing function propagating
  `f`'s error;
- `e!` — **raise**: exit with the plain value `e` as the failure (`"bad input"!`).

Raise and propagate are one operator. (`!` is the symbol freed when logical-not was dropped
in [Layer 3](match.md#what-this-dissolves).) An unconsumed `T ! E` or `T | ()` may simply
be ignored — it is a value like any other; a linter may warn later.

## Streams

A stateful function is defined with `>>`. Calling it returns a fresh stream **instance**;
`>> value` emits a value and suspends, resuming there on the next call. Exhaustion needs no
machinery — when the body completes, the stream just yields `()`:

```grid
each = (xs: [T]) >> T { xs @ { (_, x) => >> x } }   // emit each element, then finish -> ()

s = each([10, 20, 30])         // s : () -> T | ()
s()                            // 10, then 20, then 30, then () forever
```

So a stream is simply a function of type `() -> T | ()`, and it plugs straight into the
[triad](triad.md) — `s @ { v => … }` runs until `()`, `s # { v => … }` collects until `()`.
The "done" flag and the presence pair both evaporate into the one nothing. This is the job a
[closure](holes.md#sited-vs-detached) does elsewhere — carrying state between calls — made
explicit, with no captured environment to keep alive. (`>>` is positional: after a parameter
list it defines a stream, before a value it emits, between two `int`s it is right-shift.)

## Sources

The same `()` that ends a stream ends *every* collection. Reaching past the end of a list is
`xs[len]` — out of bounds — which [Layer 3](present.md#every-operator-is-partial) already
makes `()`. So iteration needs no length, no `hasNext`, no bounds check: you take the next,
and stop when it is `()`. This is `car`/`cdr` against `nil`, with `()` as the `nil`.

A **source** is therefore anything that yields *next-or-`()`* — a list, a tuple, a map, a
range, a stream alike — and the triad iterates any of them through that one interface:

- `@` threads over **any** source, one at a time, stopping at `()` — including a live
  stream;
- `#` fans out over a source whose elements are already present (list, tuple, map); a stream
  is drained first, since you cannot fan out what has not yet been produced.

A collection and a stream are the same thing to `?` `#` `@`: a source you pull from until
nothing comes back.

## Modules

`module name` and `import path` at a file's head are the only declarations outside
expression space — the two keywords the language keeps. Module-scope labels are constants:
immutable, shared everywhere ([Layer 1](holes.md#sited-vs-detached)).

```grid
module main
import str
import sys

main = (args: [str]) -> int {
  sys.println(str.upper("ready"))
  0
}
```

A fuller treatment of modules and the standard library will accompany the implementation.

---

That is the whole model: a [scope is an ownership boundary](substrate.md); the
[triad](triad.md) is the three ways a scope composes; [present vs `()`](present.md) is the
one bit it all reads; [one symbol, one type](types.md); and the features above, which mostly
turn out to be consequences of the rest. From here, the [Reference](ref/grammar.md) pins the
exact syntax, and [In Practice](examples/tour.md) puts it to work.
