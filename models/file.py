from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from models.base import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    size: Mapped[int] = mapped_column(BigInteger)
    content_type: Mapped[str] = mapped_column(String(100))
    checksum: Mapped[str | None] = mapped_column(String(64))
    visibility: Mapped[str] = mapped_column(String(20), default="private") # public, private
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    last_modified_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="files")
    last_modifier = relationship("User", foreign_keys=[last_modified_by_id])
    permissions = relationship("Permission", back_populates="file", cascade="all, delete-orphan")
    access_requests = relationship("AccessRequest", back_populates="file", cascade="all, delete-orphan")
