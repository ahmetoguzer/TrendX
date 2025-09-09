"""Mock publisher for testing and development."""

import asyncio
from typing import List

from ..ai.base import TweetContent
from ..common.logging import get_logger
from .base import BasePublisher, PublishResult

logger = get_logger(__name__)


class MockPublisher(BasePublisher):
    """Mock publisher that simulates publishing without actually posting."""

    def __init__(self) -> None:
        """Initialize mock publisher."""
        self.published_tweets = []
        self.published_threads = []

    async def publish_tweet(self, content: TweetContent) -> PublishResult:
        """
        Mock publish a tweet.

        Args:
            content: Tweet content to publish

        Returns:
            Mock publish result
        """
        logger.info("Mock publishing tweet", content_preview=content.turkish_text[:50])

        # Simulate API delay
        await asyncio.sleep(0.1)

        # Generate mock post ID
        post_id = f"mock_tweet_{len(self.published_tweets) + 1}"

        # Store published tweet
        self.published_tweets.append({
            "post_id": post_id,
            "content": content,
            "timestamp": asyncio.get_event_loop().time(),
        })

        logger.info("Mock tweet published", post_id=post_id)

        return PublishResult(
            success=True,
            post_id=post_id,
        )

    async def publish_thread(self, contents: List[TweetContent]) -> List[PublishResult]:
        """
        Mock publish a thread of tweets.

        Args:
            contents: List of tweet contents to publish as thread

        Returns:
            List of mock publish results
        """
        logger.info("Mock publishing thread", tweet_count=len(contents))

        results = []
        thread_id = f"mock_thread_{len(self.published_threads) + 1}"

        for i, content in enumerate(contents):
            # Simulate API delay
            await asyncio.sleep(0.1)

            post_id = f"{thread_id}_{i + 1}"
            
            results.append(PublishResult(
                success=True,
                post_id=post_id,
            ))

            logger.info("Mock thread tweet published", post_id=post_id, tweet_index=i + 1)

        # Store published thread
        self.published_threads.append({
            "thread_id": thread_id,
            "contents": contents,
            "results": results,
            "timestamp": asyncio.get_event_loop().time(),
        })

        logger.info("Mock thread published", thread_id=thread_id, tweet_count=len(contents))

        return results

    def get_published_tweets(self) -> List[dict]:
        """
        Get list of published tweets.

        Returns:
            List of published tweet data
        """
        return self.published_tweets.copy()

    def get_published_threads(self) -> List[dict]:
        """
        Get list of published threads.

        Returns:
            List of published thread data
        """
        return self.published_threads.copy()

    def clear_history(self) -> None:
        """Clear publishing history."""
        self.published_tweets.clear()
        self.published_threads.clear()
        logger.info("Mock publisher history cleared")
