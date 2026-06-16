import logging
import re
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup

from config import GAME8_TIER_LIST_URL, REQUEST_TIMEOUT_SECONDS, UNITE_DB_TIER_LIST_URL, USER_AGENT

LOGGER = logging.getLogger(__name__)

TIER_ORDER = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
EXTERNAL_TIER_MAP = {
    "op": "S",
    "ss": "S",
    "s+": "S",
    "s": "S",
    "a": "A",
    "b": "B",
    "c": "C",
    "d": "D",
}


@dataclass(frozen=True)
class ExternalTierList:
    name: str
    url: str
    tiers: dict[str, str]
    ok: bool
    error: str | None = None


@dataclass(frozen=True)
class ComparisonReport:
    sources: list[ExternalTierList]
    consensus_top: list[str]
    warnings: list[str]
    compared_count: int

    @property
    def available_sources(self) -> list[ExternalTierList]:
        return [source for source in self.sources if source.ok and source.tiers]

    def short_status(self) -> str:
        if not self.sources:
            return "Comparacion externa no ejecutada"
        parts = []
        for source in self.sources:
            status = f"{len(source.tiers)} Pokemon" if source.ok else "no disponible"
            parts.append(f"{source.name}: {status}")
        return " | ".join(parts)

    def discord_lines(self) -> list[str]:
        lines = [f"🔎 Comparación externa: {self.short_status()}"]
        if self.consensus_top:
            lines.append(f"✅ Consenso alto: {', '.join(self.consensus_top[:6])}")
        if self.warnings:
            lines.append(f"⚖️ Diferencias a revisar: {'; '.join(self.warnings[:3])}")
        return lines


def compare_with_external_sources(
    tiers: dict[str, list[dict[str, Any]]],
    no_browser: bool = False,
) -> ComparisonReport:
    our_tiers = flatten_own_tiers(tiers)
    candidate_names = list(our_tiers)
    sources = [
        fetch_game8_tier_list(candidate_names),
        fetch_unite_db_tier_list(candidate_names, no_browser=no_browser),
    ]
    return build_report(our_tiers, sources)


def flatten_own_tiers(tiers: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    own: dict[str, str] = {}
    for tier, pokemon in tiers.items():
        for item in pokemon:
            own[canonical_name(item["name"])] = tier
    return own


def build_report(our_tiers: dict[str, str], sources: list[ExternalTierList]) -> ComparisonReport:
    consensus_top: list[str] = []
    warnings: list[str] = []
    compared_count = 0

    for canonical, our_tier in our_tiers.items():
        external_tiers = [source.tiers[canonical] for source in sources if canonical in source.tiers]
        if not external_tiers:
            continue
        compared_count += 1
        top_votes = sum(1 for tier in external_tiers if tier in {"S", "A"})
        if our_tier in {"S", "A"} and top_votes >= max(1, len(external_tiers) // 2):
            consensus_top.append(display_name(canonical))

        avg_external = sum(TIER_ORDER[tier] for tier in external_tiers) / len(external_tiers)
        delta = TIER_ORDER[our_tier] - avg_external
        if abs(delta) >= 2:
            direction = "mas alto" if delta > 0 else "mas bajo"
            warnings.append(f"{display_name(canonical)} {direction} que fuentes externas")

    return ComparisonReport(
        sources=sources,
        consensus_top=consensus_top[:8],
        warnings=warnings[:5],
        compared_count=compared_count,
    )


def fetch_game8_tier_list(candidate_names: list[str]) -> ExternalTierList:
    try:
        html = fetch_html(GAME8_TIER_LIST_URL)
        soup = BeautifulSoup(html, "html.parser")
        tiers = parse_image_alt_tiers(soup, candidate_names)
        return ExternalTierList(
            "Game8",
            GAME8_TIER_LIST_URL,
            tiers,
            ok=bool(tiers),
            error=None if tiers else "sin datos",
        )
    except Exception as exc:
        LOGGER.warning("No se pudo comparar con Game8: %s", exc)
        return ExternalTierList("Game8", GAME8_TIER_LIST_URL, {}, ok=False, error=str(exc))


def fetch_unite_db_tier_list(candidate_names: list[str], no_browser: bool = False) -> ExternalTierList:
    try:
        html = fetch_html(UNITE_DB_TIER_LIST_URL)
        tiers = parse_textual_tiers(BeautifulSoup(html, "html.parser"), candidate_names)
        if not tiers and not no_browser:
            html = fetch_rendered_html(UNITE_DB_TIER_LIST_URL)
            tiers = parse_textual_tiers(BeautifulSoup(html, "html.parser"), candidate_names)
        return ExternalTierList(
            "Unite-DB",
            UNITE_DB_TIER_LIST_URL,
            tiers,
            ok=bool(tiers),
            error=None if tiers else "sin datos",
        )
    except Exception as exc:
        LOGGER.warning("No se pudo comparar con Unite-DB: %s", exc)
        return ExternalTierList("Unite-DB", UNITE_DB_TIER_LIST_URL, {}, ok=False, error=str(exc))


def fetch_html(url: str) -> str:
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.text


def fetch_rendered_html(url: str) -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(url, wait_until="networkidle", timeout=REQUEST_TIMEOUT_SECONDS * 1000)
        html = page.content()
        browser.close()
        return html


def parse_image_alt_tiers(soup: BeautifulSoup, candidate_names: list[str]) -> dict[str, str]:
    candidates = {canonical_name(name) for name in candidate_names}
    tiers: dict[str, str] = {}
    current_tier: str | None = None

    for image in soup.find_all("img"):
        alt = image.get("alt", "").strip()
        tier = tier_from_text(alt)
        if tier:
            current_tier = tier
            continue
        if not current_tier:
            continue
        canonical = canonical_name(alt)
        if canonical in candidates:
            tiers[canonical] = current_tier
    return tiers


def parse_textual_tiers(soup: BeautifulSoup, candidate_names: list[str]) -> dict[str, str]:
    text = soup.get_text(" ", strip=True)
    candidates = {canonical_name(name): name for name in candidate_names}
    tiers: dict[str, str] = {}
    for canonical, original in candidates.items():
        match = re.search(rf"\b{re.escape(original)}\b.{0,80}?\b(OP|SS|S\+|S|A|B|C|D)\b", text, re.IGNORECASE)
        if match:
            tiers[canonical] = EXTERNAL_TIER_MAP[match.group(1).lower()]
    return tiers


def tier_from_text(text: str) -> str | None:
    clean = text.lower().replace("rank", "").replace("tier", "").replace("icon", "").strip()
    clean = re.sub(r"[^a-z+]", "", clean)
    return EXTERNAL_TIER_MAP.get(clean)


def canonical_name(name: str) -> str:
    value = name.lower()
    value = value.replace("mega ", "").replace("alolan ", "").replace("galarian ", "")
    value = value.replace("mewtwo x", "mewtwo x").replace("mewtwo y", "mewtwo y")
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def display_name(canonical: str) -> str:
    special = {
        "mewtwox": "Mewtwo X",
        "mewtwoy": "Mewtwo Y",
        "hooh": "Ho-Oh",
        "mrmime": "Mr. Mime",
    }
    if canonical in special:
        return special[canonical]
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", canonical).title()
