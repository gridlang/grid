# HTTP Server

The flagship — a tiny HTTP server that stresses every layer at once: structs, the
[triad](../triad.md), [matching](../match.md), [fallibles](../growth.md#fallibles),
[defer](../growth.md#defer), [interpolation](../types.md#interpolation), and the keyless
control flow, all together.

## Setup

The only declarations outside expression space are `module` and `import`. A struct is a
[named tuple](../types.md#tuples-and-structs--both--); a plain function returns its body's
last value.

```grid
module main

import net          // listen / accept / readline / read / write / close, and Conn
import str          // words / lines / trim / join
import sys          // print

Request  = (method: str, path: str, body: str)
Response = (status: int, body: str)

ok   = (body: str)             -> Response { (status: 200, body: body) }
fail = (status: int, msg: str) -> Response { (status: status, body: msg) }
```

## Handlers

`?` opens a block with its subject as the [topic](../match.md#the-topic); `=>` matches it.
The `hello` handler defaults an empty body with a literal arm, else binds and trims it. The
`lines` handler [fans out](../triad.md#fan-out) over the lines and collects.

```grid
hello = (req: Request) -> Response {
  name = req.body ? {
    ""  => "world"          // the literal arm: body is exactly ""
    raw => str.trim(raw)    // else bind the topic
  }
  ok(`hello, {name}!\n`)
}

echo = (req: Request) -> Response { ok(req.body) }

lines = (req: Request) -> Response {
  numbered = str.lines(req.body) # { (i, line) => `{i + 1}: {line}\n` }
  ok(str.join(numbered, ""))
}
```

## Routing

Match a **tuple topic** positionally — the request's method and path at once. The final
`(m, p)` arm binds both and acts as the catch-all 404:

```grid
route = (req: Request) -> Response {
  (req.method, req.path) ? {
    ("GET",  "/hello") => hello(req)
    ("GET",  "/echo")  => echo(req)
    ("POST", "/lines") => lines(req)
    (m, p)             => fail(404, `no route: {m} {p}\n`)
  }
}
```

## Request parsing

`-> T ! E` is [fallible](../growth.md#fallibles); `!` propagates a failure or, on a plain
value, raises it. A 3-element [list pattern](../ref/patterns.md) destructures the request
line; a `{ … } @` generator consumes header lines until the blank separator.

```grid
read_request = (c: net.Conn) -> Request ! str {
  parts = str.words(net.readline(c)!)          // ! : propagate a read failure
  parts ? {
    [method, path, _] => {                      // a 3-element list pattern
      { net.readline(c)! != "" } @ { () }       // skip headers: loop while non-blank, eat the blank
      body = net.read(c, 8192)!
      (method: method, path: path, body: body)
    }
    _ => "bad request line"!                     // raise: fail with this error value
  }
}
```

## Per connection

`~` [defers](../growth.md#defer) cleanup to every exit path, in LIFO order. The bare `@ { … }`
is the [infinite loop](../growth.md#exits-without-keywords); each iteration ends in `()` so
it keeps looping, and a propagated `!` is what finally escapes it.

```grid
handle = (c: net.Conn, id: int) -> () ! str {
  ~net.close(c)                                  // deferred; runs on every exit path
  ~sys.print(`[{id}] closed\n`)                  // LIFO: this prints, then close runs
  sys.print(`[{id}] open\n`)
  @ {
    resp = route(read_request(c)!)
    net.write(c, `HTTP/1.1 {resp.status}\r\n\r\n{resp.body}`)!
    ()                                           // body yields () -> keep looping
  }
}
```

## The accept loop and entry

`serve` loops accepting connections; a failed `accept` is fatal and propagates, while each
connection's own failures stay local (its result is dropped). `main` is not fallible, so it
takes the error pair apart by hand and turns it into an exit code — `args[0] || …` is a
[partial index](../present.md#every-operator-is-partial) defaulted with `||`.

```grid
serve = (addr: str) -> () ! str {
  listener = net.listen(addr)!
  id: &int = 0
  @ {
    c = net.accept(listener)!                    // a failed accept is fatal -> propagates
    id += 1
    handle(c, id)                                // its own failures stay local (result dropped)
    ()
  }
}

main = (args: [str]) -> int {
  addr = args[0] || "0.0.0.0:8080"               // partial index + || selector
  sys.print(`listening on {addr}\n`)
  _, err = serve(addr)                           // take the fallible pair apart
  err ? { e => { sys.print(`fatal: {e}\n`); 1 } } : 0
}
```

Every layer is here: ownership in the `&` accumulator, the triad in `#` and `@`, the
keystone in every `?` and `!`, the containers in `Request`/`Response`, and Layer 5 in
`~`, `!`, and the loops — and not one `if`, `for`, `return`, `break`, or `try`.
