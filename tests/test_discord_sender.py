from discord_sender import build_discord_message
from tierlist_comparator import ComparisonReport, ExternalTierList


def test_discord_message_includes_summary_and_source() -> None:
    tiers = {
        "S": [{"name": "Pikachu"}],
        "A": [],
        "B": [],
        "C": [],
        "D": [],
    }

    comparison = ComparisonReport(
        sources=[ExternalTierList("Game8", "https://example.com", {"pikachu": "S"}, ok=True)],
        consensus_top=["Pikachu"],
        warnings=[],
        compared_count=1,
    )

    message = build_discord_message(tiers, source_label="UniteAPI ES", used_fallback=True, comparison_report=comparison)

    assert "UniteAPI ES" in message
    assert "**S:** Pikachu" in message
    assert "respaldo" in message
    assert "Comparación externa" in message
