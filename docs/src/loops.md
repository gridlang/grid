# Loops

Looping conditionals work similarly to plain conditionals, but with a different operator and a bit more functionality.

Here's the syntax:

```
expression @ capturevar, capturevar {
  // statements
}
```

As in other captures, the capture variables are optional, and will destructure if the expression is a tuple.

In this construct, the expression is evaluated repeatedly until `break` is encountered. The keyword `continue` is also usable to skip to the beginning and repeat the iteration.

Note that unless `return`, `break`, or `exit` is used, the loop will never exit.
