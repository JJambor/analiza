from repositories.users_repository import UsersRepository
from flask import Flask, session

class UsersService:

    @staticmethod
    def auth_user(email, password):
        user = UsersRepository.find_user_by_email(email)
        if user is None:
            return False
        if user.email == email and user.password == password:
            session['user_id'] = user.id
            return True
        return False