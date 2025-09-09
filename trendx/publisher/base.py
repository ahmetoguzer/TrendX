"""Base publisher interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ..ai.base import TweetContent


class PublishResult:
    """Result of a publish operation."""

    def __init__(
        self,
        success: bool,
        post_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Initialize publish result.

        Args:
            success: Whether the publish was successful
            post_id: ID of the published post
            error_message: Error message if failed
        """
        self.success = success
        self.post_id = post_id
        self.error_message = error_message


class BasePublisher(ABC):
    """Abstract base class for publishers."""

    @abstractmethod
    async def publish_tweet(self, content: TweetContent) -> PublishResult:
        """
        Publish a tweet.

        Args:
            content: Tweet content to publish

        Returns:
            Publish result
        """
        pass

    @abstractmethod
    async def publish_thread(self, contents: list[TweetContent]) -> list[PublishResult]:
        """
        Publish a thread of tweets.

        Args:
            contents: List of tweet contents to publish as thread

        Returns:
            List of publish results
        """
        pass
