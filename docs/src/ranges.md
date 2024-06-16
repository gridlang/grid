# Ranges

Ranges are the last important piece of flow control. They use the `#` operator and iterate over the following collection types:

- String
- List
- Map

An example is:

```
<collection> # <capturevar> {
  // statements
}
```

For each item in the collection, it will be mapped to the capturevar and execute the block.

