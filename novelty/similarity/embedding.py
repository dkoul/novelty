"""Embedding-based semantic similarity."""

import os
import numpy as np
from novelty.core import Request, Asset, SimilarityResult


class EmbeddingSimilarity:
    """Embedding-based semantic similarity with multiple backends."""

    name = "embedding"

    def __init__(
        self,
        backend: str | None = None,
        model_name: str | None = None,
    ):
        # Auto-detect backend: prefer ollama if available, else sentence-transformers
        if backend is None:
            backend = os.environ.get("NOVELTY_EMBEDDING_BACKEND", "ollama")

        self._backend = backend
        self._model_name = model_name or self._default_model()
        self._model = None
        self._asset_embeddings: dict[str, np.ndarray] = {}

    def _default_model(self) -> str:
        if self._backend == "ollama":
            return "nomic-embed-text"
        return "all-MiniLM-L6-v2"

    def _ensure_model(self) -> None:
        if self._model is not None:
            return

        if self._backend == "ollama":
            import httpx
            self._model = httpx.Client(base_url="http://localhost:11434", timeout=30.0)
        else:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)

    def _get_embedding(self, text: str) -> np.ndarray:
        self._ensure_model()

        if self._backend == "ollama":
            response = self._model.post(
                "/api/embeddings",
                json={"model": self._model_name, "prompt": text},
            )
            response.raise_for_status()
            return np.array(response.json()["embedding"])
        else:
            return self._model.encode(text, convert_to_numpy=True)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _asset_to_text(self, asset: Asset) -> str:
        tags = " ".join(str(t) for t in asset.tags)
        keywords = " ".join(str(k) for k in asset.keywords)
        return f"{asset.name}. {tags}. {keywords}. {asset.content[:500]}"

    def compute_embedding(self, text: str) -> list[float]:
        """Compute embedding for text. Used for pre-computing asset embeddings."""
        return self._get_embedding(text).tolist()

    def compute_asset_embedding(self, asset: Asset) -> list[float]:
        """Compute and return embedding for an asset."""
        text = self._asset_to_text(asset)
        return self.compute_embedding(text)

    def score(self, request: Request, assets: list[Asset]) -> list[SimilarityResult]:
        if not assets:
            return []

        query_text = request.canonical_text or request.text
        query_embedding = self._get_embedding(query_text)

        results = []
        for asset in assets:
            # Use pre-computed embedding if available
            if asset.embedding is not None:
                asset_embedding = np.array(asset.embedding)
            elif asset.id in self._asset_embeddings:
                asset_embedding = self._asset_embeddings[asset.id]
            else:
                asset_text = self._asset_to_text(asset)
                asset_embedding = self._get_embedding(asset_text)
                self._asset_embeddings[asset.id] = asset_embedding

            similarity = self._cosine_similarity(query_embedding, asset_embedding)
            similarity = max(0.0, min(1.0, similarity))

            evidence = []
            if similarity > 0.5:
                evidence.append(f"High semantic similarity ({similarity:.0%})")
            elif similarity > 0.3:
                evidence.append(f"Moderate semantic similarity ({similarity:.0%})")

            results.append(
                SimilarityResult(
                    engine_name=self.name,
                    asset_id=asset.id,
                    score=similarity,
                    evidence=evidence,
                )
            )
        return results
