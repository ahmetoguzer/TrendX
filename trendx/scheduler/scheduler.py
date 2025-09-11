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
from ..publisher.selenium_twitter_publisher import SeleniumTwitterPublisher
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
        # Initialize sources - Selenium ile gerçek içerik bulma
        from ..sources.selenium_trends import SeleniumTrendsSource
        sources = {
            "selenium_trends": SeleniumTrendsSource(),  # Selenium ile gerçek içerik
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

        # Initialize publisher - UIAutomator2 kullan (Android app automation)
        from ..publisher.mock_publisher import MockPublisher
        try:
            from ..publisher.uiautomator_twitter_publisher import UIAutomatorTwitterPublisher
            self.publisher = UIAutomatorTwitterPublisher()
            logger.info("UIAutomator2 Twitter publisher initialized - Android app automation")
        except Exception as e:
            logger.warning(f"Failed to initialize UIAutomator2 publisher: {e}")
            try:
                self.publisher = SeleniumTwitterPublisher()
                logger.info("Selenium Twitter publisher initialized - fallback to web automation")
            except Exception as e2:
                logger.warning(f"Failed to initialize Selenium publisher: {e2}")
                self.publisher = MockPublisher()
                logger.info("Mock publisher initialized - final fallback")

        logger.info("Scheduler components initialized")

    def start(self) -> None:
        """Start the scheduler - bugün akşam 7'den başlat."""
        from datetime import datetime, timedelta
        
        # Bugün akşam 19:00'dan başlat
        today_7pm = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
        
        # Eğer akşam 7 geçtiyse, yarın akşam 7'den başlat
        if today_7pm <= datetime.now():
            today_7pm += timedelta(days=1)
        
        # Add job for hourly trend posting (akşam 7'den saat başı 1 tweet)
        self.scheduler.add_job(
            self._collect_and_post_trends,
            trigger=IntervalTrigger(hours=1, start_date=today_7pm),  # Akşam 7'den saat başı
            id="hourly_trend_posting",
            name="Hourly Trend Posting",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(f"Scheduler started - Akşam 7'den ({today_7pm.strftime('%Y-%m-%d %H:%M')}) saat başı 1 tweet atılacak")

    def stop(self) -> None:
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    async def _collect_and_post_trends(self) -> None:
        """Collect trends and post immediately (saat başı 1 tweet)."""
        try:
            logger.info("🚀 Saat başı trend posting başlıyor...")

            # Check if we're in quiet hours
            if self._is_quiet_hours():
                logger.info("⏰ Quiet hours - tweet atılmıyor")
                return

            # Collect trends (sadece 1 tane)
            trends = await self.aggregator.aggregate_trends(limit=1)
            logger.info(f"📊 {len(trends)} trend bulundu")

            if not trends:
                logger.warning("❌ Yeni içerik yok - tweet atılmıyor")
                return

            # İlk trendi al ve hemen tweet at
            trend = trends[0]
            logger.info(f"🎯 Seçilen trend: {trend.title}")

            # Generate tweet content
            tweet_content = await self.ai_generator.generate_tweet_content(trend)
            logger.info("🤖 AI tweet içeriği oluşturuldu")

            # Hemen tweet at
            result = await self.publisher.publish_tweet(tweet_content)
            
            if result.success:
                logger.info(f"✅ Tweet başarıyla atıldı! ID: {result.post_id}")
                
                # Database'e kaydet
                await self._save_tweet_to_db(trend, tweet_content, result.post_id)
            else:
                logger.error(f"❌ Tweet atılamadı: {result.error_message}")

        except Exception as e:
            logger.error(f"❌ Saat başı tweet hatası: {e}")

    async def _save_tweet_to_db(self, trend_item: TrendItem, tweet_content, post_id: str) -> None:
        """Tweet'i database'e kaydet."""
        try:
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
                    media_type=tweet_content.media_type,
                    media_url=tweet_content.media_url,
                    quote_tweet_id=tweet_content.quote_tweet_id,
                    quote_tweet_url=tweet_content.quote_tweet_url,
                )
                session.add(db_tweet_content)
                session.commit()
                
                logger.info(f"💾 Tweet database'e kaydedildi: {post_id}")
                
        except Exception as e:
            logger.error(f"❌ Database kaydetme hatası: {e}")

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

        # Gece 23:00 - Sabah 07:00 arası tweet atma
        start_hour = 23  # 23:00
        end_hour = 7     # 07:00

        # Overnight quiet hours (23:00 to 07:00)
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
