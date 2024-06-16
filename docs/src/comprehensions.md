# Comprehensions

Using combinations of [flow-control](flow-control.md) [operators](operators.md), we can compactly represent different types of comprehensions.

For example:

```
numbers = [1,2,3,4,5]
odds = numbers # n { n ? { n % 2 => n } }
evens = numbers # n { n ? { n % 2 !> n } }
```
