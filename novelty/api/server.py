"""FastAPI server for Novelty."""

from fastapi import FastAPI
from pydantic import BaseModel
from novelty import Novelty

app = FastAPI(
    title="Novelty API",
    description="The fastest and cheapest LLM call is the one you never make.",
    version="0.1.0",
)

engine = Novelty()


class EvaluateRequest(BaseModel):
    text: str
    metadata: dict | None = None


class SavingsResponse(BaseModel):
    tokens: int
    cost_usd: float


class EvaluateResponse(BaseModel):
    novelty_score: float
    confidence: float
    action: str
    matched_asset: str | None
    explanation: list[str]
    estimated_savings: SavingsResponse | None


@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    """Evaluate a prompt for novelty."""
    decision = engine.evaluate(request.text, request.metadata)

    savings = None
    if decision.estimated_savings:
        savings = SavingsResponse(
            tokens=decision.estimated_savings.get("tokens", 0),
            cost_usd=decision.estimated_savings.get("cost_usd", 0),
        )

    return EvaluateResponse(
        novelty_score=decision.novelty_score,
        confidence=decision.confidence,
        action=decision.action,
        matched_asset=decision.matched_asset,
        explanation=decision.explanation,
        estimated_savings=savings,
    )


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "assets_loaded": len(engine.registry)}


@app.get("/assets")
def list_assets():
    """List all available assets."""
    assets = engine.registry.all()
    return {
        "count": len(assets),
        "assets": [
            {
                "id": a.id,
                "name": a.name,
                "intent": a.intent,
                "tags": a.tags,
            }
            for a in assets
        ],
    }


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
