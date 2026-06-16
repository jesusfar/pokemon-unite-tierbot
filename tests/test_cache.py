from cache_manager import load_latest_valid_meta, save_latest_valid_meta


def test_latest_valid_cache_roundtrip(tmp_path) -> None:
    path = tmp_path / "latest_valid_meta.json"
    pokemon = [
        {"name": f"Pokemon {index}", "win_rate": 50, "pick_rate": 1, "ban_rate": 1, "score": 30.4}
        for index in range(5)
    ]

    save_latest_valid_meta(pokemon, path)

    assert len(load_latest_valid_meta(path)) == 5
