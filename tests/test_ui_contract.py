from pathlib import Path

WEB = Path(__file__).parents[1] / "nyxnight" / "web"


def test_required_ui_contract() -> None:
    html = (WEB / "index.html").read_text()
    css = (WEB / "styles.css").read_text()
    js = (WEB / "app.js").read_text()
    for name in (
        "city",
        "date",
        "party_size",
        "budget_per_person",
        "vibe",
        "start_time",
        "end_time",
    ):
        assert f'name="{name}"' in html
    assert 'aria-live="polite"' in html
    assert "#000000" in css
    assert "#C15F3C" in css
    assert "prefers-reduced-motion" in css
    assert ":focus-visible" in css
    assert "/api/plan" in js


def test_frontend_has_no_html_parsing_sink_or_external_dependency() -> None:
    source = "\n".join(path.read_text() for path in WEB.iterdir() if path.is_file())
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML"):
        assert sink not in source
    assert "https://" not in source
    assert "http://" not in source
