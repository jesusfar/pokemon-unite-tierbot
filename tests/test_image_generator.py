from image_generator import generate_tierlist_image


def test_generate_image(tmp_path) -> None:
    output = tmp_path / "tierlist.png"
    item = {"name": "Pikachu", "score": 40.0, "win_rate": 50.0, "pick_rate": 20.0, "ban_rate": 1.0}
    tiers = {"S": [item], "A": [], "B": [], "C": [], "D": []}

    generate_tierlist_image(tiers, output, source_label="test")

    assert output.exists()
    assert output.stat().st_size > 0
