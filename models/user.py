from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]

    files = relationship("File", foreign_keys="[File.owner_id]", back_populates="owner", cascade="all, delete-orphan")
    permissions = relationship("Permission", back_populates="user", cascade="all, delete-orphan")
    access_requests = relationship("AccessRequest", back_populates="user", cascade="all, delete-orphan")
    upload_sessions = relationship("UploadSession", back_populates="user", cascade="all, delete-orphan")
