import hashlib
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from config import ASSET_CACHE_DIR, REQUEST_TIMEOUT_SECONDS, USER_AGENT

LOGGER = logging.getLogger(__name__)


def attach_cached_images(pokemon: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ASSET_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    enriched: list[dict[str, Any]] = []
    for item in pokemon:
        copy = dict(item)
        cached = cached_path_for_name(copy["name"])
        if cached:
            copy["image_path"] = str(cached)
        elif copy.get("image_url"):
            downloaded = download_image(copy["image_url"], copy["name"])
            if downloaded:
                copy["image_path"] = str(downloaded)
        enriched.append(copy)
    return enriched


def cached_path_for_name(name: str) -> Path | None:
    stem = slugify(name)
    for path in ASSET_CACHE_DIR.glob(f"{stem}.*"):
        if path.is_file():
            return path
    return None


def download_image(url: str, name: str) -> Path | None:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            LOGGER.debug("URL ignorada porque no parece imagen: %s (%s)", url, content_type)
            return None
        suffix = suffix_for(url, content_type)
        path = ASSET_CACHE_DIR / f"{slugify(name)}{suffix}"
        path.write_bytes(response.content)
        LOGGER.info("Imagen cacheada para %s desde UniteAPI: %s", name, path)
        return path
    except Exception as exc:
        LOGGER.debug("No se pudo cachear imagen de %s (%s): %s", name, url, exc)
        return None


def suffix_for(url: str, content_type: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return suffix
    mapping = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
    return mapping.get(content_type.split(";")[0].strip(), f".{hashlib.sha1(url.encode()).hexdigest()[:8]}.img")


def slugify(name: str) -> str:
    value = name.lower().replace("♀", "f").replace("♂", "m")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "pokemon"
