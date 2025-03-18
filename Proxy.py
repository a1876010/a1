import socket
import sys
import os
import argparse
import re

BUFFER_SIZE = 1000000

parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='The IP Address of Proxy Server')
parser.add_argument('port', type=int, help='The port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = args.port

try:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print('Created socket')
except socket.error as e:
    print(f'Failed to create socket: {e}')
    sys.exit()

try:
    serverSocket.bind((proxyHost, proxyPort))
    print(f'Port {proxyPort} is bound')
except socket.error as e:
    print(f'Port is already in use: {e}')
    sys.exit()

try:
    serverSocket.listen(5)
    print('Listening for connections')
except socket.error as e:
    print(f'Failed to listen: {e}')
    sys.exit()

while True:
    print('Waiting for connection...')
    try:
        clientSocket, clientAddress = serverSocket.accept()
        print(f'Received a connection from {clientAddress}')
    except socket.error as e:
        print(f'Failed to accept connection: {e}')
        continue
    
    try:
        message_bytes = clientSocket.recv(BUFFER_SIZE)
        message = message_bytes.decode('utf-8')
        print('Received request:')
        print(message)
    except:
        print('Failed to receive request')
        clientSocket.close()
        continue
    
    requestParts = message.split('\r\n')
    if len(requestParts) < 1:
        clientSocket.close()
        continue
    
    first_line = requestParts[0].split()
    if len(first_line) < 3:
        clientSocket.close()
        continue
    
    method, URI, version = first_line
    
    URI = re.sub(r'^(/?)http(s?)://', '', URI, count=1)
    URI = URI.replace('/..', '')
    resourceParts = URI.split('/', 1)
    hostname = resourceParts[0]
    resource = '/' + resourceParts[1] if len(resourceParts) == 2 else '/'
    
    cacheLocation = f'./cache/{hostname}{resource.replace("/", "_")}'
    
    try:
        if os.path.isfile(cacheLocation):
            with open(cacheLocation, 'rb') as cacheFile:
                cacheData = cacheFile.read()
            print(f'Cache hit! Loading from {cacheLocation}')
            clientSocket.sendall(cacheData)
            clientSocket.close()
            continue
    except Exception as e:
        print(f'Cache miss or error: {e}')
    
    try:
        originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        originServerSocket.connect((hostname, 80))
        print(f'Connected to origin server: {hostname}')
    except socket.error as e:
        print(f'Failed to connect to origin server: {e}')
        clientSocket.close()
        continue
    
    request = f"{method} {resource} {version}\r\n" + f"Host: {hostname}\r\nConnection: close\r\n\r\n"
    
    try:
        originServerSocket.sendall(request.encode())
        print('Forwarded request to origin server')
    except socket.error as e:
        print(f'Failed to forward request: {e}')
        clientSocket.close()
        continue
    
    try:
        responseData = b''
        while True:
            part = originServerSocket.recv(BUFFER_SIZE)
            if not part:
                break
            responseData += part
        print('Received response from origin server')
    except socket.error as e:
        print(f'Failed to receive response: {e}')
        clientSocket.close()
        continue
    
    clientSocket.sendall(responseData)
    
    os.makedirs(os.path.dirname(cacheLocation), exist_ok=True)
    try:
        with open(cacheLocation, 'wb') as cacheFile:
            cacheFile.write(responseData)
        print(f'Response cached at {cacheLocation}')
    except Exception as e:
        print(f'Failed to write to cache: {e}')
    
    print('Closing connections')
    originServerSocket.close()
    clientSocket.close()
