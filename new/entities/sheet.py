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
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql.expression.true())

    def __init__(self, path):
        BaseEntity.__init__(self)
        self.path = path


