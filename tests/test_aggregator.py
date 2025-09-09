"""Tests for aggregator module."""

import pytest
from datetime import datetime, timedelta

from trendx.aggregator import TrendScorer, Deduplicator
from trendx.common.models import TrendItem, TrendSource
from trendx.sources.base import BaseTrendSource


class MockSource(BaseTrendSource):
    """Mock source for testing."""
    
    def __init__(self, name: str, authority: float = 0.5):
        super().__init__(name)
        self.authority = authority
    
    async def fetch_trends(self, limit: int = 10):
        return []
    
    def get_source_authority_score(self) -> float:
        return self.authority


class TestTrendScorer:
    """Test trend scoring functionality."""
    
    def test_calculate_scores(self):
        """Test score calculation."""
        sources = {
            "reddit": MockSource("reddit", 0.8),
            "google_trends": MockSource("google_trends", 0.9),
        }
        scorer = TrendScorer(sources)
        
        # Create test items
        now = datetime.utcnow()
        items = [
            TrendItem(
                source=TrendSource.REDDIT,
                external_id="test1",
                title="Recent news",
                social_volume=1000,
                is_turkey_related=True,
                is_global=False,
                created_at=now - timedelta(hours=1),
            ),
            TrendItem(
                source=TrendSource.GOOGLE_TRENDS,
                external_id="test2",
                title="Old news",
                social_volume=500,
                is_turkey_related=False,
                is_global=True,
                created_at=now - timedelta(hours=25),
            ),
        ]
        
        scored_items = scorer.calculate_scores(items)
        
        # Check that items are sorted by score (highest first)
        assert len(scored_items) == 2
        assert scored_items[0].score >= scored_items[1].score
        
        # Recent item should have higher score
        assert scored_items[0].external_id == "test1"
    
    def test_recency_scoring(self):
        """Test recency scoring."""
        sources = {}
        scorer = TrendScorer(sources)
        
        now = datetime.utcnow()
        item = TrendItem(
            source=TrendSource.REDDIT,
            external_id="test",
            title="Test",
            created_at=now - timedelta(hours=1),
        )
        
        recency_score = scorer._calculate_recency_score(item)
        assert 0.0 <= recency_score <= 1.0
        assert recency_score > 0.5  # Should be high for recent item
    
    def test_source_authority(self):
        """Test source authority scoring."""
        sources = {
            "reddit": MockSource("reddit", 0.8),
        }
        scorer = TrendScorer(sources)
        
        authority = scorer._get_source_authority(TrendSource.REDDIT)
        assert authority == 0.8
        
        # Test default authority
        authority = scorer._get_source_authority(TrendSource.RSS)
        assert authority == 0.5


class TestDeduplicator:
    """Test deduplication functionality."""
    
    def test_deduplicate(self):
        """Test basic deduplication."""
        deduplicator = Deduplicator()
        
        items = [
            TrendItem(
                source=TrendSource.REDDIT,
                external_id="test1",
                title="Same title",
                url="https://example.com/1",
            ),
            TrendItem(
                source=TrendSource.REDDIT,
                external_id="test2",
                title="Same title",
                url="https://example.com/1",
            ),
            TrendItem(
                source=TrendSource.REDDIT,
                external_id="test3",
                title="Different title",
                url="https://example.com/2",
            ),
        ]
        
        unique_items = deduplicator.deduplicate(items)
        
        # Should have 2 unique items
        assert len(unique_items) == 2
        assert unique_items[0].external_id == "test1"
        assert unique_items[1].external_id == "test3"
    
    def test_normalize_text(self):
        """Test text normalization."""
        deduplicator = Deduplicator()
        
        text = "Breaking: Major NEWS!!!"
        normalized = deduplicator._normalize_text(text)
        
        assert normalized == "breaking major news"
    
    def test_clear_cache(self):
        """Test cache clearing."""
        deduplicator = Deduplicator()
        
        # Add some items to cache
        items = [
            TrendItem(
                source=TrendSource.REDDIT,
                external_id="test1",
                title="Test title",
                url="https://example.com",
            ),
        ]
        deduplicator.deduplicate(items)
        
        # Cache should have items
        assert len(deduplicator.seen_hashes) > 0
        
        # Clear cache
        deduplicator.clear_cache()
        assert len(deduplicator.seen_hashes) == 0
