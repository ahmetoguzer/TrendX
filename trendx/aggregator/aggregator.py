"""Main aggregator that combines scoring and deduplication."""

from typing import Dict, List

from ..common.logging import get_logger
from ..common.models import TrendItem
from ..sources.base import BaseTrendSource
from .deduplicator import Deduplicator
from .scorer import TrendScorer

logger = get_logger(__name__)


class TrendAggregator:
    """Main aggregator for processing trend items."""

    def __init__(self, sources: Dict[str, BaseTrendSource]) -> None:
        """
        Initialize trend aggregator.

        Args:
            sources: Dictionary of source name to source instance
        """
        self.sources = sources
        self.scorer = TrendScorer(sources)
        self.deduplicator = Deduplicator()

    async def aggregate_trends(self, limit: int = 10) -> List[TrendItem]:
        """
        Aggregate trends from all sources.

        Args:
            limit: Maximum number of items to return

        Returns:
            List of aggregated and scored trend items
        """
        logger.info("Starting trend aggregation", limit=limit)

        # Fetch from all sources
        all_items = []
        for source_name, source in self.sources.items():
            try:
                logger.info("Fetching trends from source", source=source_name)
                items = await source.fetch_trends(limit=limit)
                all_items.extend(items)
                logger.info(
                    "Fetched items from source",
                    source=source_name,
                    count=len(items),
                )
            except Exception as e:
                logger.error(
                    "Failed to fetch from source",
                    source=source_name,
                    error=str(e),
                )

        if not all_items:
            logger.warning("No items fetched from any source")
            return []

        logger.info("Total items fetched", count=len(all_items))

        # Deduplicate
        unique_items = self.deduplicator.deduplicate(all_items)
        logger.info("Items after deduplication", count=len(unique_items))

        # Score items
        scored_items = self.scorer.calculate_scores(unique_items)
        logger.info("Items after scoring", count=len(scored_items))

        # Return top items
        top_items = scored_items[:limit]
        logger.info("Returning top items", count=len(top_items))

        return top_items

    def get_source_stats(self) -> Dict[str, int]:
        """
        Get statistics about sources.

        Returns:
            Dictionary of source names to item counts
        """
        stats = {}
        for source_name in self.sources.keys():
            stats[source_name] = 0  # This would be populated from actual data
        return stats
