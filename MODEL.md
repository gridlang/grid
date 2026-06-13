# Grid — The Model

> Built from the seed up, one layer at a time. This is the foundation the rest of the
> language derives from; we add a layer only once the one beneath it holds. It
> supersedes the older `design.md` (which crystallized a later, drifted syntax rather
> than the core model).
>
> 1. The Substrate — ownership = scope = purity  *(done)*
> 2. The Triad — `?` `#` `@` as the three ways scopes compose  *(done)*
> 3. Success and Nothing — `()` is the only nothing; every operator partial  *(done)*
> 4. Literals & Types — one symbol, one type  *(done)*
> 5. **The grafts** — defer, fallibles, streams  ← *you are here*

---

## 1. The Seed

Grid treats function purity not as a discipline you follow but as a fact that falls
out of a single decision: **a scope and an ownership boundary are the same thing.**

Most languages answer "what can this code reach?" (scope) and "who owns this data?"
(memory) with two separate systems. Grid answers them with one. A scope is the region
where a piece of data lives *and* the only region that can reach it. Purity is then
not a property you prove — it is the shape of the language.

Everything below is a consequence of taking that seriously.

## 2. Handles, not buckets

A label is a **handle** to data, not a bucket that contains it.

```
a = 1
```

`a` does not *hold* a `1`; it *points at* one. This is the Algol bucket turned inside
out, and it is what lets ownership and scope be one idea: you reason about who can
reach the data, never about where a value got copied to.

(An implementation is free to keep a small `int` in a register and a large structure
on the heap. That is an optimization. The model is always: a handle to data.)

## 3. The immutability hinge

The hard part of "handles to shared data" is mutation. If two handles point at one
thing and either can change it, you are back to aliasing, races, and the machinery —
borrow checkers, lifetimes — built to police them. Grid sidesteps the machinery with
a split it wants anyway: **immutable by default.**

**Immutable data is freely shared.** Because it cannot change, the difference between
"two handles to one value" and "two copies of one value" is *unobservable*. So
immutable handles are shared at will — at no cost, with nothing to track. For the
immutable majority of a program, everything is a pointer, and it is safe precisely
because nothing can write through it.

```
a = 1
b = a        // b and a are handles to the same 1 — indistinguishable from a copy
```

**Mutable data has exactly one handle.** A mutable value is marked with `&`, a symbol
chosen to *look like a handle gripping its data*. A `&` value is owned by one label at
a time. You cannot make a second handle to it; to get one you take your own owned copy.

```
c: &int = 1   // c is the single attached handle to a mutable 1
c += 1         // c now points at 2 — mutated in place, through the one handle
d: &int = c   // d is a NEW owned copy; c is untouched
```

> `&` is iconic, like the rest of Grid's symbols (`#` a grid, `@` a loop, `?` a fork):
> a little handle attached to the value, marking the one place a value may change.

The aliasing problem therefore never arises: shared things can't be written, written
things can't be shared.

## 4. Every scope is a holed block

There is one kind of scope: a **block** — a body together with its **holes**, the
handles that cross in from outside. A function is a block; the body of a `?`, `#`, or
`@` is a block; a bare `{ ... }` is a block. They differ only in *how they compose*
(next layer), never in how data enters them.

A block's holes are **inferred**, by a single rule applied everywhere — so you never
write a capture list, yet you can read any block and know exactly what crosses it,
because there is only ever one rule to run:

> For each name a block uses from outside itself —
> **read it** and the hole is a **share**: a free, read-only view;
> **write it** and the hole is a **move**: the handle moves in and moves back, and
> writing requires the name be `&`.

Reads share, writes move. That is the whole rule, identical for functions, `?`, `#`,
`@`, and bare blocks — so inference is never guesswork: there is no second case, no
context in which the same block would capture differently. Inferred *and* directly
knowable, because the rule is singular.

```
n = 4                // immutable
i: &int = 0          // mutable — the attached handle

@ i < n { i += 1 }    // i is written -> moved in/back;  n is read -> shared
                      // afterward i is 4 — the move brought it back
```

**Sited vs detached.** A `?`/`#`/`@` body or a bare block is *sited*: it sits
lexically inside an enclosing scope, so its holes are inferred from that scope. A
**function is detached**: named here and called elsewhere, with no enclosing locals at
its call sites — so it has nothing to infer from, and its inputs are its declared
parameters (its only ambient access is module constants, which are immutable, hence
shared). That is the entire function-vs-block difference: the same capture rule, but a
function has nothing to infer *from*.

```
push = (s: &Stack, v: int) -> () { s.data += v }

s: &Stack
s.push(10)           // s moves into push, is mutated, and moves back changed
```

(Grid has no closures — a function never captures enclosing locals. The job closures
usually do, carrying state between calls, is the stateful function's instead; layer 5.)

**Writes move, so parallelism is free.** A written hole is a *move*, and `#` opens many
blocks at once — one mutable cannot move into many — so a `#` body cannot write an
enclosing handle; it can only read (share) what is outside it, and independent reads
never race. `#` is parallel-safe by construction, and the racy program does not
compile. `@` opens one block at a time, so it *can* move a `&` accumulator in and
thread it through: that is reduce. Neither combinator carries a "parallel" or
"sequential" flag — it falls out of move meeting fan-out.

```
swap = (a: &int, b: &int) -> () { ... }
x: &int = 1
swap(x, x)           // error — x moves into a and is gone; it cannot also move into b
```

That last line is not a rule a checker enforces; it is simply impossible — a moved
handle is not there to be moved again.

## 5. What falls out

From "a scope is an ownership boundary," with the immutability hinge and move-in /
move-back, these are free — not features, but consequences:

- **Exclusivity without a checker.** A mutable value is reachable through one handle,
  ever. No borrows to track, no lifetimes to annotate, no checker to satisfy. The
  guarantee is structural.
- **Lifetime is scope.** Data lives exactly as long as the scope that owns it and is
  released when that scope ends. Nothing to garbage-collect, nothing to
  reference-count — the owning scope's exit *is* the free.
- **Purity by construction.** A scope can affect only what it was handed; the only way
  a call can change its caller's world is a `&` parameter, so effects are visible right
  in the signature.
- **Parallel-safe by construction.** Independent scopes that share immutable data and
  own disjoint mutable data cannot race — there is no shared writable state to race
  over. This is the property that lets one of the three combinators fan out across
  cores for free.

---

## Layer 2 — The Triad

Three combinators, three ways a block composes over an input: **`?` branches, `#` fans
out, `@` threads.** They share one shape —

```
input OP { pattern => result }
```

— where `{ … }` is a holed block (Layer 1) and the arms `pattern => result` match the
input. They differ only in how many blocks run and how those blocks relate. (*How* an
arm matches is Layer 3; here we fix what each operator does and what it yields.)

### `?` — branch

`?` matches the input and runs **one** block — the first arm that matches — yielding
that arm's result; if nothing matches, `()`.

```
x ? {
  0 => "zero"
  _ => "some"
}
```

`if`/`else`, `switch`, and guard-matching in one operator: one input, one chosen
block, one result.

### `#` — fan-out

`#` runs **one independent block per element** of the input and collects the results
into a list. A block that yields `()` contributes nothing — so the same operator
filters (an arm yields `()` to drop its element; *how* it decides is Layer 3).

```
doubled = nums # { n => n * 2 }     // map -> [2, 4, 6, …]
```

Each block is its own scope. By Layer 1 it may *read* (share) the surrounding scope but
cannot *write* it — a write is a move, and one handle cannot move into every parallel
block — so the blocks are independent and `#` runs them in parallel, safely, with no
annotation.

### `@` — thread

`@` runs **one block, in sequence, threaded over the input**, carrying state from step
to step. The state is nothing special: it is the captured `&` the block writes (Layer
1), moved in and back across the run.

```
sum: &int = 0
nums @ { n => sum += n }     // reduce — sum threads through; afterward it is the total
```

What you thread over decides the shape:

- a **collection** → the block runs once per element — **reduce**;
- a **condition** → the input is re-checked each step and the block runs while it holds
  — **loop**.

```
i: &int = 0
i < 4 @ { i += 1 }          // loop — runs while i < 4; afterward i is 4
```

Reduce and loop are not two constructs; they are `@` handed two kinds of input. Because
`@` is sequential, its block *may* write a captured `&` — which is precisely why the
accumulator needs no syntax of its own. (The bare infinite form `@ { … }` and
early-exit-with-a-value are Layer 3 — they need the truthiness machinery.)

### Why the three are one family

`#` and `@` are the *same* iteration over the *same* kind of block. The only difference
is **independent vs threaded** — and that is not a new axis; it is Layer 1's
**read-share** (safe in parallel) versus **write-move** (must run in sequence). The
substrate already drew the line; the triad just names both sides of it. `?` is the
degenerate case: zero-or-one blocks — choose one rather than repeat one.

This is the property worth keeping: behavior comes from *what you hand the operator* — a
collection or a condition, an arm that yields a value or `()`, a block that reads or
writes — never from flags or modes. Same combinators, composed.

### What each yields

| operator | runs | yields |
|---|---|---|
| `?` | one block (the matching arm) | that arm's result, or `()` |
| `#` | one block per element, in parallel | the list of non-`()` results |
| `@` | one block per step, threaded | its last block's value; accumulated state read from the moved-back `&` |

---

## Layer 3 — Success and Nothing

All of control flow rests on one distinction, and only one: a thing is either
**present** — some value, meaning "yes / it worked / here it is" — or it is **`()`**,
the one nothing (Layer 1), shared by every absence the language can express: false,
null, no-match, missing key, out of bounds, empty result, end of loop. There is no
`bool`, no truthiness table. There is *present*, and there is `()`.

### No bool

`false` was only ever "the nothing of the boolean type" — and the language already has
a universal nothing, so a second one is redundant. Grid removes `bool`: **failure is
`()`, and any present value is "true."** A test does not yield `true`/`false`; it
yields a value, or it yields nothing.

That is exactly what makes the conditional clean. A *failed* test is `()` (absent),
while a *value* like `0` is present — so "if x" never confuses "x is zero" with "x is
missing," the snag that sank the falsy-by-default idea:

```
n ? doThing        // runs if n is present — and a data 0 IS present
3 >= 5 ? doThing    // skipped — the test produced ()
```

### Every operator is partial

Once `()` is the universal failure, every operation that *might not have an answer*
just returns it. Operators are partial — each yields **a value, or `()`**:

```
xs[i]        // the element, or () if out of bounds
m["key"]     // the value,  or () if the key is absent
a / b        // the quotient, or () if b is 0
find(s, c)   // the index,  or () if not found
```

No exceptions, no `get-or-default`, no bounds ritual: a missing map key and a failed
`if` are the *same thing*, handled the same way. And a relation yields **its right
operand** on success, `()` on failure — so comparison *chains* by ordinary
left-to-right composition:

```
a < b < c      //  (a < b) < c :   1 < 2 < 3  ->  3  (holds) ;  1 < 5 < 3  ->  ()  (5<3 fails)
x == y == z    //  equal the whole way -> z, else ()
```

A relation is just an operator with a canonical result, no more special than `1 + 2`.

### `?` — try

`subject ? consequent` is the one conditional. If `subject` is **present**, it yields
`consequent` — evaluated with `subject` as the block's **topic** — otherwise `()`.

```
cond ? result               // result if cond succeeded, else ()
m["k"] ? { v => use(v) }     // v bound to the value if the key was there, else skip
m["k"] ? { v => use(v) } || fallback()   // ...or supply the absent case with ||
```

`?` is the `if`, the optional-unwrap of a `T | ()`, and the success-check over any
partial operator — one operator, because they were always one idea.

### `=>` — match, from the same machinery

`pattern => result` reads the **topic** the enclosing combinator set, and yields
`result` if the topic matches, else `()`. It is not new machinery — it is `==` and `?`
plus binding:

- a **literal** — `0 => r` is `(topic == 0) ? r`; since `==` is itself partial
  (right operand on success, `()` otherwise), this yields `r` exactly when the topic is `0`;
- a **name** — `n => r` **binds** the topic to `n` (always — never gated on its value)
  and yields `r`;
- `_ => r` always matches and binds nothing.

Because a non-match yields `()`, and a block keeps the first present arm (Layer 2),
**guards and matches compose in one block** — both are just value-or-`()` over the topic:

```
status ? {
  cached ? cached            // guard arm — yield `cached` if it is present
  200    => "ok"             // match arm — the topic (status) is 200
  code   => `error {code}`   // bind  arm — name the topic, use it
}                            // first present arm wins
```

And it answers "why does `x ? { 'lit' => z }` match against `x`": `?` made `x` the
topic, and `=>` reads it.

### What this dissolves

- **`&&` / `||` are selectors**, not boolean algebra: `a && b` yields `b` if `a` is
  present (else `()`); `a || b` yields `a`, or else `b`. Short-circuit by construction.
- **An optional is `T | ()`** — present *is* "some", `()` *is* "none." No `Option`, no
  presence flag; a present `0` and an absent `()` are distinct because `()` inhabits no
  other type (Layer 1's no-null).
- **A flag fuses with its payload.** "Set a bool, branch on it later" becomes a `T | ()`
  that is present exactly when the condition holds and carries what you'd act on:
  `running: Conn | ()` — present *is* running, and it hands you the connection. The bool
  was always a lossy shadow of the data.
- **No logical `!`** — invert the predicate (`a >= b`) or take the absent branch; the
  symbol is freed for later.

### The keystone

Present vs `()`. Every value is success; `()` is the only failure; every operator is
partial; `?` tries, `=>` matches, and the triad (Layer 2) reads off that single bit.
That is the whole of Grid's conditional and control story — no bool, no null, no
coercion, no exceptions. It is goal-directed evaluation — Icon's spine — made typed and
value-returning.

---

## Layer 4 — Literals and Types

One symbol, one type — in its true form: **the bracket tells you the container's shape,
and `:` tells you it is keyed.** You know what a literal is from its delimiters alone —
no context, no inference (A1). And `{ }` is freed entirely: it is a *block*, only ever a
block (Layers 1–2), so the brace ambiguity that haunts curly-brace languages cannot
arise here.

### Two containers, two axes

There are exactly two bracket families, split by shape:

- **`( … )` is fixed** — a set number of (possibly mixed) slots.
- **`[ … ]` is variable** — any number of (uniform) elements.

and each becomes *keyed* by adding `:` — the same `:` that annotates a type everywhere
else:

|  | positional | keyed (`key: value`) |
|---|---|---|
| **`( )` — fixed** | tuple `(1, "a")` | struct `(x: 1, y: 2)` |
| **`[ ]` — variable** | list `[1, 2, 3]` | map `["a": 1, "b": 2]` |

A struct is a *named tuple*; a map is a *keyed list* — one structuring move applied to
each container. The only difference between a struct key and a map key is what sits
left of the `:`: a struct's is an **identifier** — a field name, fixed in the type
(`(x: int)`); a map's is a **value** — a key, computed at runtime (`[k: v]`).

### Base types

| type | literal | default | note |
|---|---|---|---|
| `()` | `()` | `()` | unit — the one nothing (Layer 3) |
| `int` | `-123` | `0` | |
| `num` | `-1.23e4` | `0.0` | real |
| `char` | `'z'` | `'\0'` | a representable default, not the empty `''` |
| `str` | `"hello"` | `""` | |

No `bool` (Layer 3). (Sized numerics — `u8`, `i32`, … for layout and FFI — are a later
refinement; bare `int`/`num` for now.)

### Lists and maps — both `[ ]`, both indexed, both partial

```
xs = [1, 2, 3]            // [int]
m  = ["a": 1, "b": 2]     // [str: int]
xs[1]                      // 2,  or () if out of range
m["a"]                     // 1,  or () if absent      <- same [] access, same partiality (Layer 3)
[]                         // empty list
[:]                        // empty map (the : marks it keyed even when empty)
```

Type forms mirror the literals: `[T]` a list, `[K: V]` a map. Map keys are base-type
values (they must compare for lookup).

### Tuples and structs — both `( )`

```
p = (1, "a")              // (int, str) tuple;  p.0 -> 1
q = (x: 1, y: 2)          // (x: int, y: int) struct;  q.x -> 1
(x,)                       // a 1-tuple — `(x)` alone is just grouping
Point(x: 1)                // named-struct construction; absent fields take defaults
```

Type forms: `(A, B)` a tuple, `(name: T)` a struct. In a *type* position the right of a
`:` is a type; in a *value* position it is a value — which is how `(x: foo)` stays
knowable even though any label can name a type (labels-as-types, below).

### Unions and intersection

`|` is free now (the old match-`|` became `=>` arms), so it carries **union**:

```
T | ()                     // the optional — present is "some", () is "none" (Layer 3)
Shape | Color              // either type
```

`&` carries **structural intersection** — a value satisfying both:

```
Person   = (name: str, age: int)
Employee = Person & (id: int)     // has name, age, AND id
```

`&` is positional: a **prefix** `&T` is mutability (Layer 1, the attached handle); an
**infix** `A & B` on types is intersection (and on `int`s it is bitwise-and — separated
by value-vs-type position). A union's default is the default of its first member — so
`T | ()` defaults to `()`, which is exactly "absent."

### Labels as types, structural fit

Any label may stand as a type; the type is the label's:

```
coords = [1.0, 2.0, 3.0]   // [num]
origin: coords              // type [num], default []
```

And typing is structural: a value is accepted wherever it carries *at least* the
required shape — `(name: "Bo", age: 9, id: 1)` is a valid `Person`, because it has
`Person`'s fields.

---

## Layer 5 — The Grafts

The keystone is whole. What remains are the good late ideas — and the striking thing is
how few of them are *new machinery*: most are consequences of the four layers below,
finally named.

### Functions

A function is the named, **detached** scope of Layer 1: defined here, called elsewhere,
declaring all its inputs (no closures). Its parameters are a struct (Layer 4); its body
is a block whose last expression is its value.

```
add = (x: int, y: int) -> int { x + y }
add(1, 2)                                  // 3

double = (n: int) -> int { n * 2 }         // a value; the bare name IS the function
apply  = (f: (int) -> int, n: int) -> int { f(n) }
apply(double, 5)                           // 10
```

`x.f(a)` is `f(x, a)` (UFCS) — free functions read as methods on their first argument. A
function may be **partial** like any operator: `-> T | ()`, or fallible (below), and it
composes with `?` exactly as primitives do.

### Exits, without keywords

Every exit a language usually spends a keyword on is already here in present-vs-`()` and
the operators — so Grid keeps none of them.

- **return** — the body's last expression *is* the value. An early value-exit is `!`
  (below); there is no `return`.
- **break / continue** — in `@`, a body that yields a **present** value exits the loop
  with it; a body that yields `()` continues. So a body must produce `()` to loop again
  — which a binding or an in-place `+=` does naturally — and any real value ends it.
  `break value` is just "yield a present value"; `continue` is "yield `()`." A bare
  `@ { … }` is the infinite loop, ended the same way.

```
find = (xs: [int], t: int) -> int | () {
  xs @ { x => x == t ? x }     // match -> present x -> exit with x;  else () -> continue
}                              // run out -> () -> not found
```

No `break`, no `continue`, no `return`, and `find` reports "not found" as `()` — the
optional from Layer 3, not a sentinel.

### `~` — defer

Memory needs no cleanup keyword: lifetime is scope (Layer 1), so a value is freed when
its scope ends. `~` is for *effects* that aren't memory — closing a handle, flushing,
logging. `~expr` runs when the enclosing scope exits, however it exits, in LIFO order.

```
serve = (c: Conn) -> () ! Err {
  ~c.close()                   // runs on every exit path, after the rest
  greet(c)!
  pump(c)!
}
```

### `-> T ! E` — fallible, over `T | ()`

A no-information failure is already `-> T | ()` (Layer 3). When a failure must carry a
*reason*, `-> T ! E` is the shorthand: success is a `T`, failure carries an `E`, with the
error slot being an `E | ()` (present means failed). The postfix `!` consumes it:

```
read = (path: str)  -> str    ! Err { … }
load = (path: str)  -> Config ! Err {
  text = read(path)!           // T on success; on failure, load returns the Err
  parse(text)!
}

text, err = read(path)         // or take the pair by hand
```

`f()!` unwraps to `T` on success, or exits the enclosing function propagating the `E`.
(`!` is the symbol freed when logical-not left in Layer 3.)

### `>>` — stateful streams

A stateful function is defined with `>>`. Calling it returns a fresh stream **instance**;
`>> value` emits a value and suspends, resuming there on the next call. And exhaustion
needs no machinery at all — when the body completes, the stream just yields `()`:

```
each = (xs: [T]) >> T { xs @ { x => >> x } }   // emit each element, then finish -> ()

s = each([10, 20, 30])         // s : () -> T | ()
s()                             // 10, then 20, then 30, then () forever
```

So a stream is simply a function of type `() -> T | ()`, and it plugs straight into the
triad — `s @ { v => … }` runs until `()`, `s # { v => … }` collects until `()`. The
"done" flag and the presence pair both evaporate into the one nothing. (`>>` is
positional: after a parameter list it defines a stream, before a value it emits, between
two `int`s it is right-shift.)

### Sources — iteration is just "next, or `()`"

The same `()` that ends a stream ends *every* collection. Reaching past the end of a
list is `xs[len]` — out of bounds — which Layer 3 already makes `()`. So iteration needs
no length, no `hasNext`, no bounds check: you take the next, and stop when it is `()`.
This is `car`/`cdr` against `nil`, with `()` as the nil.

So a **source** is anything that yields *next-or-`()`* — a list, a tuple, a map, a
range, a stream alike — and the triad iterates any of them through that one interface:

- `@` threads over **any** source, one at a time, stopping at `()` — including a live
  stream;
- `#` fans out over a source whose elements are already present (list, tuple, map); a
  stream is drained first, since you cannot fan out what has not yet been produced.

A collection and a stream are the same thing to `?` `#` `@`: a source you pull from until
nothing comes back. (This is the third role `()` absorbs — failure, exhaustion, and now
end-of-iteration — and it is Icon's generators, the last of the three echoes.)

### Modules (in brief)

`module name` and `import path` at a file's head are the only declarations outside
expression space. Module-scope labels are constants — immutable, shared everywhere
(Layer 1). (A fuller treatment is its own document.)

---

### The whole model, in one breath

Five layers, each falling out of the one beneath:

1. a **scope is an ownership boundary** — handles, the immutability hinge, holes inferred
   by one rule;
2. the **triad** `?` `#` `@` — branch, fan-out, thread — is the three ways a scope
   composes;
3. **present vs `()`** — `()` the only nothing, every operator partial, `?` tries and
   `=>` matches off that single bit;
4. **one symbol, one type** — bracket is shape, `:` is keyed;
5. and the **grafts** — functions, defer, fallibles, streams — that mostly turn out to
   be consequences of the above.

No `bool`, no `null`, no exceptions, no garbage collector, no borrow checker, and — save
`module`/`import` — no keywords. Goal-directed evaluation given a body.

---

## Appendix — details pinned by the flagship

The HTTP-server flagship (`examples/http-server.grid`) forced these specifics. Each
*refines* a layer; none of them changes it.

- **Interpolation (L4).** A backtick string interpolates `{expr}`: `` `hello, {name}!` `` —
  carried from the original docs.
- **`#` / `@` step value (L2).** What a per-step block receives: a list yields
  `(index, element)`, a map `(key, value)`, a string `(index, char)`, a stream the
  emitted value — destructured in the arm, e.g. `# { (i, x) => … }`.
- **Destructuring patterns in `=>` (L3).** A pattern may be structural — a tuple
  `(a, b)`, a list `[a, b]`, a list with a rest `[first, ...]` — applied recursively:
  each position is a literal (match via `==`), a name (bind), or `_`, and the whole
  matches only if every position does.
- **`!` is the failure operator (L5).** It owns a `-> T ! E` function's error channel:
  `e!` *raises* (exit with `e` as the failure); `f()!` *forwards* (exit with `f`'s error
  if it failed, else unwrap the success `T`). Raise and propagate are one operator.
- **Unconsumed fallibles are allowed (L5).** A `T ! E` or `T | ()` result may simply be
  ignored — it is a value like any other (`handle(c, id)` does). No obligation to handle
  it; a linter may warn later.
- **Loop-continue is explicit (L2/L5).** An `@` body exits on a present value, so an
  effectful body ends in `()` to keep looping. No sugar — the `()` keeps the
  present-vs-nothing rule on the page. *(Decided, with evidence: the inverse rule —
  `()` exits, present continues — was prototyped and breaks reduce, find, while, and
  every effectful loop, because `()` is exactly what a continuing body produces.
  Present-exits is the load-bearing polarity: it gives find, break-with-value, and
  exit-on-condition for free. The body's value is control, by design.)*
- **Inline `;` (syntax).** A newline ends an expression; `;` is the same separator on a
  single line: `{ sys.print(e); 1 }`.
- **Precedence (provisional).** A `{block}` binds to the `?` / `#` / `@` on its immediate
  left as a tight unit; among the rest, tightest → loosest: `.` `[]` `()`, postfix `!`,
  prefix `&` / `~`, `* / %`, `+ -`, bitwise, `..`, comparison, `&&`, `||`, bare infix `?`.
  So `err ? {…} || 0` parses as `(err ? {…}) || 0`. The interpreter will fix this exactly.
