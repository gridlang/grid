# Flow Control

Grid provides a few flow-control constructs that also provide pattern matching.

First we'll cover regular conditionals. They have the following syntax:

```
<expression> ? [<capturevar> [, <capturevar>]] {
  <value> =>  ...
}
```

This construct allows us to match on expressions, which replaces the `if`/`else` constructs in most languages. This also applies to return values from functions.

For example:

```
a < b ? {
  true =>  ...
  false =>  ...
}

read = (f: str) -> str, str {
  syscall_read(f) ? result, err {
    err =>  return ("", "Error reading file")
    _ =>  return (result, "")
  }
}

data = read("test.txt") ? r, e {
  e =>  panic(e)
  _ =>  r
}
```

In this example we can see both anonymous and captured conditionals. If no capture vars are provided, the result of the expression can still be matched against anonymously via literals or types.

