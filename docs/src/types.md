# Types

Grid provides a set of base types that are a core part of the language, and accompanying syntax for specifying literal data of these types.

The following table lists the type pattern for the literal, an example in Grid syntax, and the default value for the type:

| Type Pattern | Example | Default | Description |
|--------------|---------|---------|-------------|
| bool | `true` | `false` | Boolean value |
| int | `-123` | `0` | Integer number |
| num | `-1.23e4` | `0.0` | Real number |
| char | `'z'` | `''` | Single character |
| str | `"hello"` | `""` | String of characters |
| [type] | `[1, 2, 3]` | `[]` | Array of type |
| {type:type} | `{"x": 1, "y": 2}` | `{}` | Map of type to type |
| (type,type) | `(1, "2", [3])` | `()` | Anonymous tuple of types |
| (name:type) | `(name: str, age: int)` | `(field: default)` | Structured tuple of types |
| (type) -> type | `(int) -> str` | `()->` | Function |
| (type) >> type | `(int) >> str` | `()>>` | Stateful function |

Each of these types has a *default* value it's initialized with. These default values allow for a clearly defined *truthiness* when used in pattern matching or relational [operators](operators.md). The `(field:default)` for structured tuples above is indicating that whatever the type of the fields in that tuple are, their defaults will be used as the value of the fields.

We can use this in [conditionals](flow-control.md) to evaluate truthiness, because defaults are considered `false`. In other words, a non-default value can be used as shorthand for `true` in a match. This has one additional aspect with tuples, where a tuple of all default values of any set of types is also considered `false`, whereas a tuple of any non-default values is considered `true`. This is useful in [loop](loops.md) evaluation.

Here's an example to illustrate:

```go
s = ""
s ? {
  "" => print("Empty") // default
  _ => print("Non-empty") // else
}
```

This is equivalent to using `s == ""` which evaluates to a `bool`. For example:

```go
s = ""
s == "" ? e {
  e => print("Empty") // true
  _ => print("Non-empty") // else
}
```

By treating all default values of any type as false, and by using variables in patterns instead of literals, we can simplify conditional syntax without introducing type coercions or ambiguity.

## Tuples

You'll notice that [function definitions](functions.md) use structural tuples for the parameters, and function calls use anonymous tuples for arguments. We can also uses these tuples on their own, or in return types.

As mentioned in the section on [operators](operators.md), we can use the `.` operator to access the fields of tuples.

```go
a = (1, "2", [3])
a.0 // 0th field
b = (x: 1, y: "2", z: [3])
b.x // named field 'x'
```
