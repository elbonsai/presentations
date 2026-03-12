"""Composer — turns research into structured slide content via LLM."""

import json
from dataclasses import dataclass

from .providers import LLMProvider, Message
from .researcher import ResearchResult


@dataclass
class Slide:
    """A single slide definition."""
    slide_type: str  # "title", "content", "stats", "comparison", "quote", "cards", "code", "closing"
    label: str  # small category label above the headline
    headline: str
    body: str  # main text or empty
    items: list[dict]  # cards, stats, bullets — depends on type
    notes: str  # speaker notes


@dataclass
class DeckContent:
    """Complete deck structure ready for rendering."""
    title: str
    subtitle: str
    date: str
    slides: list[Slide]


COMPOSER_SYSTEM_PROMPT = """You are an expert presentation designer creating slide content for a professional "Useful Apple Keynote" style deck.

Given research data, compose a sequence of slides that tell a compelling story.

SLIDE TYPES available:
- "title": Opening slide with hero text. items=[]
- "content": Headline + body text + optional bullet list. items=[{"text": "bullet point"}, ...]
- "cards": 2-4 cards with titles and descriptions. items=[{"title": "...", "body": "...", "accent": "copper|malachite|amethyst|slate"}, ...]
- "stats": Big number statistics (2-4). items=[{"number": "42%", "label": "...", "note": "...", "color": "copper|malachite|amethyst|slate"}, ...]
- "comparison": Before/after or two-column comparison. items=[{"header": "...", "points": ["...", ...]}, {"header": "...", "points": ["...", ...]}]
- "quote": A featured quote or key insight. items=[]
- "code": Code example or technical snippet. items=[{"code": "the code block"}]
- "closing": Final slide with takeaway. items=[]

RULES:
1. Start with a "title" slide.
2. End with a "closing" slide.
3. One concept per slide. Brief text. Let the design do the work.
4. Headlines should be punchy — statements, not descriptions.
5. Body text should be 1-3 sentences max.
6. Card titles should be single words or very short phrases.
7. Vary slide types — don't use the same type consecutively.
8. Statistics should have BIG numbers that look impressive on screen.
9. Write speaker notes for each slide (what to say when presenting).

Return ONLY valid JSON:
{
  "title": "Presentation Title",
  "subtitle": "One-line subtitle",
  "date": "Month Year",
  "slides": [
    {
      "slide_type": "title",
      "label": "Category",
      "headline": "The Big Title",
      "body": "subtitle or tagline",
      "items": [],
      "notes": "Speaker notes for this slide"
    },
    ...more slides...
  ]
}
"""


def compose_deck(
    provider: LLMProvider,
    research: ResearchResult,
    num_slides: int | None = None,
) -> DeckContent:
    """Use the LLM to compose slide content from research."""

    if num_slides:
        count_instruction = f"Create a {num_slides}-slide presentation"
        count_constraint = f"Create exactly {num_slides} slides."
    else:
        count_instruction = "Create a presentation with the ideal number of slides"
        count_constraint = "Choose the right number of slides to cover the content thoroughly without padding."

    user_prompt = f"""{count_instruction} from this research:

RESEARCH DATA:
{json.dumps({
    "topic": research.topic,
    "summary": research.summary,
    "key_points": research.key_points,
    "statistics": research.statistics,
    "quotes": research.quotes,
    "comparisons": research.comparisons,
    "narrative_arc": research.narrative_arc,
    "audience": research.audience,
}, indent=2)}

{count_constraint} Use varied slide types.
The first slide must be type "title" and the last must be type "closing".

Return ONLY the JSON object, no markdown fencing."""

    messages = [
        Message(role="system", content=COMPOSER_SYSTEM_PROMPT),
        Message(role="user", content=user_prompt),
    ]

    raw = provider.chat(messages, temperature=0.5)

    # Clean up potential markdown fencing
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    data = json.loads(raw)

    slides = []
    for s in data["slides"]:
        slides.append(Slide(
            slide_type=s.get("slide_type", "content"),
            label=s.get("label", ""),
            headline=s.get("headline", ""),
            body=s.get("body", ""),
            items=s.get("items", []),
            notes=s.get("notes", ""),
        ))

    return DeckContent(
        title=data.get("title", research.topic),
        subtitle=data.get("subtitle", research.summary),
        date=data.get("date", ""),
        slides=slides,
    )
