# Conditional

The `?` conditional operator allows us to match on expressions, replacing the `if`/`else` constructs in most languages. This also includes handling return values from functions.

## Expression Mapping

Expression mapping will evaluate a given expression and map its result to optionally captured variables. If the expression evaluates to a truthy value, the attached block will be executed.

Additional conditions can be attached using `?!`. If no expression is given, it serves as a final `else` block.

### Syntax:

```go
expression ? captures {
  // if
} expression ?! captures {
  // else if
} ?! {
  // else
}
```

### Example:
```go
read(file) ? data, err {
  err ? {
    print(err)
    return -1
  }
  print(data)
}
```

In this example:
- The result of `read(file)` is destructured into `data` and `err`.
- The block executes if the expression evaluates truthy.
- Within the block, another conditional checks and handles `err`.

