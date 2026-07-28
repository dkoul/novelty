# Novelty

**The fastest and cheapest LLM call is the one you never make.**

---

## The Cookie Story

You have two smart friends who answer questions for cookies:

| Friend | Cookies | How Smart |
|--------|---------|-----------|
| **Deepak** (frontier) | 1 full cookie | 100% smart |
| **Anuj** (small) | ½ cookie | 90% smart |

Your whole class keeps asking the same questions. Every time, you give away cookies. But what if you wrote down the answers?

---

### The Shared Notebook

```
┌─────────────────────────────────────────┐
│           CLASS NOTEBOOK                │
│         (Shared Database)               │
│                                         │
│  "Toy not working" → Check batteries    │
│  "Toy makes noise" → Turn volume down   │
│  "Toy won't move"  → Wind it up         │
│                                         │
└─────────────────────────────────────────┘
         ↑           ↑           ↑
       Alice        Bob        Carol
```

Everyone shares ONE notebook. Alice's answer helps Bob and Carol too.

---

### How Novelty Decides

```
Alice: "My toy stopped working"

Novelty: *checks notebook*
         "I know this one!"
         → Returns saved answer
         → NO COOKIES
```

```
Bob: "How do I make my toy waterproof?"

Novelty: *checks notebook*
         "Similar to something, but not exact..."
         "Needs SOME thinking, but not the HARDEST"
         → Asks Anuj (½ cookie)
         → Good enough!
```

```
Carol: "How do I build a mass produced robot?"

Novelty: *checks notebook*
         "Never seen ANYTHING like this!"
         → Asks Deepak (1 cookie)
         → Only the best will do
```

---

### The Savings

| Question | Who Answered | Cookies |
|----------|--------------|---------|
| Toy stopped working | Notebook | 0 |
| Toy waterproof | Anuj | ½ |
| Robot army | Deepak | 1 |
| Battery died | Notebook | 0 |
| Toy floats? | Anuj | ½ |
| **Total** | | **2 cookies** |

**Old way (always ask Deepak): 5 cookies**

**Saved: 3 cookies (60%)**

---

## Quick Start

```bash
pip install -e .
novelty demo
```

---

## How It Works

```
Question
    ↓
Novelty Score (0.0 = seen before, 1.0 = completely new)
    ↓
├── 0.0 - 0.45  →  REUSE      →  Use notebook (no cookies)
├── 0.45 - 0.70 →  ANUJ       →  Small model (½ cookie)
└── 0.70 - 1.0  →  DEEPAK     →  Frontier model (1 cookie)
```

---

## CLI Usage

```bash
# Evaluate a prompt
novelty evaluate "Playwright test timing out"

# Output:
# ╭─────────────── REUSE  Novelty: 0.42 (Low) ───────────────╮
# │ Matched: playwright-timeout                              │
# │ Confidence: 94%                                          │
# │ Savings: ~1,200 tokens ($0.02)                           │
# ╰──────────────────────────────────────────────────────────╯

# Novel question
novelty evaluate "Implement WebSocket reconnection"

# Output:
# ╭─────────── SMALL MODEL  Novelty: 0.65 (Medium) ──────────╮
# │ Recommended: gpt-4o-mini                                 │
# │ Confidence: 72%                                          │
# ╰──────────────────────────────────────────────────────────╯

# List assets
novelty assets

# Run demo
novelty demo
```

---

## Shared Storage (PostgreSQL)

For teams to share the notebook:

```bash
# Install with PostgreSQL support
pip install -e ".[postgres]"

# Start PostgreSQL
docker run -d --name novelty-postgres \
  -e POSTGRES_USER=novelty \
  -e POSTGRES_PASSWORD=novelty \
  -e POSTGRES_DB=novelty \
  -p 5432:5432 \
  postgres:16-alpine

# Import assets with pre-computed embeddings
export NOVELTY_POSTGRES_URL="postgresql://novelty:novelty@localhost/novelty"
novelty import-assets ./novelty/assets

# Now everyone connects to the same notebook
novelty evaluate "Playwright timeout"
```

---

## Embedding Backend

Uses **Ollama** by default (local, no API costs):

```bash
ollama pull nomic-embed-text
novelty demo
```

Or use sentence-transformers:
```bash
pip install -e ".[sentence-transformers]"
NOVELTY_EMBEDDING_BACKEND=sentence-transformers novelty demo
```

---

## Configuration

```python
from novelty import Novelty

config = {
    "thresholds": {
        "reuse": 0.45,       # Below → use notebook
        "cache": 0.55,       # Below → use cached reasoning  
        "small_model": 0.70, # Below → ask Anuj
        # Above → ask Deepak
    },
    "models": {
        "small_model": "gpt-4o-mini",    # Anuj (½ cookie)
        "frontier_model": "gpt-4o",       # Deepak (1 cookie)
    },
}

engine = Novelty(config=config)
decision = engine.evaluate("How do I fix this bug?")

print(decision.action)            # "reuse", "small_model", or "frontier_model"
print(decision.recommended_model) # "gpt-4o-mini" or "gpt-4o"
```

---

## API Server

```bash
python -m novelty.api.server

curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{"text": "OAuth token not refreshing"}'
```

Response:
```json
{
  "novelty_score": 0.39,
  "action": "reuse",
  "matched_asset": "oauth-refresh",
  "recommended_model": null,
  "estimated_savings": {"tokens": 1200, "cost_usd": 0.02}
}
```

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                        Novelty                             │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Question → Canonicalize → Score Similarity → Decide       │
│                                                            │
│  Similarity Engines:          Storage:                     │
│    • Keyword (TF-IDF)           • Local YAML (default)     │
│    • Embedding (Ollama)         • PostgreSQL (shared)      │
│    • Intent (rules)                                        │
│                                                            │
│  Decision:                                                 │
│    • REUSE      → notebook    (0 cookies)                  │
│    • SMALL      → Anuj        (½ cookie)                   │
│    • FRONTIER   → Deepak      (1 cookie)                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Why This Matters

| Without Novelty | With Novelty |
|-----------------|--------------|
| Every question → Deepak | Check notebook first |
| 5 questions = 5 cookies | 5 questions = 2 cookies |
| Everyone solves same problems | Answers are shared |
| Slow (always thinking) | Fast (instant lookup) |

**Reasoning becomes a reusable artifact, not a disposable computation.**

---

## License

MIT
