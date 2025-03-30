from sqlalchemy.orm import Session
from db import get_db
from sqlalchemy import select

from entities.user import User


class UsersRepository:
    @staticmethod
    def add_user(name, email, password):
        db = next(get_db())
        try:
            user = User(name=name, email=email, password=password)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise e


    @staticmethod
    def find_user_by_email(email):
        db = next(get_db())
        try:
            query = select(User).where(User.email == email)
            return db.scalar(query)
        except Exception as e:

            raise e