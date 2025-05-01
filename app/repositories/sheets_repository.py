import contextlib

from sqlalchemy import select, update

from db import get_db
from entities.sheet import Sheet

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
        with contextlib.closing(next(get_db())) as db:
            try:
                query = select(Sheet).where(Sheet.deleted_at.is_(None))
                return db.execute(query).scalars().all()
            except Exception as e:
                raise e
    @staticmethod
    def update_sheet(sheet):
        with contextlib.closing(next(get_db())) as db:
            try:
                db.add(sheet)
                db.commit()
                db.refresh(sheet)
                return sheet
            except Exception as e:
                raise e
    @staticmethod
    def get_active_sheets_paths():
        with contextlib.closing(next(get_db())) as db:
            try:
                query = select(Sheet.path).where(Sheet.is_active.is_(True)).where(Sheet.deleted_at.is_(None))
                return db.execute(query).scalars().all()
            except Exception as e:
                raise e
    @staticmethod
    def get_sheets_by_id(id_list):
        with contextlib.closing(next(get_db())) as db:
            try:
                query = select(Sheet).where(Sheet.id.in_(id_list))
                return db.execute(query).scalars().all()
            except Exception as e:
                raise e

    @staticmethod
    def update_many_sheets(sheets):
        with contextlib.closing(next(get_db())) as db:
            try:
                for sheet in sheets:
                    db.merge(sheet)
                db.commit()
                return len(sheets)
            except Exception as e:
                db.rollback()
                raise e
