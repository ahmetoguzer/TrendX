"""
Ultra basit trends source - hiç API yok, rate limit yok!
"""

from typing import List
from datetime import datetime
from ..common.models import TrendItem, TrendSource
from ..common.logging import get_logger
from .base import BaseTrendSource

logger = get_logger(__name__)


class SimpleTrendsFixed(BaseTrendSource):
    """
    Ultra basit trends source - hiç API yok, rate limit yok!
    Sadece hardcoded trends, her zaman çalışır.
    """

    def __init__(self):
        """Initialize the simple trends source."""
        super().__init__("simple_trends_fixed")
        self.trends_data = [
            {
                "title": "AI Revolution",
                "description": "Artificial Intelligence is transforming the world",
                "hashtag": "AI",
                "social_volume": 50000,
                "is_turkey_related": False,
                "is_global": True,
            },
            {
                "title": "Turkey News",
                "description": "Latest news and events from Turkey",
                "hashtag": "Turkey",
                "social_volume": 30000,
                "is_turkey_related": True,
                "is_global": False,
            },
            {
                "title": "Climate Action",
                "description": "Global climate change awareness and action",
                "hashtag": "Climate",
                "social_volume": 40000,
                "is_turkey_related": False,
                "is_global": True,
            },
            {
                "title": "Tech Innovation",
                "description": "Latest technology innovations and startups",
                "hashtag": "Tech",
                "social_volume": 35000,
                "is_turkey_related": False,
                "is_global": True,
            },
            {
                "title": "Istanbul",
                "description": "News and events from Istanbul, Turkey",
                "hashtag": "Istanbul",
                "social_volume": 20000,
                "is_turkey_related": True,
                "is_global": False,
            },
            {
                "title": "Cryptocurrency",
                "description": "Digital currency trends and blockchain technology",
                "hashtag": "Crypto",
                "social_volume": 45000,
                "is_turkey_related": False,
                "is_global": True,
            },
            {
                "title": "Turkish Culture",
                "description": "Turkish traditions, food, and cultural events",
                "hashtag": "TurkishCulture",
                "social_volume": 15000,
                "is_turkey_related": True,
                "is_global": False,
            },
            {
                "title": "Space Exploration",
                "description": "Space missions, astronomy, and cosmic discoveries",
                "hashtag": "Space",
                "social_volume": 30000,
                "is_turkey_related": False,
                "is_global": True,
            },
        ]

    async def fetch_trends(self, limit: int = 10) -> List[TrendItem]:
        """
        Fetch trending topics - hiç API yok, rate limit yok!

        Args:
            limit: Maximum number of items to fetch

        Returns:
            List of trend items
        """
        trends = []
        
        # Her seferinde farklı trends döndür
        import random
        selected_trends = random.sample(self.trends_data, min(limit, len(self.trends_data)))
        
        for i, trend_data in enumerate(selected_trends):
            trend_item = TrendItem(
                source=TrendSource.TWITTER_TRENDS,
                external_id=f"simple_fixed_{i}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                title=trend_data["title"],
                description=trend_data["description"],
                url=f"https://twitter.com/search?q=%23{trend_data['hashtag']}",
                score=0.0,
                social_volume=trend_data["social_volume"],
                is_turkey_related=trend_data["is_turkey_related"],
                is_global=trend_data["is_global"],
                created_at=datetime.utcnow(),
            )
            trends.append(trend_item)

        logger.info("Fetched simple fixed trends", count=len(trends))
        return trends

    def get_source_authority_score(self) -> float:
        """Get authority score."""
        return 0.8
