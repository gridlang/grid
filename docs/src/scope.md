# Scope

Grid operates similarly to most modern languages when it comes to the concept of ***scope***.

- The topmost scope is the module scope; ***functions*** here are visible from other modules
- Blocks are delineated with braces `{}`, and can be nested
- Each block defines a scope, which confines variables and functions within that scope

However, there are some key differences:

- Variables in outer scopes are not accessible from inner scopes
- Variables can be passed into function scopes as arguments, or operator scopes as captures

The key concept here is that scopes are pure. They cannot have side-effects because they cannot directly access variables from other scopes, and variables passed into them are pass-by-value.

## Blocks

Blocks have an implicit value. The result of the last expression in a block is considered the value of the block, so if it occurs in a larger expression it can be replaced with its effective value.

They can be used directly to encapsulate statements, and thus can be used directly in an expression.

For example:

```
result = {
  // do calculations
  data
}
```

This will assign `data` to `result` in the outer scope.
