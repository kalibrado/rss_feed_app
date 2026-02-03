"""
SQLAlchemy Models - RSS Feed App
Optimized for PostgreSQL with proper indexing
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models"""

    pass


class User(Base):
    """
    User model
    Supports both regular users and admins
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # AI Configuration (provider-agnostic)
    ai_provider: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'openai', 'claude', 'none'
    ai_api_key: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Encrypted in production
    ai_model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # 'gpt-4', 'claude-3-opus', etc.

    # User preferences
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    feeds: Mapped[list["Feed"]] = relationship(
        "Feed", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<User(id={self.id}, username='{self.username}', admin={self.is_admin})>"
        )


class Feed(Base):
    """
    RSS Feed model
    Each user can have multiple feeds with custom configurations
    """

    __tablename__ = "feeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Feed info
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    site_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Feed configuration
    refresh_interval: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )  # minutes
    auto_delete_after: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # days, null = never
    max_articles: Mapped[int] = mapped_column(
        Integer, default=100, nullable=False
    )  # per fetch

    # Fetcher configuration
    fetcher_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # Example: {"preferred_method": "jina", "timeout": 30, "enabled_methods": ["jina", "playwright"]}

    # State
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fetch_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="feeds")
    articles: Mapped[list["Article"]] = relationship(
        "Article", back_populates="feed", cascade="all, delete-orphan"
    )

    # Composite unique constraint: one URL per user
    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_user_feed_url"),
        Index("ix_feeds_user_active", "user_id", "is_active"),
        Index("ix_feeds_last_fetched", "last_fetched_at"),
    )

    def __repr__(self):
        return f"<Feed(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class Article(Base):
    """
    Article model
    Stores enriched RSS entries with content, images, tags
    """

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    feed_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Article identifiers
    guid: Mapped[str] = mapped_column(String(512), nullable=False)  # RSS GUID
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Content
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # AI-generated

    # Metadata
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pub_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Enrichments
    images: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # {"article_image": "url", "site_logo": "url", "favicon": "url"}

    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    # ["tech", "ai", "python"]

    # Extraction metadata
    fetch_method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'cascade', 'jina', etc.
    content_length: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # User interactions
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    is_starred: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # AI summary metadata
    summary_provider: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # 'openai', 'claude'
    summary_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    summary_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    feed: Mapped["Feed"] = relationship("Feed", back_populates="articles")

    # Composite unique constraint: one GUID per feed
    __table_args__ = (
        UniqueConstraint("feed_id", "guid", name="uq_feed_article_guid"),
        Index("ix_articles_feed_date", "feed_id", "pub_date"),
        Index("ix_articles_feed_read", "feed_id", "is_read"),
        Index("ix_articles_feed_starred", "feed_id", "is_starred"),
        Index("ix_articles_search", "title"),  # For full-text search later
    )

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:30]}...', feed_id={self.feed_id})>"


class SystemConfig(Base):
    """
    System-wide configuration (admin panel)
    Key-value store for global settings
    """

    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<SystemConfig(key='{self.key}')>"


class JobLog(Base):
    """
    Log for scheduled jobs (refresh, auto-delete)
    Useful for debugging and monitoring
    """

    __tablename__ = "job_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # 'refresh', 'auto_delete'
    feed_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("feeds.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'success', 'error', 'partial'
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metrics
    articles_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_job_logs_type_status", "job_type", "status"),
        Index("ix_job_logs_started", "started_at"),
    )

    def __repr__(self):
        return f"<JobLog(id={self.id}, type='{self.job_type}', status='{self.status}')>"
