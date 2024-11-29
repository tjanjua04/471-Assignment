import socket
import sys
import os

def send_command(sock, command):
    sock.sendall((command + '\n').encode())

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
        key, value = line.split(": ")
        headers[key] = value
    return headers

def download_file(sock, filename):
    # Wait for server status code
    response = receive_line(sock)
    print("Server:", response)
    if not response.startswith("SUCCESS 200"):
        print("Server rejected the GET command.")
        return

    # Receive headers
    headers = receive_headers(sock)
    filesize = int(headers.get("Content-Length", 0))
    if filesize == 0:
        print("Invalid file size received.")
        return

    print(f"Downloading '{filename}' of size {filesize} bytes.")
    received_bytes = 0
    with open(filename, 'wb') as file:
        while received_bytes < filesize:
            buffer_size = min(4096, filesize - received_bytes)
            chunk = sock.recv(buffer_size)
            if not chunk:
                print("Connection lost while receiving file data.")
                break
            file.write(chunk)
            received_bytes += len(chunk)
            print(f"Received {received_bytes}/{filesize} bytes")
    print(f"File '{filename}' downloaded successfully.")

    # Now read the file and display its contents
    print("\nFile contents:")
    try:
        with open(filename, 'r') as file:
            print(file.read())
    except UnicodeDecodeError:
        print("The file is not a text file and cannot be displayed.")

def upload_file(sock, filename):
    try:
        filesize = os.path.getsize(filename)
        print(f"Uploading '{filename}' of size {filesize} bytes.")
        # Send the PUT command with filename
        send_command(sock, f"PUT {filename}")

        # Wait for server status code
        response = receive_line(sock)
        print("Server:", response)
        if not response.startswith("SUCCESS 200"):
            print("Server rejected the PUT command.")
            return

        # Send headers
        sock.sendall(f"Content-Length: {filesize}\n\n".encode())

        # Send the file data
        with open(filename, 'rb') as file:
            bytes_sent = 0
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                sock.sendall(chunk)
                bytes_sent += len(chunk)
                print(f"Sent {bytes_sent}/{filesize} bytes")
        print("Finished sending file data.")

        # Wait for server's final acknowledgment
        response = receive_line(sock)
        print("Server:", response)
        if response.startswith("SUCCESS 201"):
            print(f"File '{filename}' uploaded successfully.")
        else:
            print("Error: Did not receive upload completion confirmation from server.")
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
            send_command(client_socket, command)
            download_file(client_socket, filename)
        elif command.startswith("PUT "):
            upload_file(client_socket, command.split()[1])
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
