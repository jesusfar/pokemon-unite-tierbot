import json
import logging
import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from asset_cache import attach_cached_images
from cache_manager import load_latest_valid_meta, load_sample_data, save_latest_valid_meta
from config import (
    META_URL_EN,
    META_URL_ES,
    MIN_VALID_POKEMON,
    REQUEST_BACKOFF_SECONDS,
    REQUEST_RETRIES,
    REQUEST_TIMEOUT_SECONDS,
    USER_AGENT,
)
from models import FetchResult
from utils import dedupe_by_name, flatten_json_candidates, normalize_pokemon

LOGGER = logging.getLogger(__name__)


def fetch_pokemon_meta(no_browser: bool = False) -> list[dict[str, Any]]:
    return fetch_pokemon_meta_result(no_browser=no_browser).pokemon


def fetch_pokemon_meta_result(no_browser: bool = False) -> FetchResult:
    for url, locale in ((META_URL_ES, "es"), (META_URL_EN, "en")):
        try:
            LOGGER.info("Intentando obtener datos desde %s", url)
            html = fetch_with_requests(url)
            pokemon = parse_meta_html(html, url)
            if is_usable_dataset(pokemon):
                LOGGER.info("Datos obtenidos desde UniteAPI con requests: %s Pokemon", len(pokemon))
                save_latest_valid_meta(pokemon)
                return FetchResult(
                    pokemon=attach_cached_images(pokemon),
                    source=f"uniteapi-{locale}-requests",
                    used_fallback=False,
                )
            LOGGER.warning("Requests no produjo suficientes Pokemon desde %s: %s", url, len(pokemon))
        except Exception as exc:
            LOGGER.warning("Fallo requests para %s: %s", url, exc)

        if not no_browser:
            try:
                html = fetch_with_playwright(url)
                pokemon = parse_meta_html(html, url)
                if is_usable_dataset(pokemon):
                    LOGGER.info("Datos obtenidos con Playwright: %s Pokemon", len(pokemon))
                    save_latest_valid_meta(pokemon)
                    return FetchResult(
                        pokemon=attach_cached_images(pokemon),
                        source=f"uniteapi-{locale}-playwright",
                        used_fallback=False,
                    )
                LOGGER.warning("Playwright no produjo suficientes Pokemon desde %s: %s", url, len(pokemon))
            except Exception as exc:
                LOGGER.warning("Fallo Playwright para %s: %s", url, exc)

    cached = load_latest_valid_meta()
    if cached:
        return FetchResult(pokemon=attach_cached_images(cached), source="cache", used_fallback=True)

    LOGGER.warning("Usando sample_data.json como ultimo respaldo.")
    return FetchResult(pokemon=attach_cached_images(load_sample_data()), source="sample", used_fallback=True)


def fetch_with_requests(url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "es,en;q=0.8"},
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            if attempt < REQUEST_RETRIES:
                sleep_for = REQUEST_BACKOFF_SECONDS * attempt
                LOGGER.warning(
                    "Intento %s/%s fallo para %s; reintentando en %.1fs",
                    attempt,
                    REQUEST_RETRIES,
                    url,
                    sleep_for,
                )
                time.sleep(sleep_for)
    raise RuntimeError(f"No se pudo descargar {url}: {last_error}")


def fetch_with_playwright(url: str) -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(url, wait_until="networkidle", timeout=REQUEST_TIMEOUT_SECONDS * 1000)
        html = page.content()
        browser.close()
        return html


def parse_meta_html(html: str, base_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    json_candidates = parse_embedded_json(soup)
    table_candidates = parse_tables(soup, base_url)
    card_candidates = parse_cards(soup, base_url)
    LOGGER.info(
        "Extraccion HTML: json=%s tablas=%s cards=%s",
        len(json_candidates),
        len(table_candidates),
        len(card_candidates),
    )
    return dedupe_by_name(json_candidates + table_candidates + card_candidates)


def parse_embedded_json(soup: BeautifulSoup) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for script in soup.find_all("script"):
        text = script.string or script.get_text(" ", strip=True)
        if not text or ("win" not in text.lower() and "pokemon" not in text.lower()):
            continue

        if script.get("type") == "application/json":
            try:
                candidates.extend(flatten_json_candidates(json.loads(text)))
                continue
            except json.JSONDecodeError:
                pass

        for match in re.finditer(r"(\{[^<>]{30,}\}|\[[^<>]{30,}\])", text):
            snippet = match.group(0)
            try:
                candidates.extend(flatten_json_candidates(json.loads(snippet)))
            except json.JSONDecodeError:
                continue
    return candidates


def parse_tables(soup: BeautifulSoup, base_url: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for table in soup.find_all("table"):
        headers = [cell.get_text(" ", strip=True).lower() for cell in table.find_all("th")]
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            values = [cell.get_text(" ", strip=True) for cell in cells]
            row_data = row_to_data(headers, values)
            image = row.find("img")
            if image and image.get("src"):
                row_data["image_url"] = urljoin(base_url, image["src"])
            normalized = normalize_pokemon(row_data)
            if normalized:
                candidates.append(normalized)
    return candidates


def parse_cards(soup: BeautifulSoup, base_url: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    selectors = ["article", "[class*=card]", "[class*=pokemon]", "[class*=Pokemon]"]
    for element in soup.select(",".join(selectors)):
        text = element.get_text(" ", strip=True)
        if not text or ("win" not in text.lower() and "victoria" not in text.lower()):
            continue

        image = element.find("img")
        row_data = {
            "name": image.get("alt") if image else guess_name(text),
            "win_rate": labeled_percent(text, ("win rate", "victoria", "wr")),
            "pick_rate": labeled_percent(text, ("pick rate", "uso", "pick", "pr")),
            "ban_rate": labeled_percent(text, ("ban rate", "baneo", "ban", "br")),
            "image_url": urljoin(base_url, image["src"]) if image and image.get("src") else None,
        }
        normalized = normalize_pokemon(row_data)
        if normalized:
            candidates.append(normalized)
    return candidates


def row_to_data(headers: list[str], values: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if headers and len(headers) == len(values):
        for header, value in zip(headers, values, strict=True):
            if "pokemon" in header or "pokémon" in header or "name" in header or "nombre" in header:
                data["name"] = value
            elif "win" in header or "victoria" in header:
                data["win_rate"] = value
            elif "pick" in header or "uso" in header:
                data["pick_rate"] = value
            elif "ban" in header or "baneo" in header:
                data["ban_rate"] = value
    else:
        data = {
            "name": values[0],
            "win_rate": values[1] if len(values) > 1 else None,
            "pick_rate": values[2] if len(values) > 2 else 0,
            "ban_rate": values[3] if len(values) > 3 else 0,
        }
    return data


def labeled_percent(text: str, labels: tuple[str, ...]) -> str | None:
    for label in labels:
        pattern = rf"{re.escape(label)}\D*(-?\d+(?:[.,]\d+)?)\s*%"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def guess_name(text: str) -> str | None:
    parts = re.split(r"\s{2,}|Win|Victoria|WR", text, maxsplit=1, flags=re.IGNORECASE)
    return parts[0].strip() if parts and parts[0].strip() else None


def is_usable_dataset(pokemon: list[dict[str, Any]]) -> bool:
    return len(pokemon) >= MIN_VALID_POKEMON
