"""Renderer — converts DeckContent into a self-contained HTML presentation."""

import html
import os
from pathlib import Path

from .composer import DeckContent, Slide


TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

ACCENT_COLORS = {
    "copper": "c-copper",
    "malachite": "c-malachite",
    "amethyst": "c-amethyst",
    "slate": "c-slate",
}

ACCENT_CARD_CLASSES = {
    "copper": "card-accent",
    "malachite": "card-accent card-accent-m",
    "amethyst": "card-accent card-accent-a",
    "slate": "card-accent card-accent-s",
}

STAT_COLORS = {
    "copper": "var(--copper)",
    "malachite": "var(--malachite)",
    "amethyst": "var(--amethyst)",
    "slate": "var(--slate)",
}


def _esc(text: str) -> str:
    """HTML-escape text."""
    return html.escape(str(text))


def _render_title_slide(slide: Slide) -> str:
    return f'''  <div class="slide active center">
    <div class="label">{_esc(slide.label)}</div>
    <h1 class="hero">{_esc(slide.headline)}</h1>
    <div class="rule"></div>
    <p class="sub narrow">{_esc(slide.body)}</p>
    <div class="spacer-lg"></div>
  </div>'''


def _render_content_slide(slide: Slide) -> str:
    bullets = ""
    if slide.items:
        items_html = "\n".join(
            f'      <li>{_esc(item.get("text", str(item)))}</li>'
            for item in slide.items
        )
        bullets = f'''
    <div class="spacer"></div>
    <ul class="bullet-list narrow">
{items_html}
    </ul>'''

    return f'''  <div class="slide">
    <div class="label">{_esc(slide.label)}</div>
    <h2 class="headline">{_esc(slide.headline)}</h2>
    <p class="body-text narrow">{_esc(slide.body)}</p>{bullets}
  </div>'''


def _render_cards_slide(slide: Slide) -> str:
    num_items = len(slide.items)
    grid_class = "grid-2" if num_items <= 2 else ("grid-3" if num_items <= 3 else "grid-4")

    cards = []
    for item in slide.items:
        accent = item.get("accent", "copper")
        card_cls = ACCENT_CARD_CLASSES.get(accent, "card-accent")
        title_cls = ACCENT_COLORS.get(accent, "c-copper")
        cards.append(f'''      <div class="card {card_cls}">
        <div class="card-title {title_cls}">{_esc(item.get("title", ""))}</div>
        <div class="card-body">{_esc(item.get("body", ""))}</div>
      </div>''')

    cards_html = "\n".join(cards)

    return f'''  <div class="slide">
    <div class="label">{_esc(slide.label)}</div>
    <h2 class="headline">{_esc(slide.headline)}</h2>
    <p class="body-text narrow">{_esc(slide.body)}</p>
    <div class="spacer-lg"></div>
    <div class="{grid_class}">
{cards_html}
    </div>
  </div>'''


def _render_stats_slide(slide: Slide) -> str:
    stats = []
    for item in slide.items:
        color = STAT_COLORS.get(item.get("color", "copper"), "var(--copper)")
        note_html = ""
        if item.get("note"):
            note_html = f'\n        <div class="stat-note">{_esc(item["note"])}</div>'
        stats.append(f'''      <div>
        <div class="stat-number" style="color:{color}">{_esc(item.get("number", ""))}</div>
        <div class="stat-label">{_esc(item.get("label", ""))}</div>{note_html}
      </div>''')

    stats_html = "\n".join(stats)

    return f'''  <div class="slide">
    <div class="label">{_esc(slide.label)}</div>
    <h2 class="headline">{_esc(slide.headline)}</h2>
    <div class="spacer"></div>
    <div class="stat-grid">
{stats_html}
    </div>
  </div>'''


def _render_comparison_slide(slide: Slide) -> str:
    cells = []
    colors = ["c-malachite", "c-copper", "c-amethyst", "c-slate"]
    for i, item in enumerate(slide.items):
        color = colors[i % len(colors)]
        points = "\n".join(
            f'          <li>{_esc(p)}</li>' for p in item.get("points", [])
        )
        cells.append(f'''      <div class="comp-cell">
        <div class="comp-header {color}">{_esc(item.get("header", ""))}</div>
        <ul class="bullet-list">
{points}
        </ul>
      </div>''')

    cells_html = "\n".join(cells)

    return f'''  <div class="slide">
    <div class="label">{_esc(slide.label)}</div>
    <h2 class="headline">{_esc(slide.headline)}</h2>
    <p class="body-text narrow">{_esc(slide.body)}</p>
    <div class="spacer-lg"></div>
    <div class="comparison">
{cells_html}
    </div>
  </div>'''


def _render_quote_slide(slide: Slide) -> str:
    return f'''  <div class="slide center">
    <div class="label">{_esc(slide.label)}</div>
    <div class="rule"></div>
    <div class="spacer"></div>
    <p class="quote narrow">{_esc(slide.headline)}</p>
    <div class="spacer-lg"></div>
    <p class="body-text narrow">{_esc(slide.body)}</p>
  </div>'''


def _render_code_slide(slide: Slide) -> str:
    code_content = ""
    if slide.items:
        code_content = _esc(slide.items[0].get("code", ""))

    return f'''  <div class="slide">
    <div class="label">{_esc(slide.label)}</div>
    <h2 class="headline">{_esc(slide.headline)}</h2>
    <p class="body-text narrow">{_esc(slide.body)}</p>
    <div class="spacer-lg"></div>
    <div class="code">{code_content}</div>
  </div>'''


def _render_closing_slide(slide: Slide) -> str:
    return f'''  <div class="slide center">
    <div class="rule"></div>
    <div class="spacer"></div>
    <p class="quote narrow">{_esc(slide.headline)}</p>
    <div class="spacer-lg"></div>
    <p class="medium c-copper narrow">{_esc(slide.body)}</p>
    <div class="spacer-lg"></div>
  </div>'''


RENDERERS = {
    "title": _render_title_slide,
    "content": _render_content_slide,
    "cards": _render_cards_slide,
    "stats": _render_stats_slide,
    "comparison": _render_comparison_slide,
    "quote": _render_quote_slide,
    "code": _render_code_slide,
    "closing": _render_closing_slide,
}


def render_deck(deck: DeckContent, output_path: str | Path) -> Path:
    """Render a DeckContent into a self-contained HTML file."""

    # Load template
    template_path = TEMPLATE_DIR / "deck_base.html"
    template = template_path.read_text()

    # Render each slide
    slide_htmls = []
    for i, slide in enumerate(deck.slides):
        renderer = RENDERERS.get(slide.slide_type, _render_content_slide)
        slide_html = renderer(slide)
        # Only first slide gets 'active' class (already in title renderer)
        if i > 0:
            slide_html = slide_html.replace('class="slide active', 'class="slide')
        elif i == 0 and 'active' not in slide_html:
            slide_html = slide_html.replace('class="slide', 'class="slide active', 1)
        slide_htmls.append(slide_html)

    slides_combined = "\n\n".join(slide_htmls)

    # Fill template
    final_html = template.replace("{{title}}", _esc(deck.title))
    final_html = final_html.replace("{{slides}}", slides_combined)

    # Write output
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(final_html)

    return output
