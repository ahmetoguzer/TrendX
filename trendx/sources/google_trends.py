"""Google Trends source implementation."""

from datetime import datetime, timedelta
from typing import List

from pytrends.request import TrendReq

from ..common.config import settings
from ..common.logging import get_logger
from ..common.models import TrendItem, TrendSource
from .base import BaseTrendSource

logger = get_logger(__name__)


class GoogleTrendsSource(BaseTrendSource):
    """Google Trends source for trending topics."""

    def __init__(self) -> None:
        """Initialize Google Trends source."""
        super().__init__("google_trends")
        self.pytrends = None
        self._initialize_pytrends()

    def _initialize_pytrends(self) -> None:
        """Initialize pytrends client."""
        try:
            self.pytrends = TrendReq(
                hl="en-US",
                tz=360,  # UTC+6 (Turkey timezone)
                timeout=(10, 25),
                retries=2,
                backoff_factor=0.1,
            )
            logger.info("Google Trends API initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Google Trends API", error=str(e))
            self.pytrends = None

    async def fetch_trends(self, limit: int = 10) -> List[TrendItem]:
        """
        Fetch trending topics from Google Trends.

        Args:
            limit: Maximum number of items to fetch

        Returns:
            List of trend items
        """
        if not self.pytrends:
            return self._get_mock_data(limit)

        trends = []
        try:
            # Get trending searches
            trending_searches = self.pytrends.trending_searches(pn=settings.google_trends.geolocation)
            
            if trending_searches is not None and not trending_searches.empty:
                for idx, row in trending_searches.head(limit).iterrows():
                    topic = row[0] if len(row) > 0 else None
                    if topic:
                        trend_item = self._convert_trending_topic(topic)
                        if trend_item:
                            trends.append(trend_item)

        except Exception as e:
            logger.error("Failed to fetch Google Trends data", error=str(e))
            return self._get_mock_data(limit)

        return trends[:limit]

    def _convert_trending_topic(self, topic: str) -> TrendItem | None:
        """
        Convert Google Trends topic to TrendItem.

        Args:
            topic: Trending topic

        Returns:
            TrendItem or None if invalid
        """
        try:
            # Check if Turkey-related
            is_turkey_related = self._is_turkey_related(topic)

            return TrendItem(
                source=TrendSource.GOOGLE_TRENDS,
                external_id=f"google_trends_{hash(topic)}",
                title=f"Trending: {topic}",
                description=f"'{topic}' is currently trending on Google",
                url=f"https://trends.google.com/trends/explore?q={topic.replace(' ', '+')}",
                score=0.0,  # Will be calculated by aggregator
                social_volume=0,  # Google Trends doesn't provide volume
                is_turkey_related=is_turkey_related,
                is_global=not is_turkey_related,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error("Failed to convert Google Trends topic", topic=topic, error=str(e))
            return None

    def _is_turkey_related(self, topic: str) -> bool:
        """
        Check if topic is Turkey-related.

        Args:
            topic: Trending topic

        Returns:
            True if Turkey-related
        """
        turkey_keywords = [
            "turkey",
            "türkiye",
            "istanbul",
            "ankara",
            "izmir",
            "turkish",
            "türk",
            "erdogan",
            "akp",
            "chp",
            "türkiye",
        ]

        topic_lower = topic.lower()
        return any(keyword in topic_lower for keyword in turkey_keywords)

    def _get_mock_data(self, limit: int) -> List[TrendItem]:
        """
        Get mock data when Google Trends API is not available.

        Args:
            limit: Number of mock items to return

        Returns:
            List of mock trend items
        """
        mock_items = [
            TrendItem(
                source=TrendSource.GOOGLE_TRENDS,
                external_id="google_trends_mock_1",
                title="Trending: Artificial Intelligence",
                description="'Artificial Intelligence' is currently trending on Google",
                url="https://trends.google.com/trends/explore?q=artificial+intelligence",
                social_volume=0,
                is_turkey_related=False,
                is_global=True,
            ),
            TrendItem(
                source=TrendSource.GOOGLE_TRENDS,
                external_id="google_trends_mock_2",
                title="Trending: Turkey Economy",
                description="'Turkey Economy' is currently trending on Google",
                url="https://trends.google.com/trends/explore?q=turkey+economy",
                social_volume=0,
                is_turkey_related=True,
                is_global=False,
            ),
            TrendItem(
                source=TrendSource.GOOGLE_TRENDS,
                external_id="google_trends_mock_3",
                title="Trending: Climate Change",
                description="'Climate Change' is currently trending on Google",
                url="https://trends.google.com/trends/explore?q=climate+change",
                social_volume=0,
                is_turkey_related=False,
                is_global=True,
            ),
        ]

        return mock_items[:limit]

    def get_source_authority_score(self) -> float:
        """
        Get the authority score for Google Trends source.

        Returns:
            Authority score (0.9 for Google Trends)
        """
        return 0.9
