# Structure

A grid program can be split into multiple source files called modules that serve to group files into namespaces. So a source file has the following structure:

```
#module <name>

[import [path/]module]

[statements]
```

The only required module is `main`, which must exist in at least one source file the compiler reads. If a source file is in a subdirectory of the project root, it can be addressed via the `path` portion for importing into the current module as seen above.

Importing a module makes its contents available in the current module via namespacing and the [Member](membership.md) operator `.`. If we have the following module named `main.grid` for example:

```
module main

import hello

main = (argc: int, argv: [str]) -> int {
  print(test.greeting)
}
```

And we have another module `hello.grid` with the following:

```
module hello

greeting = "Hello, world!"
```

Then compiling and running the project will print the line "Hello, world!" as you might expect.

The `main` module is special as it is where a `main` function must be defined, and is where execution of your program will begin. The `main` function always takes two arguments -- the length of the program arguments, and an array of the arguments -- and must return an integer -- the exit code for the program.
