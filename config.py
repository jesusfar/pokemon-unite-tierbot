from pathlib import Path

PROJECT_NAME = "pokemon-unite-tierbot"

META_URL_ES = "https://uniteapi.dev/es/meta"
META_URL_EN = "https://uniteapi.dev/en/meta"
GAME8_TIER_LIST_URL = "https://game8.co/games/Pokemon-UNITE/archives/335997"
UNITE_DB_TIER_LIST_URL = "https://unite-db.com/tier-list/competitive"

OUTPUT_DIR = Path("output")
OUTPUT_IMAGE = OUTPUT_DIR / "tierlist_pokemon_unite.png"
OUTPUT_DISCORD_IMAGE = OUTPUT_DIR / "tierlist_pokemon_unite_discord.png"
SAMPLE_DATA_PATH = Path("sample_data.json")
DATA_DIR = Path("data")
ASSET_CACHE_DIR = Path("assets") / "cache" / "pokemon"
LATEST_VALID_META_PATH = DATA_DIR / "latest_valid_meta.json"

IMAGE_WIDTH = 1400
IMAGE_MARGIN = 56
DISCORD_MAX_FILE_BYTES = 8 * 1024 * 1024

DISCORD_WEBHOOK_ENV = "DISCORD_WEBHOOK_URL"

TIERS = ("S", "A", "B", "C", "D")
TIER_PERCENTAGES = {
    "S": 0.15,
    "A": 0.20,
    "B": 0.30,
    "C": 0.20,
    "D": 0.15,
}

REQUEST_TIMEOUT_SECONDS = 25
REQUEST_RETRIES = 3
REQUEST_BACKOFF_SECONDS = 1.5
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)

MIN_VALID_POKEMON = 5
PROPERTY_NOTICE = "Propiedad de 🌙 𝑺𝑻𝑨𝑹𝑹𝒀 𝑮𝑨𝑹𝑫𝑬𝑵 ✦"
