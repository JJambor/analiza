import bcrypt
from flask_login import login_user

from repositories.users_repository import UsersRepository
from repositories.redis_repository import RedisRepository
class UsersService:

    @staticmethod
    def register_user(userDTO):
        print(f"Name: {userDTO.name}")
        print(f"Email: {userDTO.email}")
        print(f"Password: {userDTO.password}")
        userDTO.password = UsersService.__hash_password(userDTO.raw_password)
        UsersRepository.add_user(userDTO)
        pass
    @staticmethod
    def auth_user(userDTO):
        print(userDTO.email)
        user = UsersRepository.find_user_by_email(userDTO.email)

        if user is None:
            return False
        if user.email == userDTO.email and UsersService.__check_password(userDTO.raw_password, user.password):
            login_user(user)
            RedisRepository.cache_auth_user(user)

            return True
        return False
    @staticmethod
    def get_user(id):
        user = RedisRepository.get_cached_user(id)
        if (user is not None):
            return user
        user = UsersRepository.find_user_by_id(id)
        if user is None:
            return False
        else:
            return user

    @staticmethod
    def __hash_password(raw_password):
        salt = bcrypt.gensalt()
        pass_bytes = raw_password.encode('utf-8')
        return bcrypt.hashpw(pass_bytes, salt).decode('utf-8')

    @staticmethod
    def __check_password(raw_password,hashed_password):
        raw_pass_bytes = raw_password.encode('utf-8')
        hashed_pass_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(raw_pass_bytes, hashed_pass_bytes)