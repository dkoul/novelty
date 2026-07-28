"""Intent-based similarity."""

from novelty.core import Request, Asset, SimilarityResult


INTENT_COMPATIBILITY = {
    ("debug", "debug"): 1.0,
    ("debug", "configure"): 0.3,
    ("implement", "implement"): 1.0,
    ("implement", "configure"): 0.4,
    ("explain", "explain"): 1.0,
    ("explain", "debug"): 0.5,
    ("optimize", "optimize"): 1.0,
    ("optimize", "debug"): 0.4,
    ("configure", "configure"): 1.0,
    ("configure", "debug"): 0.3,
}


class IntentSimilarity:
    """Rule-based intent similarity."""

    name = "intent"

    def score(self, request: Request, assets: list[Asset]) -> list[SimilarityResult]:
        request_intent = request.extracted_entities.get("intent", "unknown")

        results = []
        for asset in assets:
            asset_intent = asset.intent or "unknown"

            if request_intent == "unknown" or asset_intent == "unknown":
                score = 0.2
                evidence = ["Intent unclear"]
            elif request_intent == asset_intent:
                score = 1.0
                evidence = [f"Intent match: {request_intent}"]
            else:
                key = (request_intent, asset_intent)
                reverse_key = (asset_intent, request_intent)
                score = INTENT_COMPATIBILITY.get(
                    key, INTENT_COMPATIBILITY.get(reverse_key, 0.1)
                )
                evidence = [f"Intent: {request_intent} vs {asset_intent}"]

            results.append(
                SimilarityResult(
                    engine_name=self.name,
                    asset_id=asset.id,
                    score=score,
                    evidence=evidence,
                )
            )
        return results
