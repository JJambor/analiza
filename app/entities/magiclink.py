from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func, Boolean, sql
from datetime import datetime,timedelta
from entities.baseentity import BaseEntity



class Magiclink(BaseEntity):
    __tablename__ = 'magiclinks'
    __LINK_ACTIVE_HOURS__ = 48

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    link: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    cancelled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + timedelta(hours=48)
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sql.expression.true())

    def __init__(self, link_value):
        BaseEntity.__init__(self)
        self.link = link_value


