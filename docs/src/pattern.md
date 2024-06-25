# Pattern Matching

Pattern matching can be used with any of the [flow-control](flow-control.md) operators. These operators take an expression as input, and have distinct behaviors based on the operator.

Patterns are composed of clauses using the `=>` operator. The left-hand side can be a [literal](types.md) or map the result of the input expression to [variables](variables.md), matching against the pattern they occur in.

The match pattern represents truthiness (non-default) evaluation in the following ways:
- For each literal, it must match the value of the input in that position
- For each variable, it must be truthy in that position

The `_` symbol is used to represent a pattern position which always matches.

### Minimal Syntax:

```go
expression flow-operator {
  literal => { // match if literal matches expression result
    // statements
  }
  var => { // map to var and match if non-default
    // statements using mapped variable
  }
  _ => {
    // default else case if no patterns match
  }
}
```

The pattern position concept is better illustrated when the input is a tuple, and we want to match some of the fields and map others.

The left-hand side can destructure the input tuple, mapping by field, or `_` can match the whole input as ultimate fallback.

### Example:

```go
httpGet(url) ? { // returns (response, status) tuple
  response, 200 => { // map response var, match status literal
    print("Success: {response}")
  }
  response, 404 => {
    print("Not found")
  }
  _ => { // No pattern matched
    print("HTTP error with status: {status}")
  }
}
```

In this example:
- The `httpGet(url)` function call returns a `(response, status)` tuple.
- Depending on the `status`, different blocks of code are executed.
- The default case (`_`) handles situations where none of the specific patterns match.

### Example:

We can also use only `_` in some fields of tuple matches and mapped variables in others, which in effect singles out the mapped fields for truthy evaluation, allowing us to pick which parts to match on for further sub-expressions or blocks using those variables.

```go
authenticate(user, pass) ? { // returns (authResult, error)
  _, error => {
    print("Authentication failed")
    return -1
  }
  authResult, _ => {
    authResult.role ? {
      "admin" => {
        fetchData(authResult.userId, "admin") ? { // returns (data, fetchErr)
          _, fetchErr => {
            print("Failed to fetch admin data: {fetchErr}")
            return -1
          }
          data, _ => processAdminData(data)
        }
      }
      "user" => {
        fetchData(authResult.userId, "user") ? { // returns (data, fetchErr)
          _, fetchErr => {
            print("Failed to fetch user data: {fetchErr}")
            return -1
          }
          data, _ => processUserData(data)
        }
      }
      _ => {
        print("Unknown role: {role}")
        return -1
      }
    }
  }
}
```

This example illustrates how you can:
- Authenticate a user and map the result.
- Handle errors that occur during authentication.
- Use pattern matching to execute role-based logic, including fetching and processing data only if the user role matches specific patterns.
