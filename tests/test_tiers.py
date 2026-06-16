from utils import assign_tiers


def test_assign_tiers_keeps_all_pokemon() -> None:
    pokemon = [
        {"name": f"Pokemon {index}", "score": float(index), "win_rate": 50, "pick_rate": 0, "ban_rate": 0}
        for index in range(20)
    ]

    tiers = assign_tiers(pokemon)

    assert [len(tiers[tier]) for tier in ("S", "A", "B", "C", "D")] == [3, 4, 6, 4, 3]
    assert sum(len(items) for items in tiers.values()) == 20
    assert tiers["S"][0]["name"] == "Pokemon 19"
