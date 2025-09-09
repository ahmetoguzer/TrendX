"""Reddit trend source implementation."""

import re
from datetime import datetime, timedelta
from typing import List

import praw
from praw.models import Submission

from ..common.config import settings
from ..common.logging import get_logger
from ..common.models import TrendItem, TrendSource
from .base import BaseTrendSource

logger = get_logger(__name__)


class RedditTrendSource(BaseTrendSource):
    """Reddit trend source for r/worldnews and r/Turkey."""

    def __init__(self) -> None:
        """Initialize Reddit trend source."""
        super().__init__("reddit")
        self.reddit = None
        self._initialize_reddit()

    def _initialize_reddit(self) -> None:
        """Initialize Reddit API client."""
        if not settings.reddit.client_id or not settings.reddit.client_secret:
            logger.warning("Reddit credentials not configured, using mock data")
            return

        try:
            self.reddit = praw.Reddit(
                client_id=settings.reddit.client_id,
                client_secret=settings.reddit.client_secret,
                user_agent=settings.reddit.user_agent,
            )
            logger.info("Reddit API initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Reddit API", error=str(e))
            self.reddit = None

    async def fetch_trends(self, limit: int = 10) -> List[TrendItem]:
        """
        Fetch trending posts from Reddit.

        Args:
            limit: Maximum number of items to fetch

        Returns:
            List of trend items
        """
        if not self.reddit:
            logger.warning("Reddit credentials not configured, skipping Reddit trends")
            return []

        trends = []
        subreddits = ["worldnews", "Turkey"]

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                posts = subreddit.hot(limit=limit // len(subreddits))

                for post in posts:
                    if isinstance(post, Submission):
                        trend_item = self._convert_reddit_post(post, subreddit_name)
                        if trend_item:
                            trends.append(trend_item)

            except Exception as e:
                logger.error(
                    "Failed to fetch from subreddit",
                    subreddit=subreddit_name,
                    error=str(e),
                )

        return trends[:limit]

    def _convert_reddit_post(self, post: Submission, subreddit: str) -> TrendItem | None:
        """
        Convert Reddit post to TrendItem.

        Args:
            post: Reddit submission
            subreddit: Subreddit name

        Returns:
            TrendItem or None if invalid
        """
        try:
            # Skip if post is too old (more than 24 hours)
            post_age = datetime.utcnow() - datetime.fromtimestamp(post.created_utc)
            if post_age > timedelta(hours=24):
                return None

            # Check if Turkey-related
            is_turkey_related = self._is_turkey_related(post.title, post.selftext or "")

            return TrendItem(
                source=TrendSource.REDDIT,
                external_id=f"reddit_{post.id}",
                title=post.title,
                description=post.selftext[:500] if post.selftext else None,
                url=post.url,
                score=0.0,  # Will be calculated by aggregator
                social_volume=post.score,
                is_turkey_related=is_turkey_related,
                is_global=subreddit == "worldnews",
                created_at=datetime.fromtimestamp(post.created_utc),
            )

        except Exception as e:
            logger.error("Failed to convert Reddit post", post_id=post.id, error=str(e))
            return None

    def _is_turkey_related(self, title: str, content: str) -> bool:
        """
        Check if content is Turkey-related.

        Args:
            title: Post title
            content: Post content

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
        ]

        text = (title + " " + content).lower()
        return any(keyword in text for keyword in turkey_keywords)

    def _get_mock_data(self, limit: int) -> List[TrendItem]:
        """
        Get mock data when Reddit API is not available.

        Args:
            limit: Number of mock items to return

        Returns:
            List of mock trend items
        """
        mock_items = [
            TrendItem(
                source=TrendSource.REDDIT,
                external_id="reddit_mock_1",
                title="Breaking: Major development in global politics",
                description="A significant political development has occurred...",
                url="https://reddit.com/r/worldnews/mock1",
                social_volume=1250,
                is_turkey_related=False,
                is_global=True,
            ),
            TrendItem(
                source=TrendSource.REDDIT,
                external_id="reddit_mock_2",
                title="Turkey announces new economic policy",
                description="The Turkish government has announced...",
                url="https://reddit.com/r/Turkey/mock2",
                social_volume=850,
                is_turkey_related=True,
                is_global=False,
            ),
            TrendItem(
                source=TrendSource.REDDIT,
                external_id="reddit_mock_3",
                title="Technology breakthrough affects global markets",
                description="A new technological advancement...",
                url="https://reddit.com/r/worldnews/mock3",
                social_volume=2100,
                is_turkey_related=False,
                is_global=True,
            ),
        ]

        return mock_items[:limit]

    def get_source_authority_score(self) -> float:
        """
        Get the authority score for Reddit source.

        Returns:
            Authority score (0.8 for Reddit)
        """
        return 0.8
