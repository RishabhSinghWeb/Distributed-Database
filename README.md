# Distributed Database for Group Chat
<div style="text-align:center">
  <img src="https://raw.githubusercontent.com/RishabhSinghWeb/Distributed-Database/main/Static/images/model.png" alt="Working Model" height="300px"/>
</div>

## Usage
1. Clone the repository:
  ``` shell
  git clone https://github.com/RishabhSinghWeb/Distributed-Databases.git
  cd Distributed-Databases
  python3 -m pip install -r Requirements.txt
  ```
2. Run as many databases as required:
  ``` shell
  python3 database.py 8001
  python3 database.py 8002
  ```
  Then you can see `> Running socket on port: 8001` on your Command-line interface.
3. Run databases coordinator and webserver:
  ``` shell
  python3 coordinator.py 8000 localhost:8001 localhost:8002
  python3 webserver.py 8888 localhost:8000
  ```
  OR
  ``` shell
  python3 coordinator.py [coordinator_port] [database_host:port] [database_host:port]
  python3 webserver.py [webserver_port] [coordinator_port]
  ```
  Then you can see `> Running Web Server socket on port: [webserver_port]` on your Command-line interface.

4. Open http://localhost:8888/
5. Login with your credentials or use Username "Guest" with no password.
6. Now you can send or read the messages.
