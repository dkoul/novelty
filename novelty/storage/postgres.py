"""PostgreSQL storage backend for shared assets with pre-computed embeddings."""

import json
from dataclasses import asdict
from novelty.core import Asset


class PostgresAssetStore:
    """PostgreSQL-backed asset storage with embeddings."""

    def __init__(self, connection_string: str):
        import psycopg
        self._conn_string = connection_string
        self._conn = psycopg.connect(connection_string)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    tags JSONB DEFAULT '[]',
                    keywords JSONB DEFAULT '[]',
                    intent TEXT DEFAULT '',
                    content TEXT DEFAULT '',
                    cost_to_create REAL DEFAULT 0,
                    reuse_count INTEGER DEFAULT 0,
                    embedding JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_assets_intent ON assets(intent)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_assets_tags ON assets USING GIN(tags)
            """)
        self._conn.commit()

    def save(self, asset: Asset) -> None:
        with self._conn.cursor() as cur:
            cur.execute("""
                INSERT INTO assets (id, name, version, tags, keywords, intent, content,
                                   cost_to_create, reuse_count, embedding, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    version = EXCLUDED.version,
                    tags = EXCLUDED.tags,
                    keywords = EXCLUDED.keywords,
                    intent = EXCLUDED.intent,
                    content = EXCLUDED.content,
                    cost_to_create = EXCLUDED.cost_to_create,
                    reuse_count = EXCLUDED.reuse_count,
                    embedding = EXCLUDED.embedding,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                asset.id,
                asset.name,
                asset.version,
                json.dumps(asset.tags),
                json.dumps(asset.keywords),
                asset.intent,
                asset.content,
                asset.cost_to_create,
                asset.reuse_count,
                json.dumps(asset.embedding) if asset.embedding else None,
            ))
        self._conn.commit()

    def get(self, asset_id: str) -> Asset | None:
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, version, tags, keywords, intent, content,
                       cost_to_create, reuse_count, embedding
                FROM assets WHERE id = %s
            """, (asset_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_asset(row)

    def all(self) -> list[Asset]:
        with self._conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, version, tags, keywords, intent, content,
                       cost_to_create, reuse_count, embedding
                FROM assets ORDER BY id
            """)
            return [self._row_to_asset(row) for row in cur.fetchall()]

    def _row_to_asset(self, row: tuple) -> Asset:
        return Asset(
            id=row[0],
            name=row[1],
            version=row[2],
            tags=row[3] if isinstance(row[3], list) else json.loads(row[3] or "[]"),
            keywords=row[4] if isinstance(row[4], list) else json.loads(row[4] or "[]"),
            intent=row[5] or "",
            content=row[6] or "",
            cost_to_create=row[7] or 0,
            reuse_count=row[8] or 0,
            embedding=row[9] if isinstance(row[9], list) else json.loads(row[9]) if row[9] else None,
        )

    def increment_reuse(self, asset_id: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute("""
                UPDATE assets SET reuse_count = reuse_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (asset_id,))
        self._conn.commit()

    def delete(self, asset_id: str) -> bool:
        with self._conn.cursor() as cur:
            cur.execute("DELETE FROM assets WHERE id = %s", (asset_id,))
            deleted = cur.rowcount > 0
        self._conn.commit()
        return deleted

    def count(self) -> int:
        with self._conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM assets")
            return cur.fetchone()[0]

    def close(self) -> None:
        self._conn.close()
