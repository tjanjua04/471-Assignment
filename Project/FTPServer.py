import socket
import os

# run 2 terminals, 1 for server, 1 for client
# server command: python3 FTPServer.py
# client commands: python3 FTPClient.py -> GET test.txt 

def handle_client(connection, addr):
    print(f"Connection established with {addr}")
    while True:
        message = connection.recv(1024).decode().strip()
        if not message:
            break
        
        command, *args = message.split()
        
        if command == "GET":
            filename = args[0]
            if os.path.exists(filename):
                filesize = os.path.getsize(filename)
                connection.send(f"SUCCESS 200 OK\nFILE {filename} {filesize}".encode())
                
                with open(filename, 'rb') as file:
                    chunk = file.read(1024)  # Initialize chunk
                    while chunk:
                        connection.send(chunk)
                        chunk = file.read(1024)
                connection.send("EOF".encode())
            else:
                connection.send("FAILURE 404 File Not Found".encode())


def main():
    server_port = 12000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', server_port))
    server_socket.listen(5)
    print("Server is ready to receive connections...")
    
    while True:
        connection_socket, addr = server_socket.accept()
        handle_client(connection_socket, addr)

if __name__ == "__main__":
    main()
