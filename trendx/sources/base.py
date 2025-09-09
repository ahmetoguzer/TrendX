"""Base trend source interface."""

from abc import ABC, abstractmethod
from typing import List

from ..common.models import TrendItem


class BaseTrendSource(ABC):
    """Abstract base class for trend sources."""

    def __init__(self, name: str) -> None:
        """Initialize the trend source."""
        self.name = name

    @abstractmethod
    async def fetch_trends(self, limit: int = 10) -> List[TrendItem]:
        """
        Fetch trending items from the source.

        Args:
            limit: Maximum number of items to fetch

        Returns:
            List of trend items
        """
        pass

    @abstractmethod
    def get_source_authority_score(self) -> float:
        """
        Get the authority score for this source (0.0 to 1.0).

        Returns:
            Authority score
        """
        pass
