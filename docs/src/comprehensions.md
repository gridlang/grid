# Comprehensions

Using combinations of [flow-control](flow-control.md) [operators](operators.md), we can compactly represent different types of comprehensions.

### Example:

```go
numbers = [1,2,3,4,5]
evens = numbers # _, n {
  n % 2 => (0:n)
}
odds = numbers # _, n {
  n % 2 => (1:n)
}
```
