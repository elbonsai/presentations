# Presentations

Self-contained HTML slide decks, generated with `deckgen` and hosted on [GitHub Pages](https://elbonsai.github.io/presentations/).

## Decks

| Deck | Link |
|------|------|
| The Blank Canvas Paradox | [View](https://elbonsai.github.io/presentations/the-blank-canvas-paradox/) |

## Setup

Requires **Python 3.10+** on macOS. Install the CLI in editable mode:

```bash
pip3 install -e ".[all]"
```

This registers the `generate-deck` command and installs dependencies for all LLM providers (OpenAI, Anthropic).

### LLM Provider

`deckgen` auto-detects your provider from environment variables. Configure **one** of:

| Provider | Environment Variables |
|----------|----------------------|
| Azure OpenAI (Entra ID) | `AZURE_OPENAI_ENDPOINT` |
| Azure OpenAI (API key) | `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Ollama (local) | Just run `ollama serve` |

Add these to a `.env` file in the repo root (gitignored):

```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_MODEL=gpt-4o
```

## Creating a New Presentation

### 1. Generate the deck

```bash
generate-deck "Your Topic Here" --slides 10 --audience "developers"
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--slides`, `-s` | 10 | Number of slides |
| `--audience`, `-a` | "technical professionals" | Target audience |
| `--context`, `-c` | — | Additional angle or focus |
| `--output`, `-o` | auto-generated | Custom output file path |
| `--output-dir`, `-d` | `presentations/` | Output directory |
| `--research-only` | — | Output research JSON, skip slides |

**Examples:**

```bash
generate-deck "AI Design Patterns" --slides 12 --audience "UX designers"
generate-deck "WebSocket vs SSE" --context "Focus on real-time chat"
generate-deck "RAG Architecture" --research-only   # just get the research JSON
```

### 2. Move into the folder structure

Each deck lives in its own folder with an `index.html` for clean GitHub Pages URLs:

```
your-topic/
  index.html       # the deck
  assets/           # images, if any
    screenshot.png
```

```bash
mkdir -p your-topic/assets
mv presentations/your-topic.html your-topic/index.html
```

### 3. Customize

The generated HTML is a starting point. Common next steps:

- Replace LLM-generated statistics with verified research
- Add screenshots or images to `your-topic/assets/`
- Adjust slide content, order, or types
- Update CSS variables for theming

### 4. Deploy

```bash
git add -A
git commit -m "Add your-topic deck"
git push
```

GitHub Pages deploys automatically. Your deck is live at:

```
https://elbonsai.github.io/presentations/your-topic/
```

## How It Works

`deckgen` runs a 3-phase pipeline:

1. **Research** — Sends the topic to the LLM, returns structured JSON (summary, key points, statistics, quotes, comparisons, sources)
2. **Compose** — Converts research into slide definitions across 8 slide types: title, content, cards, stats, comparison, quote, code, closing
3. **Render** — Generates a self-contained HTML file using the base template (`templates/deck_base.html`)

## Repo Structure

```
├── deckgen/              # Python CLI package
│   ├── cli.py            # Entry point (generate-deck command)
│   ├── providers.py      # LLM abstraction (Azure, OpenAI, Anthropic, Ollama)
│   ├── researcher.py     # Research agent
│   ├── composer.py       # Slide composition agent
│   └── renderer.py       # HTML renderer
├── templates/
│   └── deck_base.html    # HTML/CSS/JS presentation template
├── the-blank-canvas-paradox/   # Example deck
│   ├── index.html
│   └── assets/
└── pyproject.toml        # Package config
```
