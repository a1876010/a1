import socket
import sys
import os
import argparse
import re
import http.client
import socketserver

BUFFER_SIZE = 1000000

parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', type=int, help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = args.port

# Create a server socket and start listening
class ProxyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        clientSocket = self.request
        print('Received a connection')
        
        try:
            message_bytes = clientSocket.recv(BUFFER_SIZE)
            message = message_bytes.decode('utf-8')
            print('< ' + message)
        except:
            print('Failed to receive request')
            clientSocket.close()
            return

        # Extract method, URI, and version
        requestParts = message.split()   
        if len(requestParts) < 3:
            clientSocket.close()
            return
        
        method = requestParts[0]
        URI = requestParts[1]
        version = requestParts[2]
        
        print(f'Method: {method}, URI: {URI}, Version: {version}')

        # Process URI to extract hostname and resource path
        URI = re.sub('^(/?)http(s?)://', '', URI, count=1)
        URI = URI.replace('/..', '')
        resourceParts = URI.split('/', 1)
        hostname = resourceParts[0]
        resource = '/' + resourceParts[1] if len(resourceParts) == 2 else '/'
        
        print(f'Requested Resource: {resource}')
        cacheLocation = f'./cache/{hostname}{resource.replace("/", "_")}'
        os.makedirs(os.path.dirname(cacheLocation), exist_ok=True)
        
        # Check cache
        if os.path.isfile(cacheLocation):
            print(f'Cache hit! Loading from {cacheLocation}')
            with open(cacheLocation, 'rb') as cacheFile:
                clientSocket.sendall(cacheFile.read())
            clientSocket.close()
            return

        # Fetch from origin server
        try:
            conn = http.client.HTTPConnection(hostname, 80)
            conn.request(method, resource, headers={'Host': hostname, 'Connection': 'close'})
            response = conn.getresponse()
            responseData = response.read()
            statusLine = f'HTTP/1.1 {response.status} {response.reason}\r\n'
            headers = ''.join(f'{key}: {value}\r\n' for key, value in response.getheaders())
            fullResponse = (statusLine + headers + '\r\n').encode() + responseData
            
            clientSocket.sendall(fullResponse)
            with open(cacheLocation, 'wb') as cacheFile:
                cacheFile.write(fullResponse)
            print('Response cached successfully')
        except Exception as e:
            print(f'Failed to connect to origin server: {e}')
        finally:
            conn.close()
            clientSocket.close()

# Start the proxy server
try:
    with socketserver.ThreadingTCPServer((proxyHost, proxyPort), ProxyHandler) as server:
        print(f'Proxy server running on {proxyHost}:{proxyPort}')
        server.serve_forever()
except Exception as e:
    print(f'Failed to start proxy server: {e}')
    sys.exit()

