from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func, Boolean, Enum
from datetime import datetime
from flask_login import UserMixin
from enums.user_role import UserRole
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
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_signed: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def __init__(self, id = None, name = None, email = None, password = None, raw_password=None, is_active=False, role=None, role_value=None,created_at=None, updated_at=None, is_signed=False):
        BaseEntity.__init__(self)
        UserMixin.__init__(self)
        if id is not None:
            self.id = id
        if updated_at is not None:
            self.updated_at = updated_at
        if created_at is not None:
            self.created_at = created_at

        self.name = name
        self.raw_password = raw_password
        self.email = email
        self.password = password
        self.is_active = is_active
        self.is_signed = is_signed
        self.role = self.__set_role(role, role_value)

    def get_id(self):
        return str(self.id)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'is_signed': self.is_signed
        }
    def __set_role(self, role=None, role_value=None):
        if role is not None:
            return role
        elif role_value is not None:
            for enum_role in UserRole:
                if enum_role.value == role_value:
                    return enum_role
        return None