# Loop

The `@` operator is used to loop over a block while the input expression is truthy.

Here's the syntax:

```go
expression @ captures {
  // statements
  continue // continue the loop
  break // break the loop
}
```

This will evaluate the expression before each iteration of the loop body. If the result of the expression is truthy, it will execute the body. Returning a truthy value will continue the loop, and a falsy one will break out of the loop.

If the input expression results in a tuple, if any of the tuple fields are truthy, the expression is considered truthy as well, as detailed in [types](types.md).

For example, a simple case:

```go
a = 0
b = 5
a < b @ {
  a += 1
}
// a == b
```

And a more complicated case, assuming a function that returns a tuple:

```go
// call read function repeatedly, destructuring tuple to data, err captures
read(100) @ data, err {
  err => {
    print(err)
    break // break out of loop
  }
  _ => print(data) // continue is implicit
```
