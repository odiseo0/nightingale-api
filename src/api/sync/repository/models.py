from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.model import Base


class AccountSyncHead(Base):
    account_id: Mapped[UUID] = mapped_column(primary_key=True)
    last_sequence: Mapped[int] = mapped_column(BigInteger, server_default="0")
    retained_from_sequence: Mapped[int] = mapped_column(BigInteger, server_default="1")
    permission_epoch: Mapped[int] = mapped_column(BigInteger, server_default="1")
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
