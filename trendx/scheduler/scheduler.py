"""Scheduler for automated trend posting."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..aggregator import TrendAggregator
from ..ai import MockAIGenerator
from ..common.config import settings
from ..common.database import get_session
from ..common.logging import get_logger
from ..common.models import PostQueue, TrendItem, TweetContent
from ..publisher import MockPublisher
from ..sources import RedditTrendSource, GoogleTrendsSource, TwitterTrendsSource

logger = get_logger(__name__)


class TrendScheduler:
    """Scheduler for automated trend collection and posting."""

    def __init__(self) -> None:
        """Initialize trend scheduler."""
        self.scheduler = AsyncIOScheduler(timezone=settings.scheduler.timezone)
        self.aggregator = None
        self.ai_generator = None
        self.publisher = None
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize scheduler components."""
        # Initialize sources
        sources = {
            "reddit": RedditTrendSource(),
            "google_trends": GoogleTrendsSource(),
            "twitter_trends": TwitterTrendsSource(),
        }

        # Initialize aggregator
        self.aggregator = TrendAggregator(sources)

        # Initialize AI generator (OpenAI if configured, otherwise mock)
        from ..ai.openai_generator import OpenAIGenerator
        if settings.ai.api_key and settings.ai.api_key != "your_openai_api_key_here":
            self.ai_generator = OpenAIGenerator()
            logger.info("OpenAI AI generator initialized")
        else:
            self.ai_generator = MockAIGenerator()
            logger.info("Mock AI generator initialized (OpenAI API key not configured)")

        # Initialize publisher (mock for now)
        self.publisher = MockPublisher()

        logger.info("Scheduler components initialized")

    def start(self) -> None:
        """Start the scheduler."""
        # Add job for trend collection and posting
        self.scheduler.add_job(
            self._collect_and_post_trends,
            trigger=IntervalTrigger(minutes=settings.scheduler.posting_interval_minutes),
            id="collect_and_post_trends",
            name="Collect and Post Trends",
            replace_existing=True,
        )

        # Add job for queue processing
        self.scheduler.add_job(
            self._process_post_queue,
            trigger=IntervalTrigger(minutes=5),
            id="process_post_queue",
            name="Process Post Queue",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    async def _collect_and_post_trends(self) -> None:
        """Collect trends and add to post queue."""
        try:
            logger.info("Starting trend collection")

            # Check if we're in quiet hours
            if self._is_quiet_hours():
                logger.info("Skipping trend collection during quiet hours")
                return

            # Collect trends
            trends = await self.aggregator.aggregate_trends(limit=5)
            logger.info("Collected trends", count=len(trends))

            # Generate content and add to queue
            for trend in trends:
                await self._process_trend_item(trend)

        except Exception as e:
            logger.error("Error in trend collection", error=str(e))

    async def _process_trend_item(self, trend_item: TrendItem) -> None:
        """
        Process a single trend item.

        Args:
            trend_item: Trend item to process
        """
        try:
            # Generate tweet content
            tweet_content = await self.ai_generator.generate_tweet_content(trend_item)

            # Save to database
            with get_session() as session:
                # Save trend item
                session.add(trend_item)
                session.commit()
                session.refresh(trend_item)

                # Save tweet content
                db_tweet_content = TweetContent(
                    trend_item_id=trend_item.id,
                    turkish_text=tweet_content.turkish_text,
                    english_text=tweet_content.english_text,
                    hashtags=tweet_content.hashtags,
                    media_path=tweet_content.media_path,
                )
                session.add(db_tweet_content)
                session.commit()
                session.refresh(db_tweet_content)

                # Add to post queue
                scheduled_time = self._calculate_next_post_time()
                post_queue_item = PostQueue(
                    tweet_content_id=db_tweet_content.id,
                    scheduled_at=scheduled_time,
                )
                session.add(post_queue_item)
                session.commit()

            logger.info(
                "Trend item processed and queued",
                trend_id=trend_item.id,
                scheduled_at=scheduled_time,
            )

        except Exception as e:
            logger.error("Error processing trend item", error=str(e))

    async def _process_post_queue(self) -> None:
        """Process items in the post queue."""
        try:
            with get_session() as session:
                # Get items ready to post
                now = datetime.utcnow()
                ready_items = session.query(PostQueue).filter(
                    PostQueue.scheduled_at <= now,
                    PostQueue.status == "pending",
                ).limit(settings.rate_limit.posts_per_hour).all()

                if not ready_items:
                    return

                logger.info("Processing post queue", count=len(ready_items))

                for queue_item in ready_items:
                    await self._post_queue_item(queue_item)

        except Exception as e:
            logger.error("Error processing post queue", error=str(e))

    async def _post_queue_item(self, queue_item: PostQueue) -> None:
        """
        Post a single queue item.

        Args:
            queue_item: Queue item to post
        """
        try:
            with get_session() as session:
                # Get tweet content
                tweet_content = session.query(TweetContent).filter(
                    TweetContent.id == queue_item.tweet_content_id
                ).first()

                if not tweet_content:
                    logger.error("Tweet content not found", queue_id=queue_item.id)
                    return

                # Create content object
                from ..ai.base import TweetContent as AITweetContent
                content = AITweetContent(
                    turkish_text=tweet_content.turkish_text,
                    english_text=tweet_content.english_text,
                    hashtags=tweet_content.hashtags,
                    media_path=tweet_content.media_path,
                )

                # Publish tweet
                result = await self.publisher.publish_tweet(content)

                # Update queue item
                if result.success:
                    queue_item.status = "posted"
                    queue_item.posted_at = datetime.utcnow()
                    queue_item.twitter_post_id = result.post_id
                else:
                    queue_item.status = "failed"
                    queue_item.error_message = result.error_message

                session.commit()

                logger.info(
                    "Queue item processed",
                    queue_id=queue_item.id,
                    success=result.success,
                    post_id=result.post_id,
                )

        except Exception as e:
            logger.error("Error posting queue item", error=str(e))

    def _is_quiet_hours(self) -> bool:
        """
        Check if current time is within quiet hours.

        Returns:
            True if in quiet hours
        """
        now = datetime.now()
        current_hour = now.hour

        start_hour = settings.scheduler.quiet_hours_start
        end_hour = settings.scheduler.quiet_hours_end

        if start_hour <= end_hour:
            # Same day quiet hours (e.g., 23:00 to 07:00)
            return start_hour <= current_hour < end_hour
        else:
            # Overnight quiet hours (e.g., 23:00 to 07:00)
            return current_hour >= start_hour or current_hour < end_hour

    def _calculate_next_post_time(self) -> datetime:
        """
        Calculate the next available post time.

        Returns:
            Next post time
        """
        now = datetime.utcnow()

        # Check if we're in quiet hours
        if self._is_quiet_hours():
            # Schedule for after quiet hours
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(
                hour=settings.scheduler.quiet_hours_end,
                minute=0,
                second=0,
                microsecond=0,
            )

        # Schedule for next interval
        return now + timedelta(minutes=settings.scheduler.posting_interval_minutes)
