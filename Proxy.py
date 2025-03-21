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

# Create a server socket, bind it to a port, and start listening
try:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((proxyHost, proxyPort))
    serverSocket.listen(5)
    print('Proxy server is running on {}:{}'.format(proxyHost, proxyPort))
except:
    print('Failed to create or bind socket')
    sys.exit()

# Continuously accept connections
while True:
    print('Waiting for connection...')
    clientSocket, clientAddress = serverSocket.accept()
    print('Received a connection from', clientAddress)
    
    try:
        message_bytes = clientSocket.recv(BUFFER_SIZE)
        message = message_bytes.decode('utf-8')
    except:
        print('Failed to receive request')
        clientSocket.close()
        continue
    
    print('Received request:\n' + message)
    requestParts = message.split()
    if len(requestParts) < 3:
        print('Malformed request received, closing connection.')
        clientSocket.close()
        continue
    
    method, URI, version = requestParts[:3]
    print(f'Method: {method}\nURI: {URI}\nVersion: {version}\n')
    
    # Remove http protocol from the URI and handle security
    URI = re.sub('^(/?)http(s?)://', '', URI, count=1)
    URI = URI.replace('/..', '')
    
    # Extract hostname and resource
    resourceParts = URI.split('/', 1)
    hostname = resourceParts[0]
    resource = '/' + resourceParts[1] if len(resourceParts) == 2 else '/'
    print(f'Requested Resource: {resource}')
    
    # Check if resource is in cache
    cacheLocation = './' + hostname + resource
    if cacheLocation.endswith('/'):
        cacheLocation += 'default'
    print(f'Cache location: {cacheLocation}')
    
    if os.path.isfile(cacheLocation):
        try:
            with open(cacheLocation, 'rb') as cacheFile:
                cacheData = cacheFile.read()
            print(f'Cache hit! Loading from cache file: {cacheLocation}')
            clientSocket.sendall(cacheData)
            clientSocket.close()
            continue
        except:
            print('Cache read error, retrieving from origin server')
    
    # Cache miss: Get resource from origin server
    try:
        originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f'Connecting to: {hostname}')
        address = socket.gethostbyname(hostname)
        originServerSocket.connect((address, 80))
        print('Connected to origin server')
    except:
        print('Failed to connect to origin server')
        clientSocket.close()
        continue
    
    # Forward request to origin server
    requestHeaders = f"{method} {resource} {version}\r\nHost: {hostname}\r\nConnection: close\r\n\r\n"
    try:
        originServerSocket.sendall(requestHeaders.encode())
    except:
        print('Failed to forward request to origin server')
        clientSocket.close()
        continue
    
    # Receive response from the origin server
    responseData = b''
    try:
        while True:
            part = originServerSocket.recv(BUFFER_SIZE)
            if not part:
                break
            responseData += part
        print('Received response from origin server')
    except:
        print('Failed to receive response')
        clientSocket.close()
        continue
    
    # Send response to the client
    clientSocket.sendall(responseData)
    
    # Cache the response
    cacheDir = os.path.dirname(cacheLocation)
    if not os.path.exists(cacheDir):
        os.makedirs(cacheDir)
    try:
        with open(cacheLocation, 'wb') as cacheFile:
            cacheFile.write(responseData)
        print('Response cached successfully')
    except:
        print('Failed to write to cache')
    
    # Close connections
    originServerSocket.close()
    clientSocket.close()

