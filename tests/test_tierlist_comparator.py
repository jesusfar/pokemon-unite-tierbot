from bs4 import BeautifulSoup

from tierlist_comparator import build_report, parse_image_alt_tiers


def test_parse_game8_style_image_alt_tiers() -> None:
    html = """
    <img alt="Image: SS">
    <img alt="Image: Miraidon">
    <img alt="Zacian">
    <img alt="Image: A">
    <img alt="Pikachu">
    """

    tiers = parse_image_alt_tiers(BeautifulSoup(html, "html.parser"), ["Miraidon", "Zacian", "Pikachu"])

    assert tiers["miraidon"] == "S"
    assert tiers["zacian"] == "S"
    assert tiers["pikachu"] == "A"


def test_parse_game8_mega_names_match_base_candidates() -> None:
    html = """
    <img alt="Image: A">
    <img alt="Image: Mega Mewtwo X">
    <img alt="Image: Ho-oh">
    """

    tiers = parse_image_alt_tiers(BeautifulSoup(html, "html.parser"), ["Mewtwo X", "Ho-Oh"])

    assert tiers["mewtwox"] == "A"
    assert tiers["hooh"] == "A"


def test_build_report_flags_large_difference() -> None:
    report = build_report(
        {"pikachu": "D"},
        [
            type("Source", (), {"tiers": {"pikachu": "S"}, "ok": True})(),
        ],
    )

    assert report.warnings
