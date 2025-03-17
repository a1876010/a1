import socket
import sys
import os
import argparse
import re
import time

BUFFER_SIZE = 1000000
CACHE_DIR = "./cache"

parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='IP Address of Proxy Server')
parser.add_argument('port', type=int, help='Port Number of Proxy Server')
args = parser.parse_args()

proxyHost = args.hostname
proxyPort = args.port

# Ensure cache directory exists
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

# Create a server socket
try:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind((proxyHost, proxyPort))
    serverSocket.listen(5)
    print(f"Proxy listening on {proxyHost}:{proxyPort}")
except Exception as e:
    print(f"Error creating socket: {e}")
    sys.exit(1)

while True:
    print("Waiting for a connection...")
    try:
        clientSocket, clientAddress = serverSocket.accept()
        print(f"Received connection from {clientAddress}")
    except Exception as e:
        print(f"Error accepting connection: {e}")
        continue

    try:
        message_bytes = clientSocket.recv(BUFFER_SIZE)
        message = message_bytes.decode('utf-8')
        print(f"Received request:\n{message}")

        requestParts = message.split()
        if len(requestParts) < 3:
            print("Invalid request format.")
            clientSocket.close()
            continue

        method, URI, version = requestParts[0], requestParts[1], requestParts[2]
        print(f"Method: {method}, URI: {URI}, Version: {version}")

        # Remove protocol from URI
        URI = re.sub(r'^(/?)http(s?)://', '', URI, count=1)
        URI = URI.replace('/..', '')  # Security fix

        resourceParts = URI.split('/', 1)
        hostname = resourceParts[0]
        resource = '/' + resourceParts[1] if len(resourceParts) == 2 else '/'

        print(f"Requested Resource: {resource}")

        # Cache location
        cacheFilePath = os.path.join(CACHE_DIR, hostname.replace("/", "_") + resource.replace("/", "_"))

        # Check if resource is in cache
        if os.path.isfile(cacheFilePath):
            with open(cacheFilePath, 'rb') as cacheFile:
                cacheData = cacheFile.read()
            print(f"Cache hit! Serving from {cacheFilePath}")
            clientSocket.sendall(cacheData)
            clientSocket.close()
            continue

        # Cache miss, connect to origin server
        try:
            originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            originServerSocket.settimeout(5)  # Avoid long wait times
            originServerSocket.connect((hostname, 80))
            print(f"Connected to origin server: {hostname}")
        except Exception as e:
            print(f"Failed to connect to origin server: {e}")
            clientSocket.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            clientSocket.close()
            continue

        # Forward request
        originServerRequest = f"{method} {resource} {version}\r\n"
        originServerRequestHeader = f"Host: {hostname}\r\nConnection: close\r\n\r\n"
        request = originServerRequest + originServerRequestHeader

        print("Forwarding request to origin server...")
        originServerSocket.sendall(request.encode())

        # Receive response
        responseData = b""
        while True:
            part = originServerSocket.recv(BUFFER_SIZE)
            if not part:
                break
            responseData += part

        print("Received response from origin server")

        # Handle redirections (301, 302)
        if b"HTTP/1.1 301" in responseData or b"HTTP/1.1 302" in responseData:
            print("Redirect detected! Updating location...")
            location = re.search(r"Location: (.+?)\r\n", responseData.decode(), re.IGNORECASE)
            if location:
                new_location = location.group(1)
                print(f"Redirecting to: {new_location}")
                clientSocket.sendall(f"HTTP/1.1 302 Found\r\nLocation: {new_location}\r\n\r\n".encode())
                clientSocket.close()
                continue

        # Handle 404 Not Found
        if b"HTTP/1.1 404" in responseData:
            print("Page not found (404)")
            clientSocket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
            clientSocket.close()
            continue

        # Send response to client
        clientSocket.sendall(responseData)

        # Handle Cache-Control max-age
        cache_max_age = re.search(r"Cache-Control: max-age=(\d+)", responseData.decode(), re.IGNORECASE)
        if cache_max_age:
            max_age = int(cache_max_age.group(1))
            print(f"Caching resource with max-age: {max_age} seconds")
            time.sleep(max_age)  # Simulate cache expiration

        # Cache response
        try:
            with open(cacheFilePath, 'wb') as cacheFile:
                cacheFile.write(responseData)
            print("Response cached successfully")
        except Exception as e:
            print(f"Failed to write to cache: {e}")

        # Close sockets
        originServerSocket.close()
        clientSocket.close()

    except Exception as e:
        print(f"Error processing request: {e}")
        clientSocket.close()


