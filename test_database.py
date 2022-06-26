import unittest
import socket
import subprocess
import json
import time
import os

PORT = 50321


class TestDatabase(unittest.TestCase):
    def setUp(self):
        '''
        make a new socket for every test
        '''
        print("starting up database")

        self.database = subprocess.Popen(
            ["python", "database.py", str(PORT)],
            cwd=os.getcwd()

        )
        time.sleep(0.3)
        print("connecting")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('127.0.0.1', PORT))
        self.sock.settimeout(2)  # shouldn't happen!

    def tearDown(self):
        self.database.terminate()
        self.database.wait(10)
        self.sock.close()

    def test_get_data_success(self):
        '''
        database should start up with at least 1 key to fetch:
        "P" with value "=NP"
        fetch seeded P value
        '''
        # send a 'GET'
        self.sock.sendall(
            '{ "type": "GET", "key": "P"}\n'.encode()
        )
        # now get the response
        back = self.sock.recv(1024)
        obj = json.loads(back)

        # { "type": "GET-RESPONSE", "key": "P", "value": null}
        self.assertEqual(obj['type'], "GET-RESPONSE")
        self.assertEqual(obj['key'], "P")
        self.assertEqual(obj['value'], "=NP")

    def test_get_data_failure(self):
        '''
        Fetches a value that is not there
        '''
        # send a 'GET'
        self.sock.sendall(
            '{ "type": "GET", "key": "x"}\n'.encode()
        )
        # now get the response
        back = self.sock.recv(1024)
        obj = json.loads(back)

        # { "type": "GET-RESPONSE", "key": "P", "value": null}
        self.assertEqual(obj['type'], "GET-RESPONSE")
        self.assertEqual(obj['key'], "x")
        self.assertIsNone(obj['value'])

    def test_set_data(self):
        '''
        Try to set some data.
        '''
        key = "Test"
        value = "McTester"
        # First check that it is none
        first = {
            "type": "GET",
            "key": key
        }
        firstStr = json.dumps(first) + "\n"
        self.sock.sendall(
            firstStr.encode()
        )
        # now get the response
        back = self.sock.recv(1024)
        obj = json.loads(back)

        self.assertEqual(obj['type'], "GET-RESPONSE")
        self.assertEqual(obj['key'], key)
        self.assertIsNone(obj['value'])

        # then start the commit
        second = {
            "type": "QUERY",
            "key": key,
            "value": value
        }
        secondStr = json.dumps(second) + "\n"
        self.sock.sendall(
            secondStr.encode()
        )

        # get the query reply, should be shaped like
        # {type: QUERY-REPLY, key=k, answer=True/False}
        back = self.sock.recv(1024)
        obj = json.loads(back)
        self.assertEqual(obj['type'], "QUERY-REPLY")
        self.assertEqual(obj['key'], key)
        self.assertTrue(obj['answer'])

        # start the commit
        third = {
            "type": "COMMIT",
            "key": key,
            "value": value
        }
        thirdStr = json.dumps(third) + "\n"
        self.sock.sendall(
            thirdStr.encode()
        )

        # get the response
        # {type: COMMIT-REPLY, key=k, value=v}
        back = self.sock.recv(1024)
        obj = json.loads(back)
        self.assertEqual(obj['type'], "COMMIT-REPLY")
        self.assertEqual(obj['key'], key)
        self.assertEqual(obj['value'], value)

    def test_double_set(self):
        '''
        test failure case.
        Try to set two at the same time
        '''
        key = "Test"
        value = "McTester"
        # First check that it is none
        first = {
            "type": "GET",
            "key": key
        }
        firstStr = json.dumps(first) + "\n"
        self.sock.sendall(
            firstStr.encode()
        )
        # now get the response
        back = self.sock.recv(1024)
        obj = json.loads(back)

        self.assertEqual(obj['type'], "GET-RESPONSE")
        self.assertEqual(obj['key'], key)
        self.assertIsNone(obj['value'])

        # then start the commit
        second = {
            "type": "QUERY",
            "key": key,
            "value": value
        }
        secondStr = json.dumps(second) + "\n"
        self.sock.sendall(
            secondStr.encode()
        )

        # get the query reply, should be shaped like
        # {type: QUERY-REPLY, key=k, answer=True/False}
        back = self.sock.recv(1024)
        obj = json.loads(back)
        self.assertEqual(obj['type'], "QUERY-REPLY")
        self.assertEqual(obj['key'], key)
        self.assertTrue(obj['answer'])

        key = "Test"
        badvalue = "McTester"
        # First check that the value is not set without the commit
        first = {
            "type": "GET",
            "key": key
        }
        firstStr = json.dumps(first) + "\n"
        self.sock.sendall(
            firstStr.encode()
        )
        # now get the response
        back = self.sock.recv(1024)
        obj = json.loads(back)
        self.assertEqual(obj['type'], "GET-RESPONSE")
        self.assertEqual(obj['key'], key)
        self.assertIsNone(obj['value'])

        # then start the bad commit
        second = {
            "type": "QUERY",
            "key": key,
            "value": badvalue
        }
        secondStr = json.dumps(second) + "\n"
        self.sock.sendall(
            secondStr.encode()
        )

        # get the query reply, should be shaped like
        # {type: QUERY-REPLY, key=k, answer=True/False}
        back = self.sock.recv(1024).decode('utf-8')
        print(back)
        # should have 2
        # find the opening bracket, start looking at spot 2 to skip
        # the first one

        obj = json.loads(back)
        self.assertEqual(obj['type'], "QUERY-REPLY")
        self.assertEqual(obj['key'], key)
        self.assertFalse(obj['answer'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
