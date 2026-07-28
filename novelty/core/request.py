"""Request data structure."""

from dataclasses import dataclass, field


@dataclass
class Request:
    """A normalized request to be evaluated for novelty."""

    text: str
    metadata: dict = field(default_factory=dict)
    canonical_text: str | None = None
    extracted_entities: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.text.strip():
            raise ValueError("Request text cannot be empty")
