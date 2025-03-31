from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func
from datetime import datetime
from flask_login import UserMixin

from entities.baseentity import BaseEntity

class User(BaseEntity, UserMixin):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    def __init__(self, name = None, email = None, password = None, raw_password=None):
        BaseEntity.__init__(self)
        UserMixin.__init__(self)
        self.name = name
        self.raw_password = raw_password
        self.email = email
        self.password = password

    def get_id(self):
        return str(self.id)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
        }