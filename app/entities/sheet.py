from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func, Boolean, sql
from datetime import datetime
from entities.baseentity import BaseEntity



class Sheet(BaseEntity):
    __tablename__ = 'datasheets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql.expression.true())

    def __init__(self, id = None, path = None, is_active=None, created_at=None, deleted_at=None, updated_at=None):
        BaseEntity.__init__(self)
        self.id = id
        self.path = path
        self.deleted_at = deleted_at
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_active = is_active


