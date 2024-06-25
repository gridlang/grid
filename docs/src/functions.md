# Functions

Functions are a way to define a named unit of code which can be called later, optionally passing data into it, and optionally receiving data back out.

### Syntax:

```go
funcname = (name:type) -> type {
  // ...
}
```

This is the minimum required syntax with no inputs or outputs.

```go
funcname = () -> () {
  // ...
}
```

## Calling

Functions are called with a similar syntax.

```go
varname = funcname(argument)
```

If the function returns a value you can assign it in an expression as seen above, but this is not required.

## Returns

When a function is called, any arguments passed into it become variables available to the function's scope, mapped to the names given in the definition. The value of the arguments is used to initialize the variables.

### Example:

The `return` keyword will immediately exit the function, optionally returning a value if the function definition specifies a return type.

```go
returnInt = () -> int {
  return 1
}

i = returnInt()
```

## Stateful Functions

In many languages there is the concept of a closure, which is a function that encloses the scope it's defined in, essentially capturing state. Grid has a similar feature but it's implemented in a way that's easier to reason about, in the form of ***stateful functions***.

### Syntax:

Stateful functions are defined with this pattern.

```go
f = (name:type) >> type {
  // ...
}
```

Just like `return`, the `yield` keyword will also exit a stateful function, optionally returning a value, but the state of the function's execution will be retained at the location of the yield if the function is defined as stateful.

### Example:

```go
cycle = (items: [str]) >> str {
  @ {
    items # {
      _, item => yield item
    }
  }
}
```

When we call `cycle` we can provide a list of strings which initializes the function, but it does not return a string value. Instead it returns a function which has the same return type as the stateful function, but takes no arguments. In this example, `() -> str` is the type of the returned function.

We can think of this as returning an instance or copy of the stateful function that's been initialized with the arguments passed into it.

Calling the returned function will repeat the function body each time, passing back execution and values on `yield`, and resuming from that point when repeated again.

### Example:

```go
color = cycle(["red", "green", "blue"]) // Initialize
// color = () -> str
color() // "red"
color() // "green"
color() // "blue"
color() // "red"
```

### Example:

We can create another function with different initializers with the same syntax.

```go
names = cycle(["bob", "alice"])
names() // "bob"
names() // "alice"
```
