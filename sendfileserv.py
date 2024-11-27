# *****************************************************
# This file implements a server for receiving the file
# sent using sendfile(). The server receives a file and
# prints its contents.
# *****************************************************

import socket

# The port on which to listen
listenPort = 1234

# Create a welcome socket.
welcomeSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
welcomeSock.bind(('', listenPort))

# Start listening on the socket
welcomeSock.listen(1)

# ************************************************
# Receives the specified number of bytes
# from the specified socket
# @param sock - the socket from which to receive
# @param numBytes - the number of bytes to receive
# @return - the bytes received
# *************************************************
def recvAll(sock, numBytes):
    # The buffer to hold received bytes
    recvBuff = b""  # Use bytes instead of str

    # Keep receiving until all bytes are received
    while len(recvBuff) < numBytes:
        # Attempt to receive bytes
        tmpBuff = sock.recv(numBytes - len(recvBuff))

        # The other side has closed the socket
        if not tmpBuff:
            break

        # Add the received bytes to the buffer
        recvBuff += tmpBuff

    return recvBuff


# Accept connections forever
while True:
    print("Waiting for connections...")

    # Accept connections
    clientSock, addr = welcomeSock.accept()

    print("Accepted connection from client: ", addr)
    print("\n")

    # The buffer to hold all data received from the client
    fileData = b""  # Use bytes

    # The size of the incoming file
    fileSize = 0

    # Receive the first 10 bytes indicating the size of the file
    fileSizeBuff = recvAll(clientSock, 10)

    # Convert the file size from bytes to int
    try:
        fileSize = int(fileSizeBuff.decode())  # Decode bytes to string for conversion
    except ValueError:
        print("Invalid file size received. Closing connection.")
        clientSock.close()
        continue

    print("The file size is ", fileSize)

    # Get the file data
    fileData = recvAll(clientSock, fileSize)

    print("The file data is: ")
    print(fileData.decode())  # Decode bytes to string to display

    # Close the client socket
    clientSock.close()
