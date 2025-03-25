# Create a server socket
# ~~~~ INSERT CODE ~~~~
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# ~~~~ END CODE INSERT ~~~~

# Bind the server socket to a host and port
# ~~~~ INSERT CODE ~~~~
serverSocket.bind((proxyHost, proxyPort))
# ~~~~ END CODE INSERT ~~~~

# Listen on the server socket
# ~~~~ INSERT CODE ~~~~
serverSocket.listen(5)
# ~~~~ END CODE INSERT ~~~~

# Accept connection from client and store in the clientSocket
# ~~~~ INSERT CODE ~~~~
clientSocket, clientAddress = serverSocket.accept()
# ~~~~ END CODE INSERT ~~~~

# Get HTTP request from client and store it in the variable: message_bytes
# ~~~~ INSERT CODE ~~~~
message_bytes = clientSocket.recv(BUFFER_SIZE)
# ~~~~ END CODE INSERT ~~~~

# Send back response to client 
# ~~~~ INSERT CODE ~~~~
clientSocket.sendall(''.join(cacheData).encode())
# ~~~~ END CODE INSERT ~~~~

# Create a socket to connect to origin server
# ~~~~ INSERT CODE ~~~~
originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# ~~~~ END CODE INSERT ~~~~

# Connect to the origin server
# ~~~~ INSERT CODE ~~~~
originServerSocket.connect((address, 80))
# ~~~~ END CODE INSERT ~~~~

# Create origin server request line and headers
# ~~~~ INSERT CODE ~~~~
originServerRequest = method + " " + resource + " " + version
originServerRequestHeader = "Host: " + hostname + "\r\nConnection: close"
# ~~~~ END CODE INSERT ~~~~

# Get the response from the origin server
# ~~~~ INSERT CODE ~~~~
responseData = b''
while True:
    part = originServerSocket.recv(BUFFER_SIZE)
    if not part:
        break
    responseData += part
# ~~~~ END CODE INSERT ~~~~

# Send the response to the client
# ~~~~ INSERT CODE ~~~~
clientSocket.sendall(responseData)
# ~~~~ END CODE INSERT ~~~~

# Save origin server response in the cache file
# ~~~~ INSERT CODE ~~~~
cacheFile.write(responseData)
# ~~~~ END CODE INSERT ~~
