# Operators

Grid provides a variety of operators for use in expressions, with some particular interactions between different types.

| Category | Operators | Input Types | Output Types |
|----------|-----------|-------------|-------------|
| Comparison | `< <= != == >= >` | int, float, char, str | bool |
| Boolean | `&& \|\| !!` | bool | bool |
| Bitwise | `& \| ^ ~ << >>` | int, char | int, char |
| Arithmetic | `+ - * / % **` | int, float | int, float |
| Assignment | `= += -= *= /=` | int, float | int, float |

There are a few other operators available as well:

- The default operator `!` is used to return the default value of a type.
- The membership operator `.` is used for accessing a member of a [namespace](structure.md) or [type](types.md). See those sections for details.
- The [pattern matching](flow-control.md) operator `=>` is used to indicate a true match.
- The [function](functions.md) operator `->` is used to define a function and optional return types.
