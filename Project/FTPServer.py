import socket
import os

# run 2 terminals, 1 for server, 1 for client
# server command: python3 FTPServer.py
# client commands: python3 FTPClient.py -> GET test.txt 

# Define a directory for uploaded files
UPLOAD_DIRECTORY = "uploads"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

def read_line(sock):
    line = b''
    while not line.endswith(b'\n'):
        char = sock.recv(1)
        if not char:
            break
        line += char
    return line.decode().strip()

def handle_client(connection, addr):
    print(f"Connection established with {addr}")
    while True:
        # Read a line (command) from the client
        line = read_line(connection)
        if not line:
            break  # Client closed the connection
        message = line.strip()
        print(f"Received message: {message}")

        command, *args = message.split()

        if command == "GET":
            if len(args) < 1:
                connection.sendall("FAILURE 400 Invalid GET command format\n".encode())
                continue

            filename = args[0]
            # Access files in the server's current working directory
            filepath = os.path.join(os.getcwd(), filename)
            if os.path.exists(filepath):
                filesize = os.path.getsize(filepath)
                # Send success status code and message
                connection.sendall(f"SUCCESS 200 OK\n".encode())

                # Send the file size in a header
                connection.sendall(f"Content-Length: {filesize}\n\n".encode())

                # Send the file data
                with open(filepath, 'rb') as file:
                    while True:
                        chunk = file.read(4096)
                        if not chunk:
                            break
                        connection.sendall(chunk)
                print(f"File '{filename}' sent to client.")
            else:
                connection.sendall("FAILURE 404 File Not Found\n".encode())

        elif command == "PUT":
            if len(args) < 1:
                connection.sendall("FAILURE 400 Invalid PUT command format\n".encode())
                continue

            filename = args[0]
            filepath = os.path.join(UPLOAD_DIRECTORY, filename)  # Save in upload directory
            # Send success status code and message
            connection.sendall(f"SUCCESS 200 OK\n".encode())

            # Read the headers
            headers = {}
            while True:
                header_line = read_line(connection)
                if header_line == '':
                    break  # End of headers
                key, value = header_line.split(": ")
                headers[key] = value

            filesize = int(headers.get("Content-Length", 0))
            if filesize == 0:
                print("Invalid file size received.")
                connection.sendall("FAILURE 400 Invalid file size\n".encode())
                continue

            print(f"Receiving file '{filename}' of size {filesize} bytes.")

            # Receive the file data
            with open(filepath, 'wb') as file:
                received_bytes = 0
                while received_bytes < filesize:
                    buffer_size = min(4096, filesize - received_bytes)
                    chunk = connection.recv(buffer_size)
                    if not chunk:
                        print("Connection lost while receiving file data.")
                        break
                    file.write(chunk)
                    received_bytes += len(chunk)
                    print(f"Received {received_bytes}/{filesize} bytes")
            print(f"File '{filename}' uploaded successfully.")
            # Send final acknowledgment to client
            connection.sendall("SUCCESS 201 Upload Complete\n".encode())

        elif command == "LS":
            # List files in the upload directory
            try:
                files = os.listdir(UPLOAD_DIRECTORY)
                # Filter out directories if you only want files
                files = [f for f in files if os.path.isfile(os.path.join(UPLOAD_DIRECTORY, f))]
                file_list = '\n'.join(files)
                content_length = len(file_list.encode())
                # Send success status code and message
                connection.sendall(f"SUCCESS 200 OK\n".encode())
                # Send the content length header
                connection.sendall(f"Content-Length: {content_length}\n\n".encode())
                # Send the file list
                connection.sendall(file_list.encode())
                print("Sent file list to client.")
            except Exception as e:
                print(f"Error retrieving file list: {e}")
                connection.sendall("FAILURE 500 Internal Server Error\n".encode())

        elif command == "QUIT":
            connection.sendall("SUCCESS 200 Goodbye\n".encode())
            connection.shutdown(socket.SHUT_WR)  # Ensure the client receives the message
            break  # Exit the loop and close the connection

        else:
            connection.sendall("FAILURE 400 Invalid Command\n".encode())

    connection.close()
    print(f"Connection with {addr} closed.")

def main():
    server_port = 12000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', server_port))
    server_socket.listen(5)
    print("Server is ready to receive a connection...")

    connection_socket, addr = server_socket.accept()
    handle_client(connection_socket, addr)

    # Close the server socket after handling one client
    server_socket.close()
    print("Server has been shut down.")

if __name__ == "__main__":
    main()