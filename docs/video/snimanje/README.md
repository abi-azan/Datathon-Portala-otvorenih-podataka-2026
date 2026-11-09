# Snimanje i montaža videa

Video za natjecanje nije snimljen ručno. Kadrove snima Playwright iz stranice uživo
(https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/) u okviru 1920×1080,
s lažnim kursorom i glatkim pomicanjem, a ffmpeg ih reže, dodaje natpise i glas.
Tako se svaki kadar može ponoviti kad se stranica promijeni.

## Što je što

| Datoteka | Uloga |
|---|---|
| `snimi.js` | kadrovi 1–7, 10 i 11 sa stranice (`node snimi.js 1 2 3`), izlaz `kadrovi/kadar-N.webm` |
| `snimi-mcp.js` | kadar 8: MCP Inspector s alatom `scenarij_spajanja` za Pag + Povljana |
| `slike.js` | natpisi (prozirni PNG) i shema arhitekture iz `docs/arhitektura.svg`, s fontovima stranice |
| `timeline.json` | redoslijed kadrova: izvor, početak (`in`), trajanje (`dur`), natpis |
| `glas.js` | uskladi trajanja s glasom (7 snimki, po jedna za svaki odjeljak scenarija) i pomakni titlove |
| `montaza.js` | složi MP4: `node montaza.js timeline.json video.mp4 [glas.m4a]` |

Kadar 9 (Excel tablica Ministarstva financija) je slika prozora Excela s listom "OPĆINA POVLJANA"
iz `data/raw/mf/prras/13.xlsx`, pretvorena u klip od 3 s polaganim zumom.

## Pokretanje

```
cd docs/video/snimanje
npm install                      # playwright-core i ffmpeg-static
npx playwright install chromium  # ako Chromium još nije na računalu
node slike.js
node snimi.js 1 2 3 4 5 6 7 10 11
npx @modelcontextprotocol/inspector ../../../.venv/Scripts/python -m fiskalna_mcp   # ispiše adresu s tokenom
node snimi-mcp.js "http://127.0.0.1:6274/?MCP_INSPECTOR_API_TOKEN=..."
node glas.js ../../../../glas    # mapa sa snimkama 1.m4a … 7.m4a
node montaza.js timeline-glas.json fiskalna-karta.mp4 glas.m4a
```

Playwright se pokreće s `channel: 'chromium'` (novi headless), jer tada karta koristi pravi GPU;
stari headless crta WebGL softverski i zum karte pada na 8 sličica u sekundi.

## Alati

- Playwright (Apache-2.0) i Chromium (BSD) za snimanje.
- ffmpeg (GPL, build gyan.dev preko paketa `ffmpeg-static`) za rezanje, natpise i zvuk.
- MCP Inspector (Apache-2.0) za kadar MCP servera.
- Glas je snimljen aplikacijom Snimač zvuka u Windowsima.
