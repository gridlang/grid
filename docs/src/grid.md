# Grid

The `#` operator -- also known as the Grid operator -- is used to iterate over the following types:

| Input | Output |
|-------|--------|
|`str`|`char`|
|`[type]`|`type`|
|`{key:value}`|`(key, value)`|

An example is:

```go
expression # indexvar, itemvar -> returntype {
  // statements
}
```

For each item in the input, it will be mapped to the capture and execute the block.

As indicated in the example, the grid operator will generate an index (int) and item (depending on input type). If only one capture variable is provided, it's type will be `(int, _)` where the item type depends on the input as listed above. If you provide an index variable and item variable, it will be destructured to those variables accordingly.
