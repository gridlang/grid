# Scope

Grid operates similarly to most modern languages when it comes to the concept of ***scope***.

- The topmost scope is the module scope; functions and variables here are visible from other modules
- Blocks are delineated with braces `{}`, and can be nested
- Each block defines a scope, which confines variables and functions within that scope
- Variables in outer scopes are accessible from inner scopes

## Blocks

Blocks have an implicit value. The result of the last expression in a block is considered the value of the block, so if it occurs in a larger expression it can be replaced with its effective value.

