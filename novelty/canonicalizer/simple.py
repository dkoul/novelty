"""Simple rule-based canonicalizer."""

import re
from novelty.core import Request


TECH_PATTERNS = {
    "playwright": r"\bplaywright\b",
    "selenium": r"\bselenium\b",
    "cypress": r"\bcypress\b",
    "oauth": r"\boauth\b",
    "jwt": r"\bjwt\b",
    "kubernetes": r"\b(kubernetes|k8s)\b",
    "docker": r"\bdocker\b",
    "postgres": r"\b(postgres|postgresql)\b",
    "mysql": r"\bmysql\b",
    "redis": r"\bredis\b",
    "api": r"\bapi\b",
    "rest": r"\brest\b",
    "graphql": r"\bgraphql\b",
    "websocket": r"\bwebsocket\b",
}

ERROR_PATTERNS = {
    "timeout": r"\b(timeout|timed?\s*out|timing\s*out)\b",
    "connection": r"\b(connection|connect)\s*(error|fail|refuse|reset)\b",
    "auth": r"\b(auth|authentication|authorization)\s*(error|fail)\b",
    "crash": r"\b(crash|crashed|crashing)\b",
    "oom": r"\b(oom|out\s*of\s*memory|memory\s*error)\b",
    "rate_limit": r"\b(rate\s*limit|throttl|429)\b",
    "not_found": r"\b(not\s*found|404|missing)\b",
}

INTENT_PATTERNS = {
    "debug": r"\b(debug|fix|solve|error|fail|issue|problem|broken|not\s*working)\b",
    "implement": r"\b(implement|create|build|add|write|develop)\b",
    "explain": r"\b(explain|understand|how|why|what)\b",
    "optimize": r"\b(optimi[zs]e|improve|speed|slow|performance|fast)\b",
    "configure": r"\b(config|setup|set\s*up|install)\b",
}


class SimpleCanonicalizer:
    """Rule-based text canonicalization and entity extraction."""

    def canonicalize(self, request: Request) -> Request:
        text = request.text.lower().strip()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text)

        entities = {
            "technologies": self._extract_matches(text, TECH_PATTERNS),
            "errors": self._extract_matches(text, ERROR_PATTERNS),
            "intent": self._extract_primary_intent(text),
        }

        request.canonical_text = text
        request.extracted_entities = entities
        return request

    def _extract_matches(self, text: str, patterns: dict[str, str]) -> list[str]:
        matches = []
        for name, pattern in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(name)
        return matches

    def _extract_primary_intent(self, text: str) -> str:
        for intent, pattern in INTENT_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return intent
        return "unknown"
