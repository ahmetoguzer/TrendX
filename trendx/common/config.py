"""Configuration management using pydantic-settings."""

from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    url: str = Field(default="sqlite:///.data/trendx.db", description="Database URL")

    class Config:
        env_prefix = "DATABASE_"
        extra = "ignore"


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json or text)")

    class Config:
        env_prefix = "LOG_"
        extra = "ignore"


class AISettings(BaseSettings):
    """AI/LLM configuration."""

    provider: str = Field(default="openai", description="AI provider")
    api_key: Optional[str] = Field(default=None, description="AI API key")
    model: str = Field(default="gpt-3.5-turbo", description="AI model")
    max_tokens: int = Field(default=500, description="Maximum tokens")
    temperature: float = Field(default=0.7, description="Temperature for generation")

    class Config:
        env_prefix = "AI_"
        extra = "ignore"


class TwitterSettings(BaseSettings):
    """Twitter/X configuration."""

    api_key: Optional[str] = Field(default=None, description="Twitter API key")
    api_secret: Optional[str] = Field(default=None, description="Twitter API secret")
    access_token: Optional[str] = Field(default=None, description="Twitter access token")
    access_token_secret: Optional[str] = Field(
        default=None, description="Twitter access token secret"
    )
    bearer_token: Optional[str] = Field(default=None, description="Twitter bearer token")

    class Config:
        env_prefix = "TWITTER_"
        extra = "ignore"


class RedditSettings(BaseSettings):
    """Reddit configuration."""

    client_id: Optional[str] = Field(default=None, description="Reddit client ID")
    client_secret: Optional[str] = Field(default=None, description="Reddit client secret")
    user_agent: str = Field(default="TrendX/1.0", description="Reddit user agent")

    class Config:
        env_prefix = "REDDIT_"
        extra = "ignore"


class GoogleTrendsSettings(BaseSettings):
    """Google Trends configuration."""

    geolocation: str = Field(default="TR", description="Geolocation for trends")
    timeframe: str = Field(default="now 1-d", description="Timeframe for trends")

    class Config:
        env_prefix = "GOOGLE_TRENDS_"
        extra = "ignore"


class YouTubeSettings(BaseSettings):
    """YouTube configuration."""

    api_key: Optional[str] = Field(default=None, description="YouTube API key")

    class Config:
        env_prefix = "YOUTUBE_"
        extra = "ignore"


class SchedulerSettings(BaseSettings):
    """Scheduler configuration."""

    timezone: str = Field(default="Europe/Istanbul", description="Scheduler timezone")
    posting_interval_minutes: int = Field(
        default=60, description="Posting interval in minutes"
    )
    quiet_hours_start: int = Field(default=23, description="Quiet hours start (24h format)")
    quiet_hours_end: int = Field(default=7, description="Quiet hours end (24h format)")
    max_posts_per_day: int = Field(default=20, description="Maximum posts per day")

    class Config:
        env_prefix = "SCHEDULER_"
        extra = "ignore"


class SafetySettings(BaseSettings):
    """Safety configuration."""

    safe_mode: bool = Field(default=True, description="Enable safe mode")
    allow_media_download: bool = Field(
        default=False, description="Allow media download"
    )
    max_media_size_mb: int = Field(default=10, description="Maximum media size in MB")
    banned_keywords: List[str] = Field(
        default_factory=lambda: ["spam", "scam", "fake"],
        description="Banned keywords"
    )
    url_whitelist: List[str] = Field(
        default_factory=lambda: [
            "reddit.com",
            "youtube.com",
            "google.com",
            "bbc.com",
            "cnn.com",
        ],
        description="URL whitelist"
    )

    @validator("banned_keywords", pre=True)
    def parse_banned_keywords(cls, v: str | List[str]) -> List[str]:
        """Parse banned keywords from string or list."""
        if isinstance(v, str):
            return [keyword.strip() for keyword in v.split(",")]
        return v

    @validator("url_whitelist", pre=True)
    def parse_url_whitelist(cls, v: str | List[str]) -> List[str]:
        """Parse URL whitelist from string or list."""
        if isinstance(v, str):
            return [url.strip() for url in v.split(",")]
        return v

    class Config:
        env_prefix = "SAFETY_"
        extra = "ignore"


class WebSettings(BaseSettings):
    """Web dashboard configuration."""

    host: str = Field(default="127.0.0.1", description="Web host")
    port: int = Field(default=8000, description="Web port")
    debug: bool = Field(default=False, description="Debug mode")

    class Config:
        env_prefix = "WEB_"
        extra = "ignore"


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""

    posts_per_hour: int = Field(default=4, description="Posts per hour")
    requests_per_minute: int = Field(default=60, description="Requests per minute")

    class Config:
        env_prefix = "RATE_LIMIT_"
        extra = "ignore"


class Settings(BaseSettings):
    """Main application settings."""

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    ai: AISettings = Field(default_factory=AISettings)
    twitter: TwitterSettings = Field(default_factory=TwitterSettings)
    reddit: RedditSettings = Field(default_factory=RedditSettings)
    google_trends: GoogleTrendsSettings = Field(default_factory=GoogleTrendsSettings)
    youtube: YouTubeSettings = Field(default_factory=YouTubeSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    web: WebSettings = Field(default_factory=WebSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
