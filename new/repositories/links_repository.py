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
    def find_link(link_dto, date):
        with contextlib.closing(next(get_db())) as db:
            try:
                query = select(Magiclink).where(Magiclink.link == link_dto.link).where(Magiclink.created_at < date).where(Magiclink.cancelled_at > date)
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