"""Similarity engines module."""

from novelty.similarity.base import SimilarityEngine
from novelty.similarity.keyword import KeywordSimilarity
from novelty.similarity.embedding import EmbeddingSimilarity
from novelty.similarity.intent import IntentSimilarity

__all__ = [
    "SimilarityEngine",
    "KeywordSimilarity",
    "EmbeddingSimilarity",
    "IntentSimilarity",
]
