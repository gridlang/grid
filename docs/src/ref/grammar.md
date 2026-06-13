# Grammar

A precise, lookup-oriented summary of Grid's surface syntax. For the *why* behind each
form, follow the links into [The Language](../substrate.md); for operator binding, see
[Operators and Precedence](operators.md); for the left of `=>`, see [Patterns](patterns.md).

## Lexical

- **Comments** run from `//` to end of line.
- **Separators.** A newline ends an item; `;` is the same separator on a single line, so
  `{ sys.print(e); 1 }` is two statements. Inside `(` `[` `{` and after a binary operator,
  newlines are insignificant, so an expression may wrap freely.
- **Identifiers** are `NAME`s. `_` is the wildcard name. There are only two reserved words,
  `module` and `import`; everything else — `int`, `add`, `Person` — is an ordinary label.
- **Literals:** `int` (`-123`), `num` (`-1.23e4`), `char` (`'z'`), `str` (`"hello"`),
  interpolated `str` (`` `x = {x}` ``), `()` unit. See [Literals and Types](../types.md).

## Items

A program (and a block body) is a sequence of **items**, newline- or `;`-separated:

```ebnf
program     = { item } ;
item        = module | import | destructure | binding | inplace | expr ;

module      = "module" NAME ;
import      = "import" NAME { ("/" | ".") NAME } ;

destructure = NAME { "," NAME } "=" expr ;          (* two or more names *)
binding     = NAME [ ":" ["&"] type ] "=" expr      (* "=" defines a new label *)
            | NAME ":" ["&"] type ;                 (* declaration; takes the type default *)
inplace     = NAME ("+=" | "-=" | "*=" | "/=") expr ;
```

`=` **defines** a new label in the current scope; `&` marks it
[mutable](../substrate.md#the-immutability-hinge); `+=` and friends mutate an existing `&`
in place. A type annotation (`: T`) is part of the binding but never changes a value.

## Functions

A `(...)` is a parameter list exactly when it is immediately followed by `->` or `>>`;
otherwise it is a tuple, struct, grouping, or unit.

```ebnf
fn      = "(" [ params ] ")" ( "->" type [ "!" type ] | ">>" type ) block ;
params  = param { "," param } ;
param   = NAME [ ":" ["&"] type ] ;
```

`-> T` is a plain function, `-> T ! E` is [fallible](../growth.md#fallibles), `>> T` is a
[stateful stream](../growth.md#streams). The body is a block whose last value is the
function's result.

## Expressions

```ebnf
expr     = ["~" | ">>"] ternary ;                   (* prefix defer / emit *)
ternary  = match [ "?" branch [ ":" branch ] ] ;    (* ?: — loosest, right-assoc *)
branch   = block | expr ;
match    = binary [ "=>" arm ] ;                    (* => — just under ?: *)
arm      = inplace | expr ;                          (* an arm result may be an inplace op *)
binary   = (* value & combinator operators — see Operators and Precedence *) ;
unary    = "-" unary | postfix ;
postfix  = atom { call | member | index | "!" } ;
call     = "(" [ expr { "," expr } ] ")" ;
member   = "." (NAME | INT) ;                       (* field, or tuple position *)
index    = "[" expr "]" ;
```

The `binary` level covers, tightest to loosest: `* / %`, `+ -`, bitwise `& | ^ << >>`,
`..`, comparison, the combinators `# @`, `&&`, `||`. The complete ordering — including how `?:` and `=>` sit
above them — is the [precedence table](operators.md).

## Atoms

```ebnf
atom    = INT | FLOAT | STR | CHAR | interp | NAME
        | "(" paren ")" | "[" bracket "]"
        | block | "@" block | fn ;

paren   = (* empty *)                               (* () — unit *)
        | NAME ":" expr { "," NAME ":" expr }       (* struct (x: 1, y: 2) *)
        | expr ","                                  (* (x,) — 1-tuple *)
        | expr { "," expr }                         (* (a, b) tuple, or grouping if one *)
        ;
bracket = (* empty *)                               (* [] — empty list *)
        | ":"                                       (* [:] — empty map *)
        | expr ":" expr { "," expr ":" expr }       (* map ["k": v] *)
        | expr { "," expr }                         (* list [a, b, c] *)
        ;

block   = "{" { item } "}" ;
interp  = "`" { text | "{" expr "}" } "`" ;
range   = expr ".." expr ;                          (* inclusive *)
```

`@ block` with no left operand is the [bare infinite loop](../growth.md#exits-without-keywords).
A `{ … }` is *only ever* a [block](../holes.md) — never a map or a struct — which is why the
bracket families above are unambiguous.

## Patterns

The left of `=>` is a **pattern** — syntactically a restricted literal, matched against the
block's topic ([Patterns](patterns.md) gives the matching rules):

```ebnf
pattern = literal | NAME | "_" | "(" ")"             (* literal · bind · wildcard · unit *)
        | "(" pattern { "," pattern } ")"            (* tuple — also matches a struct by position *)
        | "[" pattern { "," pattern } [ "," "..." ] "]" ;   (* list, optional trailing rest *)
```

## Blocks and combinators

A `{block}` binds to the `#` / `@` combinator on its immediate left as a tight unit, and a
combinator's left operand is its [source](../triad.md):

```ebnf
fanout  = source "#" block ;        (* map / filter, in parallel *)
thread  = source "@" block ;        (* reduce / loop / find, in sequence *)
```

A literal block *as the source* of `@` (`{ cond } @ { body }`) is a re-evaluated
[generator](../triad.md#thread) — the loop/while form; any other source is evaluated once.
