from dataclasses import dataclass
from pathlib import Path

from config import OUTPUT_DISCORD_IMAGE, OUTPUT_IMAGE, OUTPUT_WEEKLY_DISCORD_IMAGE, OUTPUT_WEEKLY_IMAGE


@dataclass(frozen=True)
class ReportConfig:
    kind: str
    title: str
    discord_title: str
    description: str
    output_image: Path
    output_discord_image: Path
    accent: tuple[int, int, int]
    accent_dark: tuple[int, int, int]


MONTHLY_REPORT = ReportConfig(
    kind="monthly",
    title="Tier List mensual de Pokémon UNITE",
    discord_title="🔴 Nueva Tier List mensual automática de Pokémon UNITE",
    description="Basada en estadísticas del meta: tasa de victoria, uso y baneo.",
    output_image=OUTPUT_IMAGE,
    output_discord_image=OUTPUT_DISCORD_IMAGE,
    accent=(229, 35, 54),
    accent_dark=(104, 16, 29),
)

WEEKLY_REPORT = ReportConfig(
    kind="weekly",
    title="Pulso semanal de Pokémon UNITE",
    discord_title="🟠 Pulso semanal automático de Pokémon UNITE",
    description="Basado en cambios recientes del meta: tasa de victoria, uso y baneo.",
    output_image=OUTPUT_WEEKLY_IMAGE,
    output_discord_image=OUTPUT_WEEKLY_DISCORD_IMAGE,
    accent=(255, 132, 36),
    accent_dark=(128, 58, 18),
)


def get_report_config(kind: str) -> ReportConfig:
    return WEEKLY_REPORT if kind == "weekly" else MONTHLY_REPORT
