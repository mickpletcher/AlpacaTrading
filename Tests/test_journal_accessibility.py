"""Credential-free structural checks; these do not certify WCAG conformance."""
from html.parser import HTMLParser
from pathlib import Path
import re

HTML = Path(__file__).resolve().parents[1] / "Journal" / "journal.html"


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def elements():
    parser = Elements()
    parser.feed(HTML.read_text(encoding="utf-8").split("<script>")[0])
    return parser.elements


def test_journal_controls_have_visible_associated_labels():
    nodes = elements()
    labels = {a.get("for") for tag, a in nodes if tag == "label"}
    controls = [a for tag, a in nodes if tag in {"input", "select", "textarea"}]
    assert len(controls) == 14
    assert all(a.get("id") in labels for a in controls)
    assert all("required" in a for a in controls if a.get("id") in {"f-date", "f-ticker", "f-qty", "f-entry"})


def test_journal_landmarks_tabs_and_feedback():
    nodes = elements()
    assert sum(tag == "main" for tag, _ in nodes) == 1
    assert sum(tag == "h1" for tag, _ in nodes) == 1
    assert any(tag == "a" and a.get("href") == "#main-content" for tag, a in nodes)
    tabs = [a for _, a in nodes if a.get("role") == "tab"]
    panels = {a["id"]: a for _, a in nodes if a.get("role") == "tabpanel"}
    assert len(tabs) == len(panels) == 4
    assert sum(a["tabindex"] == "0" for a in tabs) == 1
    for tab in tabs:
        panel = panels[tab["aria-controls"]]
        assert panel["aria-labelledby"] == tab["id"]
        assert ("hidden" not in panel) == (tab["aria-selected"] == "true")
    assert any(a.get("role") == "status" and a.get("aria-live") == "polite" and a.get("aria-atomic") == "true" for _, a in nodes)


def test_journal_tables_and_motion():
    nodes = elements()
    assert all(a.get("scope") == "col" for tag, a in nodes if tag == "th")
    text = HTML.read_text(encoding="utf-8")
    assert 'class="scanline"' not in text
    assert "prefers-reduced-motion:reduce" in text
    assert ":focus-visible" in text
    assert 'aria-label="Delete ${escapeText(t.ticker)} trade from ${escapeText(t.date)}"' in text
    for key in ["ArrowLeft", "ArrowRight", "Home", "End"]:
        assert f'e.key === "{key}"' in text


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def test_journal_palette_contrast():
    colors = dict(re.findall(r"--(bg|panel|border|accent|green|red|yellow|text|muted):\s*(#[0-9a-f]{6})", HTML.read_text(encoding="utf-8")))
    for background in ["bg", "panel"]:
        for foreground in ["accent", "green", "red", "yellow", "text", "muted", "border"]:
            bright, dark = sorted([luminance(colors[foreground]), luminance(colors[background])], reverse=True)
            assert (bright + 0.05) / (dark + 0.05) >= (3 if foreground == "border" else 4.5), (foreground, background)
