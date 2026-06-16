from discord_sender import build_discord_message


def test_discord_message_includes_summary_and_source() -> None:
    tiers = {
        "S": [{"name": "Pikachu"}],
        "A": [],
        "B": [],
        "C": [],
        "D": [],
    }

    message = build_discord_message(tiers, source_label="UniteAPI ES", used_fallback=True)

    assert "UniteAPI ES" in message
    assert "**S:** Pikachu" in message
    assert "respaldo" in message
