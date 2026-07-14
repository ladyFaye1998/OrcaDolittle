import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
DICTIONARY = (ROOT / "site" / "dictionary.html").read_text(encoding="utf-8")


def _navbar(html: str) -> str:
    match = re.search(r'<nav class="site-nav".*?</nav>', html, flags=re.DOTALL)
    assert match, "shared site navbar is missing"
    return match.group(0)


def test_navbar_markup_is_identical_on_every_page():
    assert _navbar(INDEX) == _navbar(DICTIONARY)


def test_navbar_uses_shared_assets_and_complete_link_set():
    expected = ["work", "gallery", "talk", "field", "limits", "explore", "refs"]
    for html in (INDEX, DICTIONARY):
        assert 'href="assets/site-nav.css"' in html
        assert 'src="assets/site-nav.js"' in html
        assert 'data-page="dictionary"' in _navbar(html)
        for section in expected:
            assert f'data-section="{section}"' in _navbar(html)


def test_dictionary_defers_hidden_panels_and_audio_sources():
    assert "renderTypeBar(); renderFerop();" in DICTIONARY
    assert "renderTypeBar(); renderFerop(); renderLabels(); renderSynthetic();" not in DICTIONARY
    assert re.search(r"<audio controls preload=\"none\" data-src=", DICTIONARY)
    assert not re.search(r"<audio controls preload=\"none\" src=", DICTIONARY)
