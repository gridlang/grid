# Variables

Variables are handles to data of a type. They are declared using the following syntax:

```go
name, name = expression
```

A name and value are required. The type is based on the right-hand side of the assignment:
- If it is a literal, the type is explicit in the syntax of the literal.
- If it is a function call, the return type of the function is used.
- If it is the name of another variable, the value is copied.

The left-hand side can optionally be a list of names, which are used to *destructure* a [tuple](types.md) on the right-hand side. This is useful for extracting fields from function returns, for example.

All assignments are considered [truthy](types.md) for the purpose of [block](scope.md) return values.

## Postfix Assignment

The `?` operator is used in Grid to express a postfix assignment.

It has the following syntax:

```go
expression ? capturevar, capturevar {
  // statements
}
```

Capture variables are mapped to the result of the expression, and at least one is required.

If only one is given, it represents the whole result. If multiple capture variables are provided, the expression must result to a tuple, and the fields of the tuple are *destructured* into the separate variables with the corresponding types. Therefore the tuple's type must have the same number of fields as the number of capture variables provided.

Using the postfix assignment operator allows us to chain or nest assignment and destructuring chains in a compact syntax.

Here's an example of mixing prefix and postfix assignment:

```go
// Map function return to a, b
f() ? a, b {
  // Assign result of block
  // Map function return comparison to t
  h = g(a) > b ? t {
    // t is truthy
    t => ...
  }
// map block to x
} ? x {
  ...
}
```
