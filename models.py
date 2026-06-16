from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PokemonMeta:
    name: str
    win_rate: float
    pick_rate: float = 0.0
    ban_rate: float = 0.0
    score: float = 0.0
    image_url: str | None = None
    image_path: str | None = None

    @classmethod
    def build(
        cls,
        *,
        name: Any,
        win_rate: Any,
        pick_rate: Any = 0,
        ban_rate: Any = 0,
        image_url: Any = None,
        image_path: Any = None,
    ) -> PokemonMeta | None:
        clean_name = str(name).strip() if name not in (None, "") else ""
        win = parse_percent(win_rate)
        if not clean_name or win is None or not valid_percent(win):
            return None

        pick = parse_percent(pick_rate)
        ban = parse_percent(ban_rate)
        pick = pick if pick is not None and valid_percent(pick) else 0.0
        ban = ban if ban is not None and valid_percent(ban) else 0.0
        score = win * 0.60 + pick * 0.25 + ban * 0.15

        return cls(
            name=clean_name,
            win_rate=round(win, 2),
            pick_rate=round(pick, 2),
            ban_rate=round(ban, 2),
            score=round(score, 2),
            image_url=str(image_url).strip() if image_url else None,
            image_path=str(image_path).strip() if image_path else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FetchResult:
    pokemon: list[dict[str, Any]]
    source: str
    used_fallback: bool = False

    @property
    def source_label(self) -> str:
        labels = {
            "uniteapi-es-requests": "UniteAPI ES",
            "uniteapi-es-playwright": "UniteAPI ES con Playwright",
            "uniteapi-en-requests": "UniteAPI EN",
            "uniteapi-en-playwright": "UniteAPI EN con Playwright",
            "cache": "cache local del último meta válido",
            "sample": "sample_data.json",
        }
        return labels.get(self.source, self.source)


def parse_percent(value: Any) -> float | None:
    import re

    if value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number * 100 if 0 < number <= 1 else number

    text = str(value).strip().replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    return float(match.group(0))


def valid_percent(value: float) -> bool:
    return 0 <= value <= 100
