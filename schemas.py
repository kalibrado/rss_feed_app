"""
Pydantic schemas for API request/response validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


class UserUpdate(BaseModel):
    """Schema for user profile updates"""
    email: Optional[EmailStr] = None
    ai_provider: Optional[str] = Field(None, max_length=50)
    ai_api_key: Optional[str] = Field(None, max_length=255)
    ai_model: Optional[str] = Field(None, max_length=100)
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """Schema for user response (public info)"""
    id: int
    is_admin: bool
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(UserResponse):
    """Schema for user detail response (includes AI config)"""
    ai_provider: Optional[str]
    ai_model: Optional[str]
    preferences: Dict[str, Any]
    
    # Note: ai_api_key is NEVER returned in responses
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data"""
    user_id: Optional[int] = None


# ============================================================================
# FEED SCHEMAS
# ============================================================================

class FeedBase(BaseModel):
    """Base feed schema"""
    url: str = Field(..., max_length=2048)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    refresh_interval: int = Field(default=60, ge=5, le=1440)  # 5 min to 24h
    auto_delete_after: Optional[int] = Field(None, ge=1)  # days
    max_articles: int = Field(default=100, ge=10, le=500)
    fetcher_config: Dict[str, Any] = Field(default_factory=dict)


class FeedCreate(FeedBase):
    """Schema for feed creation"""
    pass


class FeedUpdate(BaseModel):
    """Schema for feed updates"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    refresh_interval: Optional[int] = Field(None, ge=5, le=1440)
    auto_delete_after: Optional[int] = Field(None, ge=1)
    max_articles: Optional[int] = Field(None, ge=10, le=500)
    fetcher_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class FeedResponse(FeedBase):
    """Schema for feed response"""
    id: int
    user_id: int
    site_url: Optional[str]
    is_active: bool
    last_fetched_at: Optional[datetime]
    last_error: Optional[str]
    fetch_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FeedWithStats(FeedResponse):
    """Schema for feed with article statistics"""
    article_count: int
    unread_count: int
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# ARTICLE SCHEMAS
# ============================================================================

class ArticleBase(BaseModel):
    """Base article schema"""
    title: str = Field(..., max_length=512)
    url: str = Field(..., max_length=2048)
    content_html: str
    summary: Optional[str] = None
    author: Optional[str] = Field(None, max_length=255)
    pub_date: Optional[datetime] = None
    images: Dict[str, Optional[str]] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class ArticleResponse(ArticleBase):
    """Schema for article response"""
    id: int
    feed_id: int
    guid: str
    fetch_method: str
    content_length: int
    is_read: bool
    is_starred: bool
    read_at: Optional[datetime]
    summary_provider: Optional[str]
    summary_model: Optional[str]
    summary_generated_at: Optional[datetime]
    fetched_at: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ArticleUpdate(BaseModel):
    """Schema for article updates"""
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None


class ArticleSummaryRequest(BaseModel):
    """Schema for AI summary request"""
    provider: Optional[str] = Field(None, description="Override user's default AI provider")
    model: Optional[str] = Field(None, description="Override user's default AI model")


class ArticleSummaryResponse(BaseModel):
    """Schema for AI summary response"""
    summary: str
    provider: str
    model: str
    generated_at: datetime


# ============================================================================
# SYSTEM CONFIG SCHEMAS
# ============================================================================

class SystemConfigBase(BaseModel):
    """Base system config schema"""
    key: str = Field(..., max_length=100)
    value: Dict[str, Any]
    description: Optional[str] = None


class SystemConfigCreate(SystemConfigBase):
    """Schema for system config creation"""
    pass


class SystemConfigUpdate(BaseModel):
    """Schema for system config updates"""
    value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class SystemConfigResponse(SystemConfigBase):
    """Schema for system config response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PAGINATION SCHEMAS
# ============================================================================

class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    skip: int
    limit: int
    has_more: bool


# ============================================================================
# JOB LOG SCHEMAS
# ============================================================================

class JobLogResponse(BaseModel):
    """Schema for job log response"""
    id: int
    job_type: str
    feed_id: Optional[int]
    status: str
    message: Optional[str]
    articles_processed: int
    duration_seconds: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)