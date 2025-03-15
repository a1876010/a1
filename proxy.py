import socket
import sys
import os
import argparse
import re
import hashlib
import threading

BUFFER_SIZE = 1000000  # 1MB buffer size

# Get the IP address and Port number to use for this web proxy server
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='The IP Address of Proxy Server')
parser.add_argument('port', type=int, help='The port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = args.port

# Create a server socket
try:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((proxyHost, proxyPort))
    serverSocket.listen(10)
    print(f'Proxy server listening on {proxyHost}:{proxyPort}')
except socket.error as err:
    print(f'Failed to set up server: {err}')
    sys.exit()

def handle_client(clientSocket):
    try:
        message_bytes = clientSocket.recv(BUFFER_SIZE)
        message = message_bytes.decode('utf-8')
        print('Received request:\n' + message)
    except Exception as err:
        print(f'Error receiving data: {err}')
        clientSocket.close()
        return

    # Extract HTTP request details
    requestParts = message.split('\r\n')[0].split()
    if len(requestParts) < 3:
        clientSocket.close()
        return
    method, URI, version = requestParts[:3]
    print(f'Method: {method}\nURI: {URI}\nVersion: {version}')

    # Process the requested resource
    URI = re.sub('^(/?)http(s?)://', '', URI, count=1).replace('/..', '')
    resourceParts = URI.split('/', 1)
    hostname = resourceParts[0]
    resource = '/' + resourceParts[1] if len(resourceParts) == 2 else '/'

    # Hash the resource for caching
    hashed_filename = hashlib.md5(resource.encode()).hexdigest()
    cacheLocation = os.path.join('./cache', hostname, hashed_filename)
    print(f'Cache location: {cacheLocation}')

    # Check if resource is in cache
    if os.path.isfile(cacheLocation):
        try:
            with open(cacheLocation, 'rb') as cacheFile:
                cacheData = cacheFile.read()
            clientSocket.sendall(cacheData)
            print(f'Cache hit! Sent cached response.')
        except Exception as e:
            print(f'Error reading cache: {e}')
    else:
        # Cache miss, connect to origin server
        try:
            originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            address = socket.gethostbyname(hostname)
            originServerSocket.connect((address, 80))
            print(f'Connected to origin server: {hostname}')

            # Construct request to origin server
            request = f"{method} {resource} {version}\r\nHost: {hostname}\r\nConnection: close\r\n\r\n"
            originServerSocket.sendall(request.encode())
            print('Forwarded request to origin server')

            # Receive response from origin server
            response = b""
            while True:
                chunk = originServerSocket.recv(BUFFER_SIZE)
                if not chunk:
                    break
                response += chunk
            
            # Send response to client
            clientSocket.sendall(response)
            print('Sent response to client')

            # Cache the response
            os.makedirs(os.path.dirname(cacheLocation), exist_ok=True)
            with open(cacheLocation, 'wb') as cacheFile:
                cacheFile.write(response)
            print('Cached response')
        except socket.error as err:
            print(f'Error fetching from origin server: {err}')
        finally:
            originServerSocket.close()
    
    clientSocket.close()

# Accept multiple connections using threading
while True:
    try:
        clientSocket, clientAddress = serverSocket.accept()
        print(f'Received a connection from {clientAddress}')
        threading.Thread(target=handle_client, args=(clientSocket,)).start()
    except KeyboardInterrupt:
        print('\nShutting down proxy server.')
        serverSocket.close()
        sys.exit()
    except socket.error as err:
        print(f'Connection error: {err}')
