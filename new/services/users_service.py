from datetime import datetime

import bcrypt
from flask_login import login_user, current_user, logout_user
import uuid

from entities.magiclink import Magiclink
from repositories.users_repository import UsersRepository
from repositories.redis_repository import RedisRepository
from repositories.links_repository import LinksRepository
from entities.user import User


class UsersService:

    @staticmethod
    def register_user(userDTO):
        print(f"Name: {userDTO.name}")
        print(f"Email: {userDTO.email}")
        print(f"Role: {userDTO.role.value}")
        userDTO.password = UsersService.__hash_password(userDTO.raw_password)
        UsersRepository.add_user(userDTO)
        pass

    @staticmethod
    def register_user_by_link(userDTO, link_dto):
        found_link = LinksRepository.find_link(link_dto, datetime.now())
        if found_link is None:
            return False
        found_link.is_active = False
        LinksRepository.update_link(found_link)
        userDTO.password = UsersService.__hash_password(userDTO.raw_password)
        UsersRepository.add_user(userDTO)
        return True

    @staticmethod
    def auth_user(userDTO):
        user = UsersRepository.find_user_by_email(userDTO.email)

        if user is None or not user.is_active:
            return False
        if user.email == userDTO.email and UsersService.__check_password(userDTO.raw_password, user.password):
            login_user(user)
            RedisRepository.cache_auth_user(user)
            user = User(id=user.id, is_signed=True, is_active=True)
            UsersRepository.update_user(user)
            return True
        return False

    @staticmethod
    def get_user(id):
        user = RedisRepository.get_cached_user(id)
        if user is not None:
            login_user(user)
            return user
        user = UsersService.get_user_from_db(id)
        if user and user.is_signed:
            return user
        if user and not user.is_signed:
            return None

    @staticmethod
    def get_user_from_db(id):
        return UsersRepository.find_user_by_id(id)

    @staticmethod
    def update_user(user_to_update):
        user = UsersRepository.update_user(user_to_update)
        RedisRepository.del_cached_user(user.id)
        return user

    @staticmethod
    def generate_link_for_new_user():
        generated_uuid = uuid.uuid4()
        uuid_string = str(generated_uuid)
        magiclink = Magiclink(uuid_string)
        link = LinksRepository.add_link(link=magiclink)
        parsed_link = "https://kompas.website/users/new/" + link.link
        return parsed_link

    @staticmethod
    def get_new_user_form(linkDto):
        link = LinksRepository.find_link(linkDto, datetime.now())
        return link

    @staticmethod
    def get_users():
        usersArr = UsersRepository.get_users()
        return [User(id=row.id, name=row.name, email=row.email,
                     created_at=row.created_at, updated_at=row.updated_at,
                     role=row.role, is_active=row.is_active, is_signed=row.is_signed) for row in usersArr]

    @staticmethod
    def logout():
        if current_user and not current_user.is_anonymous:
            RedisRepository.del_cached_user(current_user.id)
            user = User(id=current_user.id, is_signed=False, is_active=True)
            UsersRepository.update_user(user)
            logout_user()

    @staticmethod
    def __hash_password(raw_password):
        salt = bcrypt.gensalt()
        pass_bytes = raw_password.encode('utf-8')
        return bcrypt.hashpw(pass_bytes, salt).decode('utf-8')

    @staticmethod
    def __check_password(raw_password, hashed_password):
        raw_pass_bytes = raw_password.encode('utf-8')
        hashed_pass_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(raw_pass_bytes, hashed_pass_bytes)
