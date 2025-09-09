"""Trend scoring algorithm implementation."""

from datetime import datetime, timedelta
from typing import Dict, List

from ..common.logging import get_logger
from ..common.models import TrendItem, TrendSource
from ..sources.base import BaseTrendSource

logger = get_logger(__name__)


class TrendScorer:
    """Scoring algorithm for trend items."""

    def __init__(self, sources: Dict[str, BaseTrendSource]) -> None:
        """
        Initialize trend scorer.

        Args:
            sources: Dictionary of source name to source instance
        """
        self.sources = sources

    def calculate_scores(self, items: List[TrendItem]) -> List[TrendItem]:
        """
        Calculate scores for trend items.

        Args:
            items: List of trend items to score

        Returns:
            List of trend items with calculated scores
        """
        if not items:
            return items

        # Calculate base scores
        for item in items:
            item.score = self._calculate_item_score(item)

        # Normalize scores
        self._normalize_scores(items)

        # Sort by score (highest first)
        items.sort(key=lambda x: x.score, reverse=True)

        logger.info("Calculated scores for trend items", count=len(items))
        return items

    def _calculate_item_score(self, item: TrendItem) -> float:
        """
        Calculate score for a single trend item.

        Args:
            item: Trend item to score

        Returns:
            Calculated score
        """
        score = 0.0

        # Recency score (0.0 to 1.0)
        recency_score = self._calculate_recency_score(item)
        score += recency_score * 0.3

        # Source authority score (0.0 to 1.0)
        source_authority = self._get_source_authority(item.source)
        score += source_authority * 0.2

        # Social volume score (0.0 to 1.0)
        social_volume_score = self._calculate_social_volume_score(item)
        score += social_volume_score * 0.2

        # Turkey/Global relevance bonus
        relevance_bonus = self._calculate_relevance_bonus(item)
        score += relevance_bonus * 0.2

        # Title quality score (0.0 to 1.0)
        title_quality = self._calculate_title_quality_score(item)
        score += title_quality * 0.1

        return min(score, 1.0)  # Cap at 1.0

    def _calculate_recency_score(self, item: TrendItem) -> float:
        """
        Calculate recency score based on creation time.

        Args:
            item: Trend item

        Returns:
            Recency score (0.0 to 1.0)
        """
        now = datetime.utcnow()
        age = now - item.created_at

        # Items newer than 1 hour get full score
        if age <= timedelta(hours=1):
            return 1.0

        # Items older than 24 hours get minimum score
        if age >= timedelta(hours=24):
            return 0.1

        # Linear decay between 1 and 24 hours
        hours_old = age.total_seconds() / 3600
        return max(0.1, 1.0 - (hours_old - 1) / 23)

    def _get_source_authority(self, source: TrendSource) -> float:
        """
        Get authority score for a source.

        Args:
            source: Trend source

        Returns:
            Authority score (0.0 to 1.0)
        """
        source_name = source.value
        if source_name in self.sources:
            return self.sources[source_name].get_source_authority_score()

        # Default authority scores
        authority_scores = {
            TrendSource.REDDIT: 0.8,
            TrendSource.GOOGLE_TRENDS: 0.9,
            TrendSource.TWITTER_TRENDS: 0.7,
            TrendSource.YOUTUBE_TRENDING: 0.6,
            TrendSource.RSS: 0.5,
        }

        return authority_scores.get(source, 0.5)

    def _calculate_social_volume_score(self, item: TrendItem) -> float:
        """
        Calculate social volume score.

        Args:
            item: Trend item

        Returns:
            Social volume score (0.0 to 1.0)
        """
        if item.social_volume <= 0:
            return 0.0

        # Normalize based on typical ranges
        # Reddit: 0-5000, Google Trends: 0, Twitter: 0-10000
        max_volume = 5000
        normalized_volume = min(item.social_volume / max_volume, 1.0)

        # Apply logarithmic scaling to prevent very high scores
        import math
        return math.log(1 + normalized_volume * 9) / math.log(10)

    def _calculate_relevance_bonus(self, item: TrendItem) -> float:
        """
        Calculate relevance bonus for Turkey/Global content.

        Args:
            item: Trend item

        Returns:
            Relevance bonus (0.0 to 0.2)
        """
        bonus = 0.0

        # Turkey-related content gets bonus
        if item.is_turkey_related:
            bonus += 0.1

        # Global content gets smaller bonus
        if item.is_global:
            bonus += 0.05

        return min(bonus, 0.2)

    def _calculate_title_quality_score(self, item: TrendItem) -> float:
        """
        Calculate title quality score.

        Args:
            item: Trend item

        Returns:
            Title quality score (0.0 to 1.0)
        """
        title = item.title.lower()

        # Penalize very short titles
        if len(title) < 10:
            return 0.3

        # Penalize very long titles
        if len(title) > 200:
            return 0.5

        # Bonus for proper capitalization
        if item.title[0].isupper():
            score = 0.7
        else:
            score = 0.5

        # Bonus for question marks (engaging)
        if "?" in title:
            score += 0.1

        # Bonus for numbers (specificity)
        if any(char.isdigit() for char in title):
            score += 0.1

        # Penalty for excessive punctuation
        if title.count("!") > 2 or title.count("?") > 2:
            score -= 0.1

        return min(max(score, 0.0), 1.0)

    def _normalize_scores(self, items: List[TrendItem]) -> None:
        """
        Normalize scores to ensure good distribution.

        Args:
            items: List of trend items to normalize
        """
        if not items:
            return

        scores = [item.score for item in items]
        max_score = max(scores)
        min_score = min(scores)

        if max_score == min_score:
            # All scores are the same, set to 0.5
            for item in items:
                item.score = 0.5
            return

        # Normalize to 0.0-1.0 range
        for item in items:
            item.score = (item.score - min_score) / (max_score - min_score)
