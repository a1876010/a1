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

# Create a server socket, bind it to a port and start listening
try:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Created socket')
except:
    print('Failed to create socket')
    sys.exit()

try:
    serverSocket.bind((proxyHost, proxyPort))
    print('Port is bound')
except:
    print('Port is already in use')
    sys.exit()

try:
    serverSocket.listen(5)
    print('Listening to socket')
except:
    print('Failed to listen')
    sys.exit()

# Continuously accept connections
while True:
    print('Waiting for connection...')
    clientSocket = None
    try:
        clientSocket, clientAddress = serverSocket.accept()
        print('Received a connection')
    except:
        print('Failed to accept connection')
        sys.exit()
    
    # Get HTTP request from client
    try:
        message_bytes = clientSocket.recv(BUFFER_SIZE)
    except:
        print('Failed to receive request')
        clientSocket.close()
        continue
    
    message = message_bytes.decode('utf-8')
    print('Received request:')
    print('< ' + message)
    
    requestParts = message.split()
    if len(requestParts) < 3:
        clientSocket.close()
        continue
    
    method = requestParts[0]
    URI = requestParts[1]
    version = requestParts[2]
    
    print('Method:		' + method)
    print('URI:		' + URI)
    print('Version:	' + version)
    
    # Get the requested resource from URI
    URI = re.sub('^(/?)http(s?)://', '', URI, count=1)
    URI = URI.replace('/..', '')
    resourceParts = URI.split('/', 1)
    hostname = resourceParts[0]
    resource = '/' + resourceParts[1] if len(resourceParts) == 2 else '/'
    
    print('Requested Resource:	' + resource)
    
    # Check if resource is in cache
    cacheLocation = './' + hostname + resource
    if cacheLocation.endswith('/'):
        cacheLocation += 'default'
    print('Cache location:		' + cacheLocation)
    
    try:
        if os.path.isfile(cacheLocation):
            with open(cacheLocation, 'rb') as cacheFile:
                cacheData = cacheFile.read()
            print('Cache hit! Loading from cache file:', cacheLocation)
            clientSocket.sendall(cacheData)
            clientSocket.close()
            continue
    except:
        print('Cache miss or error')
    
    # Cache miss: Get resource from origin server
    try:
        originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Connecting to:		' + hostname + '\n')
        address = socket.gethostbyname(hostname)
        originServerSocket.connect((address, 80))
        print('Connected to origin Server')
    except:
        print('Failed to connect to origin server')
        clientSocket.close()
        continue
    
    originServerRequest = f"{method} {resource} {version}\r\n"
    originServerRequestHeader = f"Host: {hostname}\r\nConnection: close\r\n\r\n"
    request = originServerRequest + originServerRequestHeader
    
    print('Forwarding request to origin server:')
    for line in request.split('\r\n'):
        print('> ' + line)
    
    try:
        originServerSocket.sendall(request.encode())
    except:
        print('Forward request to origin failed')
        clientSocket.close()
        continue
    
    # Get the response from the origin server
    try:
        responseData = b''
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
    
    # Send the response to the client
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
    
    print('Closing connections')
    originServerSocket.close()
    clientSocket.close()
