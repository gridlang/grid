# Operators

## Expressions

Grid provides a variety of operators for use in expressions, with some particular interactions between different types.

| Category | Operators | Input Types | Output Types |
|----------|-----------|-------------|-------------|
| Truthiness | `><` | any | bool |
| Equality | `== !=` | any | bool |
| Comparison | `< <= >= >` | int, float, char, str | bool |
| Boolean | `&& \|\| !` | bool | bool |
| Bitwise | `& \| ^ ~ << >>` | int, char | int, char |
| Arithmetic | `+ - * / % **` | int, float | int, float |
| In-Place | `+= -= *= /=` | int, float | int, float |
| String | `+` | char, str | str |
| Sequence | `+ - += -=` | array, map | array, map |
| Type | `& \|` | tuple | tuple |

> There are no type coercions in Grid, so all inputs to expression operators must be the same types, with the exception of the Truthiness operator.

### Truthiness

The truthiness operator compares whether the two inputs have equivalent [truthiness](types.md), returning a `true` or `false` bool accordingly.

### Equality

Equality operators compare the values of inputs directly, as you might expect.

### Comparison

Comparison operators work similarly to other languages for numeric types.

Characters are compared ordinally, and strings are compared character by character.

### Sequence

Sequence operators work to compose arrays and maps in similar but slightly different ways.

### Example:

```go
[1, 2] + 3 // [1, 2, 3]
[1, 2] + [3, 4] // [1, 2, [3, 4]]
[1, 2] - 1 // [2]

<"a": 1> + <"b": 2> // <"a": 1, "b", 2>
<"a": 1, "b": 2> - "b" // <"a": 1>
```

## Statements

There are a few statement operators available as well.

- The membership operator `.` is used for accessing a member of a [namespace](structure.md) or [type](types.md). See those sections for details.
- The [conditional](conditional.md) operator `?` is used to conditionally act based on expressions.
- The [pattern](pattern.md) operator `=>` is used to match against expressions.
- The [grid](grid.md) operator `#` is used to iterate over a range of values.
- The [loop](loop.md) operator `@` is used to repeat an expression based on conditions.
- The [function](functions.md) operators `->` and `>>` are used to define a function and optional return types.
