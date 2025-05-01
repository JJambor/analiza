import contextlib
from sqlalchemy import select

from db import get_db
from entities.magiclink import Magiclink
from entities.user import User

class LinksRepository:
    @staticmethod
    def add_link(link):
        db = next(get_db())
        try:
            db.add(link)
            db.commit()
            db.refresh(link)
            return link
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_link(link_to_update):
        db = next(get_db())
        try:
            existing_link = db.get(Magiclink, link_to_update.id)
            if not existing_link:
                return None

            for key, value in link_to_update.__dict__.items():
                if value is not None and key != '_sa_instance_state':
                    setattr(existing_link, key, value)

            db.add(existing_link)
            db.commit()
            db.refresh(existing_link)
            return existing_link
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    @staticmethod
    def find_link(link_dto, date):
        with contextlib.closing(next(get_db())) as db:
            try:
                query = select(Magiclink).where(Magiclink.link == link_dto.link).where(Magiclink.created_at < date).where(Magiclink.cancelled_at > date).where(Magiclink.is_active == True)
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
                query = select(User.id,User.name,User.email,User.created_at,User.updated_at,User.role,User.is_active)
                return db.execute(query).all()
            except Exception as e:
                raise e