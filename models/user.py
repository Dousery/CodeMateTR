from werkzeug.security import generate_password_hash, check_password_hash

# This will be a mixin class that gets the db instance from the main app
class UserMixin:
    def set_password(self, password):
        # Daha kısa hash için method belirt
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password) 