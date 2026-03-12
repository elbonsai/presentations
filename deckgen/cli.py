"""CLI for the deck generator."""

import argparse
import os
import sys
import time
from pathlib import Path

from .providers import auto_detect_provider
from .researcher import research_topic
from .researcher import ResearchResult
from .composer import compose_deck
from .renderer import render_deck


def load_dotenv():
    """Load .env file from the project root if it exists."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Don't overwrite existing env vars
            if key and key not in os.environ:
                os.environ[key] = value


def slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    slug = text.lower().strip()
    slug = "".join(c if c.isalnum() or c in (" ", "-") else "" for c in slug)
    slug = "-".join(slug.split())
    return slug[:60] or "presentation"


def main():
    parser = argparse.ArgumentParser(
        prog="generate-deck",
        description="Generate professional HTML presentations from a topic using LLM-powered research.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  generate-deck "Progressive Disclosure in Chat UIs"
  generate-deck "Conversational AI Design Patterns" --slides 12 --audience "UX designers"
  generate-deck "WebSocket vs SSE" --context "Focus on real-time chat applications"
  generate-deck "RAG Architecture" --reference notes.md
  generate-deck "RAG Architecture" --output my-rag-deck.html

Environment variables for LLM providers (set one):
  AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY   (Azure OpenAI)
  OPENAI_API_KEY                                   (OpenAI)
  ANTHROPIC_API_KEY                                (Anthropic)
  Or run: ollama serve                             (Ollama, local)
""",
    )

    parser.add_argument("topic", help="The topic to research and present")
    parser.add_argument(
        "--slides", "-s", type=int, default=None,
        help="Number of slides (omit to let the LLM decide based on content)",
    )
    parser.add_argument(
        "--audience", "-a", default="technical professionals",
        help="Target audience (default: 'technical professionals')",
    )
    parser.add_argument(
        "--context", "-c", default="",
        help="Additional context or angle for the research",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Output file path (default: presentations/<topic-slug>.html)",
    )
    parser.add_argument(
        "--output-dir", "-d", default=".",
        help="Output directory (default: project root)",
    )
    parser.add_argument(
        "--reference", "-r", nargs="+", default=[],
        help="Markdown file(s) to use as reference content for research",
    )
    parser.add_argument(
        "--research-only", action="store_true",
        help="Only perform research, output JSON, skip slide generation",
    )

    args = parser.parse_args()

    # Load .env file
    load_dotenv()

    # Detect LLM provider
    print("Detecting LLM provider...")
    try:
        provider = auto_detect_provider()
    except RuntimeError as e:
        print(f"\n  Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"  Using: {provider.name()}\n")

    # Read reference files and append to context
    context_parts = []
    if args.context:
        context_parts.append(args.context)
    for ref_path in args.reference:
        ref = Path(ref_path)
        if not ref.exists():
            print(f"  Error: reference file not found: {ref_path}", file=sys.stderr)
            sys.exit(1)
        content = ref.read_text()
        context_parts.append(f"--- Reference: {ref.name} ---\n{content}")
        print(f"  Loaded reference: {ref_path} ({len(content)} chars)")
    combined_context = "\n\n".join(context_parts)

    # Phase 1: Research
    print(f"Researching: {args.topic}")
    print(f"  Audience: {args.audience}")
    if args.context:
        print(f"  Context: {args.context}")
    if args.reference:
        print(f"  References: {len(args.reference)} file(s)")
    print()

    t0 = time.time()
    try:
        research = research_topic(
            provider=provider,
            topic=args.topic,
            audience=args.audience,
            additional_context=combined_context,
            num_slides=args.slides,
        )
    except Exception as e:
        print(f"  Research failed: {e}", file=sys.stderr)
        sys.exit(1)

    t_research = time.time() - t0
    print(f"  Research complete ({t_research:.1f}s)")
    print(f"  Found: {len(research.key_points)} key points, {len(research.statistics)} stats, "
          f"{len(research.comparisons)} comparisons")
    print()

    if args.research_only:
        import json
        from dataclasses import asdict
        print(json.dumps(asdict(research), indent=2))
        return

    # Phase 2: Compose slides
    slide_label = f"{args.slides} slides" if args.slides else "slides (auto)"
    print(f"Composing {slide_label}...")
    t1 = time.time()
    try:
        deck = compose_deck(
            provider=provider,
            research=research,
            num_slides=args.slides,
        )
    except Exception as e:
        print(f"  Composition failed: {e}", file=sys.stderr)
        sys.exit(1)

    t_compose = time.time() - t1
    print(f"  Composed {len(deck.slides)} slides ({t_compose:.1f}s)")
    print()

    # Phase 3: Render HTML
    if args.output:
        output_path = Path(args.output)
    else:
        slug = slugify(args.topic)
        output_path = Path(args.output_dir) / slug / "index.html"

    print(f"Rendering presentation...")
    try:
        final_path = render_deck(deck, output_path)
    except Exception as e:
        print(f"  Rendering failed: {e}", file=sys.stderr)
        sys.exit(1)

    total = time.time() - t0
    print(f"  Saved: {final_path}")
    print(f"\nDone in {total:.1f}s — open {final_path} in a browser to view.")


if __name__ == "__main__":
    main()
