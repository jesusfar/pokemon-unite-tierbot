import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config import LATEST_VALID_META_PATH, MIN_VALID_POKEMON, SAMPLE_DATA_PATH
from utils import load_json, normalize_pokemon

LOGGER = logging.getLogger(__name__)


def save_latest_valid_meta(pokemon: list[dict[str, Any]], path: Path = LATEST_VALID_META_PATH) -> None:
    if len(pokemon) < MIN_VALID_POKEMON:
        LOGGER.warning("No se guarda cache: solo hay %s Pokemon validos.", len(pokemon))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "pokemon": pokemon,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    LOGGER.info("Cache de ultimo meta valido guardado en %s", path)


def load_latest_valid_meta(path: Path = LATEST_VALID_META_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        raw = load_json(path)
        pokemon = normalize_collection(raw.get("pokemon", raw) if isinstance(raw, dict) else raw)
        if len(pokemon) >= MIN_VALID_POKEMON:
            LOGGER.info("Usando cache de ultimo meta valido: %s Pokemon", len(pokemon))
            return pokemon
        LOGGER.warning("Cache local insuficiente: %s Pokemon validos.", len(pokemon))
    except Exception as exc:
        LOGGER.warning("No se pudo leer cache local %s: %s", path, exc)
    return []


def load_sample_data() -> list[dict[str, Any]]:
    raw = load_json(SAMPLE_DATA_PATH)
    pokemon = normalize_collection(raw.get("pokemon", raw) if isinstance(raw, dict) else raw)
    if not pokemon:
        raise RuntimeError("sample_data.json no contiene Pokemon validos con win_rate.")
    LOGGER.info("Datos de muestra cargados: %s Pokemon", len(pokemon))
    return pokemon


def normalize_collection(source: Any) -> list[dict[str, Any]]:
    if not isinstance(source, list):
        return []
    return [item for item in (normalize_pokemon(row) for row in source) if item]
