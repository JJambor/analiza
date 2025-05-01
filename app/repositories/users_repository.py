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
    def update_user(user_to_update):
        db = next(get_db())
        try:
            existing_user = db.get(User, user_to_update.id)
            if not existing_user:
                return None

            for key, value in user_to_update.__dict__.items():
                if value is not None and key != '_sa_instance_state':
                    setattr(existing_user, key, value)

            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)
            return existing_user
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

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

    @staticmethod
    def get_users():
        with contextlib.closing(next(get_db())) as db:
            try:
                query = select(User.id,User.name,User.email,User.created_at,User.updated_at,User.role,User.is_active, User.is_signed)
                return db.execute(query).all()
            except Exception as e:
                raise e