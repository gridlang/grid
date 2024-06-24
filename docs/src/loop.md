# Loop

The `@` operator is used to loop over a block, repeating an optional input expression each iteration, and optionally passing the result of the expression into the block.

### Syntax:

```go
expression @ captures {
  // statements
  continue // continue the loop
  break // break the loop
}
```

The `continue` and `break` keywords are used to immediately restart the loop or exit the loop, respectively. Additionally, the `break` keyword can take a value to return from the loop which can be assigned as the result of the loop expression.

> Note that without a `break` keyword a loop will never exit.

The simplest form of loop has no expression and no captures, equivalent to a `loop`, `do`, or `while True` in other languages.

### Example:

```go
@ { ... }
```

When an expression is given, the loop will evaluate the expression before each iteration of the loop body. 

### Example:

```go
a = 0
b = 5
a < b @ {
  a += 1
}
// a == b
```

And a more complicated case, assuming a function that returns a tuple.

### Example:

```go
// call read function repeatedly, destructuring tuple to data, err captures
read(100) @ data, err {
  err ? {
    print(err)
    break // break out of loop
  }
  print(data) // continue is implicit
}
```
