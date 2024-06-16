# Variables

Variables are handles to data of a type. They are declared using the following syntax:

```
name, name = expression
```

A name and value are required. The type is based on the right-hand side of the assignment:
- If it is a literal, the type is explicit in the syntax of the literal.
- If it is a function call, the return type of the function is used.
- If it is the name of another variable, see the section on [moves](ownership.md)

The left-hand side can optionally be a list of names, which are used to *destructure* a [tuple](types.md) on the right-hand side. This is useful for extracting fields from function returns, for example.
