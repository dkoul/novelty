"""Base similarity engine protocol."""

from typing import Protocol
from novelty.core import Request, Asset, SimilarityResult


class SimilarityEngine(Protocol):
    """Protocol for similarity engines."""

    name: str

    def score(self, request: Request, assets: list[Asset]) -> list[SimilarityResult]:
        """Score similarity between request and each asset."""
        ...
