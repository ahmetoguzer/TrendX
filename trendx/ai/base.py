"""Base AI generator interface."""

from abc import ABC, abstractmethod
from typing import List

from ..common.models import TrendItem


class TweetContent:
    """Generated tweet content."""

    def __init__(
        self,
        turkish_text: str,
        english_text: str,
        hashtags: List[str],
        media_path: str | None = None,
        media_type: str | None = None,
        media_url: str | None = None,
        quote_tweet_id: str | None = None,
        quote_tweet_url: str | None = None,
    ) -> None:
        """
        Initialize tweet content.

        Args:
            turkish_text: Turkish tweet text
            english_text: English tweet text
            hashtags: List of hashtags
            media_path: Optional media file path
            media_type: Type of media (image, video, gif)
            media_url: URL to media file
            quote_tweet_id: ID of tweet to quote
            quote_tweet_url: URL of tweet to quote
        """
        self.turkish_text = turkish_text
        self.english_text = english_text
        self.hashtags = hashtags
        self.media_path = media_path
        self.media_type = media_type
        self.media_url = media_url
        self.quote_tweet_id = quote_tweet_id
        self.quote_tweet_url = quote_tweet_url


class BaseAIGenerator(ABC):
    """Abstract base class for AI content generators."""

    @abstractmethod
    async def generate_tweet_content(self, trend_item: TrendItem) -> TweetContent:
        """
        Generate tweet content for a trend item.

        Args:
            trend_item: Trend item to generate content for

        Returns:
            Generated tweet content
        """
        pass
