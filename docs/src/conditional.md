# Conditional

The `?` operator is used in Grid to express a conditional statement.

It has the following syntax:

```go
expression ? capturevar, capturevar {
  variable => ...
  value => ...
}
```

The capturevar(s) are optional. If only one is given, the result of the expression is assigned to that variable.

If multiple capture variables are provided, the expression must result to a tuple, and the fields of the tuple are *destructured* into the separate variables with the corresponding types. Therefore the tuple's type must have the same number of fields as the number of capture variables provided.

If no capture variables are given, the result of the expression can still be matched implicitly by literals in the pattern matches.

## Pattern Matching

This construct allows us to match on expressions, which replaces the `if`/`else` constructs in most languages. This also applies to return values from functions.

For example:

```go
a < b ? {
  true => ...
  false => ...
}

read = (f: str) -> (str, str) {
  syscall_read(f) ? result, err {
    err => return ("", "Error reading file")
    _ => return (result, "")
  }
}

data = read("test.txt") ? r, e {
  e => panic(e)
  _ => r
}
```
