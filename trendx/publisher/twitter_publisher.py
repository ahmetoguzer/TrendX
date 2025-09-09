"""Twitter/X publisher implementation using tweepy."""

import asyncio
import os
from typing import List, Optional

import tweepy

from ..ai.base import TweetContent
from ..common.config import settings
from ..common.logging import get_logger
from .base import BasePublisher, PublishResult

logger = get_logger(__name__)


class TwitterPublisher(BasePublisher):
    """Twitter/X publisher using tweepy."""

    def __init__(self) -> None:
        """Initialize Twitter publisher."""
        self.client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Twitter API client."""
        if not all([
            settings.twitter.api_key,
            settings.twitter.api_secret,
            settings.twitter.access_token,
            settings.twitter.access_token_secret,
        ]):
            logger.warning("Twitter credentials not configured, using mock publisher")
            return

        try:
            # Initialize tweepy client
            self.client = tweepy.Client(
                bearer_token=settings.twitter.bearer_token,
                consumer_key=settings.twitter.api_key,
                consumer_secret=settings.twitter.api_secret,
                access_token=settings.twitter.access_token,
                access_token_secret=settings.twitter.access_token_secret,
                wait_on_rate_limit=False,  # Manuel rate limit handling
            )

            # Verify credentials
            user = self.client.get_me()
            logger.info("Twitter API initialized successfully", username=user.data.username)

        except Exception as e:
            logger.error("Failed to initialize Twitter API", error=str(e))
            self.client = None

    async def publish_tweet(self, content: TweetContent) -> PublishResult:
        """
        Publish a tweet to Twitter.

        Args:
            content: Tweet content to publish

        Returns:
            Publish result
        """
        if not self.client:
            logger.warning("Twitter client not available, using mock publisher")
            from .mock_publisher import MockPublisher
            mock_publisher = MockPublisher()
            return await mock_publisher.publish_tweet(content)

        try:
            logger.info("Publishing tweet to Twitter", content_preview=content.turkish_text[:50])

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._publish_tweet_sync,
                content
            )

            logger.info("Tweet published successfully", post_id=response.data["id"])

            return PublishResult(
                success=True,
                post_id=str(response.data["id"]),
            )

        except tweepy.TooManyRequests as e:
            logger.warning("Twitter rate limit exceeded, waiting 15 minutes before retry", error=str(e))
            # Rate limit exceeded, wait 15 minutes and retry once
            await asyncio.sleep(900)  # Wait 15 minutes (900 seconds)
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    self._publish_tweet_sync,
                    content
                )
                logger.info("Tweet published successfully after rate limit retry", post_id=response.data["id"])
                return PublishResult(
                    success=True,
                    post_id=str(response.data["id"]),
                )
            except Exception as retry_e:
                logger.error("Failed to publish tweet after rate limit retry", error=str(retry_e))
                return PublishResult(
                    success=False,
                    error_message=f"Rate limit retry failed: {str(retry_e)}",
                )
        except Exception as e:
            logger.error("Failed to publish tweet", error=str(e))
            return PublishResult(
                success=False,
                error_message=str(e),
            )

    def _publish_tweet_sync(self, content: TweetContent) -> tweepy.Response:
        """
        Synchronous tweet publishing with media and quote tweet support.

        Args:
            content: Tweet content

        Returns:
            Twitter API response
        """
        # Choose text based on content (could be configurable)
        tweet_text = content.turkish_text
        
        # Add hashtags if they fit
        if content.hashtags:
            hashtag_text = " ".join(content.hashtags)
            if len(tweet_text + " " + hashtag_text) <= 280:
                tweet_text += " " + hashtag_text

        # Prepare tweet parameters
        tweet_params = {"text": tweet_text}

        # Add media if available
        media_ids = self._upload_media(content)
        if media_ids:
            tweet_params["media_ids"] = media_ids

        # Add quote tweet if available
        if content.quote_tweet_id:
            tweet_params["quote_tweet_id"] = content.quote_tweet_id

        return self.client.create_tweet(**tweet_params)

    def _upload_media(self, content: TweetContent) -> List[str]:
        """
        Upload media files to Twitter.

        Args:
            content: Tweet content with media information

        Returns:
            List of media IDs
        """
        media_ids = []

        # Check if we have media URL (not file path)
        if not content.media_url:
            return media_ids

        try:
            # Download media from URL first
            import requests
            import tempfile
            
            # Download media file
            response = requests.get(content.media_url, timeout=30)
            response.raise_for_status()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg' if content.media_type == 'image' else '.mp4') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            # Initialize media API (v1.1 for media upload)
            auth = tweepy.OAuthHandler(
                settings.twitter.api_key,
                settings.twitter.api_secret
            )
            auth.set_access_token(
                settings.twitter.access_token,
                settings.twitter.access_token_secret
            )
            media_api = tweepy.API(auth)

            # Upload media based on type
            if content.media_type == "video":
                # Video upload (chunked)
                media_id = self._upload_video(media_api, temp_file_path)
            else:
                # Image upload
                media = media_api.media_upload(temp_file_path)
                media_id = media.media_id

            if media_id:
                media_ids.append(str(media_id))
                logger.info("Media uploaded successfully", media_id=media_id, media_type=content.media_type, media_url=content.media_url)

            # Clean up temporary file
            os.unlink(temp_file_path)

        except Exception as e:
            logger.error("Failed to upload media", error=str(e), media_url=content.media_url)
            # Clean up temporary file if it exists
            try:
                if 'temp_file_path' in locals():
                    os.unlink(temp_file_path)
            except:
                pass

        return media_ids

    def _upload_video(self, media_api: tweepy.API, video_path: str) -> Optional[str]:
        """
        Upload video file to Twitter (chunked upload).

        Args:
            media_api: Tweepy media API instance
            video_path: Path to video file

        Returns:
            Media ID if successful, None otherwise
        """
        try:
            # Get file size
            file_size = os.path.getsize(video_path)
            
            # Initialize upload
            media = media_api.media_upload(
                video_path,
                media_category="tweet_video",
                chunked=True
            )

            # Process chunks
            media_id = media.media_id
            segment_index = 0

            with open(video_path, 'rb') as video_file:
                while True:
                    chunk = video_file.read(5 * 1024 * 1024)  # 5MB chunks
                    if not chunk:
                        break

                    media_api.media_upload_append(
                        media_id=media_id,
                        segment_index=segment_index,
                        media=chunk
                    )
                    segment_index += 1

            # Finalize upload
            media_api.media_upload_finalize(media_id=media_id)

            # Wait for processing
            import time
            while True:
                status = media_api.media_upload_status(media_id=media_id)
                if status.processing_info['state'] == 'succeeded':
                    break
                elif status.processing_info['state'] == 'failed':
                    logger.error("Video processing failed", media_id=media_id)
                    return None
                
                time.sleep(1)

            return str(media_id)

        except Exception as e:
            logger.error("Failed to upload video", error=str(e), video_path=video_path)
            return None

    async def publish_thread(self, contents: List[TweetContent]) -> List[PublishResult]:
        """
        Publish a thread of tweets to Twitter.

        Args:
            contents: List of tweet contents to publish as thread

        Returns:
            List of publish results
        """
        if not self.client:
            logger.warning("Twitter client not available, using mock publisher")
            from .mock_publisher import MockPublisher
            mock_publisher = MockPublisher()
            return await mock_publisher.publish_thread(contents)

        logger.info("Publishing thread to Twitter", tweet_count=len(contents))

        results = []
        previous_tweet_id = None

        try:
            for i, content in enumerate(contents):
                logger.info("Publishing thread tweet", tweet_index=i + 1)

                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    self._publish_thread_tweet_sync,
                    content,
                    previous_tweet_id,
                    i + 1,
                    len(contents)
                )

                tweet_id = response.data["id"]
                previous_tweet_id = tweet_id

                results.append(PublishResult(
                    success=True,
                    post_id=str(tweet_id),
                ))

                logger.info("Thread tweet published", post_id=tweet_id, tweet_index=i + 1)

                # Add delay between tweets to avoid rate limiting
                if i < len(contents) - 1:
                    await asyncio.sleep(2)

        except Exception as e:
            logger.error("Failed to publish thread", error=str(e))
            # Add failed result for remaining tweets
            while len(results) < len(contents):
                results.append(PublishResult(
                    success=False,
                    error_message=str(e),
                ))

        return results

    def _publish_thread_tweet_sync(
        self,
        content: TweetContent,
        previous_tweet_id: str | None,
        tweet_index: int,
        total_tweets: int,
    ) -> tweepy.Response:
        """
        Synchronous thread tweet publishing.

        Args:
            content: Tweet content
            previous_tweet_id: ID of previous tweet in thread
            tweet_index: Index of current tweet (1-based)
            total_tweets: Total number of tweets in thread

        Returns:
            Twitter API response
        """
        # Choose text based on content
        tweet_text = content.turkish_text

        # Add thread indicators
        if total_tweets > 1:
            tweet_text = f"{tweet_index}/{total_tweets} {tweet_text}"

        # Add hashtags if they fit
        if content.hashtags:
            hashtag_text = " ".join(content.hashtags)
            if len(tweet_text + " " + hashtag_text) <= 280:
                tweet_text += " " + hashtag_text

        # Create tweet with reply to previous tweet if it exists
        if previous_tweet_id:
            return self.client.create_tweet(
                text=tweet_text,
                in_reply_to_tweet_id=previous_tweet_id,
            )
        else:
            return self.client.create_tweet(text=tweet_text)
