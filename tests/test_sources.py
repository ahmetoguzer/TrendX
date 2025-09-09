"""Tests for sources module."""

import pytest
from unittest.mock import Mock, patch

from trendx.sources.reddit import RedditTrendSource
from trendx.sources.google_trends import GoogleTrendsSource
from trendx.sources.twitter_trends import TwitterTrendsSource
from trendx.common.models import TrendSource


class TestRedditTrendSource:
    """Test Reddit trend source."""
    
    def test_initialization(self):
        """Test source initialization."""
        source = RedditTrendSource()
        assert source.name == "reddit"
        assert source.get_source_authority_score() == 0.8
    
    @pytest.mark.asyncio
    async def test_fetch_trends_mock(self):
        """Test fetching trends with mock data."""
        source = RedditTrendSource()
        trends = await source.fetch_trends(limit=3)
        
        assert len(trends) <= 3
        for trend in trends:
            assert trend.source == TrendSource.REDDIT
            assert trend.external_id.startswith("reddit_")
            assert trend.title
            assert isinstance(trend.is_turkey_related, bool)
            assert isinstance(trend.is_global, bool)
    
    def test_is_turkey_related(self):
        """Test Turkey-related content detection."""
        source = RedditTrendSource()
        
        # Turkey-related content
        assert source._is_turkey_related("Turkey announces new policy", "")
        assert source._is_turkey_related("Istanbul'da buyuk gelisme", "")
        assert source._is_turkey_related("Turkish economy", "")
        
        # Non-Turkey content
        assert not source._is_turkey_related("Global news update", "")
        assert not source._is_turkey_related("US politics", "")


class TestGoogleTrendsSource:
    """Test Google Trends source."""
    
    def test_initialization(self):
        """Test source initialization."""
        source = GoogleTrendsSource()
        assert source.name == "google_trends"
        assert source.get_source_authority_score() == 0.9
    
    @pytest.mark.asyncio
    async def test_fetch_trends_mock(self):
        """Test fetching trends with mock data."""
        source = GoogleTrendsSource()
        trends = await source.fetch_trends(limit=3)
        
        assert len(trends) <= 3
        for trend in trends:
            assert trend.source == TrendSource.GOOGLE_TRENDS
            assert trend.external_id.startswith("google_trends_")
            assert trend.title.startswith("Trending:")
            assert isinstance(trend.is_turkey_related, bool)
            assert isinstance(trend.is_global, bool)
    
    def test_is_turkey_related(self):
        """Test Turkey-related content detection."""
        source = GoogleTrendsSource()
        
        # Turkey-related content
        assert source._is_turkey_related("Turkey Economy")
        assert source._is_turkey_related("Istanbul")
        assert source._is_turkey_related("Turkish")
        
        # Non-Turkey content
        assert not source._is_turkey_related("Artificial Intelligence")
        assert not source._is_turkey_related("Climate Change")


class TestTwitterTrendsSource:
    """Test Twitter trends source."""
    
    def test_initialization(self):
        """Test source initialization."""
        source = TwitterTrendsSource()
        assert source.name == "twitter_trends"
        assert source.get_source_authority_score() == 0.7
    
    @pytest.mark.asyncio
    async def test_fetch_trends_mock(self):
        """Test fetching trends with mock data."""
        source = TwitterTrendsSource()
        trends = await source.fetch_trends(limit=3)
        
        assert len(trends) <= 3
        for trend in trends:
            assert trend.source == TrendSource.TWITTER_TRENDS
            assert trend.external_id.startswith("twitter_trends_")
            assert trend.title.startswith("Twitter Trend:")
            assert isinstance(trend.is_turkey_related, bool)
            assert isinstance(trend.is_global, bool)
    
    def test_is_turkey_related(self):
        """Test Turkey-related content detection."""
        source = TwitterTrendsSource()
        
        # Turkey-related content
        assert source._is_turkey_related("Turkey")
        assert source._is_turkey_related("Istanbul")
        assert source._is_turkey_related("Turkish")
        
        # Non-Turkey content
        assert not source._is_turkey_related("AI")
        assert not source._is_turkey_related("Climate")
