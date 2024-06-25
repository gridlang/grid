# Conditional

The `?` conditional operator allows us to match on expressions, replacing the `if`/`else` constructs in most languages. This also includes handling return values from functions.

### Syntax:

```go
expression ? {
  patterns
}
```

### Example:
```go
read(file) ? { // returns (data, err)
  _, err => {
    print(err)
    return -1
  }
  data, _ => print(data)
}
```

In this example:
- The result of `read(file)` is evaluated by the pattern expressions, mapping into `data` and `err` accordingly
- If an error is present, the conditional returns from the enclosing function

