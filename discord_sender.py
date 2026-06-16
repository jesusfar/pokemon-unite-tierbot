import logging
import os
import time
from pathlib import Path
from typing import Any

import requests

from config import DISCORD_MAX_FILE_BYTES, DISCORD_WEBHOOK_ENV, REQUEST_RETRIES, REQUEST_TIMEOUT_SECONDS
from utils import spanish_date

LOGGER = logging.getLogger(__name__)


def build_discord_message(
    tiers: dict[str, list[dict[str, Any]]] | None = None,
    source_label: str = "UniteAPI Meta",
    used_fallback: bool = False,
    comparison_report: Any | None = None,
) -> str:
    lines = [
        "🔴 Nueva Tier List mensual automática de Pokémon UNITE",
        "📊 Basada en estadísticas del meta: tasa de victoria, uso y baneo.",
        "🌙 Generada automáticamente para STARRY GARDEN.",
        f"📅 Fecha: {spanish_date()}",
        f"🧾 Fuente: {source_label}",
    ]
    if used_fallback:
        lines.append("⚠️ UniteAPI no entregó datos frescos; se usó respaldo disponible.")
    if tiers:
        lines.append("")
        lines.extend(format_tier_summary(tiers))
    if comparison_report:
        lines.append("")
        lines.extend(comparison_report.discord_lines())
    lines.append("")
    lines.append("La tier list es automática y puede variar según disponibilidad de datos.")
    return "\n".join(lines)


def format_tier_summary(tiers: dict[str, list[dict[str, Any]]], max_names: int = 6) -> list[str]:
    summary: list[str] = []
    for tier, pokemon in tiers.items():
        names = [item["name"] for item in pokemon[:max_names]]
        extra = len(pokemon) - len(names)
        suffix = f" +{extra}" if extra > 0 else ""
        summary.append(f"**{tier}:** {', '.join(names) if names else 'Sin datos'}{suffix}")
    return summary


def send_to_discord(
    image_path: Path,
    tiers: dict[str, list[dict[str, Any]]] | None = None,
    source_label: str = "UniteAPI Meta",
    used_fallback: bool = False,
    comparison_report: Any | None = None,
) -> None:
    webhook_url = get_webhook_url()
    if not image_path.exists():
        raise FileNotFoundError(f"No existe la imagen para publicar: {image_path}")
    if image_path.stat().st_size > DISCORD_MAX_FILE_BYTES:
        raise RuntimeError(f"La imagen pesa mas de {DISCORD_MAX_FILE_BYTES} bytes: {image_path.stat().st_size}")

    message = build_discord_message(tiers, source_label, used_fallback, comparison_report)
    LOGGER.info("Publicando tier list en Discord")
    last_error: Exception | None = None
    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            with image_path.open("rb") as image_file:
                response = requests.post(
                    webhook_url,
                    data={"content": message},
                    files={"file": (image_path.name, image_file, "image/png")},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
            if response.status_code == 429:
                retry_after = response.json().get("retry_after", 2)
                LOGGER.warning("Discord aplico rate limit; reintentando en %.1fs", retry_after)
                time.sleep(float(retry_after))
                continue
            response.raise_for_status()
            LOGGER.info("Publicacion completada en Discord")
            return
        except Exception as exc:
            last_error = exc
            if attempt < REQUEST_RETRIES:
                LOGGER.warning("Intento %s/%s de Discord fallo: %s", attempt, REQUEST_RETRIES, exc)
                time.sleep(attempt * 2)
    raise RuntimeError(f"No se pudo publicar en Discord: {last_error}")


def get_webhook_url() -> str:
    webhook_url = os.getenv(DISCORD_WEBHOOK_ENV)
    if not webhook_url:
        raise RuntimeError(f"Falta la variable de entorno {DISCORD_WEBHOOK_ENV}.")
    if not webhook_url.startswith("https://discord.com/api/webhooks/"):
        LOGGER.warning("El webhook no tiene el formato habitual de Discord.")
    return webhook_url
