"""GT-59: dark premium theme pass over the #58 redesign.

CSS-only change: the #58 structure (panels, library, conversation,
activity states, mobile order) is untouched; only the visual language
changes. These tests lock the theme tokens and check that body text and
muted text actually meet WCAG contrast against the page background —
readability on dark surfaces is an acceptance criterion, not a vibe.
"""

from __future__ import annotations

import re
from pathlib import Path

import groundtruth.api

STATIC_DIR = Path(groundtruth.api.__file__).parent / "static"


def _css() -> str:
    return (STATIC_DIR / "style.css").read_text(encoding="utf-8")


def _token(css: str, name: str) -> str:
    match = re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{6}})", css)
    assert match, f"missing token --{name}"
    return match.group(1).lower()


def _luminance(hex_color: str) -> float:
    def channel(value: int) -> float:
        s = value / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast_ratio(foreground: str, background: str) -> float:
    light = max(_luminance(foreground), _luminance(background))
    dark = min(_luminance(foreground), _luminance(background))
    return (light + 0.05) / (dark + 0.05)


def test_dark_surfaces_and_gold_accent_tokens():
    """Near-black page, deep charcoal panels, champagne-gold accent."""
    css = _css()
    assert _token(css, "page-bg") == "#0c0e12"
    assert _token(css, "panel-bg") == "#14171f"
    assert _token(css, "panel-bg-raised") == "#1b1f2a"
    assert _token(css, "accent") == "#d4af6a"
    # Gold drives primary actions, progress, and citation chips.
    assert "accent-color: var(--accent)" in css
    assert ".chip" in css and "border: 1px solid var(--accent)" in css
    assert "background: var(--accent)" in css


def test_no_flat_clinical_white_surfaces():
    """The old warm-paper / white-card look must be gone."""
    css = _css()
    for banned in ("#ffffff", "#f6f4ef", "#fbfaf7"):
        assert banned not in css, banned
    assert "#fff" not in css


def test_text_readable_on_dark_surfaces():
    """Body text and muted text meet WCAG AA against the page bg."""
    css = _css()
    page_bg = _token(css, "page-bg")
    text = _token(css, "text")
    muted = _token(css, "muted")
    assert _contrast_ratio(text, page_bg) >= 7.0, (text, page_bg)
    assert _contrast_ratio(muted, page_bg) >= 4.5, (muted, page_bg)


def test_activity_and_status_states_read_on_dark():
    """Upload states and status pills keep distinct dark-safe colors."""
    css = _css()
    for selector in (
        ".activity.activity-done",
        ".activity.activity-alert",
        ".doc-status",
        ".turn-decline",
        ".turn-error",
    ):
        assert selector in css, selector
    assert _token(css, "ok") == "#4ade80"
    assert _token(css, "error-ink") == "#fca5a5"


def test_structure_and_mobile_order_unchanged():
    """The theme pass restructures nothing: same grid areas, same
    single-column mobile order as #58."""
    css = _css()
    assert '"upload conversation"' in css
    assert '"library conversation"' in css
    assert "@media (max-width: 820px)" in css
    assert '"upload"\n      "conversation"\n      "library"' in css
