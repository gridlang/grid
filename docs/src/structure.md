# Structure

A grid program can be split into multiple source files called modules that serve to group files into namespaces. A source file has the following structure:

```go
module name

import path/module

statements
```

The only required module in a project is `main`, which must exist in at least one source file the compiler reads. If a source file is in a subdirectory of the project root, it can be addressed via the `path` portion for importing into the current module as seen above.

Importing a module makes its contents available in the current module via namespacing and the [member](operators.md) operator `.`

If we have the following module named `main.grid` for example:

```go
module main

import hello
import sys

main(int, [str]) = argc, argv -> int {
  sys.print(test.greeting)
}
```

And we have another module `hello.grid` with the following:

```go
module hello

greeting = "Hello, world!"
```

Then compiling and running the project will print the line "Hello, world!" as you might expect.

The `main` module is special as it is where a `main` function must be defined, and is where execution of your program will begin. The `main` function always takes two arguments -- the length of the program arguments, and an array of the arguments -- and must return an integer -- the exit code for the program.
