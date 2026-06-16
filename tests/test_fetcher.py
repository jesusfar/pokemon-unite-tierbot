from data_fetcher import parse_meta_html


def test_parse_html_table_with_image() -> None:
    html = """
    <table>
      <tr><th>Pokemon</th><th>Win Rate</th><th>Pick Rate</th><th>Ban Rate</th></tr>
      <tr>
        <td><img src="/img/pikachu.png" alt="Pikachu">Pikachu</td>
        <td>51.2%</td><td>10.5%</td><td>3.0%</td>
      </tr>
    </table>
    """

    pokemon = parse_meta_html(html, "https://uniteapi.dev/es/meta")

    assert pokemon[0]["name"] == "Pikachu"
    assert pokemon[0]["win_rate"] == 51.2
    assert pokemon[0]["image_url"] == "https://uniteapi.dev/img/pikachu.png"


def test_parse_embedded_json() -> None:
    html = """
    <script type="application/json">
    {"pokemon":[{"name":"Lucario","winRate":0.52,"pickRate":0.11,"banRate":0.02}]}
    </script>
    """

    pokemon = parse_meta_html(html, "https://uniteapi.dev/es/meta")

    assert pokemon[0]["name"] == "Lucario"
    assert pokemon[0]["win_rate"] == 52
