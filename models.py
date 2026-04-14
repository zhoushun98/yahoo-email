from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


class YahooAccount(Base):
    __tablename__ = "yahoo_accounts"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    imap_password = Column(String, nullable=False)
    status = Column(String, default="normal")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    aliases = relationship("Alias", back_populates="account", cascade="all, delete-orphan")


class Alias(Base):
    __tablename__ = "aliases"

    id = Column(Integer, primary_key=True)
    alias_email = Column(String, unique=True, nullable=False)
    account_id = Column(Integer, ForeignKey("yahoo_accounts.id"), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    account = relationship("YahooAccount", back_populates="aliases")
