# Ownership

Many modern languages have various ways to approach management of data via variables, and Grid takes concepts from some of them, but ultimately uses a very simple set of concepts that make it easy to read and reason about the code.

Fundamentally, Grid treats variables as *handles* to data, and not *buckets* that contain values. This becomes very important when it comes to the concept of references and ownership.

## Moves

The important distinction in how Grid treats variables is that in statements where one variable is assigned to another, the old handle is invalidated. In some languages this is known as a *move*, and we'll use the same terminology here.

For example:

```
a = 1
b = a
print(a) // This will error
```

By assigning the variable `b` to the variable `a`, we have moved the ownership of data to `b`. This is the concept of variables as handles instead of buckets.

There's really only one rule to remember: **Only one handle may point to a specific piece of data at any point in time.**

## References

Another choice of language design arises when it comes to passing data into functions. Some languages use what's called pass-by-value, some use pass-by-reference, and many allow you to choose between the two. Grid always passes by reference, with a few special rules that avoid common downsides (see [Scope](scope.md) and [Memory](memory.md))

## Borrowing

When we pass a variable into a function by reference, it can also be understood as *borrowing*. This means that a new handle to the variable will exist for the passed in data for the duration of the function, but will not *move* it away from the original handle.

For example:

```
i = 0
inc = (arg: int) {
  arg = arg + 1
}
inc(i)
// i == 1 now
```

The variable `i` is passed into `inc`, but is mapped in the function as `arg`, and is thus borrowed. It is still a handle to the data pointed to by `i`, which means adding 1 to `arg` will affect `i` once the function completes.

## Returns
Additionally, when you use the `return` keyword to pass a value back out of the function, if you use a variable that was defined inside the function, the data it references will be *moved* back to the calling scope.

```
createArray = () -> [int] {
  arr = [1,2,3,4]
  return arr
}
result = createArray()
```

This will move the data referred to by `arr` to the calling scope and assign `result` to it.

