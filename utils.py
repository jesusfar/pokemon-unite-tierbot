import json
import logging
import math
from datetime import date
from pathlib import Path
from typing import Any

from config import TIER_PERCENTAGES
from models import PokemonMeta

SPANISH_MONTHS = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


def setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def spanish_date(value: date | None = None) -> str:
    value = value or date.today()
    return f"{value.day:02d}/{value.month:02d}/{value.year}"


def normalize_pokemon(raw: dict[str, Any]) -> dict[str, Any] | None:
    name = first_present(raw, "name", "pokemon", "pokemon_name", "displayName", "label")
    image_url = first_present(raw, "image", "image_url", "imageUrl", "icon", "icon_url", "sprite", "src")
    pokemon = PokemonMeta.build(
        name=name,
        win_rate=first_present(raw, "win_rate", "winRate", "wr", "win", "wins"),
        pick_rate=first_present(raw, "pick_rate", "pickRate", "pr", "pick", "use_rate", "usageRate"),
        ban_rate=first_present(raw, "ban_rate", "banRate", "br", "ban"),
        image_url=image_url,
        image_path=first_present(raw, "image_path", "imagePath", "local_image"),
    )
    return pokemon.to_dict() if pokemon else None


def first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    lower_map = {str(key).lower(): value for key, value in data.items()}
    for key in keys:
        value = lower_map.get(key.lower())
        if value not in (None, ""):
            return value
    return None


def dedupe_by_name(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_name: dict[str, dict[str, Any]] = {}
    for item in items:
        key = item["name"].casefold()
        if key not in best_by_name or item["score"] > best_by_name[key]["score"]:
            best_by_name[key] = item
    return list(best_by_name.values())


def assign_tiers(pokemon: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    ranked = sorted(pokemon, key=lambda item: item["score"], reverse=True)
    total = len(ranked)
    tiers = {tier: [] for tier in TIER_PERCENTAGES}
    if total == 0:
        return tiers

    raw_counts = {tier: total * pct for tier, pct in TIER_PERCENTAGES.items()}
    counts = {tier: int(math.floor(value)) for tier, value in raw_counts.items()}
    missing = total - sum(counts.values())
    for tier in sorted(raw_counts, key=lambda key: raw_counts[key] - counts[key], reverse=True):
        if missing <= 0:
            break
        counts[tier] += 1
        missing -= 1

    index = 0
    for tier, count in counts.items():
        tiers[tier] = ranked[index : index + count]
        index += count
    return tiers


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def flatten_json_candidates(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        normalized = normalize_pokemon(value)
        if normalized:
            found.append(normalized)
        for child in value.values():
            found.extend(flatten_json_candidates(child))
    elif isinstance(value, list):
        for item in value:
            found.extend(flatten_json_candidates(item))
    return found
