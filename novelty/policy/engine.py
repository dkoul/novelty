"""Policy engine for novelty decisions."""

from novelty.core import NoveltyDecision, SimilarityResult


DEFAULT_CONFIG = {
    "weights": {
        "keyword": 0.25,
        "embedding": 0.55,
        "intent": 0.20,
    },
    "thresholds": {
        "reuse": 0.45,
        "cache": 0.55,
        "small_model": 0.70,
    },
    "models": {
        "small_model": "gpt-4o-mini",      # 50% cost, ~90% quality
        "frontier_model": "gpt-4o",         # Full cost, full quality
    },
}


class PolicyEngine:
    """Combines similarity scores into a novelty decision."""

    def __init__(self, config: dict | None = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.weights = self.config.get("weights", DEFAULT_CONFIG["weights"])
        self.thresholds = self.config.get("thresholds", DEFAULT_CONFIG["thresholds"])
        self.models = self.config.get("models", DEFAULT_CONFIG["models"])

    def decide(
        self,
        results: list[SimilarityResult],
        asset_savings: dict[str, dict] | None = None,
    ) -> NoveltyDecision:
        if not results:
            return NoveltyDecision(
                novelty_score=1.0,
                confidence=0.5,
                action="frontier_model",
                explanation=["No assets available for comparison"],
            )

        asset_scores: dict[str, dict[str, float]] = {}
        for result in results:
            if result.asset_id not in asset_scores:
                asset_scores[result.asset_id] = {}
            asset_scores[result.asset_id][result.engine_name] = result.score

        best_asset = None
        best_weighted_score = 0.0
        best_breakdown: dict[str, float] = {}

        for asset_id, scores in asset_scores.items():
            weighted_score = 0.0
            total_weight = 0.0

            for engine_name, weight in self.weights.items():
                if engine_name in scores:
                    weighted_score += scores[engine_name] * weight
                    total_weight += weight

            if total_weight > 0:
                weighted_score /= total_weight

            if weighted_score > best_weighted_score:
                best_weighted_score = weighted_score
                best_asset = asset_id
                best_breakdown = scores

        novelty_score = 1.0 - best_weighted_score

        if novelty_score <= self.thresholds["reuse"]:
            action = "reuse"
        elif novelty_score <= self.thresholds["cache"]:
            action = "cache"
        elif novelty_score <= self.thresholds["small_model"]:
            action = "small_model"
        else:
            action = "frontier_model"

        explanation = self._build_explanation(
            best_asset, best_breakdown, novelty_score, action
        )

        confidence = self._calculate_confidence(best_breakdown, novelty_score)

        estimated_savings = None
        if action in ("reuse", "cache") and best_asset and asset_savings:
            estimated_savings = asset_savings.get(best_asset)

        recommended_model = None
        if action in ("small_model", "frontier_model"):
            recommended_model = self.models.get(action)

        return NoveltyDecision(
            novelty_score=round(novelty_score, 2),
            confidence=round(confidence, 2),
            action=action,
            matched_asset=best_asset if action in ("reuse", "cache") else None,
            explanation=explanation,
            estimated_savings=estimated_savings,
            recommended_model=recommended_model,
        )

    def _build_explanation(
        self,
        asset_id: str | None,
        breakdown: dict[str, float],
        novelty_score: float,
        action: str,
    ) -> list[str]:
        explanations = []

        if breakdown.get("keyword", 0) > 0.5:
            explanations.append(
                f"Strong keyword match ({breakdown['keyword']:.0%}) with {asset_id}"
            )
        elif breakdown.get("keyword", 0) > 0.2:
            explanations.append(f"Partial keyword match ({breakdown['keyword']:.0%})")
        else:
            explanations.append("No significant keyword overlap")

        if breakdown.get("embedding", 0) > 0.7:
            explanations.append(
                f"High semantic similarity ({breakdown['embedding']:.0%})"
            )
        elif breakdown.get("embedding", 0) > 0.4:
            explanations.append(
                f"Moderate semantic similarity ({breakdown['embedding']:.0%})"
            )
        else:
            explanations.append(
                f"Low semantic similarity ({breakdown.get('embedding', 0):.0%})"
            )

        if breakdown.get("intent", 0) > 0.8:
            explanations.append("Intent matches existing asset")
        elif breakdown.get("intent", 0) < 0.3:
            explanations.append("Intent not covered by existing assets")

        return explanations

    def _calculate_confidence(
        self, breakdown: dict[str, float], novelty_score: float
    ) -> float:
        if not breakdown:
            return 0.5

        scores = list(breakdown.values())
        variance = sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(
            scores
        )

        agreement_factor = 1.0 - min(variance * 2, 0.5)

        if novelty_score < 0.2 or novelty_score > 0.8:
            extremity_factor = 1.0
        else:
            extremity_factor = 0.8

        return min(0.99, agreement_factor * extremity_factor)
