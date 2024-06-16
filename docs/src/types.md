# Types

Grid provides a set of base types that are a core part of the language, and accompanying syntax for specifying literal data of these types. They are as follows:

- bool :: Boolean value, `true` or `false`
  - `b = true`
- int :: Integer number, using digits 0-9, optional `-` prefix for negative
  - `i = -123`
- num :: Rational number, using digits 0-9, optional `-` prefix and optional `.` for decimals
  - `f = 1.23`
- char :: UTF-8 character, specified inside single quotes `''`
  - `c = 'z'`
- str :: UTF-8 string, specified inside double quotes `""`
  - `s = "Hello"`
- [type] :: homogenous list of `type`, specified inside square brackets `[]`
  - `l = [1,2,3]`
- {typeA:typeB} :: homogenous map of `typeA` to `typeB`, specified inside braces `{}`
  - `m = {1: "a", 2: "b", 3: "c"}`
- (typeA, typeB, typeC) :: anonymous tuple of types, specified inside parens `()`
  - `t = ("a", 'b', [1, 2], 3.0)`
- (name: type) :: structural tuple, named fields with types, specified inside parens `()`
  - `s = (a: int, b: char)`

## Defaults

Each of these types has a *default* value it's initialized with. These default values allow for a clearly defined *truthiness* when used in pattern matching or relational [operators](#operators).

The default for each type is as follows:

| type          |    default |
|---------------|------------|
| `bool`        |    `false` |
| `int`         |        `0` |
| `float`       |      `0.0` |
| `char`        |       `''` |
| `str`         |       `""` |
| `[type]`      |       `[]` |
| `{type:type}` |       `{}` |
| `(type)`      |       `()` |
| `(name:type)` | `(name:_)` |

We can use this in [pattern matching](#flow-control) to evaluate truthiness, because defaults are considered `false`. In other words, a non-default value can be used as shorthand for `true` in a match.

Here's an example to illustrate:

```
s = ""
s ? {
  s => print("Non-empty")
  _ => print("Empty")
}
```

This is equivalent to using `s == ""` which evaluates to a `bool`, then matching directly on the value.

For example:

```
s = ""
s == "" ? b {
  false => print("Non-empty")
  true => print("Empty")
}
```

By treating all default values of any type as false, and by using variables in patterns instead of literals, we can simplify conditional syntax without introducing type coercions or ambiguity.

## Tuples

You'll notice that function definitions use structural tuples for the parameters, and function calls use anonymous tuples for arguments. We can also uses these tuples on their own, or in return types.

As mentioned in the section on [membership](#membership), we can use the `.` operator to access the fields of tuples.

```
a = (1, "2", [3])
a.0 // 0th field
b = (x: 1, y: "2", z: [3])
b.x // named field 'x'
```
