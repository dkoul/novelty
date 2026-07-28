"""Main Novelty engine."""

import os
from pathlib import Path
from novelty.core import Request, NoveltyDecision, Asset, AssetRegistry
from novelty.canonicalizer import SimpleCanonicalizer
from novelty.similarity import KeywordSimilarity, EmbeddingSimilarity, IntentSimilarity
from novelty.policy import PolicyEngine


class Novelty:
    """The Novelty inference elimination engine."""

    def __init__(
        self,
        assets_path: Path | None = None,
        postgres_url: str | None = None,
        config: dict | None = None,
    ):
        self.canonicalizer = SimpleCanonicalizer()
        self.policy_engine = PolicyEngine(config)

        self._embedding_engine = EmbeddingSimilarity()
        self._similarity_engines = [
            KeywordSimilarity(),
            self._embedding_engine,
            IntentSimilarity(),
        ]

        # Storage backend
        self._store = None
        postgres_url = postgres_url or os.environ.get("NOVELTY_POSTGRES_URL")

        if postgres_url:
            from novelty.storage import PostgresAssetStore
            self._store = PostgresAssetStore(postgres_url)
            self.registry = None
        else:
            self.registry = AssetRegistry()
            if assets_path is None:
                assets_path = Path(__file__).parent / "assets"
            if assets_path.exists():
                self.registry.load_from_directory(assets_path)

    def _get_assets(self) -> list[Asset]:
        if self._store:
            return self._store.all()
        return self.registry.all()

    def evaluate(self, text: str, metadata: dict | None = None) -> NoveltyDecision:
        request = Request(text=text, metadata=metadata or {})
        request = self.canonicalizer.canonicalize(request)

        assets = self._get_assets()
        if not assets:
            return NoveltyDecision(
                novelty_score=1.0,
                confidence=0.5,
                action="frontier_model",
                explanation=["No intelligence assets available"],
            )

        all_results = []
        for engine in self._similarity_engines:
            results = engine.score(request, assets)
            all_results.extend(results)

        asset_savings = {
            asset.id: asset.estimated_savings_per_reuse() for asset in assets
        }

        decision = self.policy_engine.decide(all_results, asset_savings)

        # Track reuse in database
        if self._store and decision.matched_asset and decision.action in ("reuse", "cache"):
            self._store.increment_reuse(decision.matched_asset)

        return decision

    def add_asset(self, asset: Asset, compute_embedding: bool = True) -> None:
        """Add an asset to storage, optionally computing its embedding."""
        if compute_embedding and asset.embedding is None:
            asset.embedding = self._embedding_engine.compute_asset_embedding(asset)

        if self._store:
            self._store.save(asset)
        else:
            self.registry.register(asset)

    def import_assets_from_yaml(self, path: Path) -> int:
        """Import assets from YAML files into PostgreSQL with embeddings."""
        if not self._store:
            raise ValueError("PostgreSQL storage not configured")

        count = 0
        for yaml_file in path.glob("*.yaml"):
            asset = Asset.from_yaml(yaml_file)
            self.add_asset(asset, compute_embedding=True)
            count += 1
        return count

    def get_asset(self, asset_id: str) -> Asset | None:
        if self._store:
            return self._store.get(asset_id)
        return self.registry.get(asset_id)

    def __len__(self) -> int:
        if self._store:
            return self._store.count()
        return len(self.registry)
