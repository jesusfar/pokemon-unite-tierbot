# pokemon-unite-tierbot

Bot en Python para generar una tier list mensual de Pokémon UNITE en español, exportarla como PNG y publicarla en Discord mediante webhook.

## Salidas

- `output/tierlist_pokemon_unite.png`: imagen completa compatible con el nombre original.
- `output/tierlist_pokemon_unite_discord.png`: imagen optimizada para leerse mejor en Discord.
- `output/tierlist_pokemon_unite_weekly.png`: pulso semanal completo.
- `output/tierlist_pokemon_unite_weekly_discord.png`: pulso semanal optimizado para Discord.

La versión Discord usa:

- ancho de 1400px
- tarjetas más grandes
- score a 1 decimal
- Top 3 destacado
- chips de “más usado” y “más baneado”
- panel de comparación contra Game8 y Unite-DB cuando están disponibles
- resumen textual por tier en el mensaje de Discord
- fuente de datos visible
- marca de propiedad de STARRY GARDEN en el pie de la imagen

La versión mensual usa tema rojo. La versión semanal usa tema naranja y se publica como pulso del meta.

## Datos

Orden de fallback:

```text
UniteAPI ES con requests
UniteAPI ES con Playwright
UniteAPI EN con requests
UniteAPI EN con Playwright
data/latest_valid_meta.json
sample_data.json
```

Si UniteAPI entrega imágenes, el bot las descarga en `assets/cache/pokemon/` y las reutiliza. Si no hay imagen oficial/cacheada, usa placeholder.

## Comparación externa

Antes de publicar, el bot intenta comparar su tier list contra:

- `https://game8.co/games/Pokemon-UNITE/archives/335997`
- `https://unite-db.com/tier-list/competitive`

La comparación es informativa: añade consenso y diferencias fuertes al mensaje/imagen, pero no bloquea la publicación si esas páginas fallan, cambian su HTML o no están disponibles.

## Score

```text
score = win_rate * 0.60 + pick_rate * 0.25 + ban_rate * 0.15
```

Si falta `pick_rate` o `ban_rate`, se usa `0`. Si falta `win_rate`, el Pokémon se excluye.

## Instalación local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

En Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Comandos

Generar imágenes sin publicar:

```bash
python tierbot.py --monthly --dry-run
python tierbot.py --weekly --dry-run
```

Intentar sin Playwright:

```bash
python tierbot.py --dry-run --no-browser
```

Generar y publicar:

```bash
set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
python tierbot.py --monthly --send
python tierbot.py --weekly --send
```

Publicar una imagen ya generada:

```bash
python tierbot.py --message-only
```

## Hacerlo operativo en Discord

1. En Discord, entra al servidor y canal donde quieres publicar.
2. Abre `Editar canal > Integraciones > Webhooks`.
3. Crea un webhook llamado, por ejemplo, `Pokemon Unite Tierbot`.
4. Copia la URL del webhook.
5. En GitHub, ve a `Settings > Secrets and variables > Actions`.
6. Crea el secret `DISCORD_WEBHOOK_URL` con esa URL.
7. Ve a `Actions > Monthly Pokemon Unite Tier List`.
8. Ejecuta `Run workflow` para probar manualmente.
9. Si funciona, el bot publicará automáticamente el día 1 de cada mes.

## GitHub Actions

- `.github/workflows/monthly-tierlist.yml`: publica el día 1 de cada mes y permite ejecución manual.
- `.github/workflows/weekly-tierpulse.yml`: publica el pulso semanal cada lunes y permite ejecución manual.
- `.github/workflows/ci.yml`: ejecuta lint, tests y generación de imagen sin publicar.

## Desarrollo

```bash
ruff check .
pytest
python -m compileall .
```

## Nota de transparencia

El mensaje publicado en Discord incluye la fuente real usada. Si UniteAPI falla y el bot usa cache o sample, lo avisa en el mensaje.
