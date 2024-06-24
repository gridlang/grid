# Pattern Matching

Pattern matching provides a more granular control by evaluating an expression and mapping its result to variables, then matching against specific patterns. It follows this pattern:
```go
expression => variables (
  pattern1: {
    // statements for pattern1
  },
  pattern2: {
    // statements for pattern2
  },
  _: {
    // default else case if no patterns match
  }
)
```

### Example:

Here is an example demonstrating the use of pattern matching with multiple conditions:
```go
httpGet(url) => response, status (
  (response, 200): {
    print("Success: {response}")
  },
  (response, 404): {
    print("Not found")
  },
  _: {
    print("HTTP error with status: {status}")
  }
)
```
In this example:
- The `httpGet(url)` function call returns `response` and `status`.
- Depending on the `status`, different blocks of code are executed.
- The default case (`_`) handles situations where none of the specific patterns match.

## Combining Expression Mapping and Pattern Matching

It is often useful to nest conditionals, combining both expression mapping and pattern matching to handle complex logic.

### Example:
```go
authenticate(user, pass) ? authResult, error {
  error ? {
    print("Authentication failed")
    return -1
  }

  authResult.role => role (
    "admin": {
      fetchData(authResult.userId, "admin") ? data, fetchErr {
        fetchErr ? {
          print("Failed to fetch admin data: {fetchErr}")
          return -1
        }
        processAdminData(data)
      }
    },
    "user": {
      fetchData(authResult.userId, "user") ? data, fetchErr {
        fetchErr ? {
          print("Failed to fetch user data: {fetchErr}")
          return -1
        }
        processUserData(data)
      }
    },
    _: {
      print("Unknown role: {role}")
      return -1
    }
  )
}
```

This example illustrates how you can:
- Authenticate a user and map the result.
- Handle errors that occur during authentication.
- Use pattern matching to execute role-based logic, including fetching and processing data only if the user role matches specific patterns.

