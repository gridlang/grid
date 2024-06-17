# Ranges

Ranges are the last important piece of flow control. They use the `#` operator and iterate over the following types:

| Input | Output |
|-------|--------|
|`str`|`char`|
|`[type]`|`type`|
|`{key:value}`|`(key, value)`|

An example is:

```
expression # indexvar, itemvar {
  // statements
}
```

For each item in the input, it will be mapped to the capture and execute the block.

As indicated in the example, the range operator will generate an index (int) and item (depending on input type). If only one capture variable is provided, it's type will be `(int, _)` where the item type depends on the input as listed above. If you provide an index variable and item variable name, it will be destructured to those fields accordingly.
