# Example

```go
module main

import sys

indexOf = (s: str, t: char) -> int {
  s # i, c {
    c == t => return i
  }
}

// Function to handle HTTP requests
handleRequest = (clientSocket: int) -> int {
  // Read the request from the client
  request = sys.read(clientSocket, 1024) ? result, err {
    err => {
      sys.print("Error reading request")
      return -1
    }
    result
  }

  // Parse the HTTP verb from the request
  request[0:indexOf(request, ' ')] ? {
    // Match the verb and respond accordingly
    "GET" => {
      response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello, GET request!"
      sys.write(clientSocket, response)
    }
    "POST" => {
      response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello, POST request!"
      sys.write(clientSocket, response)
    }
    _ => {
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
    err => {
      sys.print("Error creating socket")
      return -1
    }
    sock
  }

  // Bind the socket to the port
  sys.bind(serverSocket, sys.sockaddr_in(port, sys.INADDR_ANY)) ? err {
    err => {
      sys.print("Error binding socket")
      return -1
    }
  }

  // Listen for incoming connections
  sys.listen(serverSocket, 5) ? err {
    err => {
      sys.print("Error listening on socket")
      return -1
    }
  }

  sys.print("Server listening on port ", port)

  // Accept connections in a loop
  sys.closed(serverSocket) @ closed {
    closed => break

    clientSocket = sys.accept(serverSocket) ? sock, err {
      err => {
        sys.print("Error accepting connection")
        break
      }
      sock
    }

    // Handle the request in a separate function
    handleRequest(clientSocket)
  }

  // Close the server socket
  sys.close(serverSocket)
  // 0 is default
}
```
