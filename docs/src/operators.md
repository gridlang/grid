# Operators

Grid provides a variety of operators for use in expressions, with some particular interactions between different types.

| Category | Operators | Input Types | Output Types |
|----------|-----------|-------------|-------------|
| Relational | `< <= != == >= >` | int, float, char, str | bool |
| Boolean | `&& \|\| !!` | bool | bool |
| Bitwise | `& \| ^ ! << >>` | int, char | int, char |
| Arithmetic | `+ - * / % **` | int, float | int, float |
| Assignment | `+= -= *= /=` | int, float | int, float |
| Membership | `.` |  |  |

## Membership

The membership operator `.` is used for accessing a member of a [namespace](functions.md) or [type](types.md). See those sections for details.
