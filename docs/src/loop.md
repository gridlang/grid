# Loop

The `@` operator is used to loop over a block, repeating an input expression each iteration, and optionally passing the result of the expression into the block.

Here's the syntax:

```go
expression @ captures {
  // statements
  continue // continue the loop
  break // break the loop
}
```

This will evaluate the expression before each iteration of the loop body. The `continue` and `break` keywords are used to immediately restart the loop or exit the loop, respectively.

For example, a simple case with no capture:

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
  err ? {
    true => {
      print(err)
      break // break out of loop
    }
    _ => print(data) // continue is implicit
  }
}
```
