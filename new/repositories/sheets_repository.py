import contextlib
from sqlalchemy import select

from db import get_db
from entities.magiclink import Magiclink
from entities.sheet import Sheet
from entities.user import User

class SheetsRepository:
    @staticmethod
    def add_sheet(sheet):
        db = next(get_db())
        try:
            db.add(sheet)
            db.commit()
            db.refresh(sheet)
            return sheet
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_sheets():
        db = next(get_db())
        try:
            query = select(Sheet)
            return db.execute(query).scalars().all()
        except Exception as e:
            raise e