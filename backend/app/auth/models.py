from sqlalchemy import Boolean, column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = column(Integer, primary_key=True, index=True)

    email = column(String, unique=True, index=True, nullable=False)
    username = column(String, unique=True, index=True, nullable=False)

    password_hash = column(String, nullable=False)

    is_active = column(Boolean, default=True, nullable=False)

    created_at = column(DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)
    updated_at = column(DateTime, default=datetime.datetime.now(datetime.UTC), onupdate=datetime.datetime.now(datetime.UTC), nullable=False)

    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id = column(Integer, primary_key=True, index=True)

    provider = column(String, nullable=False)   # "google", "github", etc.
    provider_user_id = column(String, nullable=False)

    provider_email = column(String, nullable=True)  # Optional: email from provider for reference

    user_id = column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="oauth_accounts")

    created_at = column(DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)

    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),)