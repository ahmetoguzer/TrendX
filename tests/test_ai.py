"""Tests for AI module."""

import pytest

from trendx.ai.mock_generator import MockAIGenerator
from trendx.common.models import TrendItem, TrendSource


class TestMockAIGenerator:
    """Test mock AI generator."""
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = MockAIGenerator()
        assert generator.mock_responses is not None
    
    @pytest.mark.asyncio
    async def test_generate_tweet_content(self):
        """Test tweet content generation."""
        generator = MockAIGenerator()
        
        trend_item = TrendItem(
            source=TrendSource.REDDIT,
            external_id="test",
            title="Test trending topic",
            is_turkey_related=True,
            is_global=False,
        )
        
        content = await generator.generate_tweet_content(trend_item)
        
        assert content.turkish_text
        assert content.english_text
        assert isinstance(content.hashtags, list)
        assert len(content.hashtags) > 0
        assert content.media_path is None
    
    def test_customize_hashtags(self):
        """Test hashtag customization."""
        generator = MockAIGenerator()
        
        # Turkey-related item
        turkey_item = TrendItem(
            source=TrendSource.REDDIT,
            external_id="test",
            title="Turkey news",
            is_turkey_related=True,
            is_global=False,
        )
        
        hashtags = generator._customize_hashtags(["#News"], turkey_item)
        assert "#Turkey" in hashtags or "#Türkiye" in hashtags
        
        # Global item
        global_item = TrendItem(
            source=TrendSource.REDDIT,
            external_id="test",
            title="Global news",
            is_turkey_related=False,
            is_global=True,
        )
        
        hashtags = generator._customize_hashtags(["#News"], global_item)
        assert "#Global" in hashtags
