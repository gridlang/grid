# Memory Management

When a literal is created, memory is allocated for it. If it's assigned to a variable, that memory lasts until it goes out of scope.

Under the covers, values that map to native types will generally be allocated on the stack, where compound data structures may be allocated on the heap. Variables being treated as handles is implemented by them functioning essentially as pointers, without requiring explicit dereferencing or indirection.

When objects are moved, for simple types native to the architecture (int/float/bool/char generally) values may be copied if it's more efficient than changing pointers. From the Grid perspective however, semantically everything is moved.

Lastly, all objects within a scope are automatically freed at the end of that scope. For stack objects, nothing is required. For heap objects, the memory is freed via OS interfaces.

