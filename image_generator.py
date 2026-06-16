import logging
import math
from io import BytesIO
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageFont

from config import IMAGE_MARGIN, IMAGE_WIDTH, OUTPUT_IMAGE, REQUEST_TIMEOUT_SECONDS, USER_AGENT
from report_config import MONTHLY_REPORT, ReportConfig
from utils import spanish_date

LOGGER = logging.getLogger(__name__)

BACKGROUND = (13, 13, 17)
PANEL = (26, 27, 34)
PANEL_ALT = (36, 37, 46)
TEXT = (248, 248, 252)
MUTED = (181, 184, 196)
TIER_COLORS = {
    "S": (255, 62, 84),
    "A": (255, 117, 62),
    "B": (255, 196, 73),
    "C": (84, 201, 146),
    "D": (128, 146, 174),
}


def generate_tierlist_image(
    tiers: dict[str, list[dict[str, Any]]],
    output_path: Path = OUTPUT_IMAGE,
    source_label: str = "UniteAPI Meta",
    comparison_report: Any | None = None,
    report_config: ReportConfig | None = None,
) -> None:
    report_config = report_config or MONTHLY_REPORT
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fonts = load_fonts()
    all_pokemon = [item for items in tiers.values() for item in items]
    top_three = sorted(all_pokemon, key=lambda item: item["score"], reverse=True)[:3]
    most_used = max(all_pokemon, key=lambda item: item["pick_rate"], default=None)
    most_banned = max(all_pokemon, key=lambda item: item["ban_rate"], default=None)

    header_height = 430
    footer_height = 92
    row_layouts = [tier_row_layout(items) for items in tiers.values()]
    height = header_height + sum(layout["height"] for layout in row_layouts) + footer_height + IMAGE_MARGIN

    image = Image.new("RGB", (IMAGE_WIDTH, height), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw_background(draw, image.size, report_config)
    draw_header(draw, fonts, source_label, report_config)
    draw_highlights(image, draw, fonts, top_three, most_used, most_banned, report_config)
    draw_comparison_panel(draw, fonts, comparison_report)

    y = header_height
    for (tier_name, pokemon), layout in zip(tiers.items(), row_layouts, strict=True):
        draw_tier_row(image, draw, fonts, tier_name, pokemon, y, layout, report_config)
        y += layout["height"]

    footer = "Score = WR 60% + PR 25% + BR 15%. Datos automaticos; pueden variar segun disponibilidad."
    draw.text((IMAGE_MARGIN, height - 74), footer, font=fonts["tiny"], fill=(132, 136, 149))
    draw_property_notice(draw, fonts, IMAGE_WIDTH - IMAGE_MARGIN, height - 48)
    image.save(output_path, "PNG", optimize=True)
    LOGGER.info("Imagen generada en %s", output_path)


def tier_row_layout(pokemon: list[dict[str, Any]]) -> dict[str, int]:
    left = IMAGE_MARGIN
    right = IMAGE_WIDTH - IMAGE_MARGIN
    tier_width = 122
    card_x = left + tier_width + 20
    card_size = 182
    gap = 14
    per_line = max(1, (right - card_x) // (card_size + gap))
    lines = max(1, math.ceil(len(pokemon) / per_line))
    return {
        "height": 30 + lines * 222 + 18,
        "per_line": per_line,
        "card_size": card_size,
        "gap": gap,
        "tier_width": tier_width,
    }


def draw_background(draw: ImageDraw.ImageDraw, size: tuple[int, int], report_config: ReportConfig) -> None:
    width, height = size
    draw.rectangle((0, 0, width, height), fill=BACKGROUND)
    draw.rectangle((0, 0, width, 16), fill=report_config.accent)
    for offset, color in ((0, report_config.accent_dark), (18, (55, 26, 18)), (42, (24, 24, 31))):
        draw.line((0, 102 + offset, width, 22 + offset), fill=color, width=3)
    draw.rectangle((0, 0, width, height), outline=(42, 42, 52), width=2)


def draw_header(
    draw: ImageDraw.ImageDraw,
    fonts: dict[str, ImageFont.FreeTypeFont],
    source_label: str,
    report_config: ReportConfig,
) -> None:
    draw.text((IMAGE_MARGIN, 50), report_config.title, font=fonts["title"], fill=TEXT)
    draw.text((IMAGE_MARGIN, 118), "STARRY GARDEN", font=fonts["subtitle"], fill=MUTED)

    date_text = spanish_date().upper()
    draw_pill(
        draw,
        IMAGE_WIDTH - IMAGE_MARGIN - 260,
        58,
        260,
        48,
        date_text,
        fonts["small"],
        report_config.accent,
        report_config.accent,
    )
    draw_pill(
        draw,
        IMAGE_MARGIN,
        168,
        310,
        42,
        "Score = WR 60 + PR 25 + BR 15",
        fonts["tiny"],
        report_config.accent_dark,
        report_config.accent,
    )
    draw_pill(
        draw,
        IMAGE_MARGIN + 324,
        168,
        260,
        42,
        f"Fuente: {source_label}",
        fonts["tiny"],
        (54, 55, 68),
        report_config.accent,
    )


def draw_highlights(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: dict[str, ImageFont.FreeTypeFont],
    top_three: list[dict[str, Any]],
    most_used: dict[str, Any] | None,
    most_banned: dict[str, Any] | None,
    report_config: ReportConfig,
) -> None:
    y = 222
    draw.text((IMAGE_MARGIN, y + 16), "Top 3", font=fonts["section"], fill=TEXT)
    x = IMAGE_MARGIN + 124
    for index, item in enumerate(top_three, start=1):
        draw_mini_highlight(canvas, draw, fonts, item, x, y, index, report_config)
        x += 238

    chip_x = IMAGE_WIDTH - IMAGE_MARGIN - 410
    if most_used:
        draw_stat_chip(draw, chip_x, y + 10, "Mas usado", most_used["name"], f"{most_used['pick_rate']:.1f}% PR", fonts)
    if most_banned:
        draw_stat_chip(
            draw,
            chip_x,
            y + 70,
            "Mas baneado",
            most_banned["name"],
            f"{most_banned['ban_rate']:.1f}% BR",
            fonts,
        )


def draw_comparison_panel(
    draw: ImageDraw.ImageDraw,
    fonts: dict[str, ImageFont.FreeTypeFont],
    comparison_report: Any | None,
) -> None:
    y = 334
    left = IMAGE_MARGIN
    right = IMAGE_WIDTH - IMAGE_MARGIN
    draw.rounded_rectangle((left, y, right, y + 58), radius=8, fill=(24, 25, 32), outline=(64, 65, 78), width=1)
    if not comparison_report:
        text = "Comparacion externa: no ejecutada"
        detail = "Se publica usando datos del meta calculado."
    else:
        text = f"Comparacion externa: {comparison_report.short_status()}"
        if comparison_report.consensus_top:
            detail = "Consenso alto: " + ", ".join(comparison_report.consensus_top[:6])
        elif comparison_report.warnings:
            detail = "Diferencias: " + "; ".join(comparison_report.warnings[:2])
        else:
            detail = "Sin diferencias fuertes detectadas entre fuentes disponibles."
    draw.text(
        (left + 18, y + 10),
        fit_text(draw, text, fonts["tiny_bold"], right - left - 36),
        font=fonts["tiny_bold"],
        fill=TEXT,
    )
    draw.text(
        (left + 18, y + 34),
        fit_text(draw, detail, fonts["tiny"], right - left - 36),
        font=fonts["tiny"],
        fill=MUTED,
    )


def draw_mini_highlight(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: dict[str, ImageFont.FreeTypeFont],
    item: dict[str, Any],
    x: int,
    y: int,
    rank: int,
    report_config: ReportConfig,
) -> None:
    draw.rounded_rectangle((x, y, x + 220, y + 94), radius=8, fill=PANEL, outline=(67, 68, 80), width=1)
    draw.text((x + 14, y + 13), f"#{rank}", font=fonts["rank"], fill=report_config.accent)
    sprite = load_sprite(item)
    if sprite:
        sprite.thumbnail((62, 62), Image.Resampling.LANCZOS)
        canvas.paste(sprite, (x + 54, y + 16), sprite if sprite.mode == "RGBA" else None)
    else:
        draw_placeholder(draw, x + 58, y + 18, 54, report_config)
    name = fit_text(draw, item["name"], fonts["tiny_bold"], 94)
    draw.text((x + 126, y + 18), name, font=fonts["tiny_bold"], fill=TEXT)
    draw.text((x + 126, y + 51), f"{item['score']:.1f}", font=fonts["score"], fill=(255, 218, 224))


def draw_stat_chip(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    name: str,
    value: str,
    fonts: dict[str, ImageFont.FreeTypeFont],
) -> None:
    draw.rounded_rectangle((x, y, x + 410, y + 48), radius=8, fill=(34, 35, 44), outline=(64, 65, 78), width=1)
    draw.text((x + 16, y + 8), label.upper(), font=fonts["micro"], fill=MUTED)
    draw.text((x + 120, y + 10), fit_text(draw, name, fonts["tiny_bold"], 168), font=fonts["tiny_bold"], fill=TEXT)
    draw.text((x + 310, y + 10), value, font=fonts["tiny_bold"], fill=(255, 210, 216))


def draw_tier_row(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: dict[str, ImageFont.FreeTypeFont],
    tier_name: str,
    pokemon: list[dict[str, Any]],
    y: int,
    layout: dict[str, int],
    report_config: ReportConfig,
) -> None:
    left = IMAGE_MARGIN
    right = IMAGE_WIDTH - IMAGE_MARGIN
    tier_width = layout["tier_width"]
    row_bottom = y + layout["height"] - 18

    draw.rounded_rectangle((left, y, right, row_bottom), radius=8, fill=PANEL, outline=(50, 51, 62), width=2)
    draw.rounded_rectangle((left, y, left + tier_width, row_bottom), radius=8, fill=TIER_COLORS[tier_name])
    tier_bbox = draw.textbbox((0, 0), tier_name, font=fonts["tier"])
    draw.text(
        (left + (tier_width - (tier_bbox[2] - tier_bbox[0])) / 2, y + (row_bottom - y - 84) / 2),
        tier_name,
        font=fonts["tier"],
        fill=(20, 20, 24),
    )

    card_x = left + tier_width + 20
    card_y = y + 15
    card_size = layout["card_size"]
    gap = layout["gap"]
    per_line = layout["per_line"]

    for index, item in enumerate(pokemon):
        col = index % per_line
        line = index // per_line
        x = card_x + col * (card_size + gap)
        item_y = card_y + line * 222
        draw_pokemon_card(canvas, draw, fonts, item, x, item_y, card_size, report_config)


def draw_pokemon_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: dict[str, ImageFont.FreeTypeFont],
    item: dict[str, Any],
    x: int,
    y: int,
    size: int,
    report_config: ReportConfig,
) -> None:
    draw.rounded_rectangle((x, y, x + size, y + 202), radius=8, fill=PANEL_ALT, outline=(64, 65, 78), width=1)
    sprite = load_sprite(item)
    if sprite:
        sprite.thumbnail((118, 118), Image.Resampling.LANCZOS)
        px = x + (size - sprite.width) // 2
        canvas.paste(sprite, (px, y + 14), sprite if sprite.mode == "RGBA" else None)
    else:
        draw_placeholder(draw, x + 35, y + 18, 112, report_config)

    name = fit_text(draw, item["name"], fonts["name"], size - 16)
    name_bbox = draw.textbbox((0, 0), name, font=fonts["name"])
    draw.text((x + (size - (name_bbox[2] - name_bbox[0])) / 2, y + 133), name, font=fonts["name"], fill=TEXT)

    score = f"{item['score']:.1f}"
    score_bbox = draw.textbbox((0, 0), score, font=fonts["score"])
    draw.rounded_rectangle((x + 48, y + 164, x + size - 48, y + 192), radius=7, fill=(51, 18, 26))
    draw.text(
        (x + (size - (score_bbox[2] - score_bbox[0])) / 2, y + 163),
        score,
        font=fonts["score"],
        fill=(255, 218, 224),
    )


def draw_pill(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    width: int,
    height: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
) -> None:
    draw.rounded_rectangle((x, y, x + width, y + height), radius=8, fill=fill, outline=outline, width=1)
    text = fit_text(draw, text, font, width - 24)
    box = draw.textbbox((0, 0), text, font=font)
    draw.text(
        (x + (width - (box[2] - box[0])) / 2, y + (height - (box[3] - box[1])) / 2 - 2),
        text,
        font=font,
        fill=TEXT,
    )


def draw_property_notice(
    draw: ImageDraw.ImageDraw,
    fonts: dict[str, ImageFont.FreeTypeFont],
    right: int,
    y: int,
) -> None:
    chunks = [
        ("Propiedad de ", fonts["property"]),
        ("🌙 ", fonts["property_emoji"]),
        ("𝑺𝑻𝑨𝑹𝑹𝒀 𝑮𝑨𝑹𝑫𝑬𝑵", fonts["property"]),
        (" ✦", fonts["property_symbol"]),
    ]
    total_width = sum(draw.textlength(text, font=font) for text, font in chunks)
    x = right - total_width
    for text, font in chunks:
        draw.text((x, y), text, font=font, fill=(224, 190, 203))
        x += draw.textlength(text, font=font)


def draw_placeholder(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    size: int,
    report_config: ReportConfig,
) -> None:
    draw.rounded_rectangle(
        (x, y, x + size, y + size),
        radius=14,
        fill=(29, 30, 39),
        outline=report_config.accent_dark,
        width=3,
    )
    inset = max(8, int(size * 0.27))
    line_inset = max(6, int(size * 0.20))
    line_width = max(2, int(size * 0.045))
    draw.ellipse(
        (x + inset, y + inset, x + size - inset, y + size - inset),
        outline=report_config.accent,
        width=line_width,
    )
    draw.line(
        (x + line_inset, y + size // 2, x + size - line_inset, y + size // 2),
        fill=report_config.accent,
        width=line_width,
    )


def load_sprite(item: dict[str, Any]) -> Image.Image | None:
    image_path = item.get("image_path")
    if image_path:
        try:
            return Image.open(Path(image_path)).convert("RGBA")
        except Exception as exc:
            LOGGER.debug("No se pudo abrir imagen cacheada %s: %s", image_path, exc)

    url = item.get("image_url")
    if not url:
        return None
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as exc:
        LOGGER.debug("No se pudo cargar imagen %s: %s", url, exc)
        return None


def fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    trimmed = text
    while trimmed and draw.textlength(trimmed + "...", font=font) > max_width:
        trimmed = trimmed[:-1]
    return trimmed + "..." if trimmed else text[:1]


def load_fonts() -> dict[str, ImageFont.FreeTypeFont]:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        paths = candidates if bold else list(reversed(candidates))
        for path in paths:
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
        return ImageFont.load_default(size=size)

    def property_font(size: int) -> ImageFont.FreeTypeFont:
        for path in (
            "C:/Windows/Fonts/cambria.ttc",
            "C:/Windows/Fonts/seguisym.ttf",
            "C:/Windows/Fonts/seguiemj.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
        return font(size, True)

    def font_from(paths: tuple[str, ...], size: int) -> ImageFont.FreeTypeFont:
        for path in paths:
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
        return font(size, True)

    return {
        "title": font(52, True),
        "subtitle": font(26),
        "section": font(30, True),
        "tier": font(80, True),
        "rank": font(26, True),
        "name": font(22, True),
        "small": font(20, True),
        "score": font(22, True),
        "tiny": font(15),
        "tiny_bold": font(15, True),
        "micro": font(11, True),
        "property": property_font(18),
        "property_emoji": font_from(("C:/Windows/Fonts/seguiemj.ttf", "C:/Windows/Fonts/seguisym.ttf"), 18),
        "property_symbol": font_from(("C:/Windows/Fonts/seguisym.ttf", "C:/Windows/Fonts/cambria.ttc"), 18),
    }
