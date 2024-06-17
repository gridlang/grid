# Comprehensions

Using combinations of [flow-control](flow-control.md) [operators](operators.md), we can compactly represent different types of comprehensions.

For example:

```go
numbers = [1,2,3,4,5]
odds = numbers # _, n { n ? { n % 2 => n } }
evens = numbers # _, n { n ? { n % 2 !> n } }
```
