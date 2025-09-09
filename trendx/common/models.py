"""Common data models using SQLModel."""

from datetime import datetime
from enum import Enum
import json
from typing import List, Optional

from sqlmodel import Field, SQLModel, JSON, Column


class TrendSource(str, Enum):
    """Trend source types."""

    REDDIT = "reddit"
    GOOGLE_TRENDS = "google_trends"
    TWITTER_TRENDS = "twitter_trends"
    YOUTUBE_TRENDING = "youtube_trending"
    RSS = "rss"
    SELENIUM_TRENDS = "selenium_trends"


class TrendItem(SQLModel, table=True):
    """Trend item model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    source: TrendSource
    external_id: str
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    score: float = Field(default=0.0)
    social_volume: int = Field(default=0)
    is_turkey_related: bool = Field(default=False)
    is_global: bool = Field(default=True)
    trend_metadata: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        indexes = [
            ("source", "external_id"),
            ("score",),
            ("created_at",),
        ]


class TweetContent(SQLModel, table=True):
    """Tweet content model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    trend_item_id: int = Field(foreign_key="trenditem.id")
    turkish_text: str
    english_text: str
    hashtags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    media_path: Optional[str] = None
    media_type: Optional[str] = None  # image, video, gif
    media_url: Optional[str] = None  # URL to media file
    quote_tweet_id: Optional[str] = None  # ID of tweet to quote
    quote_tweet_url: Optional[str] = None  # URL of tweet to quote
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        indexes = [
            ("trend_item_id",),
        ]


class PostQueue(SQLModel, table=True):
    """Post queue model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    tweet_content_id: int = Field(foreign_key="tweetcontent.id")
    scheduled_at: datetime
    posted_at: Optional[datetime] = None
    twitter_post_id: Optional[str] = None
    status: str = Field(default="pending")  # pending, posted, failed
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        indexes = [
            ("scheduled_at",),
            ("status",),
        ]


class PostHistory(SQLModel, table=True):
    """Post history model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    post_queue_id: int = Field(foreign_key="postqueue.id")
    twitter_post_id: str
    posted_at: datetime = Field(default_factory=datetime.utcnow)
    response_data: Optional[str] = None  # JSON string

    class Config:
        indexes = [
            ("twitter_post_id",),
            ("posted_at",),
        ]


class PublishResult(SQLModel):
    """Publish result model."""
    
    success: bool
    post_id: Optional[str] = None
    error_message: Optional[str] = None
