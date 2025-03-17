import socket
import os
import argparse
import re
import time
import socketserver

BUFFER_SIZE = 1000000
CACHE_DIR = "./cache/"

parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='The IP Address of the Proxy Server')
parser.add_argument('port', type=int, help='The port number of the Proxy Server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = args.port

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

class ProxyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        clientSocket = self.request
        try:
            message = clientSocket.recv(BUFFER_SIZE).decode('utf-8')
            print("Received request:\n" + message)

            requestParts = message.split() 
            if len(requestParts) < 3:
                clientSocket.close()
                return

            method, URI, version = requestParts[:3]
            URI = re.sub(r'^(/?)http(s?)://', '', URI, count=1)
            URI = URI.replace('/..', '')
            
            resourceParts = URI.split('/', 1)
            hostname = resourceParts[0]
            resource = '/' + resourceParts[1] if len(resourceParts) == 2 else '/'
            cacheLocation = CACHE_DIR + hostname + resource.replace('/', '_')
            
            if os.path.isfile(cacheLocation):
                with open(cacheLocation, 'rb') as cacheFile:
                    cacheData = cacheFile.read()
                print("Cache hit! Loading from cache file:", cacheLocation)
                clientSocket.sendall(cacheData)
                clientSocket.close()
                return
            
            originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            address = socket.gethostbyname(hostname)
            originServerSocket.connect((address, 80))
            
            originRequest = f"{method} {resource} {version}\r\nHost: {hostname}\r\nConnection: close\r\n\r\n"
            originServerSocket.sendall(originRequest.encode())
            
            responseData = b''
            while True:
                part = originServerSocket.recv(BUFFER_SIZE)
                if not part:
                    break
                responseData += part
            
            headers, body = responseData.split(b'\r\n\r\n', 1)
            headers_str = headers.decode('utf-8', errors='ignore')
            
            if "301 Moved Permanently" in headers_str or "302 Found" in headers_str:
                match = re.search(r'Location: (.*?)\r\n', headers_str)
                if match:
                    new_location = match.group(1)
                    print("Redirecting to:", new_location)
                    clientSocket.sendall(responseData)
                    clientSocket.close()
                    return
            
            if "404 Not Found" in headers_str:
                print("Page not found")
                clientSocket.sendall(responseData)
                clientSocket.close()
                return
            
            cache_control_match = re.search(r'Cache-Control: max-age=(\d+)', headers_str)
            if cache_control_match:
                max_age = int(cache_control_match.group(1))
                print(f"Cache-Control max-age={max_age} seconds")
                with open(cacheLocation, 'wb') as cacheFile:
                    cacheFile.write(responseData)
                time.sleep(max_age)
                os.remove(cacheLocation)
            else:
                with open(cacheLocation, 'wb') as cacheFile:
                    cacheFile.write(responseData)
            
            clientSocket.sendall(responseData)
        except Exception as e:
            print("Error handling request:", str(e))
        finally:
            clientSocket.close()
            if 'originServerSocket' in locals():
                originServerSocket.close()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

server = ThreadedTCPServer((proxyHost, proxyPort), ProxyHandler)
print(f"Proxy server running on {proxyHost}:{proxyPort}")
server.serve_forever()

