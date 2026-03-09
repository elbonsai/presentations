"""Research agent — uses LLM to gather and structure content for a topic."""

import json
from dataclasses import dataclass

from .providers import LLMProvider, Message


@dataclass
class ResearchResult:
    """Structured research output."""
    topic: str
    summary: str
    key_points: list[dict]  # [{"title": ..., "detail": ...}, ...]
    statistics: list[dict]  # [{"number": ..., "label": ..., "note": ...}, ...]
    quotes: list[str]
    comparisons: list[dict]  # [{"before": ..., "after": ...}, ...]
    sources: list[str]
    audience: str
    narrative_arc: str  # suggested story flow


RESEARCH_SYSTEM_PROMPT = """You are an expert research analyst preparing content for a professional presentation.

Given a topic and audience, produce thorough, well-structured research.

IMPORTANT: Return ONLY valid JSON with this exact structure:
{
  "topic": "exact topic as given",
  "summary": "2-3 sentence executive summary",
  "key_points": [
    {"title": "Point Title", "detail": "1-2 sentence explanation"},
    ... (6-10 points)
  ],
  "statistics": [
    {"number": "42%", "label": "short label", "note": "optional context"},
    ... (3-6 stats, use real data where possible, clearly mark estimates)
  ],
  "quotes": [
    "Notable quote or insight relevant to the topic",
    ... (1-3 quotes)
  ],
  "comparisons": [
    {"before": "Traditional approach description", "after": "Modern/better approach description"},
    ... (1-3 comparisons if applicable, empty list if not)
  ],
  "sources": [
    "Source description or reference",
    ... (list key sources or knowledge areas used)
  ],
  "audience": "the target audience",
  "narrative_arc": "A 1-2 sentence description of the recommended story flow for the presentation"
}

Guidelines:
- Be factual. Prefer real data. Mark any estimates clearly.
- Tailor depth and vocabulary to the specified audience.
- Think about what would make a compelling presentation, not just an information dump.
- Include contrasts, surprises, and "so what" implications.
- Statistics should be impactful numbers that work visually on slides.
"""


def research_topic(
    provider: LLMProvider,
    topic: str,
    audience: str = "technical professionals",
    additional_context: str = "",
    num_slides: int = 10,
) -> ResearchResult:
    """Use the LLM to research a topic and return structured content."""

    user_prompt = f"""Research this topic for a {num_slides}-slide professional presentation:

Topic: {topic}
Target audience: {audience}
"""
    if additional_context:
        user_prompt += f"\nAdditional context provided by the author:\n{additional_context}\n"

    user_prompt += f"""
The presentation will have approximately {num_slides} slides, so provide enough
content for that — typically 6-10 key points, 3-6 statistics, and 1-3 comparisons.

Return ONLY the JSON object, no markdown fencing, no explanation."""

    messages = [
        Message(role="system", content=RESEARCH_SYSTEM_PROMPT),
        Message(role="user", content=user_prompt),
    ]

    raw = provider.chat(messages, temperature=0.4)

    # Clean up potential markdown fencing
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]  # remove first line
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    data = json.loads(raw)

    return ResearchResult(
        topic=data["topic"],
        summary=data["summary"],
        key_points=data.get("key_points", []),
        statistics=data.get("statistics", []),
        quotes=data.get("quotes", []),
        comparisons=data.get("comparisons", []),
        sources=data.get("sources", []),
        audience=data.get("audience", audience),
        narrative_arc=data.get("narrative_arc", ""),
    )
