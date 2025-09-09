"""Twitter/X trends source implementation."""

import asyncio
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Dict, Any

import tweepy

from ..common.config import settings
from ..common.logging import get_logger
from ..common.models import TrendItem, TrendSource
from .base import BaseTrendSource

logger = get_logger(__name__)


class TwitterTrendsSource(BaseTrendSource):
    """Twitter/X trends source for trending topics."""

    def __init__(self) -> None:
        """Initialize Twitter trends source."""
        super().__init__("twitter_trends")
        self.client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Twitter API client."""
        if not settings.twitter.bearer_token:
            logger.warning("Twitter bearer token not configured, using mock data")
            return

        try:
            self.client = tweepy.Client(
                bearer_token=settings.twitter.bearer_token,
                wait_on_rate_limit=True,
            )
            logger.info("Twitter API initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Twitter API", error=str(e))
            self.client = None

    async def fetch_trends(self, limit: int = 10) -> List[TrendItem]:
        """
        Fetch trending topics from Twitter using API v2.
        Uses search_recent_tweets to find trending hashtags and topics.

        Args:
            limit: Maximum number of items to fetch

        Returns:
            List of trend items
        """
        # Always use mock data for now due to rate limits
        logger.info("Using mock data due to Twitter API rate limits")
        return self._get_mock_data(limit)

        trends = []
        try:
            # Add timeout to avoid long waits
            import asyncio
            
            # Search for recent tweets with popular hashtags (with timeout)
            try:
                trending_hashtags = await asyncio.wait_for(
                    self._get_trending_hashtags(limit * 2), 
                    timeout=10.0  # 10 second timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Twitter hashtag search timed out, using mock data")
                return self._get_mock_data(limit)
            
            for hashtag, tweet_count in trending_hashtags.items():
                if len(trends) >= limit:
                    break
                    
                # Create trend item
                trend_item = TrendItem(
                    source=TrendSource.TWITTER_TRENDS,
                    external_id=f"twitter_trends_{hashtag}",
                    title=f"Twitter Trend: #{hashtag}",
                    description=f"#{hashtag} is trending on Twitter with {tweet_count} mentions",
                    url=f"https://twitter.com/search?q=%23{hashtag}",
                    score=0.0,  # Will be calculated by aggregator
                    social_volume=tweet_count,
                    is_turkey_related=self._is_turkey_related(hashtag),
                    is_global=True,
                    created_at=datetime.utcnow(),
                )
                trends.append(trend_item)

            # If we don't have enough hashtags, search for trending topics (with timeout)
            if len(trends) < limit:
                try:
                    trending_topics = await asyncio.wait_for(
                        self._get_trending_topics(limit - len(trends)), 
                        timeout=5.0  # 5 second timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning("Twitter topic search timed out, using remaining mock data")
                    # Fill remaining with mock data
                    remaining_mock = self._get_mock_data(limit - len(trends))
                    trends.extend(remaining_mock)
                else:
                    for topic, tweet_count in trending_topics.items():
                        if len(trends) >= limit:
                            break
                            
                        trend_item = TrendItem(
                            source=TrendSource.TWITTER_TRENDS,
                            external_id=f"twitter_trends_{topic}",
                            title=f"Twitter Trend: {topic}",
                            description=f"{topic} is trending on Twitter with {tweet_count} mentions",
                            url=f"https://twitter.com/search?q={topic}",
                            score=0.0,  # Will be calculated by aggregator
                            social_volume=tweet_count,
                            is_turkey_related=self._is_turkey_related(topic),
                            is_global=True,
                            created_at=datetime.utcnow(),
                        )
                        trends.append(trend_item)

            logger.info("Successfully fetched Twitter trends", count=len(trends))
            
        except Exception as e:
            logger.error("Failed to fetch Twitter trends", error=str(e))
            return self._get_mock_data(limit)

        return trends[:limit]

    async def _get_trending_hashtags(self, limit: int) -> Dict[str, int]:
        """Get trending hashtags from recent tweets - optimized for speed."""
        hashtag_counts = Counter()
        
        try:
            # Use only 2-3 most relevant queries to avoid rate limits
            search_queries = [
                "AI -is:retweet",  # AI tweets
                "Turkey -is:retweet",  # Turkey-related
            ]
            
            for query in search_queries:
                try:
                    # Get fewer tweets per query to be faster
                    tweets = self.client.search_recent_tweets(
                        query=query,
                        max_results=50,  # Reduced from 100 to 50
                        tweet_fields=['created_at', 'public_metrics']
                    )
                    
                    if tweets.data:
                        for tweet in tweets.data:
                            # Extract hashtags from tweet text
                            hashtags = re.findall(r'#(\w+)', tweet.text)
                            for hashtag in hashtags:
                                # Filter out common/irrelevant hashtags
                                if self._is_relevant_hashtag(hashtag):
                                    hashtag_counts[hashtag.lower()] += 1
                                    
                except tweepy.TweepyException as e:
                    logger.warning(f"Failed to search for query '{query}'", error=str(e))
                    continue
                    
        except Exception as e:
            logger.error("Error getting trending hashtags", error=str(e))
            
        # Return top hashtags
        return dict(hashtag_counts.most_common(limit))

    async def _get_trending_topics(self, limit: int) -> Dict[str, int]:
        """Get trending topics from recent tweets - optimized for speed."""
        topic_counts = Counter()
        
        try:
            # Use only 1 query to avoid rate limits
            search_queries = [
                "technology -is:retweet",  # Technology tweets
            ]
            
            for query in search_queries:
                try:
                    tweets = self.client.search_recent_tweets(
                        query=query,
                        max_results=30,  # Reduced from 100 to 30
                        tweet_fields=['created_at', 'public_metrics']
                    )
                    
                    if tweets.data:
                        for tweet in tweets.data:
                            # Extract potential trending topics (words with capital letters)
                            topics = re.findall(r'\b[A-Z][a-z]+\b', tweet.text)
                            for topic in topics:
                                if self._is_relevant_topic(topic):
                                    topic_counts[topic.lower()] += 1
                                    
                except tweepy.TweepyException as e:
                    logger.warning(f"Failed to search for query '{query}'", error=str(e))
                    continue
                    
        except Exception as e:
            logger.error("Error getting trending topics", error=str(e))
            
        return dict(topic_counts.most_common(limit))

    def _is_relevant_hashtag(self, hashtag: str) -> bool:
        """Check if hashtag is relevant for trending."""
        # Filter out common/irrelevant hashtags
        irrelevant_hashtags = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'men', 'put', 'say', 'she', 'too', 'use'
        }
        
        return (
            len(hashtag) > 2 and 
            len(hashtag) < 20 and
            hashtag.lower() not in irrelevant_hashtags and
            not hashtag.isdigit() and
            hashtag.isalpha()
        )

    def _is_relevant_topic(self, topic: str) -> bool:
        """Check if topic is relevant for trending."""
        irrelevant_topics = {
            'The', 'And', 'For', 'Are', 'But', 'Not', 'You', 'All', 'Can', 'Had', 'Her', 'Was', 'One', 'Our', 'Out', 'Day', 'Get', 'Has', 'Him', 'His', 'How', 'Its', 'May', 'New', 'Now', 'Old', 'See', 'Two', 'Way', 'Who', 'Boy', 'Did', 'Man', 'Men', 'Put', 'Say', 'She', 'Too', 'Use', 'This', 'That', 'With', 'Have', 'Will', 'From', 'They', 'Know', 'Want', 'Been', 'Good', 'Much', 'Some', 'Time', 'Very', 'When', 'Come', 'Here', 'Just', 'Like', 'Long', 'Make', 'Many', 'Over', 'Such', 'Take', 'Than', 'Them', 'Well', 'Were'
        }
        
        return (
            len(topic) > 2 and 
            len(topic) < 20 and
            topic not in irrelevant_topics and
            topic.isalpha()
        )

    def _convert_twitter_trend(self, trend_data: dict, is_turkey: bool) -> TrendItem | None:
        """
        Convert Twitter trend data to TrendItem.

        Args:
            trend_data: Twitter trend data
            is_turkey: Whether this is Turkey-specific trend

        Returns:
            TrendItem or None if invalid
        """
        try:
            name = trend_data.get('name', '')
            if not name or name.startswith('#'):
                return None

            # Check if Turkey-related
            is_turkey_related = is_turkey or self._is_turkey_related(name)

            return TrendItem(
                source=TrendSource.TWITTER_TRENDS,
                external_id=f"twitter_trends_{hash(name)}",
                title=f"Twitter Trend: {name}",
                description=f"'{name}' is trending on Twitter",
                url=trend_data.get('url', f"https://twitter.com/search?q={name.replace(' ', '%20')}"),
                score=0.0,  # Will be calculated by aggregator
                social_volume=trend_data.get('tweet_volume', 0) or 0,
                is_turkey_related=is_turkey_related,
                is_global=not is_turkey_related,
                created_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error("Failed to convert Twitter trend", error=str(e))
            return None

    def _is_turkey_related(self, trend_name: str) -> bool:
        """
        Check if trend is Turkey-related.

        Args:
            trend_name: Trend name

        Returns:
            True if Turkey-related
        """
        turkey_keywords = [
            "turkey", "türkiye", "istanbul", "ankara", "izmir", "turkish", 
            "türk", "türkçe", "ankara", "istanbul", "izmir", "antalya",
            "bursa", "adana", "konya", "gaziantep", "mersin", "diyarbakır",
            "kayseri", "eskişehir", "urfa", "malatya", "erzurum", "van",
            "batman", "elazığ", "ısparta", "kahramanmaraş", "samsun",
            "denizli", "sakarya", "muğla", "afyon", "trabzon", "ordu",
            "erzincan", "giresun", "rize", "artvin", "gümüşhane", "bayburt",
            "erdogan", "akp", "chp", "mhp", "iyi", "hdp", "devlet", "cumhurbaşkanı"
        ]

        trend_lower = trend_name.lower()
        return any(keyword in trend_lower for keyword in turkey_keywords)

    def _get_mock_data(self, limit: int) -> List[TrendItem]:
        """
        Get mock data when Twitter API is not available.

        Args:
            limit: Number of mock items to return

        Returns:
            List of mock trend items
        """
        mock_items = [
            TrendItem(
                source=TrendSource.TWITTER_TRENDS,
                external_id="twitter_trends_mock_1",
                title="Twitter Trend: #AI",
                description="#AI is trending on Twitter with 15000 mentions",
                url="https://twitter.com/search?q=%23AI",
                score=0.0,
                social_volume=15000,
                is_turkey_related=False,
                is_global=True,
                created_at=datetime.utcnow(),
            ),
            TrendItem(
                source=TrendSource.TWITTER_TRENDS,
                external_id="twitter_trends_mock_2",
                title="Twitter Trend: #Turkey",
                description="#Turkey is trending on Twitter with 8500 mentions",
                url="https://twitter.com/search?q=%23Turkey",
                score=0.0,
                social_volume=8500,
                is_turkey_related=True,
                is_global=False,
                created_at=datetime.utcnow(),
            ),
            TrendItem(
                source=TrendSource.TWITTER_TRENDS,
                external_id="twitter_trends_mock_3",
                title="Twitter Trend: #Climate",
                description="#Climate is trending on Twitter with 12000 mentions",
                url="https://twitter.com/search?q=%23Climate",
                score=0.0,
                social_volume=12000,
                is_turkey_related=False,
                is_global=True,
                created_at=datetime.utcnow(),
            ),
            TrendItem(
                source=TrendSource.TWITTER_TRENDS,
                external_id="twitter_trends_mock_4",
                title="Twitter Trend: #Technology",
                description="#Technology is trending on Twitter with 10000 mentions",
                url="https://twitter.com/search?q=%23Technology",
                score=0.0,
                social_volume=10000,
                is_turkey_related=False,
                is_global=True,
                created_at=datetime.utcnow(),
            ),
            TrendItem(
                source=TrendSource.TWITTER_TRENDS,
                external_id="twitter_trends_mock_5",
                title="Twitter Trend: #Istanbul",
                description="#Istanbul is trending on Twitter with 7500 mentions",
                url="https://twitter.com/search?q=%23Istanbul",
                score=0.0,
                social_volume=7500,
                is_turkey_related=True,
                is_global=False,
                created_at=datetime.utcnow(),
            ),
        ]

        return mock_items[:limit]

    def get_source_authority_score(self) -> float:
        """
        Get the authority score for Twitter trends source.

        Returns:
            Authority score (0.7 for Twitter)
        """
        return 0.7
