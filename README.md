# 471-Assignment
Write a README file (text file; do not submit a .doc file) that contains

– Names and email addresses of all partners.
Tauheed Janjua - tjanjua@csu.fullerton.edu
Michael Rivera - michaelrivaroni@gmail.com
Tiffany Tran - 21ttran11@gmail.com
  
– The programming language you use (e.g., C++, Java, or Python)
Python

– How to execute your program.
*Run both codes on 2 terminals, server first so that the server opens*
# On the first terminal, start the server:
python3 FTPServer.py

# On the second terminal, start the client:
python3 FTPClient.py localhost 12000

# After connecting, use the following commands:
# 1. Download a file from the server:
GET <filename>
# Example:
GET test.txt

# 2. Upload a file to the server:
PUT <filename>
# Example:
PUT test.txt

# 3. List files in the server's upload directory:
LS

# 4. Disconnect from the server and exit:
QUIT


– Anything special about your submission that we should take note of
N/A
