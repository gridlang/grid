# Variables

Variables are handles to data of a type.

### Syntax:

```go
name, name = expression
```

A name and value are required. The type is based on the right-hand side of the assignment:
- If it is a literal, the type is explicit in the syntax of the literal.
- If it is a function call, the return type of the function is used.
- If it is the name of another variable, the value is copied.

The left-hand side can optionally be a list of names, which are used to *destructure* a [tuple](types.md) on the right-hand side. This is useful for extracting fields from function returns, for example.

All assignments are considered [truthy](types.md) for the purpose of [block](scope.md) return values.
