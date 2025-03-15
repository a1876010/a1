import socket
import sys
import os
import argparse
import re

# 1MB buffer size
BUFFER_SIZE = 1000000

# Get the IP address and Port number to use for this web proxy server
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = int(args.port)

# Create a server socket
try:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print('Created socket')
except socket.error as err:
    print(f'Failed to create socket: {err}')
    sys.exit()

# Bind the server socket
try:
    serverSocket.bind((proxyHost, proxyPort))
    print('Port is bound')
except socket.error as err:
    print(f'Port binding failed: {err}')
    sys.exit()

# Listen on the server socket
try:
    serverSocket.listen(5)
    print('Listening to socket')
except socket.error as err:
    print(f'Failed to listen: {err}')
    sys.exit()

# Continuously accept connections
while True:
    print('Waiting for connection...')
    try:
        clientSocket, clientAddr = serverSocket.accept()
        print(f'Received a connection from {clientAddr}')
    except socket.error as err:
        print(f'Failed to accept connection: {err}')
        continue
    
    # Receive HTTP request from client
    try:
        message_bytes = clientSocket.recv(BUFFER_SIZE)
        message = message_bytes.decode('utf-8')
        print(f'Received request:\n{message}')
    except Exception as e:
        print(f'Failed to receive data: {e}')
        clientSocket.close()
        continue

    # Extract the method, URI, and HTTP version
    requestParts = message.split('\r\n')[0].split()
    if len(requestParts) < 3:
        print('Invalid HTTP request received')
        clientSocket.close()
        continue
    
    method, URI, version = requestParts
    
    # Process URL
    URI = re.sub('^(/?)http(s?)://', '', URI, count=1)
    URI = URI.replace('/..', '')
    resourceParts = URI.split('/', 1)
    hostname = resourceParts[0]
    resource = '/' + resourceParts[1] if len(resourceParts) == 2 else '/'
    
    print(f'Method: {method}\nURI: {URI}\nVersion: {version}')

    # Check cache
    cacheLocation = f'./cache/{hostname}{resource.replace("/", "_")}'
    if os.path.isfile(cacheLocation):
        print(f'Cache hit: {cacheLocation}')
        try:
            with open(cacheLocation, 'rb') as cacheFile:
                response = cacheFile.read()
                clientSocket.sendall(response)
                print('Sent cached response to client')
        except Exception as e:
            print(f'Error reading cache: {e}')
    else:
        print('Cache miss, forwarding request to origin server')
        
        # Connect to origin server
        try:
            originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            originServerSocket.connect((hostname, 80))
            print(f'Connected to origin server: {hostname}')

            # Forward request to origin server
            request = f'{method} {resource} {version}\r\nHost: {hostname}\r\nConnection: close\r\n\r\n'
            originServerSocket.sendall(request.encode())
            print('Request forwarded to origin server')
        
            # Receive response from origin server
            response = b''
            while True:
                part = originServerSocket.recv(BUFFER_SIZE)
                if not part:
                    break
                response += part
            
            print('Received response from origin server')
            
            # Save to cache if no-cache is not present
            if b'Cache-Control: no-cache' not in response:
                os.makedirs(os.path.dirname(cacheLocation), exist_ok=True)
                with open(cacheLocation, 'wb') as cacheFile:
                    cacheFile.write(response)
                    print('Saved response to cache')
            
            # Send response to client
            clientSocket.sendall(response)
            print('Sent response to client')
            
        except Exception as e:
            print(f'Error handling request: {e}')
        finally:
            originServerSocket.close()
    
    clientSocket.close()
    print('Connection closed')

