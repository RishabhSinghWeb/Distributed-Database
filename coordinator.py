import sys, socket, json, select, time, random

# connnecting to all the databases
DATABASES = []
for i in range(2, len(sys.argv)): # database addresses from second command line argument
    try:
        print("Connecting to " + sys.argv[i])
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        parts = sys.argv[i].split(":")
        sock.connect((parts[0], int(parts[1])))
        DATABASES.append(sock) # add database to database list
    except Exception as e:
        print("Could not connnet. Quitting")
        print(e)
        sys.exit(1)

PORT = int(sys.argv[1])

# socket = socket.socket()
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"coordinator starting on port {PORT}")
socket.bind(("", PORT))

socket.listen(5)
inputs = [socket]
print("connecting")

while True:
    read_sockets, write_sockets, error_sockets = select.select(inputs, inputs, [], 1) # it monitors socket requests
    for client in read_sockets: 

        if client is socket:  # New Connection
            clientsock, clientaddr = client.accept()
            inputs.append(clientsock)
            print("request from", socket)
            # clientsock.settimeout(60)
            # print ('checking timeout')

        else:  # Existing Connection
            print("Got request from client:", client.getpeername())
            data = client.recv(1024)
            if data is None:
                inputs.remove(client) # removes closed clients
            else: # data exist in request
                for req in data.split(b"}"): # process available requests
                    if len(req)>3: # ignore \n
                        data = req+b"}"
                        obj = json.loads(data)
                        # load balancing
                        database = random.choice(DATABASES) # select a random database
                        print("using database ", database.getpeername())
                        try:
                            key = obj["key"]
                        except:
                            key = None
                        try:
                            value = obj["value"]
                        except:
                            value = None
                        try:
                            username = obj["username"]
                        except:
                            username = None

                        if obj["type"] == "GET":
                            if key: # send data of specific key
                                database.send(
                                    ('{ "type": "GET", "key": "' + str(key) + '"}\n').encode()
                                )
                                data = database.recv(10240)
                                obj = json.loads(data)
                                response = {
                                    "type": "GET-RESPONSE",
                                    "key": obj["key"],
                                    "value": obj["value"],
                                }
                            else: # send all the data in DB when no key is specified
                                database.send('{"type": "GET"}\n'.encode())
                                data = database.recv(10240).decode()
                                # obj = json.loads(data)
                                response = {
                                    "type": "GET-RESPONSE",
                                    "key": None,
                                    "value": data,
                                }

                        elif obj["type"] == "SET": # Create or Update value in DB

                            lockable = True
                            req = []
                            for database in DATABASES:
                                database.send(
                                    (
                                        '{ "type": "QUERY", "key": "' + key
                                        + '","value":"' + value
                                        + '","username":"' + username
                                        + '"}\n'
                                    ).encode()
                                )
                                req.append(database)
                            for r in req: # check every database locks the value
                                data = json.loads(r.recv(1024))
                                if data["answer"] != True:
                                    lockable = False
                            response = {"type": "QUERY-REPLY", "key": key, "value": value}
                            if lockable: # if every database locked the new value then commit the changes
                                for database in DATABASES:
                                    database.send(
                                        (
                                            '{ "type": "COMMIT", "key": "' + str(key)
                                            + '","value":"' + value
                                            + '","username":"' + username
                                            + '"}\n'
                                        ).encode()
                                    )
                                    data = json.loads(database.recv(1024))
                                    # assuming all databases did commit
                                    # response = {"locked":locked}
                                    response = {
                                        "type": "COMMIT-REPLY",
                                        "key": data["key"],
                                        "value": data["value"],
                                    }
                            # else the database automatically removes the lock after timeout period

                        elif obj["type"] == "DELETE": # delete the key and its values 
                            lockable = True
                            req = []
                            for database in DATABASES: 
                                database.send(
                                    (
                                        '{ "type": "QUERY", "key": "' + str(key)
                                        + '","value":"' + "=DELETE"
                                        + '","username":"' + str(username)
                                        + '"}\n'
                                    ).encode()
                                )
                                req.append(database)
                            for r in req:
                                data = json.loads(r.recv(1024))
                                if data["answer"] != True:
                                    lockable = False
                            response = {"type": "QUERY-REPLY", "key": key, "value": value}
                            if lockable:
                                for database in DATABASES:
                                    database.send(
                                        (
                                            '{ "type": "COMMIT", "key": "' + key
                                            + '","value":"' + "=DELETE"
                                            + '","username":"' + str(username)
                                            + '"}\n'
                                        ).encode()
                                    )
                                    data = json.loads(database.recv(1024))
                                    # assuming all databases did commit
                                    # response = {"locked":locked}
                                    response = {
                                        "type": "COMMIT-REPLY",
                                        "key": data["key"],
                                        "value": "=DELETE",
                                    }
                        response = json.dumps(response)
                        client.send(response.encode())
