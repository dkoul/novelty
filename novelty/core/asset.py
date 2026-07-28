"""Asset data structure and registry."""

from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class Asset:
    """A reusable intelligence asset."""

    id: str
    name: str
    version: int = 1
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    intent: str = ""
    content: str = ""
    cost_to_create: float = 0.0
    reuse_count: int = 0
    embedding: list[float] | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> "Asset":
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def estimated_savings_per_reuse(self) -> dict:
        tokens = 1200
        cost_per_1k_tokens = 0.015
        return {
            "tokens": tokens,
            "cost_usd": round(tokens * cost_per_1k_tokens / 1000, 4),
        }


class AssetRegistry:
    """Registry of intelligence assets."""

    def __init__(self):
        self._assets: dict[str, Asset] = {}

    def register(self, asset: Asset) -> None:
        self._assets[asset.id] = asset

    def get(self, asset_id: str) -> Asset | None:
        return self._assets.get(asset_id)

    def all(self) -> list[Asset]:
        return list(self._assets.values())

    def load_from_directory(self, path: Path) -> int:
        count = 0
        for yaml_file in path.glob("*.yaml"):
            asset = Asset.from_yaml(yaml_file)
            self.register(asset)
            count += 1
        return count

    def __len__(self) -> int:
        return len(self._assets)
