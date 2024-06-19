# Functions

Functions are a way to define a named unit of code which can be called later, optionally passing data into it, and optionally receiving data back out. They are defined as follows:

```go
funcname(argtypes) = argnames -> returntypes {
  // ...
}
```

The minimum required syntax with no inputs or outputs is:

```go
funcname() = -> { }
```

Functions are called with a similar syntax:

```go
varname = funcname(argument)
```

If the function returns a value you can assign it in an expression as seen above, but this is not required.
