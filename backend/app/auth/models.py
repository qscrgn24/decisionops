import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    session_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC), onupdate=lambda: datetime.datetime.now(datetime.UTC), nullable=False)

    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    provider: Mapped[str] = mapped_column(String, nullable=False)   # "google", "github", etc.
    provider_user_id: Mapped[str] = mapped_column(String, nullable=False)

    provider_email: Mapped[str | None] = mapped_column(String, nullable=True)  # Optional: email from provider for reference

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="oauth_accounts")

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)

    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),)
