# Grid

The `#` operator -- also known as the Grid operator -- is used to iterate over the following types:

| Input | Output |
|-------|--------|
|`str`|`char`|
|`[type]`|`type`|
|`{key:value}`|`(key, value)`|

### Syntax:

```go
expression # {
  patterns
}
```

For each item in the input, the grid operator will generate an `(index, item)` tuple. The `index` field is an `int`, and the `item` field's type depends on the input type. If only one capture variable is mapped, its type will be `(int, _)`. If you provide an index variable and item variable, it will be destructured to those variables accordingly.

### Example:

```go
[1, 2, 3] # {
  i, n => print(`Item {i} = {n}`)
}
```
