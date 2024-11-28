import socket
import sys

def send_command(sock, command):
    sock.send(command.encode())

def receive_response(sock):
    response = sock.recv(1024).decode()
    print("Server:", response)
    return response

def download_file(sock, filename):
    response = receive_response(sock)
    print(f"Debug: Response received - {response}")  # Debugging line
    response_lines = response.split("\n")
    if len(response_lines) < 2:  # Check if the response has the required parts
        print("Error: Incomplete response from server.")
        return
    header = response_lines[1].split()  # File info is in the second line
    if len(header) < 3:
        print("Error: Unexpected header format.")
        return
    
    filename = header[1]  # Extract filename
    filesize = int(header[2])  # Extract filesize
    response = receive_response(sock)
    if response.startswith("SUCCESS"):
        response_lines = response.split("\n")
        header = response_lines[0].split()  # First line contains the status
        filename = header[3]                # Extract filename from the header
        filesize = int(header[4])  
        filesize = int(filesize)
        with open(filename, 'wb') as file:
            received_bytes = 0
            while received_bytes < filesize:
                chunk = sock.recv(1024)
                if chunk == b'EOF':
                    break
                file.write(chunk)
                received_bytes += len(chunk)
        print(f"File {filename} downloaded successfully.")

def upload_file(sock, filename):
    try:
        filesize = os.path.getsize(filename)
        send_command(sock, f"FILE {filename} {filesize}")
        with open(filename, 'rb') as file:
            chunk = file.read(1024)
        while chunk:
            sock.send(chunk)
            chunk = file.read(1024)
        sock.send("EOF".encode())
        print(receive_response(sock))
    except FileNotFoundError:
        print(f"File {filename} not found.")

def main():
    if len(sys.argv) != 3:
        print("Usage: python client.py <server_address> <server_port>")
        sys.exit(1)
    
    server_address = sys.argv[1]
    server_port = int(sys.argv[2])
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_address, server_port))
    
    while True:
        command = input("ftp> ")
        if command.startswith("GET"):
            send_command(client_socket, command)
            download_file(client_socket, command.split()[1])
        elif command.startswith("PUT"):
            send_command(client_socket, command)
            upload_file(client_socket, command.split()[1])
        elif command == "LS":
            send_command(client_socket, command)
            print(receive_response(client_socket))
        elif command == "QUIT":
            send_command(client_socket, command)
            print(receive_response(client_socket))
            break
        else:
            print("Invalid command.")
    
    client_socket.close()

if __name__ == "__main__":
    main()
