# Literals and Types

> **Layer 4 of the model.** One symbol, one type.

You know what a literal is from its delimiters alone — no context, no inference. The rule
has two halves: **the bracket tells you the container's shape, and `:` tells you it is
keyed.** And `{ }` is freed entirely — it is a [block](holes.md), only ever a block — so the
brace ambiguity that haunts curly-brace languages cannot arise here.

## Two containers, two axes

There are exactly two bracket families, split by shape:

- **`( … )` is fixed** — a set number of (possibly mixed) slots.
- **`[ … ]` is variable** — any number of (uniform) elements.

and each becomes *keyed* by adding `:` — the same `:` that annotates a type everywhere
else:

|  | positional | keyed (`key: value`) |
|---|---|---|
| **`( )` — fixed** | tuple `(1, "a")` | struct `(x: 1, y: 2)` |
| **`[ ]` — variable** | list `[1, 2, 3]` | map `["a": 1, "b": 2]` |

A struct is a *named tuple*; a map is a *keyed list* — one structuring move applied to each
container. The only difference between a struct key and a map key is what sits left of the
`:`: a struct's is an **identifier** — a field name, fixed in the type (`(x: int)`); a
map's is a **value** — a key, computed at runtime (`[k: v]`).

## Base types

| type | literal | default | note |
|---|---|---|---|
| `()` | `()` | `()` | unit — [the one nothing](present.md) |
| `int` | `-123` | `0` | |
| `num` | `-1.23e4` | `0.0` | real |
| `char` | `'z'` | `'\0'` | a representable default, not the empty `''` |
| `str` | `"hello"` | `""` | |

There is no `bool` ([Layer 3](present.md#no-bool)). Sized numerics — `u8`, `i32`, … for
layout and FFI — are a later refinement; bare `int` / `num` for now.

## Lists and maps — both `[ ]`, both indexed, both partial

```grid
xs = [1, 2, 3]            // [int]
m  = ["a": 1, "b": 2]     // [str: int]
xs[1]                     // 2,  or () if out of range
m["a"]                    // 1,  or () if absent      <- same [] access, same partiality
[]                        // empty list
[:]                       // empty map (the : marks it keyed even when empty)
```

Type forms mirror the literals: `[T]` a list, `[K: V]` a map. Map keys are base-type values
(they must compare for lookup). That indexing is **partial** — a value, or `()` — is what
unifies `xs[i]` and `m["k"]` with every other operator ([Layer 3](present.md)), and what
makes iteration "take the next, stop at `()`" ([sources](growth.md#sources)).

## Tuples and structs — both `( )`

```grid
p = (1, "a")              // (int, str) tuple;  p.0 -> 1
q = (x: 1, y: 2)          // (x: int, y: int) struct;  q.x -> 1
(x,)                      // a 1-tuple — `(x)` alone is just grouping
Point(x: 1)               // named-struct construction; absent fields take defaults
```

Type forms: `(A, B)` a tuple, `(name: T)` a struct. In a *type* position the right of a `:`
is a type; in a *value* position it is a value — which is how `(x: foo)` stays knowable even
though any label can name a type (below).

A label that names a struct type is callable as a **constructor**: `Point(x: 1, y: 2)`
builds a `Point`, and any field left out takes its type's default. Construction by name and
the bare struct literal `(x: 1, y: 2)` produce the same value.

## Unions and intersection

`|` carries **union** — a value of either type:

```grid
T | ()                    // the optional — present is "some", () is "none" (Layer 3)
Shape | Color             // either type
```

`&` carries **structural intersection** — a value satisfying both:

```grid
Person   = (name: str, age: int)
Employee = Person & (id: int)     // has name, age, AND id
```

`&` is positional: a **prefix** `&T` is [mutability](substrate.md#the-immutability-hinge)
(the attached handle); an **infix** `A & B` on types is intersection (and on `int`s it is
bitwise-and — separated by value-vs-type position). A union defaults to `()` when `()` is a
member, and otherwise to the default of its first member — so `T | ()` defaults to `()`,
which is exactly "absent." (Composite defaults follow from the parts: `[]` for a list,
`[:]` for a map, and each field at its own default for a tuple or struct.)

## Labels as types, structural fit

Any label may stand as a type; the type is the label's:

```grid
coords = [1.0, 2.0, 3.0]   // [num]
origin: coords             // type [num], default []
```

And typing is **structural**: a value is accepted wherever it carries *at least* the
required shape — `(name: "Bo", age: 9, id: 1)` is a valid `Person`, because it has
`Person`'s fields. This is the same "has at least the shape" rule that makes `Employee` pass
where a `Person` is wanted.

## Interpolation

A backtick string interpolates `{expr}`:

```grid
a = 0
c = 'z'
`a = {a}, c = {c}`          // "a = 0, c = z"
```

The interpolation is brace-nesting–aware, so `{ }` inside an interpolated expression (a map
literal, a nested string) parses correctly. With the value layer pinned, the remaining
pieces — functions, defer, fallibles, streams — grow [From the Seed](growth.md).
