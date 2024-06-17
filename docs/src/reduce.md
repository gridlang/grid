# Reduce

The `@` operator is used to reduce a sequence of types to a single type.

Here's the syntax:

```
expression @ accumulator, item -> type {
  // statements
}
```

This will iterate over the sequence input, capturing the item and the accumulator. For the first iteration, it's set to the default value of the item type. Each subsequent iteration is set to the return value of the previous iteration.

For example:

```
numbers = [1,2,3,4,5]
sum = numbers @ acc, n -> int {
  acc + n
}
// sum == 15
```
