# Licence softvera trećih strana

Fiskalna karta JLS gradi se i radi samo uz softver otvorenog koda. Ovdje su izravne ovisnosti s licencama. Provjereno je 4.11.2026. iz metapodataka instaliranih paketa (`.venv`, `web/node_modules`) i iz npm registryja.

- Naš kod je pod licencom [EUPL-1.2](LICENSE), a naši podaci pod [CC BY 4.0](LICENSE-DATA.md).
- Nijedna komponenta nije u sukobu s tim licencama. Obrazloženje je u odjeljku "Provjera sukoba".
- Licence skupova podataka su u [docs/skupovi-podataka.md](docs/skupovi-podataka.md), a AI alati u [README](README.md#korišteni-ai-alati).

## Web aplikacija (ide u preglednik)

| Paket | Verzija | Licenca | Za što |
|---|---|---|---|
| react, react-dom | 19.3.1 | MIT | sučelje |
| maplibre-gl | 6.16.0 | BSD-3-Clause | interaktivna karta |
| topojson-client | 3.1.0 | ISC | granice iz TopoJSON-a |
| lucide-react | 1.66.0 | ISC | ikone |
| @fontsource-variable/public-sans | 5.3.0 | OFL-1.1 | font Public Sans (© The Public Sans Project Authors) |
| @fontsource-variable/source-serif-4 | 5.3.1 | OFL-1.1 | font Source Serif 4 (© The Source Serif 4 Project Authors) |

- Svih 35 paketa u produkcijskom stablu ima licence MIT, ISC, BSD-2-Clause, BSD-3-Clause, OFL-1.1 ili "MIT OR Apache-2.0".
- Minifikacija briše napomene o autorskim pravima, a MIT, BSD i ISC traže da prate kod. Zato `npm run build` piše `licence-trecih-strana.txt` s punim tekstom licence svakog paketa u JS paketu (`build.license` u `web/vite.config.ts`). Podnožje stranice vodi na tu datoteku.
- Fontovi se učitavaju preko CSS-a, pa ih Vite u tu datoteku možda neće uključiti. Tekst OFL-a je u `node_modules/@fontsource-variable/*/LICENSE` i na https://openfontlicense.org.

## Razvoj web aplikacije (ne ide u preglednik)

| Paket | Verzija | Licenca |
|---|---|---|
| vite | 8.3.5 | MIT |
| @vitejs/plugin-react | 6.2.1 | MIT |
| tailwindcss, @tailwindcss/vite | 4.3.4 | MIT |
| typescript | 7.0.2 | Apache-2.0 |
| oxlint | 1.90.0 | MIT |
| @types/* | — | MIT |
| Node.js | 22 (CI) | MIT |

## ETL i testovi (Python 3.12, PSF-2.0)

| Paket | Verzija | Licenca | Za što |
|---|---|---|---|
| pandas | 3.1.0 | BSD-3-Clause | tablice |
| openpyxl | 3.1.5 | MIT | XLSX Ministarstva financija |
| pyarrow | 26.0.0 | Apache-2.0 | Parquet |
| requests | 2.34.2 | Apache-2.0 | CKAN API, WFS, preuzimanja |
| pypdf | 6.21.4 | BSD-3-Clause | tekst PDF izvješća Državnog ureda za reviziju (mišljenje i revidirana godina) |
| geopandas | 1.2.0 | BSD-3-Clause | granice |
| shapely | 2.2.0 | BSD-3-Clause | geometrija (wheel sadrži GEOS 3.14, LGPL-2.1) |
| libpysal | 4.15.1 | BSD-3-Clause | susjedstvo (Queen) |
| spopt | 0.8.0 | BSD-3-Clause | u `requirements.txt` za Kartu reforme; kod ga još ne uvozi |
| jsonschema, referencing | 4.26.0, 0.37.0 | MIT | provjera API-ja prema OpenAPI shemama |
| pytest | 9.2.0 | MIT | testovi |
| mcp (službeni MCP Python SDK) | 2.3.0 | MIT | MCP server `fiskalna_mcp` (stdio), vidi `docs/mcp.md` |

- U `.venv` je ukupno 98 paketa, s prijelaznim ovisnostima (numpy, pyogrio s GDAL-om, pyproj s PROJ-om, a za MCP pydantic, starlette, uvicorn, anyio i dr.; provjereno 5.11.).
- Sve su pod licencama otvorenog koda: MIT, BSD, Apache-2.0, ISC, PSF ili MPL-2.0 (certifi, tqdm).
- Copyleft imaju samo GEOS (LGPL-2.1, u wheelovima shapely i pyogrio) i text-unidecode (Artistic ili GPL-2.0+). text-unidecode dolazi s Kaggle CLI-jem preko python-slugify.

## Alati u izgradnji i AI dijelu

| Alat | Verzija | Licenca | Za što |
|---|---|---|---|
| mapshaper | 0.6.102 | MPL-2.0 | pojednostavljenje granica i TopoJSON (`npx` u `pipeline/geo.py`) |
| llama.cpp | commit `2cbca38` | MIT | izvođenje Gemme na Kaggle GPU-u, izgrađen iz izvornog koda |
| Gemma 4 31B-it (QAT Q4_0, GGUF) | Kaggle v2 | Apache-2.0 | tekst objašnjenja ocjene |
| Kaggle CLI (kaggle, kagglesdk) | 2.2.5, 0.1.38 | Apache-2.0 | slanje bilježnice na Kaggle |
| MCP Inspector (`@modelcontextprotocol/inspector`, `npx`) | 2.13.0 | Apache-2.0 (stariji doprinosi MIT) | provjera MCP servera; nije dio rješenja |
| markdown-it-py | 4.2.0 | MIT | `docs/DOKUMENTACIJA.md` u HTML za PDF (`pipeline/dokumentacija.py`); nije dio rješenja |
| GitHub Actions: checkout, setup-python, setup-node, cache, upload-pages-artifact, deploy-pages | v5 do v7 | MIT | CI i objava |

## Video

| Alat | Verzija | Licenca | Za što |
|---|---|---|---|
| Playwright (`playwright-core`) | 1.65.0 | Apache-2.0 | snimanje kadrova sa stranice uživo u 1920×1080 |
| Chromium (Playwright build 1254) | 158 | BSD-3-Clause | preglednik u kojem se kadrovi snimaju |
| ffmpeg (paket `ffmpeg-static`, build gyan.dev "essentials") | 6.1.1 | GPL-3.0-or-later (paket), GPL (build) | rezanje kadrova, natpisi, zvuk, izvoz MP4 |
| MCP Inspector | 2.13.0 | Apache-2.0 | kadar MCP servera (vidi i tablicu iznad) |
| faster-whisper (s CTranslate2) | 1.x | MIT | prepoznavanje govora lokalno: vremena riječi za rezove i titlove, provjera izgovorenih brojki |
| Whisper large-v3-turbo (model, OpenAI; pretvorba mobiuslabsgmbh) | – | MIT | model za gornje prepoznavanje; tekst titlova je ručno ispravljen |
| Snimač zvuka (Windows) | – | vlasnički, dio Windowsa | snimanje glasa |

Programi za snimanje i montažu ne ulaze u rješenje, pa njihove licence ne utječu na naše. Glazbe nema, ili je pod CC0.

## Usluge i infrastruktura (nisu dio našeg koda)

| Usluga | Uvjeti | Napomena |
|---|---|---|
| GitHub (repozitorij, Actions, Pages) | GitHub Terms of Service | pravila natjecanja izričito spominju github.com |
| Kaggle (bilježnice, T4 GPU, Kaggle Models) | Kaggle Terms of Use | tekstove generiramo jednom i commitamo, pa aplikacija o Kaggleu ne ovisi |
| NVIDIA CUDA (na Kaggleu) | NVIDIA EULA, vlasnički | služi samo za GPU izgradnju llama.cpp. llama.cpp radi i bez CUDA-e, na CPU-u |
| OpenFreeMap (pločice) | MIT, podaci ODbL | podloga karte; karta radi i bez nje |

## Provjera sukoba

- **EUPL-1.2 (naš kod):** sve biblioteke koje su dio rješenja imaju permisivne licence (MIT, BSD, ISC, Apache-2.0), a njih se smije uključiti u djelo pod EUPL-om.
- **Alati koje ne distribuiramo:**
  - mapshaper (MPL-2.0) samo se pokreće preko `npx`. Njegov izlaz (TopoJSON) nije pod MPL-om.
  - GEOS (LGPL-2.1) i text-unidecode (GPL-2.0+) rade samo u ETL-u i alatima i ne ulaze u objavljeni kod.
  - Copyleft uvjeti vrijede tek pri distribuciji tih komponenti, a mi ih ne distribuiramo.
- **CC BY 4.0 (naši podaci):**
  - Apache-2.0 ne ograničava izlaze modela.
  - OpenStreetMap podaci (ODbL) nisu u našim podacima.
  - Za izvorne podatke vrijede Otvorena dozvola i ZPPI. Oba dopuštaju spajanje i stvaranje novih skupova uz navođenje izvora, a to navođenje tražimo i od korisnika (`LICENSE-DATA.md`).
- **Vlasnički alati:**
  - NVIDIA CUDA i usluge GitHub i Kaggle su infrastruktura, a ne softver rješenja.
  - Claude (Anthropic) je razvojni alat i nije dio rješenja (README, "Korišteni AI alati").
  - Ovo je otvoreno pitanje strogog čitanja pravila (Pravila, VIII.), vidi `docs/research/03-tehnologija-i-licence.md` §1.2.
