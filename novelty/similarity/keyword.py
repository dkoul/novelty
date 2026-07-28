"""Keyword-based similarity using TF-IDF."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from novelty.core import Request, Asset, SimilarityResult


class KeywordSimilarity:
    """TF-IDF based keyword similarity."""

    name = "keyword"

    def __init__(self):
        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
        )
        self._fitted = False
        self._asset_vectors = None
        self._assets: list[Asset] = []

    def fit(self, assets: list[Asset]) -> None:
        self._assets = assets
        if not assets:
            self._fitted = False
            return

        corpus = [self._asset_to_text(a) for a in assets]
        self._asset_vectors = self._vectorizer.fit_transform(corpus)
        self._fitted = True

    def _asset_to_text(self, asset: Asset) -> str:
        parts = [
            asset.name,
            " ".join(str(t) for t in asset.tags),
            " ".join(str(k) for k in asset.keywords),
            asset.content,
        ]
        return " ".join(parts)

    def score(self, request: Request, assets: list[Asset]) -> list[SimilarityResult]:
        if not self._fitted or assets != self._assets:
            self.fit(assets)

        if not self._fitted:
            return []

        query_text = request.canonical_text or request.text
        query_vector = self._vectorizer.transform([query_text])
        similarities = cosine_similarity(query_vector, self._asset_vectors)[0]

        results = []
        for i, asset in enumerate(self._assets):
            score = float(similarities[i])
            evidence = []
            if score > 0.1:
                matching_keywords = [
                    str(kw) for kw in asset.keywords if str(kw).lower() in query_text.lower()
                ]
                if matching_keywords:
                    evidence.append(f"Matching keywords: {', '.join(matching_keywords)}")
            results.append(
                SimilarityResult(
                    engine_name=self.name,
                    asset_id=asset.id,
                    score=score,
                    evidence=evidence,
                )
            )
        return results
