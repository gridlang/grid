# Loop

The `@` operator is used to loop over a block while the input expression is truthy.

Here's the syntax:

```go
expression @ {
  // statements
}
```

This will evaluate the expression before each iteration of the loop body. If the result of the expression is truthy, it will execute the body.

For example:

```go
a = 0
b = 5
a < b @ {
  a += 1
}
// a == b
```
