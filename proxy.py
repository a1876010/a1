import signal
import socket
import threading

class proxy():
    def __init__(self):
        # creating a tcp socket
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # reuse the socket
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.your_ip = "127.0.0.1" # loop back address
        self.your_port = 80 # use a port thats open like port 80

    def shutdown(self):
        # add your signal shutdown code here
        pass

    def main(self):
        # shutdown on cntrl c
        signal.signal(signal.SIGINT, self.shutdown)

        self.serverSocket.bind((self.your_ip, self.your_port))

        self.serverSocket.listen(10)
        self.__clients = {}

        while True:
            # establish the connection
            (clientSocket, client_address) = self.serverSocket.accept()

            d = threading.Thread(name=self._getClientName(client_address),
                                 target=self.proxy_thread,
                                 args=(clientSocket, client_address))
            d.setDaemon(True)
            d.start()

        # get the request from browser
        request = conn.recv(4096)

        # parse the first line
        first_line = request.split('\n')[0]

        # get url
        url = first_line.split(' ')[1]

        http_pos = url.find("://")
        if http_pos == -1:
            temp = url
        else:
            temp = url[(http_pos + 3):]

        port_pos = temp.find(":")

        # find end of web server
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1

        if port_pos == -1 or webserver_pos < port_pos:

            # default port
            port = 80
            webserver = temp[:webserver_pos]

        else:  # specific port
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((webserver, port))
        s.sendall(request)

        while 1:
            # receive data from web server
            data = s.recv(4096)

            if len(data) > 0:
                conn.send(data)  # send to browser/client

            else:
                break

p = proxy()
p.main()
