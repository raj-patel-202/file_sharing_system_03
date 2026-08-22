from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"))
    level: Mapped[str] = mapped_column(String(20), default="read") # read, write

    user = relationship("User", back_populates="permissions")
    file = relationship("File", back_populates="permissions")

class AccessRequest(Base):
    __tablename__ = "access_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending, approved, rejected

    user = relationship("User", back_populates="access_requests")
    file = relationship("File", back_populates="access_requests")
