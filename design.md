# Grid Language Design

## Philosophy

Grid is a systems language built around a small number of composable, orthogonal ideas:

- **Every literal is directly knowable** — the type of any literal is unambiguous from its syntax alone, without context or inference
- **All syntax is symbolic** — no reserved keywords; control flow and semantics are expressed entirely through operators
- **Everything is an expression** — every construct produces a value; blocks, pattern arms, and flow operators all evaluate to something
- **Immutable by default** — mutation is explicit and visible at the type level
- **Value semantics** — no references; everything is copied. The compiler may optimize this, but the programmer's mental model is always "copy"
- **Labels, not variables** — a name is a label attached to a value, not a bucket containing one

---

## Labels and Mutability

A label binds a name to a value. The type is inferred from the value if not provided.

```go
a = 1          // immutable int, type inferred
b: int         // immutable int, explicit type, default value (0)
c: &int        // mutable int, default value (0)
d: &int = 5   // mutable int, initialized to 5
```

Types are **immutable by default**. The `&` prefix makes a type mutable. Mutability is part of the type and must match wherever a specific type is required.

```go
a = 1          // immutable
a = 2          // not allowed

b: &int = 1   // mutable
b = 2          // allowed

c: &int = a   // copies a's value into a new mutable label
// a is still 1
```

If no value is given for an immutable label, it holds the type's default value permanently.

---

## Types

All types have a default value. The default is what a label holds when no value is given, and defines the type's **falsy** state (see Truthiness).

### Base Types

| Type | Literal | Default | Description |
|------|---------|---------|-------------|
| `()` | `()` | `()` | Unit — the empty tuple, one possible value |
| `bool` | `true` | `false` | Boolean |
| `int` | `1` | `0` | Integer |
| `num` | `-1.23` | `0.0` | Real number |
| `char` | `'z'` | `''` | UTF-8 character |
| `str` | `"hello"` | `""` | String |

### Composite Types

| Type Pattern | Example | Default | Description |
|---|---|---|---|
| `{label: type}` | `{x: int, y: int}` | `{field: default}` | Struct |
| `{type -> type}` | `{str -> int}` | `{() -> ()}` | Map |
| `[type]` | `[int]` | `[()]` | List |
| `(type, ...)` | `(int, str)` | `((), ...)` | Tuple |
| `(type) -> type` | `(int) -> str` | `() -> ()` | Function |
| `(type) >> type` | `(int) >> str` | `() >> ()` | Streaming function |

An empty list literal `[]` without a type annotation infers as `[()]`. To declare a typed empty list, use an explicit annotation: `xs: &[int]`.

An empty struct literal `{}` without annotation infers as `{() -> ()}`.

### Truthiness

A value is **falsy** if it equals its type's default. A value is **truthy** if it does not. No coercions — only default vs non-default.

```go
0    // falsy int
1    // truthy int
""   // falsy str
"a"  // truthy str
()   // falsy — unit has only one value, which is also its default
[]   // falsy list (empty)
```

A tuple is falsy if **all** its fields are default; truthy if **any** field is non-default.

### Structs

Struct literals use `{label: value}` syntax. Fields are accessed with `.`. Default construction `T{}` creates a value with all fields at their type defaults.

```go
alice = {name: "Alice", age: 42}
alice.name  // "Alice"

blank: Person{}  // all fields at defaults
```

### Maps

Maps are `{type -> type}` — variable-length key/value collections. Keys must be base-type literals; values can be any expression.

```go
sides = {"square": 4, "triangle": 3}  // {str -> int}
sides."square"                          // 4
```

### Lists

Lists are `[type]` — all elements the same type. 0-based indexing; negative indices count from the end.

```go
a = [1, 2, 3, 4, 5]
a[0]      // 1 (first element)
a[-1]     // 5 (last element)
a[1..]    // [2, 3, 4, 5] (slice from index 1 to end)
a[1..-1]  // [2, 3, 4, 5] (inclusive of -1)
```

The `..` operator creates ranges, usable in list literals and slices.

```go
[1..5]     // [1, 2, 3, 4, 5]
['a'..'e'] // ['a', 'b', 'c', 'd', 'e']
```

### Tuples

Tuples are fixed-length sequences of (potentially mixed) types. Fields are accessed by 0-based index.

```go
point  = (1, 2)
result = ("data", "")  // (str, str) — falsy error field means no error
point.0                 // 1
result.1                // "" (the error field)
```

A tuple is falsy if all fields equal their type defaults.

### Struct Composition

Structs can be merged with `+` to produce a new struct type containing all fields.

```go
Named    = {name: str}
Aged     = {age: int}
Person   = Named + Aged             // {name: str, age: int}
Employee = Person + {id: int}       // {name: str, age: int, id: int}
```

Structural typing: a value is valid as a function argument if it contains at least the required fields.

```go
greet = (p: Named) -> str { `Hello, {p.name}` }

e = {name: "Bob", age: 35, id: 1}
greet(e)  // valid — e contains Named's fields
```

### Labels as Types

Any label can be used as a type annotation. The type is inferred from the label's value.

```go
coords = [1.0, 2.0, 3.0]  // type [num]
origin: coords              // type [num], default []
```

---

## Functions

### Definition and Calling

```go
add = (x: int, y: int) -> int {
    x + y     // last expression is the return value
}

result = add(1, 2)  // 3
```

The function's parameter list uses struct syntax. The return type follows `->`. The block's last expression is the return value.

`->` is **purely definitional** — it maps a parameter set to a return type and body. It does not appear in expression position.

### First-Class Functions

A label name alone refers to the function value. Calling requires `()`.

```go
double = (n: int) -> int { n * 2 }

apply = (f: (int) -> int, x: int) -> int { f(x) }

apply(double, 5)                          // 10
apply((n: int) -> int { n + 1 }, 5)      // 6 — anonymous literal
```

### UFCS — Uniform Function Call Syntax

`x.f(args)` desugars to `f(x, args)`. Free functions can be called as if they were methods on the first argument's type.

```go
Stack = {data: &[int]}

push = (s: &Stack, val: int) -> () { s.data += val }
peek = (s: &Stack)            -> int { s.data[-1] }
len  = (s: Stack)             -> int { s.data.len }

s: &Stack
s.push(10)  // push(s, 10)
s.peek()    // peek(s)
s.len()     // len(s)
```

---

## Error Handling

### Fallible Function Signatures — `-> T ! E`

Functions that can fail declare `-> T ! E` instead of `-> T`. This makes fallibility explicit in the signature and enables postfix `!` at call sites. At runtime it is sugar over a `(T, E)` tuple, but callers interact with `T` directly on the success path.

```go
listen   = (addr: str)       -> Listener ! str { ... }
accept   = (l: Listener)     -> Conn     ! str { ... }
readline = (c: Conn)         -> str      ! str { ... }
read     = (c: Conn, n: int) -> str      ! str { ... }
write    = (c: Conn, s: str) -> int      ! str { ... }
```

On the success path, the function returns a value of type `T` directly. On the failure path, it exits via `!` (see below).

### Postfix `!` — Function Exit on Truthy

`expr!` checks if `expr` is truthy. If truthy, exits the enclosing function immediately, propagating the value up. If falsy, continues execution and produces the expression's value.

When applied to a `-> T ! E` call result (a `(T, E)` tuple at runtime):
- Error field truthy → exits enclosing function with `(T{}, E)` (propagates error)
- Error field falsy → unwraps and produces just `T` (continues)

```go
readAll = (path: str) -> str ! str {
    f    = open(path)!   // propagate if open fails; f: File on success
    data = f.read()!     // propagate if read fails; data: str on success
    data                 // return data
}
```

### Explicit Failure — `"message"!`

A non-empty string literal is always truthy. `"message"!` is therefore always an unconditional failure. It is the same `!` operator with the same rule — no special syntax needed.

```go
parseRequest = (line: str) -> Request ! str {
    parts = str.words(line)
    parts.len == 3
        | true -> {method: parts[0], path: parts[1], body: ""}
        | _    -> "bad request line"!
}
```

### Call-Site Patterns

Three ways to handle a `-> T ! E` call:

```go
// 1. Propagate — unwrap to T, exit function on error
data = open("input.txt")!

// 2. Destructure — handle the (T, E) tuple manually
f, err = open("input.txt")

// 3. Thread — keep as (T, E) for later or pass through
result = open("input.txt")
```

### Deferred Cleanup — `~`

Prefixing an expression with `~` defers its evaluation until the enclosing function returns, regardless of how (normally or via `!`). Deferred calls run in LIFO order.

```go
handleConn = (conn: Conn, id: int) -> () ! str {
    ~conn.close()                       // always runs on exit
    ~sys.print(`[{id}] disconnected`)   // runs before conn.close() (LIFO)

    sys.print(`[{id}] connected`)
    // ... rest of handling ...
}
```

---

## Pattern Matching

Pattern matching uses `|` (match) and `->` (arm). The value is compared against each arm's left side in order; the first match evaluates its right side and that becomes the result of the whole expression. If no arm matches, the expression produces `()`.

```go
value | arm1 -> result1
      | arm2 -> result2
      | _    -> fallback
```

### Arm Left Side

**Literal** — matches exactly:
```go
n | 0 -> "zero"
  | 1 -> "one"
  | _ -> "other"
```

**Binding** — always matches, binds the value (no truthiness check):
```go
x | n -> `got {n}`   // always matches, n is bound to x
```

**Wildcard** — always matches, discards:
```go
x | _ -> "ignored"
```

**Tuple positional** — each position matched independently:
```go
(method, status) | "GET", 200  -> processOk(data)
                 | "GET", 404  -> "not found"
                 | m,    s     -> `{m} {s}`
```

### Expression LHS

The left side of an arm can be any expression, enabling structural patterns.

**String prefix** — matches strings starting with the prefix, binds the remainder:
```go
req.path | "/hello/" + name -> greet(name)
         | "/api/"   + rest -> api(rest)
         | _                -> notFound()
```

**List structural** — matches by length and element:
```go
parts | []              -> "empty"
      | [x]             -> `one: {x}`
      | [x, y]          -> `two: {x} and {y}`
      | [first, ...]    -> `starts with {first}`
```

**View pattern** — apply a function to the matched value, then match the result:
```go
str.split(req.path, "/") | ["", "api", ver, res] -> handleApi(ver, res)
                          | ["", resource]         -> handleSimple(resource)
                          | _                      -> notFound()
```

### Nested Matching

An arm's right side can itself contain `|`, building tree-structured routing:

```go
(req.method, req.path)
    | "GET",  "/health"        -> {status: 200, body: "ok"}
    | "GET",  "/hello/" + name -> handleHello(name)
    | "POST", path             ->
        path | "/echo"  -> handleEcho(req)
             | "/lines" -> handleLines(req)
             | _        -> {status: 404, body: "not found"}
    | _, _                     -> {status: 405, body: "method not allowed"}
```

---

## Flow Control

### `@` — Loop

`@ { body }` loops indefinitely. The body is evaluated on each iteration. Loop behavior is determined by the body's last expression:

- `()` → continue
- any non-`()` value → exit loop with that value

```go
// Find first matching element
findFirst = (xs: [int], target: int) -> (int, bool) {
    i: &int = 0
    @ {
        i >= xs.len     | true -> (0, false)      // end of list: exit not-found
        xs[i] == target | true -> (xs[i], true)   // match: exit found
        i += 1
    }
}
```

### Postfix `?` — Loop Exit on Falsy

`val?` exits the enclosing `@` loop with `()` if `val` is falsy. This is shorthand for the common "exit on done/empty/EOF" pattern.

```go
// Skip HTTP request headers (read until blank line)
@ { net.readline(conn)! ? }
// readline returns str; ! unwraps (propagating any error to caller);
// ? exits loop when the line is "" (blank line = end of headers)

// Process lines until EOF
@ {
    line = sys.readline()
    line?                // exit if "" (EOF)
    sys.print(line)
}
```

### `#` — Iterate and Collect

`xs # { i, elem -> body }` iterates over `xs`, applies the arm body to each element, and collects non-`()` results into a new list. Arms that produce `()` are skipped — this is how filtering works.

| Input type | Arm receives |
|---|---|
| `[type]` | `(int, type)` — index and element |
| `str` | `(int, char)` — index and character |
| `{K -> V}` | `(int, (K, V))` — index and key/value pair |

```go
// Map
doubled = [1, 2, 3] # { _, n -> n * 2 }
// [2, 4, 6]

// Filter (produce () to skip)
evens = [1..6] # { _, n -> n % 2 == 0 | true -> n }
// [2, 4, 6] — odd arms produce () from unmatched |, which # skips

// Map + filter
result = [1..10] # { _, n -> n % 2 == 0 | true -> n * 3 }
// [6, 12, 18, 24, 30]

// Chained
summary = users # { _, u -> u.active | true -> u.name }
               # { _, name -> str.upper(name) }
```

---

## Streaming Functions

A streaming function is defined with `>>` instead of `->`. It produces a sequence of values over time. The unary prefix `>>` in expression position streams a value to the caller and suspends at that point, resuming on the next call. All inner state (loop positions, local labels) is preserved across suspensions.

```go
counter = (start: int, step: int) >> int {
    n: &int = start
    @ {
        >> n      // stream n to caller, suspend here
        n += step // resumes here on next call
    }
}

c = counter(0, 1)  // c: () -> int
c()  // 0
c()  // 1
c()  // 2
```

### Stream Exhaustion

When the streaming function body ends without hitting `>>`, the stream is exhausted. Subsequent calls return the stream type's default value (falsy). Callers use truthiness or `?` to detect exhaustion.

```go
// Consume all values from a stream
@ {
    val = myStream()
    val?         // exit loop when stream is exhausted (falsy default)
    process(val)
}
```

### Stream over Collections

`#` can iterate the results of a streaming function once attached (open question — see below). The natural pattern for a streaming function over a fixed collection is to use `#` internally:

```go
// Stream characters of a string
chars = (s: str) >> char {
    s # { _, c -> >> c }
}
```

---

## Operators

### Expression Operators

| Category | Operators | Input | Output |
|---|---|---|---|
| Equality | `== !=` | any | `bool` |
| Comparison | `< <= >= >` | `int num char str` | `bool` |
| Truthiness | `><` | any | `bool` |
| Boolean | `&& \|\|` | `bool` | `bool` |
| Boolean NOT | `!` (prefix) | `bool` | `bool` |
| Bitwise | `& \| ^ << >>` | `int char` | `int char` |
| Arithmetic | `+ - * / % **` | `int num` | `int num` |
| In-place | `+= -= *= /=` | `int num` | `()` |
| String concat | `+` | `char str` | `str` |
| Sequence append | `+ +=` | `[type]` | `[type]` |
| Sequence remove | `- -=` | `[type]` | `[type]` |
| Map merge | `+` | `{K->V}` | `{K->V}` |
| Map remove | `-` | `{K->V}` | `{K->V}` |
| Struct merge | `+` | struct types | struct type |
| Range | `..` | `int char` | `[type]` |
| Member | `.` | struct, map, namespace | field type |
| Error propagate | `!` (postfix) | `(T, E)` or any truthy | exits function |
| Loop exit | `?` (postfix) | any falsy | exits `@` loop |

No type coercions. All binary operators require matching input types (except `><`).

The truthiness operator `><` returns `true` if both sides have the same truthiness.

### Disambiguation Notes

`!` prefix is boolean NOT; `!` postfix is error propagation. These are syntactically unambiguous by position: `!x` is boolean NOT, `x!` is propagation.

`>>` appears as both bitwise right-shift (binary infix between two integers) and streaming (definition form following a parameter tuple, or unary prefix `>> value`). Always syntactically unambiguous.

`&` appears as both the mutability prefix on types (`&int`) and bitwise AND (binary infix between two integers).

### Control Operators

| Operator | Description |
|---|---|
| `\|` | Pattern match — compare value against arms |
| `->` | Function definition; pattern arm body |
| `!` (postfix) | Exit enclosing function if truthy (error propagation / unconditional fail) |
| `?` (postfix) | Exit enclosing `@` loop if falsy |
| `~` (prefix) | Defer expression until enclosing function returns |
| `#` | Iterate and collect — map, filter, both |
| `@` | Loop — repeat body until non-`()` result |
| `>>` | Streaming: definition paired with `>>` expression; or stream value and suspend (unary prefix) |
| `:` | Type annotation |
| `=` | Label binding |

---

## String Interpolation

Backtick strings support inline expression interpolation.

```go
name = "Alice"
age  = 42
sys.print(`{name} is {age} years old`)
sys.print(`connecting to {host}:{port}`)
```

---

## Modules

A program can be split into modules across multiple files.

```go
module main

import sys
import util/strings

main = (args: [str]) -> int {
    sys.print(strings.join(args, " "))
    0
}
```

- The `main` module must define a `main` function: `(args: [str]) -> int`
- All module-scope labels are immutable (constants and functions)
- Imported module contents are accessed via `.` and the module name

---

## Example — HTTP Server

A realistic example showing the full design working together.

```go
module main

import net
import sys
import str

Request  = {method: str, path: str, body: str}
Response = {status: int, body: str}

ok   = (body: str)           -> Response { {status: 200, body: body} }
fail = (code: int, msg: str) -> Response { {status: code, body: msg} }

handleHello = (req: Request) -> Response {
    name = req.body | "" -> "world" | n -> str.trim(n)
    ok(`hello, {name}!\n`)
}

handleEcho  = (req: Request) -> Response { ok(req.body) }

handleLines = (req: Request) -> Response {
    lines = str.lines(req.body) # { i, line -> `{i+1}: {line}\n` }
    ok(lines.join(""))
}

route = (req: Request) -> Response {
    (req.method, req.path)
        | "GET",  "/hello"       -> handleHello(req)
        | "GET",  "/hello/" + n  -> handleHello({req + {body: n}})
        | "POST", "/echo"        -> handleEcho(req)
        | "POST", "/lines"       -> handleLines(req)
        | m,      p              -> fail(404, `no route: {m} {p}\n`)
}

readRequest = (conn: net.Conn) -> Request ! str {
    line  = net.readline(conn)!
    parts = str.words(line)
    parts.len == 3
        | true -> {
            @ { net.readline(conn)! ? }   // skip headers until blank line
            body = net.read(conn, 8192)!
            {method: parts[0], path: parts[1], body: body}
        }
        | _ -> "bad request line"!
}

handleConn = (conn: net.Conn, id: int) -> () ! str {
    ~net.close(conn)
    sys.print(`[{id}] connected`)
    ~sys.print(`[{id}] disconnected`)
    @ {
        req  = readRequest(conn)!
        resp = route(req)
        net.write(conn, `HTTP/1.1 {resp.status}\r\n\r\n{resp.body}`)!
    }
}

serve = (addr: str) -> () ! str {
    listener = net.listen(addr)!
    id: &int = 0
    @ {
        conn = net.accept(listener)!
        id  += 1
        _ = handleConn(conn, id)   // _ = discard; errors handled inside
    }
}

main = (args: [str]) -> int {
    addr = args | [a, ...] -> a | _ -> "0.0.0.0:8080"
    sys.print(`listening on {addr}`)
    serve(addr) | _, "" -> 0 | _, e -> { sys.print(`fatal: {e}`); 1 }
}
```

---

## Open Questions

1. **Guard syntax in pattern matching** — matching a bound value against a condition (e.g., `n >= 90`) inside a pattern arm needs a clean syntax. Computed comparisons can be nested with additional `|`, but verbose.

2. **Anonymous function type inference** — can parameter types be omitted when the call site makes them unambiguous? `fold((a, b) -> { a + b }, 0, xs)` vs the fully annotated form.

3. **Integer widths** — `int` and `num` have no explicit width. Systems programming requires `u8`, `i32`, `u64`, etc. for layout, FFI, and overflow semantics. The `u8`/`i32`/`f16` pattern is the agreed direction; exact set and syntax TBD.

4. **Recursive types** — a struct that contains a field of its own type (e.g. linked list node) is not expressible without explicit indirection. Mechanism TBD.

5. **Generics / type parameters** — the label-as-type system hints at a path, but how type parameters work in function signatures is not yet designed.

6. **Struct literal vs block disambiguation** — `{label: value}` (struct) and `{statements}` (block) can be syntactically ambiguous in some positions. Proposed resolution: `T{field: value}` for named struct construction distinguishes from bare blocks.

7. **Streaming termination** — `->` is no longer available in expression position inside `>>` bodies for early stream exit. Current model: stream exhausts naturally when the body ends. Mechanism for early termination (analogous to `break` in a generator) is TBD.

8. **`#` over streaming functions** — can `#` consume a `() -> T` stream instance directly? This would complete the `#` / `>>` pairing the way Python's `for` iterates over generators.

9. **Streaming suspension model** — how is state preserved across `>>` suspensions? The semantics say "all inner state is preserved" but the implementation model (coroutines, state machines, closures) is open.

10. **`-> () ! E` vs `-> E`** — for functions with no meaningful success value, `-> () ! str` is slightly verbose. Whether this deserves sugar (e.g., just `-> str` on a function that can only fail) is worth deciding deliberately.

11. **`self` and struct field methods** — UFCS handles method call syntax, but a function defined as a struct field cannot currently refer to the enclosing struct instance by any name.

12. **Bitwise NOT** — `~` is now the defer prefix, leaving bitwise NOT without a symbol. Candidates: `^x` (prefix XOR), a dedicated operator, or a stdlib function.
