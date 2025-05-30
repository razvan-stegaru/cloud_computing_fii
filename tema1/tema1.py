import json
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

XML_FILE = "users.xml"

def load_users():
    if not os.path.exists(XML_FILE):
        return {}
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    users = {}
    for user in root.findall("user"):
        user_id = int(user.get("id"))
        users[user_id] = {
            "name": user.find("name").text,
            "age": int(user.find("age").text)
        }
    return users

def save_users():
    root = ET.Element("users")
    for user_id, data in users.items():
        user_elem = ET.SubElement(root, "user", id=str(user_id))
        ET.SubElement(user_elem, "name").text = data["name"]
        ET.SubElement(user_elem, "age").text = str(data["age"])
    tree = ET.ElementTree(root)
    tree.write(XML_FILE)

users = load_users()
next_id = max(users.keys(), default=0) + 1

class SimpleAPIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == '/users':
            self._set_headers(200)
            self.wfile.write(json.dumps(users).encode())
        elif self.path.startswith('/users/'):
            try:
                user_id = int(self.path.split('/')[-1])
                if user_id in users:
                    self._set_headers(200)
                    self.wfile.write(json.dumps(users[user_id]).encode())
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": "User not found"}).encode())
            except ValueError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid user ID"}).encode())

    def do_POST(self):
        global next_id
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        path_parts = self.path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'users' and path_parts[1].isdigit():
            specific_id = int(path_parts[1])
            if specific_id in users:
                self._set_headers(409)
                self.wfile.write(json.dumps({"error": f"User with ID {specific_id} already exists"}).encode())
                return

            # Create user with the specified ID if valid data
            if "name" in post_data and "age" in post_data:
                users[specific_id] = {"name": post_data["name"], "age": post_data["age"]}
                save_users()
                self._set_headers(201)
                self.wfile.write(json.dumps({"id": specific_id, "message": "User created with specific ID"}).encode())
                if specific_id >= next_id:
                    next_id = specific_id + 1
                return
            else:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid data"}).encode())
                return
        if isinstance(post_data, list):
            new_users_added = 0
            for user in post_data:
                if "name" in user and "age" in user:
                    while next_id in users:
                        next_id += 1
                    users[next_id] = {"name": user["name"], "age": user["age"]}
                    next_id += 1
                    new_users_added += 1
            save_users()
            self._set_headers(201)
            self.wfile.write(json.dumps({"message": f"{new_users_added} users created"}).encode())

        elif "name" in post_data and "age" in post_data:
            while next_id in users:
                next_id += 1
            users[next_id] = {"name": post_data["name"], "age": post_data["age"]}
            user_id = next_id
            next_id += 1
            save_users()
            self._set_headers(201)
            self.wfile.write(json.dumps({"id": user_id, "message": "User created"}).encode())

        else:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid data"}).encode())

    def do_PUT(self):
        if self.path == '/users':
            try:
                content_length = int(self.headers['Content-Length'])
                put_data = json.loads(self.rfile.read(content_length))
                for user_id, data in users.items():
                    data.update(put_data)
                save_users()
                self._set_headers(200)
                self.wfile.write(json.dumps({"message": "All users updated"}).encode())
            except ValueError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid data"}).encode())
        elif self.path.startswith('/users/'):
            try:
                user_id = int(self.path.split('/')[-1])
                if user_id in users:
                    content_length = int(self.headers['Content-Length'])
                    put_data = json.loads(self.rfile.read(content_length))
                    users[user_id].update(put_data)
                    save_users()
                    self._set_headers(200)
                    self.wfile.write(json.dumps({"message": "User updated"}).encode())
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": "User not found"}).encode())
            except ValueError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid user ID"}).encode())

    def do_DELETE(self):
        if self.path == '/users':
            users.clear()
            save_users()
            self._set_headers(200)
            self.wfile.write(json.dumps({"message": "All users deleted"}).encode())
        elif self.path.startswith('/users/'):
            try:
                user_id = int(self.path.split('/')[-1])
                if user_id in users:
                    del users[user_id]
                    save_users()
                    self._set_headers(200)
                    self.wfile.write(json.dumps({"message": "User deleted"}).encode())
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"error": "User not found"}).encode())
            except ValueError:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid user ID"}).encode())

PORT = 8080
server_address = ('', PORT)
httpd = HTTPServer(server_address, SimpleAPIHandler)
print(f"Server running on port {PORT}...")
httpd.serve_forever()
