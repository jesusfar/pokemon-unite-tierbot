from bs4 import BeautifulSoup

from tierlist_comparator import build_report, parse_image_alt_tiers


def test_parse_game8_style_image_alt_tiers() -> None:
    html = """
    <img alt="SS">
    <img alt="Miraidon">
    <img alt="Zacian">
    <img alt="A">
    <img alt="Pikachu">
    """

    tiers = parse_image_alt_tiers(BeautifulSoup(html, "html.parser"), ["Miraidon", "Zacian", "Pikachu"])

    assert tiers["miraidon"] == "S"
    assert tiers["zacian"] == "S"
    assert tiers["pikachu"] == "A"


def test_build_report_flags_large_difference() -> None:
    report = build_report(
        {"pikachu": "D"},
        [
            type("Source", (), {"tiers": {"pikachu": "S"}, "ok": True})(),
        ],
    )

    assert report.warnings
