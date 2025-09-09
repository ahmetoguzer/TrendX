"""Mock AI generator for testing and development."""

from typing import List, Optional

from ..common.logging import get_logger
from ..common.models import TrendItem
from .base import BaseAIGenerator, TweetContent

logger = get_logger(__name__)


class MockAIGenerator(BaseAIGenerator):
    """Mock AI generator that returns predefined content."""

    def __init__(self) -> None:
        """Initialize mock AI generator."""
        self.mock_responses = {
            "reddit": {
                "turkish": "Reddit'te trend olan bu konu hakkında daha fazla bilgi edinin.",
                "english": "This trending topic on Reddit is worth following.",
                "hashtags": ["#Reddit", "#Trending", "#News"],
            },
            "google_trends": {
                "turkish": "Google'da trend olan bu konu dikkat çekiyor.",
                "english": "This topic is trending on Google and gaining attention.",
                "hashtags": ["#GoogleTrends", "#Trending", "#Search"],
            },
            "default": {
                "turkish": "Bu konu şu anda gündemde ve takip edilmeye değer.",
                "english": "This topic is currently trending and worth following.",
                "hashtags": ["#Trending", "#News", "#Update"],
            },
        }

    async def generate_tweet_content(self, trend_item: TrendItem) -> TweetContent:
        """
        Generate mock tweet content for a trend item.

        Args:
            trend_item: Trend item to generate content for

        Returns:
            Generated tweet content
        """
        logger.info("Generating mock tweet content", item_id=trend_item.external_id)

        # Get mock response based on source
        source_key = trend_item.source.value
        response = self.mock_responses.get(source_key, self.mock_responses["default"])

        # Customize based on content
        turkish_text = self._customize_turkish_text(response["turkish"], trend_item)
        english_text = self._customize_english_text(response["english"], trend_item)
        hashtags = self._customize_hashtags(response["hashtags"], trend_item)

        # Add media and quote tweet support
        media_path, media_type, media_url = self._generate_media_info(trend_item)
        quote_tweet_id, quote_tweet_url = self._generate_quote_tweet_info(trend_item)

        return TweetContent(
            turkish_text=turkish_text,
            english_text=english_text,
            hashtags=hashtags,
            media_path=media_path,
            media_type=media_type,
            media_url=media_url,
            quote_tweet_id=quote_tweet_id,
            quote_tweet_url=quote_tweet_url,
        )

    def _customize_turkish_text(self, base_text: str, trend_item: TrendItem) -> str:
        """
        Customize Turkish text based on trend item.

        Args:
            base_text: Base Turkish text
            trend_item: Trend item

        Returns:
            Customized Turkish text
        """
        # Add title reference if short enough
        if len(trend_item.title) < 100:
            return f"{trend_item.title}\n\n{base_text}"
        return base_text

    def _customize_english_text(self, base_text: str, trend_item: TrendItem) -> str:
        """
        Customize English text based on trend item.

        Args:
            base_text: Base English text
            trend_item: Trend item

        Returns:
            Customized English text
        """
        # Add title reference if short enough
        if len(trend_item.title) < 100:
            return f"{trend_item.title}\n\n{base_text}"
        return base_text

    def _customize_hashtags(self, base_hashtags: List[str], trend_item: TrendItem) -> List[str]:
        """
        Customize hashtags based on trend item.

        Args:
            base_hashtags: Base hashtags
            trend_item: Trend item

        Returns:
            Customized hashtags
        """
        hashtags = base_hashtags.copy()

        # Add Turkey-related hashtags
        if trend_item.is_turkey_related:
            hashtags.extend(["#Turkey", "#Türkiye"])

        # Add global hashtags
        if trend_item.is_global:
            hashtags.append("#Global")

        # Add source-specific hashtags
        if trend_item.source.value == "reddit":
            hashtags.append("#Reddit")
        elif trend_item.source.value == "google_trends":
            hashtags.append("#GoogleTrends")

        # Limit to 5 hashtags
        return hashtags[:5]

    def _generate_media_info(self, trend_item: TrendItem) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Generate media information for trend item.

        Args:
            trend_item: Trend item

        Returns:
            Tuple of (media_path, media_type, media_url)
        """
        # Mock media generation - in real implementation, this would:
        # 1. Download media from trend item URL
        # 2. Process/optimize media
        # 3. Return local path and metadata
        
        # For now, return None (no media)
        return None, None, None

    def _generate_quote_tweet_info(self, trend_item: TrendItem) -> tuple[Optional[str], Optional[str]]:
        """
        Generate quote tweet information for trend item.

        Args:
            trend_item: Trend item

        Returns:
            Tuple of (quote_tweet_id, quote_tweet_url)
        """
        # Mock quote tweet generation - in real implementation, this would:
        # 1. Find relevant tweets to quote
        # 2. Extract tweet ID and URL
        # 3. Return for quote tweet functionality
        
        # For now, return None (no quote tweet)
        return None, None
