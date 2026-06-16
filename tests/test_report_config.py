from report_config import get_report_config


def test_weekly_report_uses_orange_outputs() -> None:
    weekly = get_report_config("weekly")

    assert weekly.kind == "weekly"
    assert "weekly" in weekly.output_discord_image.name
    assert weekly.accent == (255, 132, 36)


def test_monthly_report_is_default() -> None:
    monthly = get_report_config("monthly")

    assert monthly.kind == "monthly"
    assert monthly.output_discord_image.name == "tierlist_pokemon_unite_discord.png"
