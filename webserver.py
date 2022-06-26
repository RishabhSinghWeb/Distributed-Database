import socket
import threading
import json
import uuid
import sys

users = [
    {"username": "Guest", "password": ""},
    {"username": "Rishabh", "password": "Rishabh123"},
    {"username": "Dhina", "password": "Dhina17"},
]

# connect to coordinator
coordinator = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
parts = sys.argv[2].split(":")
coordinator.connect((parts[0], int(parts[1])))

def threaded(client):
    request = client.recv(1024).decode()
    print(request.split("\n")[0])
    headers = request.split("\r\n\r\n")[0].split() # request.split()
    body = request.split("\r\n\r\n")[1]
    req_type = headers[0]
    location = headers[1]
    response = "HTTP/1.1 200 OK\n"

    if location[:4] == "/api":
        for header in headers:
            if header[:9] == "username=":
                username = header[9:]

        if location[:10] == "/api/login":  # manages all login requests

            if req_type == "POST": # login with username and password
                body = json.loads(body)
                username = None
                login = False
                for user in users: # check username and password matching in users list
                    if user["username"] == body["username"] and user["password"] == body["password"]:
                        username = body["username"]
                        login = True
                if login: # valid login
                    response += "set-cookie: username=" + username + "; SameSite=Lax; Max-Age=3600; Path=/;\n"
                else: # invalid login
                    response = "HTTP/1.1 403 Not Authorized\n"

            elif req_type == "DELETE": # remove the cookie header
                response += "set-cookie: username=; SameSite=Lax ; Path=/;\n"

            response += "\r\n"  # ends HTTP header section
        elif location[:11] == "/api/messages":  # manages all messages requests
            response += "\r\n"  # ends HTTP header section

            if req_type == "GET": 
                coordinator.send('{"type": "GET", "key": null}\n'.encode()) # get DB entries from coordinator

            elif req_type == "POST": # create a new entry in DB through coordinator
                coordinator.send(json.dumps({
                    "type": "SET", 
                    "key": str(uuid.uuid4())[:8], 
                    "username": username, 
                    "value": body 
                }).encode())

            elif req_type == "DELETE": # delete entry from the DB through coordinator
                coordinator.send(json.dumps({
                    "type": "DELETE", 
                    "key": body,
                    "username": username
                }).encode())

            response += coordinator.recv(10240).decode()

        client.send(response.encode())

    else:  # send file from Static directory/folder
        if location == "/": # redirect / requests to /index.html internal redirect
            location = "/index.html"
        location = location[1:]  # removes prefix "/"
        print(location)
        extension = location.split(".")[::-1][0]
        
        response = (response + f"Content-Type: text/{extension}\n\n").encode()
        try:
            with open("Static/" + location, "rb") as file: 
                response += file.read()
        except OSError as e:
            print("error while reading the file", e)
            response = b"HTTP/1.0 404 Not Found\n\nError 404: File not found"
        client.send(response)

    client.close()


host = ""
try:
    port = int(sys.argv[1])
except:
    port = 8888
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
print("Running Web Server socket on port", port)
    
s.listen(5) # start listening to web requests
print(f"socket is listening\nPress Ctrl then click on link http://localhost:{port}")

while True:
    client, addr = s.accept()
    print("Connected by :", addr)
    # create a new thread for every new request that runs parallelly in CPU
    threading.Thread(target=threaded, args=(client,)).start()

s.close()
