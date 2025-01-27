from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, data):
        self.id = str(data.get('_id', ''))
        self.username = data.get('username', '')
        self.password_hash = data.get('password_hash', '')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
        }
