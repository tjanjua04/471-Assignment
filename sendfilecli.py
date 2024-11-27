# *******************************************************************
# This file illustrates how to send a file using an
# application-level protocol where the first 10 bytes
# of the message from client to server contain the file
# size and the rest contain the file data.
# *******************************************************************
import socket
import sys

# Command line checks
if len(sys.argv) < 2:
    print("USAGE python " + sys.argv[0] + " <FILE NAME>")
    sys.exit(1)  # Exit if no file name is provided

# Server address
serverAddr = "localhost"

# Server port
serverPort = 1234

# The name of the file
fileName = sys.argv[1]

try:
    # Open the file in binary mode
    fileObj = open(fileName, "rb")
except FileNotFoundError:
    print(f"ERROR: File '{fileName}' not found.")
    sys.exit(1)

# Create a TCP socket
connSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to the server
    connSock.connect((serverAddr, serverPort))
except ConnectionRefusedError:
    print("ERROR: Could not connect to the server.")
    sys.exit(1)

# The number of bytes sent
numSent = 0

# The file data
fileData = None

# Keep sending until all is sent
while True:
    # Read 65536 bytes of data
    fileData = fileObj.read(65536)

    # Make sure we did not hit EOF
    if fileData:
        # Get the size of the data read and convert it to string
        dataSizeStr = str(len(fileData))

        # Prepend 0's to the size string until the size is 10 bytes
        while len(dataSizeStr) < 10:
            dataSizeStr = "0" + dataSizeStr

        # Prepend the size of the data to the file data
        fileData = dataSizeStr.encode() + fileData  # Convert header and data to bytes

        # The number of bytes sent
        numSent = 0

        # Send the data!
        while len(fileData) > numSent:
            numSent += connSock.send(fileData[numSent:])
    else:
        break

print(f"Sent {numSent} bytes.")

# Close the socket and the file
connSock.close()
fileObj.close()
