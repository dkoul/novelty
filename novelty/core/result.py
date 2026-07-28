"""Similarity result data structure."""

from dataclasses import dataclass, field


@dataclass
class SimilarityResult:
    """Result from a single similarity engine for a single asset."""

    engine_name: str
    asset_id: str
    score: float
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")
