# Conditional

The `?` conditional operator allow us to match on expressions, which replaces the `if`/`else` constructs in most languages. This also applies to return values from functions.

There are two forms of conditionals available, value-matching, and expression-mapping.

Value matching has the following pattern:

```go
expression ? {
  value => statement
}
```

In this pattern, the result of the expression is used to match against in the following block, by specifying match clauses as literal values.

For example:

```go
a < b ? {
  true => print("Less")
  false => print("More")
}
```

Expression mapping has a bit more options, and follows this pattern:

```go
expression ? variables {
  expression => statement
}
```

This will map the result of the expression to one or more variables, including potentially destructuring a tuple result. These variables are usable inside the conditional block, allowing for full expressions using those variables to match against.

For example:

```go
data = read(f) ? result, err {
  err => panic(err)
  _ => return result
}
```

This shows how we might call a `read` function which returns a `(str, str)` tuple, destructuring and mapping it to `result` and `err`. Inside the block, we can use the vars in match clauses instead of literal values.

And a bit more complex example:

```go
// Map function return to a, b
f() ? a, b {
  // Assign result of block
  // Map function return comparison to t
  h = g(a) > b ? t {
    // t is truthy
    t => ...
  }
// map block to x
} ? x {
  ...
}
```
