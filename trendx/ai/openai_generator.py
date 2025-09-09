"""OpenAI-based AI generator implementation."""

import json
from typing import List

import httpx

from ..common.config import settings
from ..common.logging import get_logger
from ..common.models import TrendItem
from .base import BaseAIGenerator, TweetContent

logger = get_logger(__name__)


class OpenAIGenerator(BaseAIGenerator):
    """OpenAI-based AI generator for tweet content."""

    def __init__(self) -> None:
        """Initialize OpenAI generator."""
        self.api_key = settings.ai.api_key
        self.model = settings.ai.model
        self.max_tokens = settings.ai.max_tokens
        self.temperature = settings.ai.temperature

    async def generate_tweet_content(self, trend_item: TrendItem) -> TweetContent:
        """
        Generate tweet content using OpenAI API.

        Args:
            trend_item: Trend item to generate content for

        Returns:
            Generated tweet content
        """
        if not self.api_key:
            logger.warning("OpenAI API key not configured, using mock generator")
            from .mock_generator import MockAIGenerator
            mock_generator = MockAIGenerator()
            return await mock_generator.generate_tweet_content(trend_item)

        logger.info("Generating tweet content with OpenAI", item_id=trend_item.external_id)

        try:
            prompt = self._create_prompt(trend_item)
            response = await self._call_openai_api(prompt)
            
            return self._parse_response(response, trend_item)

        except Exception as e:
            logger.error("Failed to generate content with OpenAI", error=str(e))
            # Fallback to mock generator
            from .mock_generator import MockAIGenerator
            mock_generator = MockAIGenerator()
            return await mock_generator.generate_tweet_content(trend_item)

    def _create_prompt(self, trend_item: TrendItem) -> str:
        """
        Create prompt for OpenAI API.

        Args:
            trend_item: Trend item

        Returns:
            Formatted prompt
        """
        return f"""
Generate bilingual tweet content for the following trending topic:

Title: {trend_item.title}
Description: {trend_item.description or 'No description available'}
Source: {trend_item.source.value}
URL: {trend_item.url or 'No URL available'}
Turkey Related: {trend_item.is_turkey_related}
Global: {trend_item.is_global}

Please generate:
1. A short Turkish tweet (max 200 characters)
2. A short English tweet (max 200 characters)  
3. 3-5 relevant hashtags

Format your response as JSON:
{{
    "turkish_text": "Turkish tweet text here",
    "english_text": "English tweet text here", 
    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"]
}}

Make the tweets engaging, informative, and appropriate for social media.
"""

    async def _call_openai_api(self, prompt: str) -> str:
        """
        Call OpenAI API with the prompt.

        Args:
            prompt: Prompt to send

        Returns:
            API response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30.0,
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]

    def _parse_response(self, response: str, trend_item: TrendItem) -> TweetContent:
        """
        Parse OpenAI response into TweetContent.

        Args:
            response: OpenAI API response
            trend_item: Original trend item

        Returns:
            Parsed tweet content
        """
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            return TweetContent(
                turkish_text=data.get("turkish_text", ""),
                english_text=data.get("english_text", ""),
                hashtags=data.get("hashtags", []),
            )

        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI response as JSON, using fallback")
            # Fallback to mock generator
            from .mock_generator import MockAIGenerator
            mock_generator = MockAIGenerator()
            # This is a sync call, but we're in an async context
            # We'll handle this by returning a basic response
            return TweetContent(
                turkish_text=f"Trend: {trend_item.title[:100]}...",
                english_text=f"Trending: {trend_item.title[:100]}...",
                hashtags=["#Trending", "#News"],
            )
