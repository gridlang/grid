# Operators

Grid provides a variety of operators for use in expressions, with some particular interactions between different types.

| Category | Operators | Input Types | Output Types |
|----------|-----------|-------------|-------------|
| Comparison | `< <= != == >= >` | int, float, char, str | bool |
| Boolean | `&& \|\| !` | bool | bool |
| Bitwise | `& \| ^ ~ << >>` | int, char | int, char |
| Arithmetic | `+ - * / % **` | int, float | int, float |
| Assignment | `= += -= *= /=` | int, float | int, float |

There are a few other operators available as well:

- The membership operator `.` is used for accessing a member of a [namespace](structure.md) or [type](types.md). See those sections for details.
- The [conditional](conditional.md) operator `?` is used to match against expressions.
- The [grid](grid.md) operator `#` is used to iterate over a range of values.
- The [loop](loop.md) operator `@` is used to repeat an expression based on conditions.
- The [pattern matching](flow-control.md) operators `=>` and `!>` are used to indicate a true/false match respectively.
- The [function](functions.md) operators `->` and `>>` are used to define a function and optional return types.
