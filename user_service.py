import hashlib
from models import User
from repositories import UserRepository


class UserService:

    def __init__(self):
        self.user_repository = UserRepository()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def register(self, username, password) -> User:
        if not username or not password:
            raise ValueError("Логин и пароль не могут быть пустыми")
        existing_user = self.user_repository.find_by_username(username)
        existing_user = self.user_repository.find_by_username(username)
        if existing_user:
            return None

        new_user = User(username=username, password_hash=self._hash_password(password))

        return self.user_repository.save(new_user)

    def login(self, username, password) -> User:
        user = self.user_repository.find_by_username(username)

        if user and user.password_hash == self._hash_password(password):
            return user

        return None