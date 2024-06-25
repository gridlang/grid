# Loop

The `@` operator is used to loop over a pattern match, repeating an optional input expression each iteration.

### Syntax:

```go
expression @ {
  pattern => ...
}
```

The `continue` and `break` keywords are used to immediately restart the loop or exit the loop, respectively. Additionally, the `break` keyword can take a value to return from the loop which can be assigned as the result of the loop expression.

> Without a `break` keyword a loop will never exit.

The simplest form of loop has no expression, equivalent to a `loop`, `do`, or `while True` in other languages.

### Example:

```go
@ { ... }
```

### Example:

When an expression is given, the loop will evaluate the expression before each iteration of the loop body. 

```go
a = 0
b = 5
a < b @ {
  true => a += 1
  false => break
}
// a == b
```

### Example:

And a more complicated case, assuming a function that returns a tuple.

```go
// call read function repeatedly
read(100) @ { // returns (data, err)
  _, err => {
    print(err)
    break // break out of loop
  }
  data, _ => print(data) // continue is implicit
}
```
