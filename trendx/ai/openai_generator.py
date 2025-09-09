"""OpenAI-based AI generator implementation."""

import json
from typing import List, Optional

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
            
            # Parse response and add media/quote tweet support
            content = self._parse_response(response, trend_item)
            
            # Add media and quote tweet information
            media_path, media_type, media_url = self._generate_media_info(trend_item)
            quote_tweet_id, quote_tweet_url = self._generate_quote_tweet_info(trend_item)
            
            # Update content with media and quote tweet info
            content.media_path = media_path
            content.media_type = media_type
            content.media_url = media_url
            content.quote_tweet_id = quote_tweet_id
            content.quote_tweet_url = quote_tweet_url
            
            return content

        except Exception as e:
            logger.error("Failed to generate content with OpenAI", error=str(e))
            # Fallback to mock generator
            from .mock_generator import MockAIGenerator
            mock_generator = MockAIGenerator()
            return await mock_generator.generate_tweet_content(trend_item)

    def _create_prompt(self, trend_item: TrendItem) -> str:
        """
        Create prompt for OpenAI API with advanced prompt engineering.

        Args:
            trend_item: Trend item

        Returns:
            Formatted prompt
        """
        # Determine context and tone based on source and content
        context = self._get_context_info(trend_item)
        tone = self._get_tone_guidance(trend_item)
        
        return f"""
You are a professional social media content creator for TrendX, a bilingual trending news platform. 
Generate engaging, informative, and viral-worthy tweet content.

TRENDING TOPIC:
Title: {trend_item.title}
Description: {trend_item.description or 'No description available'}
Source: {trend_item.source.value}
URL: {trend_item.url or 'No URL available'}
Turkey Related: {trend_item.is_turkey_related}
Global: {trend_item.is_global}
Social Volume: {trend_item.social_volume or 'Unknown'}

CONTEXT: {context}
TONE: {tone}

REQUIREMENTS:
1. Turkish tweet: 180-200 characters, engaging, use Turkish cultural references if relevant
2. English tweet: 180-200 characters, engaging, use global cultural references if relevant
3. Hashtags: 3-5 relevant hashtags, mix of trending and niche tags
4. Make content shareable and discussion-worthy
5. Include emojis appropriately (1-2 per tweet)
6. Avoid controversial or sensitive topics
7. Make it feel authentic and human-written

FORMAT (JSON only, no additional text):
{{
    "turkish_text": "Turkish tweet with emojis and engaging content",
    "english_text": "English tweet with emojis and engaging content",
    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4"]
}}

Generate now:
"""

    def _get_context_info(self, trend_item: TrendItem) -> str:
        """Get contextual information for the trend item."""
        if trend_item.source.value == "twitter_trends":
            return "This is trending on Twitter/X - focus on social media engagement and viral potential"
        elif trend_item.source.value == "reddit":
            return "This is trending on Reddit - focus on community discussion and detailed insights"
        elif trend_item.source.value == "google_trends":
            return "This is trending on Google - focus on search interest and information value"
        else:
            return "This is a general trending topic - focus on broad appeal and information"

    def _get_tone_guidance(self, trend_item: TrendItem) -> str:
        """Get tone guidance based on trend characteristics."""
        if trend_item.is_turkey_related:
            return "Use a tone that resonates with Turkish audience, include local context and cultural references"
        elif trend_item.is_global:
            return "Use a tone that appeals to global audience, focus on universal themes and international perspective"
        else:
            return "Use a balanced, informative tone that works for both local and global audiences"

    async def _call_openai_api(self, prompt: str) -> str:
        """
        Call OpenAI API with the prompt, including error handling and rate limiting.

        Args:
            prompt: Prompt to send

        Returns:
            API response

        Raises:
            Exception: If API call fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional social media content creator. Always respond with valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=60.0,  # Increased timeout for complex requests
                )
                
                # Handle different HTTP status codes
                if response.status_code == 429:
                    logger.warning("OpenAI API rate limit exceeded")
                    raise Exception("Rate limit exceeded")
                elif response.status_code == 401:
                    logger.error("OpenAI API authentication failed")
                    raise Exception("Invalid API key")
                elif response.status_code == 400:
                    logger.error("OpenAI API bad request", status_code=response.status_code)
                    raise Exception("Bad request to OpenAI API")
                
                response.raise_for_status()
                
                result = response.json()
                
                # Validate response structure
                if "choices" not in result or not result["choices"]:
                    raise Exception("Invalid response from OpenAI API")
                
                content = result["choices"][0]["message"]["content"]
                if not content:
                    raise Exception("Empty response from OpenAI API")
                
                return content
                
        except httpx.TimeoutException:
            logger.error("OpenAI API request timed out")
            raise Exception("Request timed out")
        except httpx.RequestError as e:
            logger.error("OpenAI API request failed", error=str(e))
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            raise

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

    def _generate_media_info(self, trend_item: TrendItem) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Generate media information for trend item using AI analysis.

        Args:
            trend_item: Trend item

        Returns:
            Tuple of (media_path, media_type, media_url)
        """
        # TODO: Implement AI-powered media analysis
        # This could analyze the trend content and suggest relevant media
        # For now, return None (no media)
        return None, None, None

    def _generate_quote_tweet_info(self, trend_item: TrendItem) -> tuple[Optional[str], Optional[str]]:
        """
        Generate quote tweet information for trend item using AI analysis.

        Args:
            trend_item: Trend item

        Returns:
            Tuple of (quote_tweet_id, quote_tweet_url)
        """
        # TODO: Implement AI-powered quote tweet analysis
        # This could find relevant tweets to quote based on the trend
        # For now, return None (no quote tweet)
        return None, None

    def get_source_authority_score(self) -> float:
        """Get the authority score for OpenAI generator."""
        return 0.9  # OpenAI has high authority
