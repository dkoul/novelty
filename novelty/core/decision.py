"""NoveltyDecision data structure."""

from dataclasses import dataclass, field
from typing import Literal


Action = Literal["reuse", "hint", "small_model", "frontier_model"]


@dataclass
class NoveltyDecision:
    """The result of novelty evaluation."""

    novelty_score: float
    confidence: float
    action: Action
    matched_asset: str | None = None
    explanation: list[str] = field(default_factory=list)
    estimated_savings: dict | None = None
    recommended_model: str | None = None
    hint: str | None = None

    def __post_init__(self):
        if not 0.0 <= self.novelty_score <= 1.0:
            raise ValueError("novelty_score must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict:
        return {
            "novelty_score": self.novelty_score,
            "confidence": self.confidence,
            "action": self.action,
            "matched_asset": self.matched_asset,
            "explanation": self.explanation,
            "estimated_savings": self.estimated_savings,
            "recommended_model": self.recommended_model,
            "hint": self.hint,
        }
