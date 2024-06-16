# Operators

Grid provides a variety of operators for use in expressions, with some particular interactions between different types.

| Category | Operators | Input Types | Output Types |
|----------|-----------|-------------|-------------|
| Comparison | `< <= != == >= >` | int, float, char, str | bool |
| Boolean | `&& \|\| !` | bool | bool |
| Bitwise | `& \| ^ ~ << >>` | int, char | int, char |
| Arithmetic | `+ - * / % **` | int, float | int, float |
| Assignment | `= += -= *= /=` | int, float | int, float |
| Membership | `.` |  |  |
| Pattern | `=> !>` |  |  |
| Function | `->` |  |  |

## Membership

The membership operator `.` is used for accessing a member of a [namespace](structure.md) or [type](types.md). See those sections for details.

## Pattern Matching

The [pattern matching](flow-control.md) operators `=>` and `!>` are used to indicate a true match or a false match, respectively.

## Function

The [function](functions.md) operator `->` is used to define a function and optional return types
