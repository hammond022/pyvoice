class User:
    def __init__(self, username, password, is_admin=False):
        self.username = username
        self.password = password
        self.is_admin = is_admin

class UserAuth:
    def __init__(self):
        self.users = {
            "admin": User("admin", "admin123", True),
            "user": User("user", "user123", False)
        }
    
    def authenticate(self, username, password):
        if username in self.users:
            user = self.users[username]
            if user.password == password:
                return user
        return None
