from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base, Date


class User(Date, Base, kw_only=True):
    id: Mapped[int] = mapped_column(
        BigInteger,
        init=False,
        autoincrement=True,
        primary_key=True,
    )
    external_id: Mapped[str | None]
    role_id: Mapped[int] = mapped_column(ForeignKey("user_roles.id"))
    name: Mapped[str] = mapped_column(String(511))
    alias: Mapped[str | None]
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    password: Mapped[str] = mapped_column(String(320))
    phone_number: Mapped[str | None] = mapped_column(String(20))
    phone_code: Mapped[str | None]
    id_number: Mapped[str | None]
