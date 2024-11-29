import socket
import os

# run 2 terminals, 1 for server, 1 for client
# server command: python3 FTPServer.py
# client commands: python3 FTPClient.py localhost 12000 -> GET test.txt 

UPLOAD_DIRECTORY = "uploads"

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

def read_line(sock):
    line = b''
    while not line.endswith(b'\n'):
        char = sock.recv(1)
        if not char:
            break
        line += char
    return line.decode().strip()

def receive_headers(sock):
    headers = {}
    while True:
        line = read_line(sock)
        if line == '':
            break  # End of headers
        if ': ' in line:
            key, value = line.split(": ", 1)
            headers[key] = value
        else:
            print(f"Malformed header line: {line}")
    return headers

def handle_client(connection, addr):
    print(f"Connection established with {addr}")
    while True:
        # Read command from client over control channel
        line = read_line(connection)
        if not line:
            break  # Client closed the connection
        message = line.strip()
        print(f"Received message: {message}")

        command, *args = message.split()

        if command in ["GET", "PUT", "LS"]:
            # Read headers to get Data-Port
            headers = receive_headers(connection)
            data_port = int(headers.get("Data-Port", 0))
            if data_port == 0:
                connection.sendall("FAILURE 400 Data-Port not specified\n".encode())
                continue

            client_ip = addr[0]  # Client's IP from control connection

            # Create data socket to connect to client's data port
            try:
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.connect((client_ip, data_port))
                print(f"Connected to client's data port {data_port}")
            except Exception as e:
                print(f"Failed to connect to client's data port: {e}")
                connection.sendall("FAILURE 400 Failed to connect to client's data port\n".encode())
                continue

            if command == "GET":
                if len(args) < 1:
                    connection.sendall("FAILURE 400 Invalid GET command format\n".encode())
                    data_socket.close()
                    continue

                filename = args[0]
                filepath = os.path.join(os.getcwd(), filename)
                if os.path.exists(filepath):
                    filesize = os.path.getsize(filepath)
                    # Send success status code over control channel
                    connection.sendall(f"SUCCESS 200 OK\n".encode())

                    # Send headers over data channel
                    send_headers(data_socket, {"Content-Length": str(filesize)})

                    # Send file data over data channel
                    with open(filepath, 'rb') as file:
                        bytes_sent = 0
                        while True:
                            chunk = file.read(4096)
                            if not chunk:
                                break
                            data_socket.sendall(chunk)
                            bytes_sent += len(chunk)
                    print(f"File '{filename}' sent to client.")
                    print(f"Total bytes transferred: {bytes_sent}")
                else:
                    connection.sendall("FAILURE 404 File Not Found\n".encode())
                data_socket.close()

            elif command == "PUT":
                if len(args) < 1:
                    connection.sendall("FAILURE 400 Invalid PUT command format\n".encode())
                    data_socket.close()
                    continue

                filename = args[0]
                filepath = os.path.join(UPLOAD_DIRECTORY, filename)

                # Send success status code over control channel
                connection.sendall(f"SUCCESS 200 OK\n".encode())

                # Receive headers over data channel
                data_headers = receive_headers(data_socket)
                filesize = int(data_headers.get("Content-Length", 0))
                if filesize == 0:
                    print("Invalid file size received.")
                    data_socket.close()
                    connection.sendall("FAILURE 400 Invalid file size\n".encode())
                    continue

                print(f"Receiving file '{filename}' of size {filesize} bytes.")

                # Receive file data over data channel
                with open(filepath, 'wb') as file:
                    received_bytes = 0
                    while received_bytes < filesize:
                        buffer_size = min(4096, filesize - received_bytes)
                        chunk = data_socket.recv(buffer_size)
                        if not chunk:
                            print("Connection lost while receiving file data.")
                            break
                        file.write(chunk)
                        received_bytes += len(chunk)
                print(f"File '{filename}' uploaded successfully.")
                print(f"Total bytes transferred: {received_bytes}")

                data_socket.close()

                # Send final acknowledgment over control channel
                connection.sendall("SUCCESS 201 Upload Complete\n".encode())

            elif command == "LS":
                # Send success status code over control channel
                connection.sendall(f"SUCCESS 200 OK\n".encode())

                # Generate directory listing
                try:
                    files = os.listdir(UPLOAD_DIRECTORY)
                    files = [f for f in files if os.path.isfile(os.path.join(UPLOAD_DIRECTORY, f))]
                    file_list = '\n'.join(files)
                    content_length = len(file_list.encode())

                    # Send headers over data channel
                    send_headers(data_socket, {"Content-Length": str(content_length)})

                    # Send directory listing over data channel
                    data_socket.sendall(file_list.encode())
                    print("Sent file list to client.")
                except Exception as e:
                    print(f"Error retrieving file list: {e}")
                    connection.sendall("FAILURE 500 Internal Server Error\n".encode())

                data_socket.close()

        elif command == "QUIT":
            connection.sendall("SUCCESS 200 Goodbye\n".encode())
            connection.shutdown(socket.SHUT_WR)  # Ensure the client receives the message
            break  # Exit the loop and close the connection

        else:
            connection.sendall("FAILURE 400 Invalid Command\n".encode())

    connection.close()
    print(f"Connection with {addr} closed.")

def send_headers(sock, headers):
    for key, value in headers.items():
        sock.sendall(f"{key}: {value}\n".encode())
    sock.sendall(b'\n')  # End of headers

def main():
    server_port = 12000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', server_port))
    server_socket.listen(5)
    print(f"Server is ready to receive connections on port {server_port}...")

    connection_socket, addr = server_socket.accept()
    handle_client(connection_socket, addr)

    # Close the server socket after handling one client
    server_socket.close()
    print("Server has been shut down.")

if __name__ == "__main__":
    main()
