import argparse
import logging

from data_fetcher import fetch_pokemon_meta_result
from discord_sender import get_webhook_url, send_to_discord
from image_generator import generate_tierlist_image
from report_config import get_report_config
from tierlist_comparator import compare_with_external_sources
from utils import assign_tiers, setup_logging

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera y publica una tier list mensual de Pokemon UNITE.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Genera la imagen sin publicar en Discord.")
    mode.add_argument("--send", action="store_true", help="Genera la imagen y la publica en Discord.")
    mode.add_argument("--image-only", action="store_true", help="Alias explicito de --dry-run.")
    mode.add_argument("--message-only", action="store_true", help="Publica en Discord una imagen ya generada.")
    report = parser.add_mutually_exclusive_group()
    report.add_argument("--monthly", action="store_true", help="Genera la tier list mensual roja.")
    report.add_argument("--weekly", action="store_true", help="Genera el pulso semanal naranja.")
    parser.add_argument("--no-browser", action="store_true", help="No usa Playwright; intenta solo con requests.")
    parser.add_argument("--verbose", action="store_true", help="Muestra logs de depuracion.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)
    report_config = get_report_config("weekly" if args.weekly else "monthly")

    should_send = args.send or args.message_only
    if should_send:
        get_webhook_url()

    if not any((args.dry_run, args.send, args.image_only, args.message_only)):
        LOGGER.info("No se indico modo; se usara --dry-run por seguridad.")

    try:
        if not args.message_only:
            result = fetch_pokemon_meta_result(no_browser=args.no_browser, fast_fail=args.weekly)
            tiers = assign_tiers(result.pokemon)
            comparison_report = compare_with_external_sources(tiers, no_browser=args.no_browser)
            generate_tierlist_image(
                tiers,
                report_config.output_image,
                source_label=result.source_label,
                comparison_report=comparison_report,
                report_config=report_config,
            )
            generate_tierlist_image(
                tiers,
                report_config.output_discord_image,
                source_label=result.source_label,
                comparison_report=comparison_report,
                report_config=report_config,
            )
        else:
            tiers = None
            result = None
            comparison_report = None

        if should_send:
            send_to_discord(
                report_config.output_discord_image,
                tiers=tiers,
                source_label=result.source_label if result else "imagen generada previamente",
                used_fallback=result.used_fallback if result else False,
                comparison_report=comparison_report,
                report_config=report_config,
            )
        else:
            LOGGER.info("Dry run completado; no se publico en Discord.")
        return 0
    except Exception as exc:
        LOGGER.exception("No se pudo completar la tier list: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
