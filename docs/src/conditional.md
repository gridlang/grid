# Conditional

The `?` conditional operator allows us to match on expressions, replacing the `if`/`else` constructs in most languages. This also includes handling return values from functions.

There are two primary forms of conditionals available: expression-mapping and [pattern-matching](pattern.md).

## Expression Mapping

Expression mapping will evaluate a given expression and map its result to optionally captured variables. If the expression evaluates to a truthy value, the specified block will be executed.

### Syntax:

```go
expression ? captures {
  // statements using variables
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

