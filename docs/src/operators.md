# Operators

## Expressions

Grid provides a variety of operators for use in expressions, with some particular interactions between different types.

| Category | Operators | Input Types | Output Types |
|----------|-----------|-------------|-------------|
| Equality | `== !=` | any | bool |
| Comparison | `< <= >= >` | int, float, char, str | bool |
| Boolean | `&& \|\| !` | bool | bool |
| Bitwise | `& \| ^ ~ << >>` | int, char | int, char |
| Arithmetic | `+ - * / % **` | int, float | int, float |
| In-Place | `+= -= *= /=` | int, float | int, float |
| String | `+` | char, str | str |
| Sequence | `+ - += -=` | array, map | array, map |
| Type | `& \|` | tuple | tuple |

### Notes

Comparison operators on strings and characters work similarly to other languages. Characters are compared ordinally, with strings being compared for each character in them.

Sequence operators work to compose arrays and maps in similar but slightly different ways.

### Example:

```go
[1, 2] + 3 // [1, 2, 3]
[1, 2] + [3, 4] // [1, 2, [3, 4]]
[1, 2] - 1 // [2]

{"a": 1} + {"b": 2} // {"a": 1, "b", 2}
{"a": 1, "b": 2} - {"b": 2} // {"a": 1}
```

## Statements

There are a few statement operators available as well.

- The membership operator `.` is used for accessing a member of a [namespace](structure.md) or [type](types.md). See those sections for details.
- The [conditional](conditional.md) operator `?` is used to conditionally act based on expressions.
- The [pattern](pattern.md) operator `=>` is used to match against expressions.
- The [grid](grid.md) operator `#` is used to iterate over a range of values.
- The [loop](loop.md) operator `@` is used to repeat an expression based on conditions.
- The [function](functions.md) operators `->` and `>>` are used to define a function and optional return types.
