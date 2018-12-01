import socket
import select
from threading import Thread
import os
import time

BUFFER_SIZE = 32768

REDIRECT_HOST = "debauche.xyz"
REDIRECT_PORT = 80
LISTEN_PORT = 8080

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    OKRED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Proxy(Thread):
    def __init__(self, LISTEN_PORT, REDIRECT_PORT, REDIRECT_HOST):
        super(Proxy, self).__init__()

        self.LISTEN_PORT = LISTEN_PORT
        self.REDIRECT_PORT = REDIRECT_PORT
        self.REDIRECT_HOST = REDIRECT_HOST

        self.listenSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listenSock.setblocking(0)
        self.listenSock.bind(('', LISTEN_PORT))
        self.listenSock.listen(5)

        # Lists of sockets to clients and to the server
        # Dictionnary, to get the client socket with the corresponding server socket (vice versa)
        self.socks_c2s = {}
        self.socks_s2c = {}

    def show_information(self):
        show = "[I] Dic 1: \t%i" % len(self.socks_c2s) + "\n[I] Dic 2: \t%i" % len(self.socks_s2c)
        try:
            if self.show_information_memory == show:
                return
        except: pass
        self.show_information_memory = show
        print(show + "\n")

    def on_c2s(self, data):
        # You can perform operations here
        data = ''.join([chr(d) if d < 127 else '?' for d in data])
        print(bcolors.OKRED, "\n[V] Client -> Server\n", bcolors.ENDC, "\n", data)

    def on_s2c(self, data):
        # You can perform operations here
        data = ''.join([chr(d) if d < 127 else '?' for d in data])
        print(bcolors.OKGREEN, "\n[V] Server -> Client\n", bcolors.ENDC, "\n", data)

    def run(self):
        while True:
            self.show_information()

            # Check for accepting clients
            sockets_readable, sockets_writable, sockets_error = select.select([self.listenSock], [], [self.listenSock], 0.0)
            for sock in sockets_readable:
                # get the socket to the client
                client_socket, addr = sock.accept()
                client_socket.setblocking(0)
                # Create a socket to the server
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.connect((self.REDIRECT_HOST, self.REDIRECT_PORT))
                # Feed dictionnary
                self.socks_c2s[client_socket] = server_socket
                self.socks_s2c[server_socket] = client_socket
                print(bcolors.WARNING, "[N] New client, ", addr, bcolors.ENDC)

            # Check sockets from clients
            if self.socks_c2s:
                sockets_readable, sockets_writable, sockets_error = select.select(self.socks_c2s.keys(), [], self.socks_c2s.keys(), 0.0)

                for sock in sockets_readable:
                    data = sock.recv(BUFFER_SIZE)
                    if data:
                        self.on_c2s(data)
                        self.socks_c2s[sock].sendall(data)
                    else:
                        sock.close()
                        self.socks_c2s[sock].close()
                        del self.socks_s2c[self.socks_c2s[sock]]
                        del self.socks_c2s[sock]

            # Check sockets from servers
            if self.socks_s2c:
                sockets_readable, sockets_writable, sockets_error = select.select(self.socks_s2c.keys(), [], self.socks_s2c.keys(), 0.0)

                for sock in sockets_readable:
                    data = sock.recv(BUFFER_SIZE)
                    if data:
                        self.on_s2c(data)
                        self.socks_s2c[sock].sendall(data)
                    else:
                        sock.close()
                        self.socks_s2c[sock].close()
                        del self.socks_c2s[self.socks_s2c[sock]]
                        del self.socks_s2c[sock]



proxy = Proxy(LISTEN_PORT, REDIRECT_PORT, REDIRECT_HOST)
proxy.start()
proxy.join()
