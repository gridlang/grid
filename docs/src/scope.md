# Scope

Grid operates similarly to most modern languages when it comes to the concept of ***scope***.

- The topmost scope is the module scope; functions and constants here are visible from other modules
- Values defined at the module scope are always constant
- Constants are visible from any scope
- Blocks are delineated with braces `{}`, and can be nested
- Each block defines a scope, which confines variables and functions within that scope
- Variables in outer scopes are accessible from inner scopes within the same function

## Blocks

Blocks have an implicit value. The result of the last expression in a block is considered the value of the block, so if it occurs in a larger expression it can be replaced with its effective value.
