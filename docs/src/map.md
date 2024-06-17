# Map

The `#` operator -- also known as the Grid operator -- is used to map over the following types:

| Input | Output |
|-------|--------|
|`str`|`char`|
|`[type]`|`type`|
|`{key:value}`|`(key, value)`|

An example is:

```
expression # indexvar, itemvar -> returntype {
  // statements
}
```

For each item in the input, it will be mapped to the capture and execute the block.

As indicated in the example, the range operator will generate an index (int) and item (depending on input type). If only one capture variable is provided, it's type will be `(int, _)` where the item type depends on the input as listed above. If you provide an index variable and item variable name, it will be destructured to those fields accordingly.

## Parallelism

Grid blocks are executed in parallel, without the need for synchronization primitives, because all scopes are pure. No data is shared across the threaded scopes, so parallelizing is straightforward.

## Return Value

Grid blocks can specify a return type, which defines how to map returns from the parallel executions.

For example:

```
numbers = [1,2,3,4,5]
plusOne = numbers # _, n -> [int] {
  n + 1
}
// plusOne == [2,3,4,5,6]
```

