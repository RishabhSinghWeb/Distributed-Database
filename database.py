import sys, socket, json, select, time, random

PORT = int(sys.argv[1])
socket = socket.socket()
print(f"database starting on port {PORT}")
socket.bind(("", PORT))
socket.listen(5)
inputs = [socket]
timeouts = []
DB = [{"key": "uniqueID", "username": "Guest", "value": "Hey! How you doing?", "lock": False, "locked_value": None}]

while True:
    read_sockets, write_sockets, error_sockets = select.select(inputs, inputs, [], 5)
    for client in read_sockets:
        if client is socket:
            clientsock, clientaddr = client.accept()
            inputs.append(clientsock)
            print("connect from:", clientaddr)
        else:
            print("enter data recv from:", client.getpeername())
            data = client.recv(1024)
            if not data:
                inputs.remove(client)
            else:
                print("Timeout is set to 60")

                print("Got request from ")
                obj = json.loads(data.decode())
                # extract available data form request
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
                    if key: # send value of specified key
                        response = {
                            "type": "GET-RESPONSE",
                            "key": key,
                            "value": details["value"] if details else None,
                        }
                    else: # send all the entries of database
                        response = {
                            "type": "GET-RESPONSE",
                            "key": key,
                            "value": DB
                        }

                elif obj["type"] == "QUERY": # handles all the query requests
                    details = None
                    for entry in DB: # find the key in DB
                        if entry["key"] == obj['key']:
                            details = entry
                    answer = False

                    if details is None: # create new key
                        answer = True
                        DB.append({
                            "key": key,
                            "username": obj["username"],
                            "value": None,
                            "lock": True,
                            "locked_value": value,
                        })
                        timeouts.append((key, time.time()))

                    elif details["lock"] == False: # if key is not already locked
                        if details["username"] == username:
                            answer = True
                            details["lock"] = True # lock the key
                            details["locked_value"] = value
                            timeouts.append((key, time.time())) # set timeout for the query
                    response = {"type": "QUERY-REPLY", "key": key, "answer": answer}

                elif obj["type"] == "COMMIT": # commit the changes in DB
                    for entry in DB:
                        if entry["key"] == key: 
                            if entry["locked_value"] == value:
                                if obj["value"] == "=DELETE": # delete the entry
                                    DB.remove(entry)
                                else: # change the value of entry
                                    entry["value"] = value
                                    entry["lock"] = False
                            response = {
                                "type": "COMMIT-REPLY",
                                "key": key,
                                "value": value,
                            }
                client.send(json.dumps(response).encode()) # send the response

    # remove pending queries after certain time period 
    now = time.time()
    for key, t in timeouts: # check the timeouts of pending queries
        if now - t > 1:
            timeouts.remove((key, t))
            for entry in DB:
                if entry["key"] == key:
                    entry["lock"] = False

