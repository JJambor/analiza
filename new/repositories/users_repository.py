import contextlib
from sqlalchemy import select

from db import get_db
from entities.user import User

class UsersRepository:
    @staticmethod
    def add_user(user):
        db = next(get_db())
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def find_user_by_email(email):
        with contextlib.closing(next(get_db())) as db:
            try:
                query = select(User).where(User.email == email)
                return db.scalar(query)
            except Exception as e:
                raise e
    @staticmethod
    def find_user_by_id(id):
        with contextlib.closing(next(get_db())) as db:
            try:
                query = select(User).where(User.id == id)
                return db.scalar(query)
            except Exception as e:
                raise e