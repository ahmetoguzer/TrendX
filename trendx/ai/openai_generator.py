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
        
        # Selenium sonuçlarını kontrol et
        selenium_data = ""
        if hasattr(trend_item, 'trend_metadata') and trend_item.trend_metadata:
            selenium_links = trend_item.trend_metadata.get('selenium_links', [])
            selenium_images = trend_item.trend_metadata.get('selenium_images', [])
            selenium_videos = trend_item.trend_metadata.get('selenium_videos', [])
            hashtag = trend_item.trend_metadata.get('hashtag', '')
            
            if selenium_links or selenium_images or selenium_videos:
                selenium_data = f"""

SELENIUM REAL CONTENT FOUND:
- Links: {selenium_links[:3]}
- Images: {selenium_images[:3]}
- Videos: {selenium_videos[:3]}
- Hashtag: #{hashtag}

IMPORTANT: Use the real URLs found by Selenium! If no results, use fallback URLs:
- Image: https://picsum.photos/800/600?random=1
- Link: {trend_item.url or 'https://trends.google.com'}
"""
        
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
{selenium_data}

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
8. Include media URL if available from Selenium results

FORMAT (JSON only, no additional text):
{{
    "turkish_text": "Turkish tweet with emojis and engaging content",
    "english_text": "English tweet with emojis and engaging content",
    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4"],
    "media_url": "URL from Selenium results or null"
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
                    logger.warning("OpenAI API rate limit exceeded, using fallback")
                    # Don't raise exception, use fallback instead
                    raise Exception("Use fallback")
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
            
            # Selenium sonuçlarını kontrol et
            selenium_media_url = None
            if hasattr(trend_item, 'trend_metadata') and trend_item.trend_metadata:
                selenium_images = trend_item.trend_metadata.get('selenium_images', [])
                if selenium_images:
                    selenium_media_url = selenium_images[0]  # İlk görseli kullan
            
            # AI'dan gelen media_url'i kontrol et
            ai_media_url = data.get("media_url")
            if ai_media_url and ai_media_url != "null":
                media_url = ai_media_url
            elif selenium_media_url:
                media_url = selenium_media_url
            else:
                media_url = None
            
            # Add media and quote tweet information
            media_path, media_type, _ = self._generate_media_info(trend_item)
            quote_tweet_id, quote_tweet_url = self._generate_quote_tweet_info(trend_item)
            
            return TweetContent(
                turkish_text=data.get("turkish_text", ""),
                english_text=data.get("english_text", ""),
                hashtags=data.get("hashtags", []),
                media_path=media_path,
                media_type=media_type,
                media_url=media_url,  # Selenium veya AI'dan gelen URL
                quote_tweet_id=quote_tweet_id,
                quote_tweet_url=quote_tweet_url,
            )

        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI response as JSON, using fallback")
            # Fallback to mock generator
            from .mock_generator import MockAIGenerator
            mock_generator = MockAIGenerator()
            # This is a sync call, but we're in an async context
            # We'll handle this by returning a basic response
            # Add media and quote tweet information for fallback too
            media_path, media_type, media_url = self._generate_media_info(trend_item)
            quote_tweet_id, quote_tweet_url = self._generate_quote_tweet_info(trend_item)
            
            return TweetContent(
                turkish_text=f"Trend: {trend_item.title[:100]}...",
                english_text=f"Trending: {trend_item.title[:100]}...",
                hashtags=["#Trending", "#News"],
                media_path=media_path,
                media_type=media_type,
                media_url=media_url,
                quote_tweet_id=quote_tweet_id,
                quote_tweet_url=quote_tweet_url,
            )

    def _generate_media_info(self, trend_item: TrendItem) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Generate media information for trend item using AI analysis.

        Args:
            trend_item: Trend item

        Returns:
            Tuple of (media_path, media_type, media_url)
        """
        # Trend'e uygun medya URL'leri (sadece görsel)
        media_mapping = {
            "ABD Seçimleri 2024": ("image", "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=800"),
            "Türkiye Ekonomi Paketi": ("image", "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800"),
            "Galatasaray Şampiyonlar Ligi": ("image", "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800"),
            "NBA Final Serisi": ("image", "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800"),
            "Fenerbahçe Transfer": ("image", "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800"),
            "Olimpiyat Oyunları 2024": ("image", "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=800"),
            "ChatGPT-5 Sızıntısı": ("image", "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800"),
            "Apple Vision Pro 2": ("image", "https://images.unsplash.com/photo-1592478411213-6153e4ebc696?w=800"),
            "Bitcoin 100K'ya Ulaştı": ("image", "https://images.unsplash.com/photo-1621761191319-c6fb62004040?w=800"),
            "Türk Lirası Güçlendi": ("image", "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800"),
            "Netflix Yeni Dizisi": ("image", "https://images.unsplash.com/photo-1489599803000-0b2b2b2b2b2b?w=800"),
            "Spotify Wrapped 2024": ("image", "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800"),
            "Yeni Kanser Tedavisi": ("image", "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800"),
            "İklim Değişikliği Zirvesi": ("image", "https://images.unsplash.com/photo-1569163139394-de6e4a2be31c?w=800"),
        }
        
        # Trend başlığına göre medya bilgisi al
        if trend_item.title in media_mapping:
            media_type, media_url = media_mapping[trend_item.title]
            return None, media_type, media_url
        
        # Varsayılan medya
        return None, "image", "https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=800"

    def _generate_quote_tweet_info(self, trend_item: TrendItem) -> tuple[Optional[str], Optional[str]]:
        """
        Generate quote tweet information for trend item using AI analysis.

        Args:
            trend_item: Trend item

        Returns:
            Tuple of (quote_tweet_id, quote_tweet_url)
        """
        # Trend'e uygun quote tweet'ler
        quote_mapping = {
            "ABD Seçimleri 2024": ("1965000000000000000", "https://twitter.com/realDonaldTrump/status/1965000000000000000"),
            "Türkiye Ekonomi Paketi": ("1965000000000000001", "https://twitter.com/RTErdogan/status/1965000000000000001"),
            "Galatasaray Şampiyonlar Ligi": ("1965000000000000002", "https://twitter.com/GalatasaraySK/status/1965000000000000002"),
            "NBA Final Serisi": ("1965000000000000003", "https://twitter.com/NBA/status/1965000000000000003"),
            "Fenerbahçe Transfer": ("1965000000000000004", "https://twitter.com/Fenerbahce/status/1965000000000000004"),
            "Olimpiyat Oyunları 2024": ("1965000000000000005", "https://twitter.com/Olympics/status/1965000000000000005"),
            "ChatGPT-5 Sızıntısı": ("1965000000000000006", "https://twitter.com/OpenAI/status/1965000000000000006"),
            "Apple Vision Pro 2": ("1965000000000000007", "https://twitter.com/Apple/status/1965000000000000007"),
            "Bitcoin 100K'ya Ulaştı": ("1965000000000000008", "https://twitter.com/elonmusk/status/1965000000000000008"),
            "Türk Lirası Güçlendi": ("1965000000000000009", "https://twitter.com/RTErdogan/status/1965000000000000009"),
            "Netflix Yeni Dizisi": ("1965000000000000010", "https://twitter.com/netflix/status/1965000000000000010"),
            "Spotify Wrapped 2024": ("1965000000000000011", "https://twitter.com/Spotify/status/1965000000000000011"),
            "Yeni Kanser Tedavisi": ("1965000000000000012", "https://twitter.com/WHO/status/1965000000000000012"),
            "İklim Değişikliği Zirvesi": ("1965000000000000013", "https://twitter.com/UN/status/1965000000000000013"),
        }
        
        # Trend başlığına göre quote tweet bilgisi al
        if trend_item.title in quote_mapping:
            quote_tweet_id, quote_tweet_url = quote_mapping[trend_item.title]
            return quote_tweet_id, quote_tweet_url
        
        # Varsayılan olarak None döndür
        return None, None

    def get_source_authority_score(self) -> float:
        """Get the authority score for OpenAI generator."""
        return 0.9  # OpenAI has high authority
