# Types

Grid provides a set of base types that are a core part of the language, accompanied by syntax for specifying literal data of these types.

The following table lists the type pattern, an example literal in Grid syntax, and the default value for the type:

| Type Pattern | Literal Example | Default | Description |
|--------------|-----------------|---------|-------------|
| `bool`       | `true`          | `false` | Boolean value |
| `int`        | `-123`          | `0`     | Integer number |
| `num`        | `-1.23e4`       | `0.0`   | Real number |
| `char`       | `'z'`           | `''`    | Single character |
| `str`        | `"hello"`       | `""`    | String of characters |
| `[type]`     | `[1, 2, 3]`     | `[]`    | Array of type |
| `<type:type>`| `<"x": 1, "y": 2>` | `<>`| Map of type to type |
| `(type,type)`| `(1, "2", [3])` | `()`    | Anonymous tuple of types |
| `(name:type)`| `(x:1, y:"2", z:[3])` | `(field:default)` | Structured tuple of types |
| `(type) -> type` | `(i:int) -> str` | `()->()` | Function |
| `(type) >> type` | `(i:int) >> str` | `()>>()` | Stateful function |
| `{...}`      | `{ ... }`       | `{}`    | Block |

Each of these types has a *default* value it's initialized with. These default values allow for a clearly defined *truthiness* when used in pattern matching or relational [operators](operators.md). The `(field:default)` for structured tuples indicates that whatever the type of the fields in that tuple are, their defaults will be used as the value of the fields.

## Truthiness

Grid evaluates truthiness based on default values. Defaults are considered `false`, whereas non-default values are considered `true`. This allows for simple and clear conditional syntax without ambiguity or type coercion. A tuple of all default values is also considered `false`, whereas a tuple with any non-default values is considered `true`.

### Example:

```go
s = ""
s ? {
  print("String is non-empty")
}
```

This is equivalent to:
```go
s = ""
s != "" ? {
  print("String is non-empty")
}
```

## Tuples

Tuples are flexible data types in Grid used in several contexts. For instance, [function definitions](functions.md) use structural tuples for the parameters, and function calls use anonymous tuples for arguments.

Anonymous tuple literals can be assigned to variables or used as type definitions. Tuple fields can be accessed using the `.` operator.

### Example:

```go
a = (1, "2", [3])
f = (g:(int, str)) -> () {
  print(g.0) // prints 1
}
f((1, "2"))
```

## Custom Types

Structural tuples are the main mechanism for defining custom types in Grid.

### Example:

```go
Person = (name: str, age: int)
p = Person(name:"Alice", age:42)
print(p.name) // prints "Alice"
```

By assigning a structural tuple a name, we can use the name as a custom type in other tuples.

### Example:

```go
Person = (name: str, age: int)
f = (p: Person) -> () {
  print(`{p.name}: {p.age}`) // uses the Person structure
}
p = Person(name:"Bob", age:35)
f(p)
```

## Composing Types

Grid allows combining custom types through composition using the `&` (intersection) and `|` (union) operators.

### Example:

```go
a = (i: int)
b = (s: str)
c = a & b // (i: int, s: str)
d = a & (i: int, t: (int)) // (i: int, t: (int))
e = b | c // (s: str)
```

## Structured Typing

Structured typing in Grid ensures that types interact seamlessly across different contexts, such as function definitions and arguments.

### Example:

```go
Person = (name: str, age: int)
Employee = Person & (id: int, job: str)
printPerson = (p: Person) -> () {
  print(`{p.name}: {p.age}`)
}

e = Employee(id: 1, name: "Bob", age: 35, job: "Manager")
printPerson(e) // valid because Employee is compatible with Person
```

## Block

Blocks in Grid are represented by `{...}` and can form various types of data structures or executable code sequences. Blocks have a value they resolve to, and can thus be assigned to variables. The last expression or value in a block is used as its effective value in larger expressions.

### Example:

```go
dataProcessor = {
  loadData()
  processData()
  exportData()
}
```
