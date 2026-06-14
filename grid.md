# Grid — Sharpened Working Spec

*Status: standalone synthesized direction for the next Grid spec pass. This document folds the
current mdBook model, `lambdas.md`, the interpreter validation slices, and the later thought
experiment into one working reference. It is intentionally spec-forward: implementation and
older docs should be migrated toward this model.*

---

## 0. The whole model

Grid is a typed, systems-oriented descendant of Icon built on one distinction:

```text
present value  vs  ()
```

`()` is the only nothing. There is no `bool`, no `null`, no `Option`, no truthiness, and no
implicit exception channel for ordinary absence. Every operation that may fail is partial:
it yields a value or `()`.

```grid
xs[i]        // element, or () if out of bounds
m[k]         // value, or () if missing
a / b        // quotient, or () if b is 0
a < b        // b if relation holds, else ()
```

A present `0`, `""`, `[]`, or `[:]` is still present. Only `()` is absent.

The core concepts are:

| Concept | Meaning |
|---|---|
| **value** | present data or `()` |
| **place** | storage that can be stored through |
| **body** | code applied to one current argument, written `_` |
| **driver** | an operator that applies bodies: `?`, `#`, `@` |
| **fallible** | a value/error pair consumed by postfix `!` |

In one line:

```text
present/() values · T/&T/*T places · _ bodies · ?/#/@ drivers · ! failures
```

---

## 1. Values and partiality

Every expression yields a value. The value may be `()`.

```grid
10 / 2          // 5
10 / 0          // ()
["a": 1]["a"]  // 1
["a": 1]["b"]  // ()
```

Relations yield their **right operand** on success and `()` on failure:

```grid
1 < 2           // 2
2 < 1           // ()
1 < 2 < 3       // 3
1 < 5 < 3       // ()
```

This is how comparisons chain without a separate boolean type.

Selectors are value selectors:

```grid
a && b          // b if a is present, else ()
a || b          // a if a is present, else b
```

`||` is never an else. It defaults a value result. Branching is `?:`.

```grid
config || default_config        // first-present selector
cond ? then : else              // branch chosen by cond's presence
```

---

## 2. Places and storage

A label is a handle, not a bucket. There are two distinct operations:

```grid
x := value       // introduce a label
x = value        // store through an existing writable/effectful place
```

`:=` introduces. `=` never introduces.

```grid
n := 1                         // immutable value label
count: &int := 0                // Grid-owned mutable place
status: *u32 := mmio.u32(A)     // effectful external cell/register

count = 5
count += 1
status |= ENABLE
```

All label-introduction and store-through forms yield `()`:

| Form | Meaning | Result |
|---|---|---|
| `x := expr` | introduce immutable label | `()` |
| `x: T := expr` | introduce typed label | `()` |
| `x: T` | introduce typed label at default | `()` |
| `x = expr` | store through existing writable/effectful place | `()` |
| `x += expr` etc. | read / compute / store through existing place | `()` |
| `a, b := expr` | destructure and introduce labels | `()` |
| `a, b = expr` | destructure and store into existing places | `()` |

This is intentional. Mutation is an effect. Returning `()` means mutation naturally
continues an ordered `@` drive:

```grid
sum: &int := 0
1..5 @ (sum += _)       // += yields (), so @ continues through all values
sum                     // 15
```

If a store can fail, it must use an explicit fallible API or a future fallible-store rule.
A successful store already returns `()`, so an indexed store cannot also silently report
failure as `()` without losing information.

---

## 3. Storage capabilities: `T`, `&T`, `*T`

Grid has three storage capabilities.

| Type form | Meaning | Reads | Writes | Sharing / capture |
|---|---|---|---|---|
| `T` | immutable value handle | effect-free | impossible | freely shareable; escapable |
| `&T` | Grid-owned mutable place | read-view, effect-free but sited | effecting write through owner | one write handle; read-views do not escape |
| `*T` | exclusive effectful external cell | effecting | effecting | unshareable; always sited |

`*T` is not raw C pointer syntax. Raw addresses are ordinary values; touching memory
requires constructing a typed handle:

```grid
addr: usize := 0x40001000
ctrl: *u32 := mmio.u32(addr)
```

Reading a `*T` is an effect. Writing a `*T` is an effect.

```grid
ready := ctrl & READY != 0       // effectful read + explicit bit test
ctrl = ENABLE | IRQ              // effectful write
```

Because Grid has no truthiness, a bitwise result is not a condition by itself. `0` is a
present value. Test masks explicitly:

```grid
x & MASK != 0
```

---

## 4. Bodies and the current argument `_`

A **body** is code applied to one current argument. That argument is written `_`.

```grid
nums # (_ * 2)
m["host"] ? str.upper(_) : "none"
```

`_` is not a fresh parameter per occurrence. Multiple `_` in one body are the same value:

```grid
nums # (_ * _)        // square each element
```

`_` requires a binder/driver. It is valid only where a body is being applied or defined.
In ordinary value position, reify a lambda explicitly:

```grid
double := _ => _ * 2
```

The current argument is **frozen for that body level**. Plain statements do not retarget it.
Nested body applications introduce nested current arguments that shadow the outer `_`.
Name the outer value if you need it inside a nested body:

```grid
points # (p => {
  neighbors(p) # (q => distance(p, q))
})
```

Named functions are explicit-parameter territory. Function parameters do not implicitly
bind `_`:

```grid
inc := (n: int) -> int { n + 1 }
// bad := (n: int) -> int { _ + 1 }       // no current argument here

scaleAll := (xs: [int]) -> [int] { xs # (_ * 2) }   // inner # binds _
```

---

## 5. Lambdas, blocks, and captures

Bodies are lambdas. The language has several body forms:

| Form | Meaning |
|---|---|
| `_ => body` | explicit current-argument lambda |
| `pat => body` | pattern body / pattern lambda |
| `{ item; item; expr }` | sequence body / block lambda |
| `(params) -> T { ... }` | named function, explicit params, no implicit `_` |
| `(params) -> T ! E { ... }` | fallible named function |
| `(params) >> T { ... }` | stateful stream function |
| bare expression in a body slot | body sugar; the driver supplies `_` |

A body may become an escaping value only if its captures allow it.

| Capture/use | Escaping lambda value? |
|---|---|
| no capture | yes |
| immutable value `T` | yes; captured into the lambda's own immutable environment |
| `&T` read-view | no; sited only |
| `&T` write | no; sited only |
| any `*T` read/write | no; sited only |

Grid therefore has closures, but only immutable ones. More precisely:

> Escaping lambdas never borrow local handles. Immutable captures are copied/shared into the
> lambda value's own immutable environment. Mutable and effectful captures are sited only.

So the programmer does not reason about lifetime. Scope remains lifetime/ownership for
places; immutable closure environments are just immutable values.

```grid
scale := 10
f := _ => _ * scale              // ok: immutable environment

sum: &int := 0
1..5 @ (sum += _)                // ok: sited ordered body
// g := _ => sum += _            // error as escaping value

reg: *u32 := mmio.u32(STATUS)
// ready := _ => reg & READY     // error as escaping value: effectful read capture
```

Drivers may run sited bodies when their execution mode can honor the effects:

- `?` applies at most one body, so it may run sited/effectful code in place.
- `@` is ordered and sequential, so it may run mutable/effectful bodies.
- `#` is fan-out; it may run pure/value bodies and parallel-safe read-only bodies, but must
  not write-move `&` captures or touch `*` handles.

---

## 6. Sequence blocks

A block is one sequence body:

```grid
{
  item
  item
  item
}
```

Rules:

- items run in order in one scope;
- labels introduced by earlier items are visible to later items;
- non-final non-committing values are discarded;
- the current argument `_`, if one exists, is frozen for the body level;
- plain statements do not retarget `_`;
- if no item commits early, the block's value is the final item's value;
- a final missing value is a real `()` result.

There is no topic-threading rule. To dispatch on a computed value, make that value the
subject of a nested driver:

```grid
str.upper(raw) ? {
  "GET"  => "read"
  "POST" => "write"
  _      => "unknown"
}
```

### Body position vs value position

A `{ ... }` in **body position** is the body to run when the surrounding driver/arm applies
it:

```grid
status ? {
  200 => { ok += 1 }
}
```

The inner block runs if the `200` arm matches.

A `{ ... }` in **value position** is a block-lambda value if its captures are escapable:

```grid
double := { _ * 2 }
double(5)        // 10
```

This distinction keeps ordinary effectful arms readable while still allowing blocks to be
first-class when safe.

---

## 7. Pattern bodies and commit

`pat => body` is a pattern body. It may appear as a body by itself, or as an item inside a
sequence body. It is not restricted to a special `match` block.

When evaluated with a current argument:

- if `pat` does not match the current argument, the pattern body yields `()` and sequence
  continues;
- if `pat` matches, its body runs and **commits the nearest enclosing sequence body** with
  that result;
- commit is keyed on the match, not on whether the result is present.

So effectful arms are concise:

```grid
ok: &int := 0
other: &int := 0

status ? {
  200 => ok += 1       // += yields (), but the arm still commits
  _   => other += 1
}
```

A sequence may freely interleave ordinary statements and pattern bodies:

```grid
status ? {
  setup()

  200 => ok += 1

  log("not 200", _)

  404 => missing += 1
  500 => retry()

  log("unhandled", _)
  _ => other += 1
}
```

Here `_` is the same frozen `status` throughout the block. `setup()` and `log()` do not
retarget it. A matching `=>` commits immediately and skips later items.

This preserves the important property: dispatch is a common style of sequence block, not a
separate kind of block.

---

## 8. Patterns and destructuring

A pattern matches the current argument and may bind names. Destructuring names parts; it
does not change `_`.

Common pattern forms:

| Pattern | Matches | Binds |
|---|---|---|
| literal — `0`, `"GET"`, `'z'` | equal value | nothing |
| name — `x`, `code` | anything | the whole argument |
| `_` | anything | nothing |
| `()` | unit/nothing | nothing |
| tuple — `(p, q)` | tuple/struct by position | positions |
| list — `[p, q]` | list of exact length | positions |
| list rest — `[p, ...]` | list of at least that length | leading positions |

Examples:

```grid
point ? {
  (0, 0) => "origin"
  (x, 0) => `x-axis at {x}`
  (0, y) => `y-axis at {y}`
  (x, y) => `{x}, {y}, whole={_}`
}
```

Inside the final arm:

- `_` is still the whole point;
- `x` and `y` are names bound by the pattern;
- destructuring did not retarget `_`.

Structs are named tuples. Positional tuple patterns match structs by field order:

```grid
req ? {
  ("GET", path, body)  => handleGet(path)
  ("POST", path, body) => handlePost(path, body)
  _                    => notFound(_)
}
```

Named-field pattern syntax remains a design item to pin down carefully because `:` is also
used for annotations, keyed values, keyed iteration, and `?:`.

A relation is not a pattern. Tests are written with `?` / `?:`:

```grid
n >= 90 ? "A" : n >= 80 ? "B" : n >= 70 ? "C" : "F"
```

not as relational `=>` arms.

---

## 9. The drivers: `?`, `#`, `@`

The triad applies bodies to values/sources.

```text
?   zero-or-one application
#   all successes
@   first success, ordered
```

### 9.1 Try / branch: `?` and `?:`

`subject ? then` applies `then` if `subject` is present. The current argument inside `then`
is the subject value. If the subject is `()`, the result is `()`.

```grid
m["host"] ? str.upper(_)        // if-let
```

`subject ? then : else` runs exactly one side, chosen by the subject's presence. The
decision is made on the subject, not on the result of `then`.

```grid
m["host"] ? str.upper(_) : "none"
```

The else branch is a body too; its current argument is `()`.

```grid
m["host"] ? str.upper(_) : fallback(_)
```

`?:` is the real if/else. `||` remains a pure first-present selector.

```grid
a || default        // preserve polarity: a if present, else default
a ? () : default    // invert: () if present, else default
a ? marker : ()     // present -> marker, absent -> ()
```

### 9.2 Fan-out: `#`

`source # body` applies `body` independently to every value in the source and collects every
present body result. A `()` body result contributes nothing.

```grid
nums # (_ * 2)                         // map
nums # (n => n % 2 == 0 ? n)           // filter
keys # (k => m[k])                     // partial map: missing keys drop
```

So `#` means **all successes**.

`#` is naturally parallel. A `#` body must not write captured `&` places or touch `*` cells.
It may read immutable values and parallel-safe read-only views.

### 9.3 Thread / ordered search: `@`

`source @ body` applies `body` sequentially. A `()` body result continues. A present body
result exits the drive with that value. If the source exhausts with no present result, `@`
yields `()`.

```grid
sum: &int := 0
nums @ (sum += _)                      // reduce; += returns (), so continue

nums @ (n => n * n > 40 ? n)           // find first n whose square exceeds 40
```

So `@` means **first success, ordered**.

This is the Icon heart of the language:

```text
# collects every success.
@ stops at the first success.
() drops/continues.
```

A literal block as `@`'s source is a re-evaluated generator/thunk source — the loop/while
form:

```grid
i: &int := 0
{ i < 3 } @ (i += 1)
i                                  // 3
```

The block source is re-run until it yields `()`. The body runs once for each present pulled
value.

---

## 10. Keyed iteration

Every iteration step has two channels:

- value channel;
- key channel.

The current argument `_` is the **value** channel. Use `key_pattern : value_pattern` to
expose the key/index as well.

| source | key | value / `_` |
|---|---|---|
| list | index | element |
| tuple | index | element |
| string | index | char |
| range | offset from start | range element |
| map | map key | map value |
| stream/generator | pull count | emitted/yielded value |

Examples:

```grid
nums # (_ * 2)                         // values
nums # (i: x => `{i}: {x}`)            // index + value

m # _                                  // map values
m # (k: _ => k)                        // map keys
m # (k: v => `{k}={v}`)                // map entries
m # ("host": v => v)                  // literal key pattern

pts # ((x, y) => x + y)                // value is a tuple
pts # (i: (x, y) => `{i}: {x + y}`)    // key + destructured value
```

The keyed pattern names parts of the step. It does not retarget `_`.

```grid
prices # (name: price => `{name}: {price}, raw={_}`)
```

Inside the body:

- `name` is the key;
- `price` is the value bound by the value pattern;
- `_` is the same value as `price`.

`key: value` is iteration-scoped. It is valid only for bodies driven by keyed sources
(`#` / `@`). A `?` subject is a plain value with no key channel; match key/value pairs there
as tuples or structs instead.

---

## 11. Fallibles and `!`

`!` is the failure-channel exit. It is not logical-not, not pointer syntax, not a storage
operator, and not a bit-test operator.

A fallible function:

```grid
read := (path: str) -> str ! Err { ... }
```

returns conceptually:

```text
(value: T | (), error: E | ())
```

On success the value is present and the error is `()`. On failure the value is `()` and the
error is present.

Postfix `!` has two related meanings:

- `f()!` unwraps the value on success or propagates the error from the enclosing fallible
  function;
- `e!` raises plain value `e` as the current function's error.

```grid
load := (path: str) -> Config ! Err {
  text := read(path)!
  parse(text)!
}

text, err := read(path)        // take the pair by hand
```

The clean split:

| Mechanism | Exits on | Carries |
|---|---|---|
| `@` | first present success | value |
| `!` | failure/error | error |
| `()` | absence/no result | nothing |

Example combining search and real errors:

```grid
firstValid := (lines: [str]) -> Record | () ! Err {
  lines @ (line => {
    rec := parse(line)!     // real error exits via !
    valid(rec) ? rec        // valid exits @; invalid yields () and continues
  })
}
```

Do not use `!` to encode ordinary successful search. `@` already exits on success; `!` is
for failures.

---

## 12. Streams and emit

A stream function is defined with `>>` after its parameter list. Calling it returns a fresh
stream instance. Prefix `>> value` emits a value and suspends; when the body finishes, the
stream yields `()` forever.

```grid
each := (xs: [T]) >> T {
  xs @ (x => >> x)
}

s := each([10, 20, 30])
s()        // 10
s()        // 20
s()        // 30
s()        // ()
```

`>> value` is an effect and yields `()`, so it naturally continues an `@` drive.

Streams are sources. `@` consumes them in order. `#` may drain/materialize a stream before
fan-out if the implementation supports that mode.

---

## 13. Defer

`~expr` defers an effect until the enclosing scope exits, in LIFO order.

```grid
serve := (c: Conn) -> () ! Err {
  ~c.close()
  greet(c)!
  pump(c)!
}
```

`~` remains defer. Do not use it for bitwise complement.

Like other effect forms, defer yields `()`.

---

## 14. Containers and structural types

The delimiter tells you the container shape; `:` marks keyed structure.

| | positional | keyed |
|---|---|---|
| fixed | tuple `(1, "a")` | struct `(x: 1, y: 2)` |
| variable | list `[1, 2, 3]` | map `["a": 1, "b": 2]` |

Type forms mirror value forms:

```grid
(int, str)          // tuple type
(x: int, y: int)    // struct type
[int]               // list type
[str: int]          // map type
```

A struct is a named tuple. A map is a keyed list.

A label that names a struct type is callable as a constructor. Absent fields take defaults:

```grid
Point := (x: int, y: int)
p := Point(x: 1)        // y defaults to 0
```

Unions are structural:

```grid
T | ()                  // optional: present or absent
Circle | Rect
```

Intersections are structural:

```grid
Employee := Person & (id: int)
```

`&` is positional:

- prefix in type position: `&T` mutable place capability;
- infix in type position: `A & B` intersection;
- infix in value position: bitwise-and on integers.

---

## 15. Generics and type labels

Generics are implicit type labels for now:

```grid
id := (x: T) -> T { x }
Pair := (a: A, b: B)
Stack := (data: [T])
```

An unbound label in type position is a type variable, unified at use sites.

`<...>` remains reserved for possible explicit generics/bounds later:

```grid
id<T> := (x: T) -> T { x }
Map<K, V> := [K: V]
```

Enums / ADTs are structural unions. Tagged variants use literal tag fields:

```grid
Circle := (kind: "circle", r: num)
Rect   := (kind: "rect", w: num, h: num)
Shape  := Circle | Rect
```

Same-shape variants collapse structurally; tags distinguish shapes when needed.

Singleton literal types are in scope, but raw int-literal unions remain an open grammar item
because `200 | 404` collides visually with value-level bitwise `|`.

---

## 16. Native and low-level direction

Expected sized types:

```grid
i8 i16 i32 i64
u8 u16 u32 u64
isize usize
f32 f64
```

`int` and `num` remain ergonomic defaults.

Rules:

- no implicit numeric coercions;
- checked conversions are partial (`u8(256)` -> `()`);
- sized arithmetic is checked/partial by default;
- wrapping/saturating/reinterpret operations are explicit;
- bitwise ops are ordinary value ops;
- mask tests must compare explicitly because `0` is present;
- `*T` is the effectful cell capability for MMIO / volatile / atomic / foreign cells;
- raw addresses are not dereferenceable without constructing a typed handle.

Open low-level items:

- exact aliases (`int = isize?`, `num = f64?`);
- wrapping operator spelling;
- bitwise complement spelling, not `~`;
- raw-address and typed-handle construction APIs;
- fallible indexed/map store policy;
- layout / ABI / packed structs / alignment / endian operations;
- atomics and memory-ordering surface.

---

## 17. Operator roles and precedence

Tightest to loosest, conceptually:

| Level | Operators | Role |
|---|---|---|
| 1 | `.`, `[]`, call `()`, postfix `!` | member, index, call, fallible consume |
| 2 | prefix `-` | unary minus |
| 3 | `*`, `/`, `%` | arithmetic |
| 4 | `+`, `-` | arithmetic / string concat |
| 5 | `&`, `|`, `^`, `<<`, `>>` | bitwise |
| 6 | `..` | inclusive range |
| 7 | `==`, `!=`, `<`, `<=`, `>`, `>=` | relations, right operand on success |
| 8 | `#`, `@` | drivers |
| 9 | `&&` | selector |
| 10 | `||` | first-present selector |
| 11 | `=>` | pattern body / commit |
| 12 | `?:` | branch, loosest, right-associative |

Statement-edge / body-edge prefixes:

- `~expr` defer;
- `>>expr` emit.

Storage forms are body/item expressions yielding `()`:

```grid
x = expr
x += expr
x |= expr
```

Worked consequences:

```grid
a || b ? c : d        // (a || b) ? c : d
cond ? xs # f : ys    // cond ? (xs # f) : ys
a ? b : c ? d : e     // a ? b : (c ? d : e)
1 < 2 < 3             // (1 < 2) < 3
f() ? x => g(x) : h() // then body is x => g(x); else body is h()
```

---

## 18. Idioms

### If-let

```grid
m["host"] ? str.upper(_) : "none"
```

The value you want is the subject, so point-free is natural.

### Dispatch

```grid
status ? {
  200 => ok += 1
  404 => missing += 1
  _   => other += 1
}
```

Effectful arms commit on match even though assignment returns `()`.

### Compute then dispatch

```grid
str.upper(raw) ? {
  "GET"  => "read"
  "POST" => "write"
  _      => "unknown"
}
```

Make the computed value the subject. Plain statements do not retarget `_`.

### Map

```grid
nums # (_ * 2)
1..10 # (_ * _)
```

### Filter

Name the element because the inner `?` rebinds `_` to its subject:

```grid
nums # (n => n % 2 == 0 ? n)
```

### Reduce

```grid
sum: &int := 0
nums @ (sum += _)
```

### Find

```grid
nums @ (n => n * n > 40 ? n)
```

### Loop

```grid
i: &int := 0
{ i < 3 } @ (i += 1)
```

### Keyed iteration

```grid
str.lines(req.body) # (i: line => `{i + 1}: {line}\n`)
prices # (_ * 2)
prices # (name: price => `{name}: {price}`)
prices # (name: _ => name)
```

### Ordered work with abort-on-error

```grid
run := (items: [Item]) -> () ! Err {
  items @ (item => process(item)!)
}
```

`process(item)!` succeeds with `()`, so `@` continues. A real error exits through `!`.

---

## 19. What changed from the older mdBook model

Kept:

- `()` as the only nothing;
- no bool/null/Option/truthiness;
- partial operators;
- relations yielding the right operand;
- `||` as pure first-present selector;
- `?:` as real branch;
- `=>` commit-on-match;
- `#` all-success collection;
- `@` first-success ordered search;
- postfix `!` as fallible raise/propagate;
- prefix `~` as defer.

Changed / sharpened:

- `:=` introduces labels;
- `=` stores through existing places;
- store-through forms yield `()`;
- storage capability split is `T` / `&T` / `*T`;
- bodies/lambdas are central;
- `_` is the current body argument;
- the current argument is frozen per body level;
- plain sequence statements no longer retarget `_`;
- `=>` may appear anywhere in a sequence body, but it matches the frozen argument;
- blocks are sequence bodies, not special case sets;
- `{ ... }` in body position runs; `{ ... }` in value position reifies if escapable;
- escaping lambdas capture only immutable values;
- mutable/effectful captures are sited only;
- iteration value channel is `_`;
- key/index channel is `k: v`;
- `(index, value)` step tuples are no longer the default model;
- no core `.enum`, `.keys`, or `.values` are needed.

---

## 20. Deferred items

Items that need precise design before the full mdBook/compiler spec is final:

1. **Escaping immutable environment representation.**
   Source semantics are clear: immutable captures become part of the lambda value and never
   borrow local handles. Implementation may copy, share, promote, refcount, or otherwise
   manage immutable environments mechanically.

2. **Exact body/value grammar.**
   Especially forcing lambda reification in body slots, if direct syntax is needed beyond
   binding the lambda to a label first.

3. **Named-field patterns.**
   Structs already destructure positionally. Named-field pattern syntax should be designed
   carefully around `:` overload with keyed iteration and `?:`.

4. **Indexed/member store.**
   `buf[i] = byte` and `m[k] = v` need a fallibility policy because successful store returns
   `()`.

5. **User combinators with sited bodies.**
   Ordinary function parameters accept escapable lambda values. A future inline/noescape
   body-parameter feature may allow user-defined combinators to drive mutable/effectful
   sited bodies.

6. **Exhaustiveness warnings.**
   A dispatch with no matching arm yields `()`; warnings for missing `_` / non-exhaustive
   coverage are a tooling/spec item.

7. **Low-level details.**
   Sized-type aliases, wrapping syntax, bitwise complement, raw handle APIs, atomics,
   layout/ABI, endian/alignment.

---

## 21. Final compact statement

Grid is a language where:

- absence is the value `()`;
- operations compose by returning present values or `()`;
- places make mutation/effects visible as `T`, `&T`, or `*T`;
- `:=` introduces and `=` stores;
- bodies receive one frozen current argument `_`;
- `=>` destructures/matches that argument and commits on match;
- `?` applies a body to zero or one value;
- `#` collects all present body results;
- `@` runs ordered bodies until the first present result;
- `!` exits through the failure channel;
- stores, emits, defers, and other continuing effects yield `()`.

That is typed goal-directed systems programming with explicit storage and one nothing.
