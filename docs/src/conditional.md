# Conditional

The `=>` and `!>` conditional operators allow us to match on expressions, which replaces the `if`/`else` constructs in most languages. This also applies to return values from functions.

Here's an example combining postfix and prefix assignments:

```go
a < b ? t {
  t => ...
  t !> ...
}

read(str) = f -> (str, str) {
  syscall_read(f) ? result, err {
    err => return ("", "Error reading file")
    return (result, "")
  }
}

data = read("test.txt") ? r, e {
  e => panic(e)
  e !> r
}
```
