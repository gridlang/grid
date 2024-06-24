# Conditional

The `?` conditional operator allows us to match on expressions, replacing the `if`/`else` constructs in most languages. This also includes handling return values from functions.

There are two primary forms of conditionals available: expression-mapping and pattern-matching.

## Expression Mapping

Expression mapping will evaluate a given expression and map its result to one or more variables. If the expression evaluates to a truthy value, a specified block will be executed.

The basic pattern follows:
```go
expression ? variables {
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

