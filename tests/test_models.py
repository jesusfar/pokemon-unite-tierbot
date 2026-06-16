from models import PokemonMeta


def test_score_and_defaults_are_calculated() -> None:
    pokemon = PokemonMeta.build(name="Pikachu", win_rate="50%", pick_rate=None, ban_rate="10%")

    assert pokemon is not None
    assert pokemon.pick_rate == 0
    assert pokemon.score == 31.5


def test_missing_win_rate_is_excluded() -> None:
    assert PokemonMeta.build(name="Pikachu", win_rate=None) is None


def test_invalid_percent_is_excluded() -> None:
    assert PokemonMeta.build(name="Pikachu", win_rate=140) is None
