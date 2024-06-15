# Grid

Grid is a high-level language using a mix of imperative and functional constructs, with a focus on being easy to read and reason about.

## Goals

- Reducing the amount of boilerplate required for powerful constructs
- Structural typing
- Type and value pattern matching
- Clear native type truthiness
- Scope-based memory management without explicit ownership or lifetime tracking
  - No garbage collector or reference counting, no borrow checking
- No external dependencies for self-hosting compiler
- First-class functions

## Structure

A grid program can be split into multiple source files called modules that serve to group files into namespaces. So a source file has the following structure:

```
#module <name>

[import [path/]module]

[statements]
```

The only required module is `main`, which must exist in at least one source file the compiler reads. If a source file is in a subdirectory of the project root, it can be addressed via the `path` portion for importing into the current module as seen above.

Importing a module makes its contents available in the current module via namespacing and the [Member](#Membership) operator `.`. If we have the following module named `main.grid` for example:

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

## Functions

Functions are a way to define a named unit of code which can be called later, optionally passing data into it, and optionally receiving data back out. They are defined as follows:

```
<funcname> = (<argname>: <argtype>) -> <returntype> {
  // ...
}
```

Functions are called with a similar syntax:

```
<varname> = <funcname>(<argname>)
```

If the function returns a value you can assign it in an expression as seen above, but this is not required.

## Membership

We can refer to objects in a namespace via the Member operator `.` as well as indexes of a tuple.

## Literals and Native Types

Grid provides a set of native types that are a core part of the language, and accompanying syntax for specifying literal data of these types. They are as follows:

- bool :: Boolean value, `true` or `false`
  - `b = true`
- int :: Integer number, using digits 0-9, optional `-` prefix for negative
  - `i = -123`
- num :: Rational number, using digits 0-9, optional `-` prefix and optional `.` for decimals
  - `f = 1.23`
- char :: UTF-8 character, specified inside single quotes `''`
  - `c = 'z'`
- str :: UTF-8 string, specified inside double quotes `""`
  - `s = "Hello"`
- [type] :: homogenous list of `type`, specified inside square brackets `[]`
  - `l = [1,2,3]`
- {typeA:typeB} :: homogenous map of `typeA` to `typeB`, specified inside braces `{}`
  - `m = {1: "a", 2: "b", 3: "c"}`
- (typeA, typeB, typeC) :: anonymous tuple of types, specified inside parens `()`
  - `t = ("a", 'b', [1, 2], 3.0)`
- (name: type) :: structural tuple, named fields with types, specified inside parens `()`
  - `s = (a: int, b: char)`

**Defaults**

Each of these types has a *default* value it's initialized with. These default values allow for a clearly defined *truthiness* when used in pattern matching or relational [operators](#operators).

The default for each type is as follows:

| bool        |  false |
| int         |      0 |
| float       |    0.0 |
| char        |     '' |
| str         |     "" |
| [type]      |     [] |
| {type:type} |     {} |
| (type)|     |     () |
| (name:type) | (name:*default*) |

We can use this in [pattern matching](#flow-control) to evaluate truthiness, because defaults are considered `false`. In other words, a non-default value can be used as shorthand for `true` in a match.

Here's an example to illustrate:

```
s = ""
s ? {
  s -> print("Non-empty")
  _ -> print("Empty")
}
```

This is equivalent to using `s == ""` which evaluates to a `bool`, then matching directly on the value.

For example:

```
s = ""
s == "" ? b {
  false -> print("Non-empty")
  true -> print("Empty")
}
```

By treating all default values of any type as false, and by using variables in patterns instead of literals, we can simplify conditional syntax without introducing type coercions or ambiguity.

**Tuples**

You'll notice that function definitions use structural tuples for the parameters, and function calls use anonymous tuples for arguments. We can also uses these tuples on their own, or in return types.

As mentioned in the section on [membership](#membership), we can use the `.` operator to access the fields of tuples.

```
a = (1, "2", [3])
a.0 // 0th field
b = (x: 1, y: "2", z: [3])
b.x // named field 'x'
```

## Operators

Grid provides a variety of operators for use in expressions, with some particular interactions between different types.

**Relational**
```
< <= != == >= >
```

*int, float, char (ordinal), str (length)*

**Boolean**
```
&& || !!
```

*Relational, bool*

**Bitwise**
```
& | ^ ! << >>
```

*int, char*

**Arithmetic**
```
+ - * / % **
```

*int, float*

**Assignment**
```
+= -= *= /=
```

*int, float*

## Variables

Variables are handles to data of a type. They are declared using the following syntax:

```
<name> [, <name>] = <expression>
```

A name and value are required. The type is based on the right-hand side of the assignment:
- If it is a literal, the type is explicit in the syntax of the literal.
- If it is a function call, the return type of the function is used.
- If it is the name of another variable, see the section on [moves](#references-ownership-borrowing-and-moves)

The left-hand side can optionally be a list of names, which are used to *destructure* a Tuple on the right-hand side. This is useful for extracting fields from function returns, for example.

## References, Ownership, Borrowing, and Moves

Many modern languages have various ways to approach management of data via variables, and Grid takes concepts from some of them, but ultimately uses a very simple set of concepts that make it easy to read and reason about the code.

Fundamentally, Grid treats variables as *handles* to data, and not *buckets* that contain values. This becomes very important when it comes to the concept of references and ownership.

The important distinction in how Grid treats variables is that in statements where one variable is assigned to another, the old handle is invalidated. In some languages this is known as a *move*, and we'll use the same terminology here.

For example:

```
a = 1
b = a
print(a) // This will error
```

By assigning the variable `b` to the variable `a`, we have moved the ownership of data to `b`. This is the concept of variables as handles instead of buckets. There's really only one rule to remember: Only one handle may point to a specific piece of data at any point in time.

Another choice of language design arises when it comes to passing data into functions. Some languages use what's called pass-by-value, some use pass-by-reference, and many allow you to choose between the two. Grid always passes by reference, with a few special rules that avoid common downsides (see [Scope](#Blocks-and-Scope) and [Memory](#Memory-Management))

When we pass a variable into a function by reference, it can also be understood as *borrowing*. This means that a new handle to the variable will exist for the passed in data for the duration of the function, but will not *move* it away from the original handle.

For example:

```
i = 0
inc = (arg: int) {
  arg = arg + 1
}
inc(i)
// i == 1 now
```

The variable `i` is passed into `inc`, but is mapped in the function as `arg`, and is thus borrowed. It is still a handle to the data pointed to by `i`, which means adding 1 to `arg` will affect `i` once the function completes.

Additionally, when you use the `return` keyword to pass a value back out of the function, if you use a variable that was defined inside the function, the data it references will be *moved* back to the calling scope.

```
createArray = () -> [int] {
  arr = [1,2,3,4]
  return arr
}
result = createArray()
```

This will move the data referred to by `arr` to the calling scope and assign `result` to it.

## Blocks and Scope

Grid operates similarly to most modern languages when it comes to the concept of *scope*.

- The topmost scope is the *global* scope; objects here are visible from other modules
- Blocks are delineated with braces `{}`, and can be nested
- Each block defines a scope, which confines variables and functions within that scope
- Outer scopes are directly accessible from inner scopes

Assigning to a variable from an outer scope moves the value into that scope the same as assigning within the same scope.

Additionally, blocks have an implicit value. The result of the last expression in a block is considered the value of the block, so if it occurs in a larger expression it can be replaced with its effective value.

## Memory Management

When a literal is created, memory is allocated for it. If it's assigned to a variable, that memory lasts until it goes out of scope.

Under the covers, values that map to native types will generally be allocated on the stack, where compound data structures may be allocated on the heap. Variables being treated as handles is implemented by them functioning essentially as pointers, without requiring explicit dereferencing or indirection.

When objects are moved, for simple types native to the architecture (int/float/bool/char generally) values may be copied if it's more efficient than changing pointers. From the Grid perspective however, semantically everything is moved.

Lastly, all objects within a scope are automatically freed at the end of that scope. For stack objects, nothing is required. For heap objects, the memory is freed via OS interfaces.

## Flow Control

Grid provides a few flow-control constructs that also provide pattern matching.

First we'll cover regular conditionals. They have the following syntax:

```
<expression> ? [<capturevar> [, <capturevar>]] {
  <type> => ...
  <value> -> ...
}
```

This construct allows us to match on expressions, which replaces the `if`/`else` constructs in most languages. This also applies to return values from functions.

For example:

```
a < b ? {
  true -> ...
  false -> ...
}

read = (f: str) -> str, str {
  syscall_read(f) ? result, err {
    err -> return ("", "Error reading file")
    _ -> return (result, "")
  }
}

data = read("test.txt") ? r, e {
  e -> panic(e)
  _ -> r
}
```

In this example we can see both anonymous and captured conditionals. If no capture vars are provided, the result of the expression can still be matched against anonymously via literals or types.

## Loops

Looping conditionals work the same way as regular ones, with a different operator and a bit more functionality.

Here's the syntax for example:

```
<expression> @ [<capturevar> [, <capturevar>]] {
  // statements
}
```

In this construct, the expression is evaluated repeatedly until `break` is encountered. The keyword `continue` is also usable to skip to the beginning and repeat the iteration.

Note that unless `return`, `break`, or `exit` is used, the loop will never exit.

## Ranges

Ranges are the last important piece of flow control. They use the `#` operator and iterate over the following collection types:

- String
- List
- Map

An example is:

```
<collection> # <capturevar> {
  // statements
}
```

For each item in the collection, it will be mapped to the capturevar and execute the block.

## Comprehensions

Using combinations of these operators, we can compactly represent different types of comprehensions.

For example:

```
numbers = [1,2,3,4,5]
evens = numbers # n { n % 2 -> n }
```

## Example

```
module main

import sys

indexOf = (s: str, t: char) -> int {
  s # i, c {
    c == t -> return i
  }
}

// Function to handle HTTP requests
handleRequest = (clientSocket: int) -> int {
  // Read the request from the client
  request = sys.read(clientSocket, 1024) ? result, err {
    err -> {
      sys.print("Error reading request")
      return -1
    }
    result -> result
    _ -> return 0
  }

  // Parse the HTTP verb from the request
  verb = request[0:indexOf(request, ' ')]

  // Match the verb and respond accordingly
  verb ? {
    "GET" -> {
      response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello, GET request!"
      sys.write(clientSocket, response)
    }
    "POST" -> {
      response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello, POST request!"
      sys.write(clientSocket, response)
    }
    _ -> {
      response = "HTTP/1.1 405 Method Not Allowed\r\nContent-Type: text/plain\r\n\r\nMethod Not Allowed"
      sys.write(clientSocket, response)
    }
  }

  // Close the client socket
  sys.close(clientSocket)
  // 0 is default
}

// Main function to start the HTTP server
main = (argc: int, argv: [str]) -> int {
  port = 8080

  // Open a socket
  serverSocket = sys.socket(sys.AF_INET, sys.SOCK_STREAM, 0) ? sock, err {
    err -> {
      sys.print("Error creating socket")
      return -1
    }
    _ -> sock
  }

  // Bind the socket to the port
  sys.bind(serverSocket, sys.sockaddr_in(port, sys.INADDR_ANY)) ? err {
    err -> {
      sys.print("Error binding socket")
      return -1
    }
  }

  // Listen for incoming connections
  sys.listen(serverSocket, 5) ? err {
    err -> {
      sys.print("Error listening on socket")
      return -1
    }
  }

  sys.print("Server listening on port ", port)

  // Accept connections in a loop

  !sys.closed(serverSocket) @ running {
    running ? {
      false -> break
    }

    clientSocket = sys.accept(serverSocket) ? sock, err {
      err -> {
        sys.print("Error accepting connection")
        break
      }
      _ -> sock
    }

    // Handle the request in a separate function
    handleRequest(clientSocket)
  }

  // Close the server socket
  sys.close(serverSocket)
  // 0 is default
}
```
