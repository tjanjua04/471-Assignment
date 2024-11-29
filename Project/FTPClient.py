import socket
import sys
import os

def send_command(sock, command, headers=None):
    sock.sendall((command + '\n').encode())
    if headers:
        send_headers(sock, headers)

def send_headers(sock, headers):
    for key, value in headers.items():
        sock.sendall(f"{key}: {value}\n".encode())
    sock.sendall(b'\n')  # End of headers

def receive_line(sock):
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
        line = receive_line(sock)
        if line == '':
            break  # End of headers
        if ': ' in line:
            key, value = line.split(": ", 1)
            headers[key] = value
        else:
            print(f"Malformed header line: {line}")
    return headers

def list_files(control_sock):
    # Generate an ephemeral port by binding to port 0
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.bind(('', 0))  # Ephemeral port
    data_socket.listen(1)
    data_port = data_socket.getsockname()[1]  # Retrieve ephemeral port number

    # Send LS command with Data-Port header over control channel
    send_command(control_sock, "LS", headers={"Data-Port": str(data_port)})

    # Wait for server response over control channel
    response = receive_line(control_sock)
    print("Server:", response)
    if not response.startswith("SUCCESS 200"):
        print("Server rejected the LS command.")
        data_socket.close()
        return

    # Accept incoming connection from server on data channel
    try:
        conn, addr = data_socket.accept()
        print(f"Data connection established with {addr}")

        # Receive headers over data channel
        headers = receive_headers(conn)
        content_length = int(headers.get("Content-Length", 0))
        if content_length == 0:
            print("Invalid content length received.")
            conn.close()
            data_socket.close()
            return

        # Receive data over data channel
        received_bytes = 0
        file_list_data = b''
        while received_bytes < content_length:
            buffer_size = min(4096, content_length - received_bytes)
            chunk = conn.recv(buffer_size)
            if not chunk:
                print("Connection lost while receiving file list.")
                break
            file_list_data += chunk
            received_bytes += len(chunk)

        # Decode and display the directory listing
        file_list = file_list_data.decode()
        print("Files on server:")
        print(file_list)

        conn.close()
    finally:
        data_socket.close()

def download_file(control_sock, filename):
    # Generate an ephemeral port for the data channel
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.bind(('', 0))  # Ephemeral port
    data_socket.listen(1)
    data_port = data_socket.getsockname()[1]

    # Send GET command with Data-Port header
    send_command(control_sock, f"GET {filename}", headers={"Data-Port": str(data_port)})

    # Wait for server response
    response = receive_line(control_sock)
    print("Server:", response)
    if not response.startswith("SUCCESS 200"):
        print("Server rejected the GET command.")
        data_socket.close()
        return

    # Accept incoming data connection from server
    try:
        conn, addr = data_socket.accept()
        print(f"Data connection established with {addr}")

        # Receive headers
        headers = receive_headers(conn)
        filesize = int(headers.get("Content-Length", 0))
        if filesize == 0:
            print("Invalid file size received.")
            conn.close()
            data_socket.close()
            return

        print(f"Downloading '{filename}' of size {filesize} bytes.")
        received_bytes = 0
        with open(filename, 'wb') as file:
            while received_bytes < filesize:
                buffer_size = min(4096, filesize - received_bytes)
                chunk = conn.recv(buffer_size)
                if not chunk:
                    print("Connection lost while receiving file data.")
                    break
                file.write(chunk)
                received_bytes += len(chunk)
                print(f"Received {received_bytes}/{filesize} bytes")
        print(f"File '{filename}' downloaded successfully.")
        print(f"Total bytes transferred: {received_bytes}")

        # Now read the file and display its contents
        print("\nFile contents:")
        try:
            with open(filename, 'r') as file:
                print(file.read())
        except UnicodeDecodeError:
            print("The file is not a text file and cannot be displayed.")
        print("\n")
        conn.close()
    finally:
        data_socket.close()

def upload_file(control_sock, filename):
    try:
        filesize = os.path.getsize(filename)
        print(f"Uploading '{filename}' of size {filesize} bytes.")

        # Generate an ephemeral port for the data channel
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind(('', 0))  # Ephemeral port
        data_socket.listen(1)
        data_port = data_socket.getsockname()[1]

        # Send PUT command with Data-Port header
        send_command(control_sock, f"PUT {filename}", headers={"Data-Port": str(data_port)})

        # Wait for server response
        response = receive_line(control_sock)
        print("Server:", response)
        if not response.startswith("SUCCESS 200"):
            print("Server rejected the PUT command.")
            data_socket.close()
            return

        # Accept incoming data connection from server
        try:
            conn, addr = data_socket.accept()
            print(f"Data connection established with {addr}")

            # Send headers over data channel
            send_headers(conn, {"Content-Length": str(filesize)})

            # Send the file data
            with open(filename, 'rb') as file:
                bytes_sent = 0
                while True:
                    chunk = file.read(4096)
                    if not chunk:
                        break
                    conn.sendall(chunk)
                    bytes_sent += len(chunk)
                    print(f"Sent {bytes_sent}/{filesize} bytes")
            print("Finished sending file data.")
            print(f"Total bytes transferred: {bytes_sent}")

            # Wait for server's final acknowledgment
            response = receive_line(control_sock)
            print("Server:", response)
            if response.startswith("SUCCESS 201"):
                print(f"File '{filename}' uploaded successfully.")
            else:
                print("Error: Did not receive upload completion confirmation from server.")

            conn.close()
        finally:
            data_socket.close()
    except FileNotFoundError:
        print(f"File '{filename}' not found.")

def main():
    if len(sys.argv) != 3:
        print("Usage: python FTPClient.py <server_address> <server_port>")
        sys.exit(1)

    server_address = sys.argv[1]
    server_port = int(sys.argv[2])

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_address, server_port))

    while True:
        command = input("ftp> ").strip()
        if command.startswith("GET "):
            filename = command.split()[1]
            download_file(client_socket, filename)
        elif command.startswith("PUT "):
            upload_file(client_socket, command.split()[1])
        elif command == "LS":
            list_files(client_socket)
        elif command == "QUIT":
            send_command(client_socket, command)
            response = receive_line(client_socket)
            print("Server:", response)
            if response.startswith("SUCCESS 200"):
                print("Connection closed by server.")
                break
        else:
            print("Invalid or unsupported command.")

    client_socket.close()

if __name__ == "__main__":
    main()
