# Project: Presentations (Deck Generator)

## What This Is
A lightweight CLI tool (`generate-deck`) that generates professional HTML slide decks using LLM-powered research. Built as a simpler alternative to the full Amplifier stack.

## Architecture
The tool runs a 3-phase pipeline: **research → compose → render**

### Package: `deckgen/`
- **providers.py** — LLM abstraction layer. Supports OpenAI, Azure OpenAI (API key + Entra ID token auth), Anthropic, Ollama. `auto_detect_provider()` picks the right one from env vars.
- **researcher.py** — Research agent. Sends topic to LLM, gets back structured JSON (`ResearchResult` dataclass: summary, key_points, statistics, quotes, comparisons, sources, narrative_arc). Temperature 0.4.
- **composer.py** — Slide composition agent. Converts research into slide definitions. 8 slide types: title, content, cards, stats, comparison, quote, code, closing. Temperature 0.5.
- **renderer.py** — HTML renderer. Per-slide-type render functions. Uses `templates/deck_base.html` as shell.
- **cli.py** — Entry point (`generate-deck` command). Loads `.env` automatically. Args: topic (positional), --slides, --audience, --context, --output, --output-dir, --research-only.

### Template: `templates/deck_base.html`
Amplifier-stories-inspired HTML/CSS/JS presentation template. Dark theme (#2C2A28), copper accent (#B87333). Responsive typography with `clamp()`. Vanilla JS navigation (keyboard, click, touch/swipe, nav dots). Progressive enhancement (no-JS fallback).

### Output
Generated decks go to `presentations/` directory as self-contained HTML files.

## Azure OpenAI Configuration
- **Resource**: `elew-openai` in `westus`
- **Model**: `gpt-4o` (version 2024-11-20, GlobalStandard SKU)
- **Endpoint**: `https://elew-openai.openai.azure.com/`
- **Auth**: Entra ID (local API keys disabled). Uses `DefaultAzureCredential` + `get_bearer_token_provider` from `azure-identity`.
- **Subscription**: `de604633-832a-4fc9-98a0-314e89703c5c` ("MCAPS-Hybrid-REQ-75305-2024-elew")
- **RBAC**: "Cognitive Services OpenAI User" + "Cognitive Services OpenAI Contributor" roles assigned to `ericlewallen@microsoft.com` (object ID `a4dbffa7-1ad1-4fde-a1df-369f5ea62616`)

## Environment
- **Python 3.10** on macOS ARM. Use `pip3` not `pip`.
- **`.env`** (gitignored): Contains `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_MODEL`
- **Editable install**: `pip3 install -e ".[all]"` — registers `generate-deck` CLI command
- **Dependencies**: openai, anthropic, azure-identity

## Usage
```bash
generate-deck "Your Topic Here" --slides 8 --audience "developers"
```

## Git
- 2 commits on `main` branch
- `.gitignore` excludes: `.env`, `__pycache__/`, `*.egg-info/`, `dist/`, `build/`

## Also Installed
- **MkDocs 1.6.1**: Scaffolded with `mkdocs new .` — `mkdocs.yml` + `docs/index.md` present but not yet configured for anything specific.
