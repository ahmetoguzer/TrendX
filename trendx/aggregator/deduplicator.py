"""Content deduplication implementation."""

import hashlib
import re
from typing import List, Set

from ..common.logging import get_logger
from ..common.models import TrendItem

logger = get_logger(__name__)


class Deduplicator:
    """Deduplication algorithm for trend items."""

    def __init__(self) -> None:
        """Initialize deduplicator."""
        self.seen_hashes: Set[str] = set()

    def deduplicate(self, items: List[TrendItem]) -> List[TrendItem]:
        """
        Remove duplicate items from the list.

        Args:
            items: List of trend items to deduplicate

        Returns:
            List of unique trend items
        """
        if not items:
            return items

        unique_items = []
        seen_hashes = set()

        for item in items:
            # Generate hash for the item
            item_hash = self._generate_item_hash(item)

            # Check if we've seen this item before
            if item_hash not in seen_hashes and item_hash not in self.seen_hashes:
                unique_items.append(item)
                seen_hashes.add(item_hash)
            else:
                logger.debug("Duplicate item found", item_id=item.external_id)

        # Update global seen hashes
        self.seen_hashes.update(seen_hashes)

        logger.info(
            "Deduplication completed",
            original_count=len(items),
            unique_count=len(unique_items),
            duplicates_removed=len(items) - len(unique_items),
        )

        return unique_items

    def _generate_item_hash(self, item: TrendItem) -> str:
        """
        Generate a hash for a trend item to identify duplicates.

        Args:
            item: Trend item to hash

        Returns:
            Hash string
        """
        # Normalize title for comparison
        normalized_title = self._normalize_text(item.title)

        # Create hash from normalized title and URL
        hash_input = f"{normalized_title}|{item.url or ''}"
        return hashlib.md5(hash_input.encode("utf-8")).hexdigest()

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common punctuation
        text = re.sub(r"[^\w\s]", "", text)

        # Remove common words that don't add meaning
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "can", "this", "that", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "me", "him",
            "her", "us", "them", "my", "your", "his", "her", "its", "our", "their",
        }

        words = text.split()
        filtered_words = [word for word in words if word not in stop_words]

        return " ".join(filtered_words)

    def clear_cache(self) -> None:
        """Clear the seen hashes cache."""
        self.seen_hashes.clear()
        logger.info("Deduplication cache cleared")
