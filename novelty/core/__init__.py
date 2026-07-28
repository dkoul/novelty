"""Core data structures for Novelty."""

from novelty.core.request import Request
from novelty.core.decision import NoveltyDecision
from novelty.core.asset import Asset, AssetRegistry
from novelty.core.result import SimilarityResult

__all__ = ["Request", "NoveltyDecision", "Asset", "AssetRegistry", "SimilarityResult"]
