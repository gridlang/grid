# Blocks and Scope

Grid operates similarly to most modern languages when it comes to the concept of *scope*.

- The topmost scope is the *global* scope; objects here are visible from other modules
- Blocks are delineated with braces `{}`, and can be nested
- Each block defines a scope, which confines variables and functions within that scope
- Outer scopes are directly accessible from inner scopes

Assigning to a variable from an outer scope moves the value into that scope the same as assigning within the same scope.

Additionally, blocks have an implicit value. The result of the last expression in a block is considered the value of the block, so if it occurs in a larger expression it can be replaced with its effective value.

