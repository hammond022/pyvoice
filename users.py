import requests

class User:
    def __init__(self, username, password, is_admin=False):
        self.username = username
        self.password = password
        self.is_admin = is_admin

class UserAuth:
    def __init__(self):
        self.auth_url = "http://localhost:8000/auth"
    
    def authenticate(self, username, password):
        try:
            response = requests.post(self.auth_url, json={
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return User(username, password, data.get("isAdmin", False))
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
