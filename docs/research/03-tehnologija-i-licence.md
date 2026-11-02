# 03 – Tehnologija i licence: Fiskalna karta JLS

Datum istraživanja: 2026-11-02. Izazov C, predaja 09.11.2026. u 24:00.
Oznake u tekstu: **[P]** znači provjereno u ovom istraživanju (izvor naveden), **[N]** znači nije provjereno ili je moja pretpostavka, **[Procjena]** je izračun ili procjena koju treba potvrditi mjerenjem.

---

## 0. Sažetak u 12 točaka

1. **Pravila dopuštaju** bilo koju biblioteku pod OSI licencom (MIT, BSD, Apache-2.0, MPL, ISC, GPL...), uz uvjet da poštujemo licence i navedemo ih u dokumentaciji. Javni poziv kaže da se rješenja „trebaju razviti koristeći otvorene podatke i software otvorenog koda”.
2. **Modeli otvorenih težina:** koristiti samo modele pod Apache-2.0 ili MIT. Llama (Meta) i Gemma 3 (Gemma Terms of Use) nisu otvoreni kod po OSI-ju. Llama 3.2 k tome izuzima korisnike iz EU-a za multimodalne modele. Kompromis nije potreban jer je **Gemma 4 objavljena pod Apache-2.0** [P].
3. **Vlasnički AI asistent za programiranje** (npr. Claude Code) je nizak rizik ako (a) ga navedemo kao razvojni alat koji nije dio rješenja, (b) se rješenje može izgraditi i pokrenuti samo s OSS alatima i (c) tim pregleda i integrira kod. Preporuka: danas poslati kratko pitanje organizatoru (nacrt u odjeljku 1.4).
4. **Besplatni hosting** (GitHub Pages, Cloudflare) je u redu. Rješenje je statičko i ne ovisi o poslužitelju.
5. **Stack:** Python 3.12 ETL (pandas, openpyxl, geopandas, libpysal, statsmodels, scikit-learn) → statički JSON API s OpenAPI 3.1 i DCAT-AP 3.0.1 → React + Vite + TypeScript + MapLibre GL + ECharts + Tailwind/shadcn na GitHub Pages, s GitHub Actions za tjedno osvježavanje.
6. **Granice JLS idu preko API-ja:** živi OGC WFS 2.0 (INSPIRE, DGU/DZS) vraća točno **556 poligona gradova i općina** u GeoJSON-u [P]. To donosi bodove za „API” i „interoperabilne standarde”.
7. **data.gov.hr CKAN API ne šalje CORS zaglavlja** [P]. Preglednik ga zato ne može izravno zvati, pa API korištenje ide kroz ETL u GitHub Actions. To treba jasno prikazati u dokumentaciji i na stranici „Izvori”.
8. **data.gov.hr ima ckanext-dcat s DCAT RDF harvesterom** [P]. Ako objavimo vlastiti DCAT-AP katalog, portal ga može automatski preuzimati. To je konkretna integracija s postojećim javnim sustavom.
9. **LLM:** **Gemma 4 E4B-it (Apache-2.0)** lokalno preko **llama.cpp (MIT)** na CPU-u, preko noći. Pričuvni model je Gemma 4 E2B-it. Za bolju kvalitetu isti pipeline može koristiti Gemma 4 26B-A4B-it na Cloudflare Workers AI u besplatnoj kvoti. Na EuroEval hrvatskoj ljestvici Gemma 4 je najbolja Apache-2.0 obitelj u klasi koja stane na ovaj laptop [P].
10. **Svaka brojka u AI tekstu automatski se provjerava** prema „paketu činjenica” izračunatom u Pythonu. Tekst koji ne prođe provjeru ponovno se generira, a nakon dva neuspjeha zamjenjuje ga deterministički predložak.
11. **Laptop je slab** [P]: i5-1035G1 (4 jezgre), 7,6 GB RAM-a, samo Intel UHD, bez NVIDIA-e i bez Ollame. Zadani `python` je 3.10, a geopandas, numpy 2.5, libpysal i shap traže Python 3.11 ili 3.12. Treba koristiti `py -3.12` (već instaliran, 3.12.7).
12. **Opseg:** jezgra (karta, profil, usporedba, API) je oko 3,8 developerskih dana. Uz AI objašnjenja i simulator spajanja to je oko 6,3 dana, što je na samoj granici. „Pitaj podatke” (text-to-SQL) i model ranog upozoravanja su samo opcija ako ostane vremena. Ocjenjuje se **isključivo iz dostavljene dokumentacije i videa** [P, Javni poziv VII.], pa video i dokumentacija nisu sporedni posao.

---

## 1. Tumačenje pravila

### 1.1 Relevantni citati (doslovno)

Pravila, III. Podaci i tehnologije [P, PDF u repozitoriju]:
> „Rješenja se razvijaju korištenjem softvera otvorenog koda, a potiče se primjena naprednih tehnologija poput umjetne inteligencije, interneta stvari, proširene stvarnosti, velikih podataka ili lanca blokova.”

> „Podaci s Portala koriste se sukladno otvorenoj dozvoli pod kojom su objavljeni, uz obvezu navođenja izvora, u skladu s Pravilnikom o vrstama i sadržaju dozvola za ponovnu uporabu informacija (»Narodne novine«, br. 67/17.).”

Pravila, VIII. Rješenje i način dostave:
> „Rješenje mora biti izvorno djelo Tima. Timovi smiju koristiti postojeće alate, biblioteke i komponente otvorenog koda, uključujući alate temeljene na umjetnoj inteligenciji, pod uvjetom da ne krše njihove licence i da ih navedu u dokumentaciji.”

Pravila, XI. (diskvalifikacija): „…je dostavio rješenje koje nije izvorno ili krši prava trećih osoba”.
Pravila, XII.: „Objava rješenja pod licencom besplatnog softvera otvorenog koda na github.com ili sličnom javnom repozitoriju boduje se… Izbor licence prepušten je Timu.” i „Sudionici jamče da rješenje ne povređuje prava intelektualnog vlasništva…”

Javni poziv, I. [P, PDF s data.gov.hr]:
> „Predložena rješenja trebaju se razviti koristeći otvorene podatke i software otvorenog koda te naprednih tehnologije poput umjetne inteligencije…”

Javni poziv, VII.:
> „Ocjenjivanje se provodi isključivo na temelju dostavljene dokumentacije (kod, tehnička i projektna dokumentacija, demo materijali, video prezentaciju u trajanju 3 minute).”

Kriterij „Upotreba otvorenih podataka”: „Koriste li se otvoreni podaci izravno putem dostupnih API servisa tijela javnog sektora ili europskih/nacionalnih/lokalnih portala otvorenih podataka…”
Kriterij „Tehnička arhitektura…”: „Koristi li rješenje interoperabilne standarde? … Jesu li navedeni potrebni tehnički, organizacijski i pravni preduvjeti?”

### 1.2 Što pravila dopuštaju: odgovori i preporuke

| Pitanje | Odgovor | Rizik | Preporuka |
|---|---|---|---|
| Smijemo li koristiti bilo koju biblioteku pod OSI licencom? | Da. MIT, BSD, Apache-2.0, ISC, MPL-2.0 i GPL su „otvoreni kod”. Uvjet je poštovanje licence (npr. zadržati NOTICE/copyright) i navođenje u dokumentaciji. | Nizak | Popis s licencama je u odjeljku 9. Permisivne licence su najjednostavnije. MPL-2.0 (mapshaper) koristimo samo kao alat u izgradnji, pa ne utječe na našu licencu. |
| Modeli otvorenih težina s ne-OSI licencom (Llama, Gemma 3)? | Pravila ne spominju modele izričito. „Softver otvorenog koda” i „komponente otvorenog koda” se strogim čitanjem odnose i na model kao komponentu rješenja. OSI javno kaže da Llama licenca nije otvoreni kod (diskriminacija korisnika i područja uporabe). Llama 3.2 Acceptable Use Policy izuzima osobe s prebivalištem u EU-u za multimodalne Llama 3.2 modele [P, `meta-llama/llama-models` USE_POLICY.md] i traži „Built with Llama” [P, LICENSE]. Gemma 3 ima Gemma Terms of Use (nije OSI). | Srednji: ocjenjivač može reći da to nije otvoreni kod | **Koristiti samo Apache-2.0 ili MIT modele.** Nema gubitka kvalitete: Gemma 4, Qwen3.5/3.6, Ministral 3, Mistral Small 3.2, gpt-oss i EuroLLM su svi Apache-2.0 [P, HF API]. Izbjegavati: Llama 3.x/4, Gemma 3 i izvedenice (npr. `cjvt/GaMS3-12B-Instruct` ima licencu `gemma`), `Qwen3.8-Flash-Next` (`qwen-community-1.0`), `Ministral-8B-Instruct-2410` (MRL, istraživačka licenca). |
| Vlasnički AI asistent za programiranje (Claude Code, Copilot)? | „…uključujući alate temeljene na umjetnoj inteligenciji” gramatički je podskup „alata… otvorenog koda”. Strogo čitanje: i AI alati bi trebali biti otvoreni. Razumno čitanje: pravilo se odnosi na **rješenje** (isporuku), ne na svaki alat na računalu tima, jer bi inače i Windows bio problem. Pravilo „izvorno djelo Tima” traži da tim usmjerava, pregledava i integrira kod. Anthropicovi Consumer Terms (odj. 4) kažu: „we assign to you all our right, title, and interest (if any) in Outputs” [P, anthropic.com/legal/consumer-terms]. | Nizak do srednji | (1) U dokumentaciji ga **navesti** kao razvojni alat koji nije dio rješenja. (2) Osigurati da se rješenje može izgraditi i pokrenuti **samo OSS alatima** i opisati to u README-u. (3) Ne lijepiti velike tuđe isječke koje predloži AI; ako nešto izgleda kao kopija iz GPL projekta, prepisati ga. (4) Historija commitova pokazuje rad tima. (5) **Danas poslati kratko pitanje organizatoru** (odj. 1.4). |
| Besplatni hosting (GitHub Pages, Cloudflare)? | Hosting nije „softver kojim se razvija”. Pravila izričito spominju github.com. GitHub Pages: do 1 GB, 100 GB/mj. „soft” promet, nije za komercijalni SaaS [P, docs.github.com Pages limits]. Šalje `Access-Control-Allow-Origin: *` [P, curl], pa naš JSON API mogu koristiti i drugi. Cloudflare Pages (besplatno): 500 buildova/mj., 20 000 datoteka, 25 MiB po datoteci [P, developers.cloudflare.com]. | Nizak | Primarno GitHub Pages (repozitorij, Actions i web na jednom mjestu). Cloudflare samo za opcionalni Worker. |
| Licenca podataka s Portala | „Otvorena dozvola” traži [P, data.gov.hr/otvorena-dozvola]: navesti izjavu o izvoru i datum zadnje izmjene. Ako izvor nema izjavu: „Sadrži informacije tijela javne vlasti u skladu s Otvorenom dozvolom” s poveznicom. Treba navesti URI skupa podataka, označiti izmjene kao izmjene i ne sugerirati službenu podršku tijela. | Nizak ako se poštuje | Stranica „Izvori i licence” u aplikaciji i u dokumentaciji. Uz svaku ocjenu odricanje: „Izračun tima, nije službena ocjena Ministarstva financija.” |
| Licenca našeg koda i podataka | Izbor je na timu. | Nema | **Kod: EUPL-1.2.** Licenca Europske komisije, OSI-odobrena, sa službenim hrvatskim tekstom „Javna licencija Europske unije v. 1.2”, i signal javnom sektoru (kriterij interoperabilnosti). Jednostavnija alternativa je Apache-2.0 ili MIT. **Izvedeni podaci: CC BY 4.0** uz obvezno navođenje izvornih tijela. |
| Označavanje AI teksta | EU AI Act (čl. 50) uvodi obveze transparentnosti za AI-generirani tekst koji informira javnost [N: točan opseg primjene na studentski prototip nisam provjeravao]. | Nizak | Svako objašnjenje označiti: „Tekst generirao AI model (Gemma 4), brojke automatski provjerene.” Dodati poveznicu na metodologiju. |

### 1.3 Što napisati u dokumentaciji (sažetak, cijeli nacrt je u odjeljku 9)

- Izjavu: „Rješenje je razvijeno i radi isključivo uz softver otvorenog koda.”
- Tablicu svih komponenti s licencom i poveznicom.
- Odvojeno: **AI u rješenju** (model, licenca, način pokretanja, provjera brojki) i **AI u razvoju** (asistent, vlasnički, nije dio rješenja, kod je pregledao tim).
- Usluge (GitHub, OpenFreeMap, opcionalno Cloudflare) uz napomenu da se rješenje može pokrenuti i bez njih (statičke datoteke, lokalni llama.cpp).
- Popis skupova podataka s izdavačem, URI-jem, licencom i datumom zadnje izmjene, te izjave o izvoru prema Otvorenoj dozvoli.

### 1.4 Nacrt upita organizatoru (open.data@mpudt.hr)

> Poštovani,
> tim [naziv] (izazov C) ima pitanje o točki VIII. Pravila. Naše rješenje u cijelosti koristi softver otvorenog koda i bit će objavljeno na GitHubu pod licencom EUPL-1.2. Jezični model ugrađen u rješenje također je pod licencom Apache 2.0. Tijekom razvoja koristimo i AI asistent za programiranje (Claude Code), koji nije otvorenog koda, kao pomoćni alat, slično kao uređivač teksta. Taj alat nije dio rješenja, rješenje ne ovisi o njemu, a sav kod pregledava i integrira tim. Navest ćemo ga u dokumentaciji. Je li takvo korištenje u skladu s Pravilima?
> Unaprijed hvala, [ime], voditelj tima

---

## 2. Razvojno okruženje (provjereno na laptopu)

| Stavka | Stanje [P] | Posljedica |
|---|---|---|
| CPU | Intel Core i5-1035G1 (Ice Lake, 4 jezgre / 8 dretvi, AVX-512) | LLM samo na CPU-u, preko noći |
| RAM | 7,6 GB | Modeli do oko 4,6 GB (Q4). 8B+ modeli ne stanu udobno. |
| GPU | Intel UHD (iGPU), nema NVIDIA-e | Nema CUDA-e. Vulkan/OpenVINO build llama.cpp može se isprobati, ali vjerojatno nije brži od CPU-a [N]. |
| Python | `python` = 3.10.11, `py -3.12` = 3.12.7 | **Raditi u `py -3.12 -m venv .venv`.** Najnovije verzije numpy 2.5, libpysal, mapclassify, pyproj, shap, xgboost i networkx traže ≥3.12, a pandas 3.1, geopandas 1.2, duckdb 2.0 i polars ≥3.11 [P, PyPI `requires_python`]. |
| Instalirano (3.10) | pandas 2.3.3, openpyxl 3.1.5, httpx 0.28.1, requests 2.34.2, numpy 2.2.6, Jinja2 3.1.6 | Postojeći `pipeline/build.py` koristi openpyxl (read-only, iter_rows), a pandas samo za `to_csv`, pa je prelazak na pandas 3.x nizak rizik. |
| Node.js | v24.19.0, npm 11.17.0 | Dovoljno za Vite 8, TypeScript 7 i mapshaper preko `npx`. |
| Ollama, uv, nvidia-smi | nisu instalirani | Za LLM koristiti prijenosni llama.cpp ZIP (25 MB) bez instalacije. |

---

## 3. Preporučeni stack: tablica komponenti

Verzije i licence provjerene su 2026-11-02 izravno iz registara: PyPI JSON `https://pypi.org/pypi/<pkg>/json`, npm `https://registry.npmjs.org/<pkg>/latest`, GitHub `https://api.github.com/repos/<o>/<r>/license` i HF `https://huggingface.co/api/models/<id>`. U stupcu „Provjereno” je točan URL.

### 3.1 ETL i analiza (Python 3.12)

| Komponenta (verzija) | Svrha | Licenca | Provjereno | Alternativa |
|---|---|---|---|---|
| pandas 3.1.0 | tablice, CSV izvoz | BSD-3-Clause | https://pypi.org/pypi/pandas/json | polars 2.1.0 (MIT) |
| openpyxl 3.1.5 | čitanje MF XLSX (već u `build.py`) | MIT | https://pypi.org/pypi/openpyxl/json | python-calamine 0.9.0 (MIT) za brzinu; fastexcel 0.21.0 (MIT) uz polars |
| duckdb 2.0.0 | Parquet izvoz, SQL provjere, datoteka za DuckDB-WASM | MIT | https://pypi.org/pypi/duckdb/json | pyarrow 26.0.0 (Apache-2.0) |
| httpx 0.28.1 | CKAN API, WFS, LLM endpoint (OpenAI-kompatibilan) | BSD-3-Clause | https://pypi.org/pypi/httpx/json | requests 2.34.2 (Apache-2.0); ckanapi 4.11 (MIT) |
| pydantic 2.14.2 | modeli izlaznog API-ja, iz njih JSON Schema za OpenAPI | MIT | https://pypi.org/pypi/pydantic/json | jsonschema 4.26.0 (MIT) za validaciju |
| pandera 0.35.0 | validacija tablica (rasponi, zbrojevi, 576 jedinica × 7 godina) | MIT | https://pypi.org/pypi/pandera/json | ručni `assert` u pytestu |
| pytest 9.2.0 | testovi ETL-a i verifikatora | MIT | https://pypi.org/pypi/pytest/json | – |
| geopandas 1.2.0 + shapely 2.2.0 + pyogrio 0.13.0 + pyproj 3.8.0 | geometrija, spajanje s podacima | BSD-3 / BSD-3 / MIT / MIT | https://pypi.org/pypi/geopandas/json (i ostali) | – |
| libpysal 4.15.1 | susjedstvo (Queen/Rook contiguity) za simulator spajanja | BSD-3-Clause | https://pypi.org/pypi/libpysal/json i https://api.github.com/repos/pysal/libpysal/license | shapely `touches` + STRtree |
| mapshaper 0.7.101 (npm CLI, `npx`) | pojednostavljenje granica uz očuvanje topologije, TopoJSON, dissolve na županije | MPL-2.0 | https://registry.npmjs.org/mapshaper/latest i https://api.github.com/repos/mbloch/mapshaper/license | topojson (Python) 2.2 (BSD-3) |
| statsmodels 0.15.0 | regresija ekonomije razmjera (OLS, robusne SE) | BSD-3-Clause | https://pypi.org/pypi/statsmodels/json | – |
| scikit-learn 1.9.1 | standardizacija, kNN „statistički blizanci”, klasteri | BSD-3-Clause | https://pypi.org/pypi/scikit-learn/json | – |
| networkx 3.7 (opcija) | provjera povezanosti odabira i prijedlozi spajanja | BSD-3-Clause | https://pypi.org/pypi/networkx/json | BFS u nekoliko redaka |
| lightgbm 4.7.0 + shap 0.54.1 (P3, opcija) | model ranog upozoravanja s objašnjenjem po JLS | MIT / MIT | https://pypi.org/pypi/lightgbm/json, https://api.github.com/repos/microsoft/LightGBM/license (preusmjerava na lightgbm-org, MIT), https://pypi.org/pypi/shap/json | xgboost 3.4.1 (Apache-2.0); logistička regresija u statsmodels |
| rdflib 7.6.0 + pyshacl 0.40.2 | generiranje i SHACL validacija DCAT-AP kataloga | BSD-3 / Apache-2.0 | https://pypi.org/pypi/rdflib/json, https://pypi.org/pypi/pyshacl/json | ručno pisan JSON-LD |
| frictionless 5.21.0 (opcija) | `datapackage.json` i validacija CSV-a | MIT | https://pypi.org/pypi/frictionless/json | – |
| Jinja2 3.1.6 | deterministički predložak objašnjenja (fallback) | BSD-3-Clause | https://pypi.org/pypi/jinja2/json | f-stringovi |
| sqlglot 30.27.0 (opcija) | testovi text-to-SQL upita u CI-ju | MIT | https://pypi.org/pypi/sqlglot/json | DuckDB `json_serialize_sql` |
| ruff 0.17.3 | lint i format | MIT | https://pypi.org/pypi/ruff/json | – |

**Odluke za ETL:**
- **pandas, ne polars.** Podaci su mali (oko 576 × 7 × 40). Cijeli ostatak lanca (geopandas, statsmodels, scikit-learn, pandera) radi s pandasom. Migracija bi koštala vremena bez koristi.
- **openpyxl ostaje.** Već radi u read-only načinu. **python-calamine** je MIT, [Procjena] višestruko je brži i ima API za čitanje redaka (`CalamineWorkbook.from_path(...).get_sheet_by_name(...).to_python()`), a pandas ga podržava kao `engine="calamine"`. Uvesti ga samo ako ETL u CI-ju traje predugo, i to uz test da daje iste brojke.
- **DuckDB** samo za Parquet i SQL provjere. Pravi „data lake” ovdje nije potreban.

### 3.2 Frontend

| Komponenta (verzija) | Svrha | Licenca | Provjereno | Alternativa |
|---|---|---|---|---|
| Vite 8.3.5 + @vitejs/plugin-react 6.1.2 | build i dev server | MIT | https://registry.npmjs.org/vite/latest | – |
| React 19.3.1 + react-dom | UI | MIT | https://registry.npmjs.org/react/latest | Svelte 5.57.3 + SvelteKit 3.1.1 (MIT) |
| TypeScript 7.0.2 | tipovi (dijele se s JSON Schema) | Apache-2.0 | https://registry.npmjs.org/typescript/latest | – |
| react-router 8.5.1 (HashRouter) | rute `/#/jls/:oib`, `/#/simulator`, `/#/api` | MIT | https://registry.npmjs.org/react-router/latest | – |
| Tailwind CSS 4.3.3 | stilovi | MIT | https://registry.npmjs.org/tailwindcss/latest | – |
| shadcn 4.23.0 (CLI, komponente se kopiraju u repo) + radix-ui 1.8.1 + lucide-react 1.66.0 | pristupačne UI komponente (Dialog, Tabs, Combobox, Tooltip) | MIT / MIT / ISC | https://registry.npmjs.org/shadcn/latest, https://api.github.com/repos/shadcn-ui/ui/license | bits-ui/shadcn-svelte (MIT) uz Svelte |
| maplibre-gl 6.16.0 | WebGL karta, choropleth, hover i odabir (feature-state) | BSD-3-Clause | https://registry.npmjs.org/maplibre-gl/latest | Leaflet 1.9.4 (BSD-2); ECharts `geo` kao pričuva bez podloge |
| OpenFreeMap (usluga, stil „Positron”) | podloga bez API ključa, bez registracije, bez kolačića, bez limita pregleda [P, openfreemap.org] | kod MIT; podaci © OpenStreetMap (ODbL); shema OpenMapTiles (BSD-3, dizajn CC-BY-4.0) | https://api.github.com/repos/hyperknot/openfreemap/license | Protomaps PMTiles (BSD-3), ali samostalni hosting podloge nije vrijedan truda; OSM raster tile.openstreetmap.org samo uz pravila korištenja [P] |
| echarts 6.1.0 + echarts-for-react 3.0.6 | trendovi, usporedbe, radar, animacije (dobro izgleda u videu) | Apache-2.0 / MIT | https://registry.npmjs.org/echarts/latest, https://api.github.com/repos/apache/echarts/license | Observable Plot 0.6.17 (ISC); Recharts 3.10.1 (MIT); Vega-Lite 6.5.0 (BSD-3) |
| topojson-client 3.1.0 | TopoJSON u GeoJSON u pregledniku | ISC | https://registry.npmjs.org/topojson-client/latest | izravno GeoJSON |
| @turf/union 7.4.0 | obris spojene jedinice u simulatoru | MIT | https://registry.npmjs.org/@turf/union/latest | – |
| fuse.js 7.5.0 | pretraga naziva (normalizirati č/ć/š/ž/đ) | Apache-2.0 | https://registry.npmjs.org/fuse.js/latest | ručni filter |
| zustand 5.0.16 (opcija) | stanje odabira u simulatoru | MIT | https://registry.npmjs.org/zustand/latest | React context |
| @duckdb/duckdb-wasm **1.32.0** (pin!) | SQL u pregledniku, samo za „Pitaj podatke” i SQL konzolu, učitava se lijeno | MIT | https://registry.npmjs.org/@duckdb/duckdb-wasm/1.32.0 | – |
| @scalar/api-reference 1.76.4 | stranica dokumentacije API-ja iz `openapi.json` | MIT | https://registry.npmjs.org/@scalar/api-reference/latest | redoc 3.0.1 (MIT); swagger-ui-dist 5.34.1 (Apache-2.0) |
| @redocly/cli 2.72.1 | lint OpenAPI u CI-ju | MIT | https://registry.npmjs.org/@redocly/cli/latest | @stoplight/spectral-cli 6.17.0 (Apache-2.0) |
| vitest 5.0.5 | test da TS formule simulatora daju isto što i Python | MIT | https://registry.npmjs.org/vitest/latest | – |
| @playwright/test 1.64.1 | smoke test glavnih tokova i **automatski screenshotovi** za predaju | Apache-2.0 | https://registry.npmjs.org/@playwright/test/latest | – |
| @fontsource/inter (font Inter) | tipografija s hrvatskim dijakriticima | MIT (paket) / OFL-1.1 (font) | https://api.github.com/repos/fontsource/fontsource/license, https://api.github.com/repos/rsms/inter/license | sistemski font |

Napomena [P]: npm oznaka `latest` za `@duckdb/duckdb-wasm` trenutno pokazuje na **razvojni build** (`1.33.1-dev57.0`). Zadnja stabilna na npm-u je 1.32.0, pa verziju treba fiksirati.

**Usporedba frontend pristupa (za 1 developera s AI asistentom, 5–6 dana):**

| Kriterij | React + Vite | SvelteKit (static) | Observable Framework | Streamlit / Dash |
|---|---|---|---|---|
| Kontrola UX-a i polish | vrlo visoka (Tailwind/shadcn) | visoka | srednja (izgled bilježnice, teže prilagoditi) | niska do srednja |
| Složena interakcija (višestruki odabir na karti → simulator) | prirodna | prirodna | nespretna (reaktivne ćelije, `Mutable`) | ograničena (rerun cijele stranice) |
| Koliko dobro AI asistenti znaju alat | najbolje | dobro, ali miješaju Svelte 4 i 5 sintaksu [N] | slabije | dobro |
| Statički hosting, nula troška | da | da | da (izvrsno; data loaderi u Pythonu) | ne, treba poslužitelj (Community Cloud uspava aplikaciju) |
| Održavanje alata | aktivno | aktivno | **usporeno**: v1.13.3 (04/2025), pa v1.13.4 tek 03/2026 nakon issuea #2045 „is Observable Framework actually being maintained anymore?”. Observable je fokus prebacio na Notebook Kit [P, GitHub API] | aktivno |
| **Odluka** | **Preporuka** | dobra alternativa ako developer zna Svelte | ozbiljna opcija za čisti dashboard, ali rizična za stateful simulator i polish | samo krajnji plan C |

Observable Framework sam ozbiljno razmotrio jer je stvoren za ovakve aplikacije: data loaderi pokreću Python pri buildu, a DuckDB i Plot su ugrađeni. Glavni razlozi protiv su usporeno održavanje i nespretnost za interaktivni simulator, koji nam je najjači UX element.

### 3.3 AI i LLM

| Komponenta | Svrha | Licenca | Provjereno |
|---|---|---|---|
| llama.cpp (build b12032, `llama-b12032-bin-win-cpu-x64.zip`, 25 MB, bez instalacije) | lokalno izvođenje GGUF modela, OpenAI-kompatibilan `llama-server`, `json_schema`/`response_format`, `cache_prompt`, `--reasoning off` | MIT | https://api.github.com/repos/ggml-org/llama.cpp/license; README servera (raw GitHub) |
| **Gemma 4 E4B-it** (GGUF `ggml-org/gemma-4-E4B-it-GGUF`, Q4_0 4,59 GB) | generiranje objašnjenja (primarni lokalni model) | **Apache-2.0** | https://huggingface.co/api/models/google/gemma-4-E4B-it (license=apache-2.0, nije „gated”); license_link vodi na ai.google.dev/gemma/apache_2 [P] |
| Gemma 4 E2B-it (Q4_0 2,84 GB) | pričuvni model kad je malo RAM-a ili treba brže | Apache-2.0 | https://huggingface.co/api/models/google/gemma-4-E2B-it |
| Gemma 4 26B-A4B-it preko Cloudflare Workers AI (`@cf/google/gemma-4-26b-a4b-it`) | veća kvaliteta za batch generiranje i „Pitaj podatke” | model Apache-2.0; usluga je vlasnička (besplatni plan 10 000 neurona/dan) | developers.cloudflare.com/workers-ai/platform/pricing [P] |
| Ollama (opcija) | jednostavnije pokretanje | MIT | https://api.github.com/repos/ollama/ollama/license. Napomena: `gemma4:e4b` u Ollami ima 6,58 GB [P, registry manifest], što je na 7,6 GB RAM-a preveliko. Bolji je llama.cpp s Q4_0 datotekom. |
| vLLM (samo uz NVIDIA GPU) | batch na GPU-u (npr. Kaggle/Colab) | Apache-2.0 | https://pypi.org/pypi/vllm/json |
| @mlc-ai/web-llm 0.2.87 (alternativa) | LLM u pregledniku (WebGPU) | Apache-2.0 | https://registry.npmjs.org/@mlc-ai/web-llm/latest. Paket 0.2.87 sadrži `Qwen3.5-4B-q4f16_1-MLC` (oko 3,9 GB VRAM-a), `Qwen3.5-2B` (oko 2,2 GB) i `gemma-4-E2B-it` (oko 3,4 GB) [P, tarball]. |

### 3.4 CI, objava, standardi, video

| Komponenta | Svrha | Licenca | Provjereno |
|---|---|---|---|
| GitHub Actions: actions/checkout, setup-python, setup-node, upload-pages-artifact, deploy-pages | ETL, testovi, build, deploy | MIT (sve) | https://api.github.com/repos/actions/checkout/license (i ostale) |
| GitHub Pages | hosting statičke aplikacije i API-ja | usluga | docs.github.com (limiti) [P] |
| Cloudflare Workers (opcija) | proxy za „Pitaj podatke” (Workers AI) | usluga; naš Worker kod pod EUPL-1.2 | Free: 100 000 zahtjeva/dan, 10 ms CPU-a po pozivu [P] |
| OpenAPI 3.1 | opis našeg statičkog API-ja | specifikacija Apache-2.0 | https://api.github.com/repos/OAI/OpenAPI-Specification/license. Najnovija verzija je 3.2.1 (09/2026), ali 3.1 ima širu podršku alata [N]. |
| DCAT-AP 3.0.1 (06/2026) | metapodaci kataloga, kompatibilno s data.gov.hr | specifikacija CC-BY-4.0 | https://api.github.com/repos/SEMICeu/DCAT-AP/releases |
| INSPIRE / OGC WFS 2.0, GeoJSON (RFC 7946) | izvor granica | – | `transformiraj.nipp.hr` (vidi 5.3) |
| OBS Studio (snimanje), Kdenlive ili Shotcut (montaža) | video do 3 min | GPL-2.0 / GPL-3.0 / GPL-3.0 | https://api.github.com/repos/obsproject/obs-studio/license, .../KDE/kdenlive/license, .../mltframework/shotcut/license |

---

## 4. LLM: izbor modela, posluživanje i provjera

### 4.1 Licence i kvaliteta na hrvatskom (EuroEval, hrvatska „generative” ljestvica)

Izvor: euroeval.com/leaderboards/croatian, podaci ažurirani 2026-10-27 [P]. „Rank score” je bolji što je manji. Zadaci: sentiment (mms_hr), NER (wikiann_hr), jezična prihvatljivost (scala_hr), razumijevanje pročitanog (multi_wiki_qa_hr), znanje (include_hr) i zdrav razum (winogrande_hr). **Ograničenje:** EuroEval mjeri razumijevanje, a ne tečnost i gramatiku slobodno generiranog teksta. Zato je obavezna interna slijepa usporedba (4.6).

| Model | Licenca [P, HF API] | Veličina (GGUF Q4) | Rank HR | RC (multi_wiki_qa_hr) | Napomena |
|---|---|---|---|---|---|
| Qwen3.6-27B | Apache-2.0 | ~16 GB | 1,52 | 66,2 | najbolji otvoreni oko 30B; prevelik za laptop |
| Gemma 4 31B-it | Apache-2.0 | ~18 GB | 1,58 | – | prevelik |
| Mistral Small 3.2 24B | Apache-2.0 | ~14 GB | 1,85 | – | prevelik |
| **Gemma 4 26B-A4B-it** | **Apache-2.0** | ~15 GB | **1,86** | – | dostupan na Workers AI besplatno [P] |
| Gemma 4 12B-it | Apache-2.0 | 6,98 GB (QAT Q4_0) | 1,92 | 67,3 | prevelik za 7,6 GB RAM-a |
| Qwen3.5-9B | Apache-2.0 | 5,68 GB | 2,02 | 34,7 | thinking uključen po defaultu; slabo razumijevanje pročitanog |
| gpt-oss-20b (medium) | Apache-2.0 | 13,8 GB (Ollama) | 2,11 | 56,5 | prevelik |
| **Gemma 4 E4B-it** | **Apache-2.0** | **4,59 GB** | **2,18** | **64,3** | **preporuka za laptop** |
| Ministral 3 8B Instruct | Apache-2.0 | 5,2 GB | 2,19 | 62,5 | dobra alternativa ako ima RAM-a |
| GaMS3-12B-Instruct (CJVT) | Gemma ToU, nije OSI | ~7 GB | 2,20 | 66,8 | slovenski; licenca ga isključuje |
| Qwen3.5-4B | Apache-2.0 | 2,74 GB | 2,41 | 30,0 | brz, ali slabije razumije zadani kontekst |
| Gemma 4 E2B-it | Apache-2.0 | 2,84 GB | 2,59 | 65,5 | **pričuva**: dobro razumije tekst, slabije znanje i zdrav razum |
| Ministral 3 3B Instruct | Apache-2.0 | 2,15 GB | 2,61 | 57,9 | – |
| EuroLLM-9B-Instruct-2512 | Apache-2.0 | ~5,5 GB [N] | nepotpuno | **70,4** | eksplicitno treniran na hrvatskom; najbolji RC, slab zdrav razum (11,8) |
| Llama 3.1 8B Instruct | Llama 3.1, nije OSI | ~4,9 GB | 2,77 | 37,1 | izbjegavati (licenca) |
| YugoGPT (7B, osnovni model) | Apache-2.0 | ~4,4 GB | 2,78 | 53,2 | iz 2024., nije instrukcijski model |
| Olmo-3-7B-Instruct | Apache-2.0 | – | 3,28 | – | slab na hrvatskom |
| Salamandra-7b-instruct | Apache-2.0 | – | 3,37 | 15,5 | slab na hrvatskom |
| BERTić (`classla/bcms-bertic`) | Apache-2.0 | – | – | – | encoder za NER i klasifikaciju BCMS jezika, ne generira tekst; nije potreban |

Zašto Gemma 4 E4B: najbolji Apache-2.0 model koji stane u RAM laptopa; dobro razumijevanje zadanog konteksta, što je ključno za tekst vezan uz činjenice; ista obitelj kao 26B-A4B, pa se prompt prenosi bez promjena. Kod Gemme 4 E-modela thinking je isključen dok se u system prompt ne doda `<|think|>` [P, model card], a llama.cpp ima `--reasoning off` [P, README].

### 4.2 (a) Offline generiranje oko 576 objašnjenja na laptopu

**Preporuka:** `llama-server` (llama.cpp CPU x64 build) + Gemma 4 E4B-it Q4_0, `--reasoning off`, `cache_prompt` za zajednički system prompt, `json_schema` za strukturirani izlaz, temperatura 0,2–0,3. Skripta `explain.py` (httpx) piše svaki rezultat u JSONL i preskače gotove jedinice, pa se može nastaviti nakon prekida.

```
llama-server -m gemma-4-E4B-it-Q4_0.gguf -c 4096 -t 4 -np 1 --reasoning off --port 8080
llama-bench  -m gemma-4-E4B-it-Q4_0.gguf -p 512 -n 128 -t 4     # 5 min, prije svega ostalog
```

Procjena trajanja [Procjena, nije izmjereno; temelji se na propusnosti memorije od oko 25–35 GB/s i 4 jezgre]. Pretpostavka po jedinici: oko 400 novih tokena prompta (system prompt u cacheu) i oko 250–300 izlaznih tokena.

| Model | Generiranje | Obrada prompta | Po jedinici | 576 jedinica (+15 % ponavljanja) |
|---|---|---|---|---|
| Gemma 4 E2B Q4_0 | ~10–17 tok/s | ~40–80 tok/s | ~25–40 s | **~4,5–7,5 h** |
| Gemma 4 E4B Q4_0 | ~5–9 tok/s | ~20–40 tok/s | ~45–80 s | **~8–15 h** (1–2 noći) |

Pravila rada:
- Prije pokretanja zatvoriti preglednik i IDE (4,6 GB modela na 7,6 GB RAM-a).
- Prompt i verifikator razvijati na **20 jedinica s E2B** (brzo iteriranje), a finalni batch pustiti s E4B preko noći.
- `llama-bench` izvršiti prvi dan i ovu tablicu zamijeniti stvarnim brojkama. Vulkan i OpenVINO buildovi (38 MB i 105 MB) mogu se isprobati na Intel iGPU-u, ali CPU je sigurniji izbor [N].

**Brži put s većom kvalitetom (isti kod, druga `base_url`):** Gemma 4 26B-A4B-it na Cloudflare Workers AI preko OpenAI-kompatibilnog `/v1/chat/completions` s JSON Mode `response_format` [P]. Cijena [P]: 9 091 neurona po milijunu ulaznih i 27 273 neurona po milijunu izlaznih tokena. Besplatno je 10 000 neurona dnevno. Uz 1 200 ulaznih i 350 izlaznih tokena to je oko 20 neurona po jedinici, oko 11 800 za svih 576, odnosno **oko 1,2 dana besplatne kvote** i nekoliko minuta stvarnog vremena. Uvjet: isključiti reasoning, inače se troše izlazni tokeni [N: provjeriti parametar za ovaj model]. Ovo je vlasnička usluga s otvorenim modelom. Kod je neutralan prema pružatelju, pa se može i potpuno lokalno.

**Odluka u srijedu:** objavljuje se ona varijanta koja ima veći postotak prolaza kroz verifikator i bolju ocjenu u slijepoj usporedbi na 20 jedinica (4.6).

### 4.3 Provjera i utemeljenje (grounding): svaka brojka mora biti iz podataka

Načelo: **Python računa sve, LLM samo piše riječi oko gotovih brojki.**

1. **Paket činjenica po jedinici** (`facts/{oib}.json`) generira se deterministički iz `jls.json`. Sve vrijednosti su već formatirane hrvatski (`12,3 %`, `1.234.567 €`, `−4,1 postotnih bodova`), uz smjer i usporedbu:
   ```json
   {"oib":"...","naziv":"Općina Andrijaševci","vrsta":"općina","zupanija":"Vukovarsko-srijemska","godina":2025,
    "ocjena":{"vrijednost":"2,4","razred":"B","opis":"dobro"},
    "cinjenice":[
      {"id":"F1","opis":"operativni saldo 2025.","prikaz":"12,3 %","usporedba":"bolje od 71 % općina slične veličine"},
      {"id":"F2","opis":"promjena operativnog salda 2019.–2025.","prikaz":"−4,1 postotnih bodova","smjer":"pad"}],
    "blizanci":["Općina X","Općina Y","Općina Z"]}
   ```
2. **Prompt (hrvatski):** koristiti isključivo dane činjenice; brojke prepisati doslovno iz polja `prikaz`; uz svaki nalaz navesti ID-jeve činjenica; ne izvoditi uzroke („zbog lošeg upravljanja”), ne spominjati osobe, ne davati političke preporuke; jezik razine B1; najviše oko 120 riječi. U promptu su dva ručno napisana primjera.
3. **Ograničeni izlaz** (JSON Schema preko llama.cpp `json_schema` ili Workers AI `response_format`):
   `{"sazetak": str ≤ 300 znakova, "nalazi": [{"tekst": str, "cinjenice": ["F1", ...]}] (2–4 nalaza), "na_sto_obratiti_pozornost": str}`
4. **Deterministički verifikator** (`verify.py`, pokriven pytestom):
   - valjan JSON prema shemi;
   - svaki nalaz citira barem jednu postojeću činjenicu;
   - **svaki broj u tekstu** (regex za hrvatski zapis: tisućice s točkom, decimale sa zarezom, `%`, `€`, „mil.”, „postotnih bodova”) nakon normalizacije mora se doslovno pojaviti u `prikaz` citiranih činjenica ili na listi dopuštenih brojeva (godine 2019–2025, rangovi i broj jedinica iz činjenica). Inače se tekst odbija;
   - riječi smjera („rast”, „porast”, „povećanje” naspram „pad”, „smanjenje”) moraju se slagati sa `smjer` citirane činjenice;
   - svako ime JLS-a u tekstu (gazeteer od 576 naziva) mora biti sama jedinica, njezina županija ili navedeni blizanac;
   - ako se spominje razred ocjene, mora biti jednak izračunatom;
   - crna lista izraza (uzročne tvrdnje, imena dužnosnika, „sigurno”, „nužno”).
5. **Ponovno generiranje** s porukom o pogrešci, najviše dva puta. Nakon toga **Jinja2 predložak** (uvijek točan, manje tečan) i oznaka `izvor: "predlozak"`.
6. **Porijeklo (provenance)** se sprema uz svaki tekst: model, kvantizacija, verzija llama.cpp, hash prompta, hash paketa činjenica, vrijeme, rezultat verifikatora. Kad se podaci promijene (novi hash činjenica), tekst se označi kao zastario i dok se offline ne regenerira prikazuje se predložak. CI ne pokreće LLM.
7. **Ljudska kontrola:** 30 nasumičnih jedinica i 20 ekstremnih (najbolje i najlošije ocjene) pregledava tim, a nalazi se bilježe u `review.csv`. Cilj je da verifikator propusti barem 90 % tekstova i da u pregledanim tekstovima nema činjeničnih pogrešaka.
8. **U sučelju:** oznaka „Objašnjenje je generirao AI model Gemma 4. Sve brojke automatski su provjerene prema podacima.” i prekidač **„Prikaži izvore”** koji ističe svaku brojku i u tooltipu pokazuje činjenicu i izvorni skup podataka. To dobro izgleda u videu i jača kriterij inovativnosti.

### 4.4 (b) Opcionalno „Pitaj podatke” (text-to-SQL), prioritet P2

- **Model i posluživanje:** Cloudflare Worker (oko 60 redaka, naš kod) poziva Workers AI `@cf/google/gemma-4-26b-a4b-it` u JSON Mode. Worker vraća **samo SQL i kratko obrazloženje**, a ne podatke. [Procjena] Uz oko 2 000 ulaznih i 200 izlaznih tokena to je oko 24 neurona po pitanju, odnosno oko 420 pitanja dnevno besplatno.
- **Izvršavanje u pregledniku:** DuckDB-WASM (lijeno učitan) nad `jls_godine.parquet`. Validacija:
  - `SELECT json_serialize_sql(?)`: točno jedna `SELECT` naredba, samo dopuštene tablice [N: oblik AST-a provjeriti u verziji 1.32.0];
  - omotati kao `SELECT * FROM (<sql>) LIMIT 200`;
  - izvršiti u workeru s timeoutom od 5 s.
  Prikazuju se SQL, tablica i graf. **Brojke dolaze iz baze, nikad iz LLM-a.**
- **Pouzdanost za demo:** 10 primjera pitanja s unaprijed izračunatim SQL-om i rezultatima u statičkoj datoteci. Rade i kad je LLM nedostupan. Dodatno, „SQL konzola” bez AI-ja gotovo ništa ne košta, a korisna je naprednim korisnicima.
- **Alternativa bez usluge:** WebLLM u pregledniku (Qwen3.5-2B ili 4B, Gemma-4-E2B). Potpuno lokalno i otvoreno, ali traži WebGPU i 2–4 GB preuzimanja, što je loše iskustvo za ocjenjivača na slabijem računalu.

### 4.5 Ostali AI i ML elementi (inovativnost)

- **Statistički blizanci:** scikit-learn kNN nad standardiziranim pokazateljima (log stanovništva, prihodi po stanovniku, udio vlastitih prihoda, udio pomoći, troškovi uprave). Izračunava se unaprijed, 5 blizanaca po jedinici.
- **Ekonomija razmjera:** statsmodels OLS, `log(admin_pc) ~ log(stanovnici) + log(stanovnici)² + otok + županija FE`, HC3 standardne pogreške. Koeficijenti i intervali pouzdanosti idu u JSON, a simulator iz njih procjenjuje uštedu s rasponom i jasnom napomenom da je to statistička procjena, a ne prognoza.
- **Rano upozoravanje (LightGBM + SHAP):** samo ako ostane vremena. Oko 3 300 jedinica-godina je malo, a definicija oznake i curenje informacija (leakage) lako odu krivo. Ako se radi, top-3 SHAP faktora ulaze u paket činjenica za LLM.

### 4.6 Slijepa usporedba kvalitete hrvatskog (pola sata, utorak)

Za 10 jedinica generirati tekst s E2B, E4B i 26B-A4B (Workers AI). Promiješati redoslijed i sakriti model. Dvoje članova tima ocjenjuje gramatiku i padeže (npr. „u Općini Andrijaševci”), jasnoću i točnost na ljestvici 1–5. Odabire se najbolji model koji prolazi verifikator.

---

## 5. Arhitektura

### 5.1 Dijagram

```
  IZVORI (javni sektor)                                    API / standard
  ─────────────────────────────────────────────────────────────────────────────
  data.gov.hr CKAN API v3 ── DZS Popis 2021, metapodaci ─── REST/JSON, DCAT
  Ministarstvo financija ── PR-RAS, RAS-funkc., Bilanca ─── HTTP XLSX (ETag/hash)
  DGU/DZS INSPIRE WFS 2.0 ── 556 poligona gradova/općina ── OGC WFS, GeoJSON
  ─────────────────────────────────────────────────────────────────────────────
                     │  GitHub Actions: tjedni cron + ručno + push
                     ▼
  ┌──────────────────────── ETL (Python 3.12) ────────────────────────────┐
  │ fetch.py   CKAN package_show → URL resursa, metadata_modified, sha256 │
  │ build.py   openpyxl → pokazatelji → pandera → jls.json, CSV, Parquet  │
  │ geo.py     WFS GeoJSON → mapshaper (simplify, TopoJSON, dissolve      │
  │            županija) → libpysal Queen + ručne veze za otoke           │
  │ model.py   statsmodels (ekonomija razmjera), sklearn kNN (blizanci)   │
  │ publish.py JSON API po OIB-u, OpenAPI 3.1, DCAT-AP 3.0.1,             │
  │            datapackage.json                                           │
  └──────────────┬────────────────────────────────────────────────────────┘
                 │                     ▲ offline, laptop (ne u CI-ju)
                 │                     │ explain.py: paket činjenica →
                 │                     │ llama.cpp + Gemma 4 E4B → verify.py
                 │                     │ → explanations.json (+ provenance)
                 ▼
  GitHub Pages (statično, CORS *, 0 €)
   ├─ /#/…            React SPA: karta (MapLibre + OpenFreeMap, pričuva bez
   │                  podloge), profil (ECharts), usporedba, simulator spajanja
   ├─ /api/v1/…       576 JSON profila, CSV, Parquet, TopoJSON, susjedstvo
   ├─ /api/v1/openapi.json  i  /#/api (Scalar dokumentacija)
   ├─ /catalog.ttl, /catalog.jsonld (DCAT-AP) ──► harvest: data.gov.hr
   │                                              (ckanext-dcat, rdf harvester)
   └─ /#/embed/jls/{oib}  ugradiva kartica za web stranice JLS-ova
  (opcija P2) Cloudflare Worker ──► Workers AI (Gemma 4 26B-A4B) vraća SQL;
              SQL se izvršava u pregledniku (DuckDB-WASM)
```

### 5.2 Statički API (`/api/v1/`)

| Putanja | Sadržaj |
|---|---|
| `meta.json` | verzija, vrijeme builda, izvori (CKAN `metadata_modified`, sha256 datoteka), commit |
| `jls.json` | 576 jedinica: `oib`, `rkp`, `rpj_kod` (DGU `localId`), naziv, vrsta, županija, zadnja ocjena |
| `jls/{oib}.json` | profil: godine × pokazatelji, bodovi, blizanci, objašnjenje s porijeklom |
| `pokazatelji.json` | definicije, formule, pragovi bodovanja, izvori |
| `susjedstvo.json` | Queen susjedi i ručne veze (otoci, mostovi) |
| `model/ekonomija-razmjera.json` | koeficijenti, intervali pouzdanosti, R², N |
| `download/jls_godine.csv`, `.parquet`; `geo/jls.topojson`, `geo/jls.geojson`, `geo/zupanije.topojson` | bulk preuzimanje |
| `openapi.json` | OpenAPI 3.1; sheme se generiraju iz pydantic modela; CI validira sve JSON datoteke prema shemama |

Identifikatori: **OIB** kao primarni ključ (već ga ima `build.py`), uz to RKP (MF registar) i RPJ kod DGU-a (INSPIRE `localId`, npr. `52000022`). Objavljeni **šifrarnik (OIB ↔ RKP ↔ RPJ ↔ naziv ↔ županija)** sam je po sebi koristan interoperabilni rezultat.

### 5.3 Provjereni API-ji i ograničenja

- **WFS s granicama** [P]: `https://transformiraj.nipp.hr/ows/services/org.14.b8096c46-3962-421f-baf8-918a45735eed_wfs`
  - sloj `su-vector:AreaStatisticalUnit`, `numberMatched="556"`;
  - `OUTPUTFORMAT=application/geo+json` i `SRSNAME=EPSG:4326` rade;
  - cijeli sloj ima **196 MB i preuzima se oko 18 s**, pa se preuzima jednom, sprema s hashom i pojednostavljuje mapshaperom (cilj oko 1 MB);
  - CORS je uključen (reflektira Origin);
  - CKAN skup: „Kućanstva – ukupno na razini gradova/općina iz Popisa stanovništva 2021. INSPIRE” (DGU). **Polje licence u CKAN-u je prazno**, pa treba koristiti izjavu „Sadrži informacije tijela javne vlasti u skladu s Otvorenom dozvolom”.
  - Napomena: skup „Upravne jedinice INSPIRE” (Otvorena dozvola) nudi samo WMS i ATOM, jer je njegov WFS isključen („Service WFS is disabled”) [P].
- **CKAN API** [P]: CKAN 2.9.9, ekstenzije uključuju `dcat`, `dcat_rdf_harvester`, `dcat_json_harvester`, `datastore`. `/ckan/catalog.ttl` vraća DCAT-AP (s `dcatap:hvdCategory`). Licenca većine skupova u katalogu je `https://data.gov.hr/id/licence/otvorena-dozvola-rh`. **Odgovori nemaju `Access-Control-Allow-Origin`**, ni uz zaglavlje `Origin`, pa preglednik ne može izravno zvati API.
- **Kako pokazati korištenje API-ja ocjenjivačima:** stranica „Izvori” s endpointom, zadnjom provjerom, `metadata_modified` i hashom za svaki izvor; poveznica na logove GitHub Actionsa; kratki isječak u videu.

### 5.4 GitHub Actions (`.github/workflows/data.yml`)

`schedule` (tjedno, npr. `17 5 * * 1`, jer cron na početku sata kasni [P]), `workflow_dispatch` i `push` na `pipeline/**`. Koraci:
1. checkout, setup-python 3.12, `pip install -r requirements.txt`;
2. `fetch.py` (ako se hash ne promijeni, preskače se ostatak);
3. build, model, publish;
4. pytest, pandera, Redocly lint, SHACL validacija DCAT-a;
5. setup-node, `npm ci`, `vite build`;
6. upload-pages-artifact i deploy-pages.

Napomene [P]: u javnom repozitoriju zakazani workflow se gasi nakon 60 dana bez aktivnosti; najkraći interval je 5 minuta. Sirove datoteke spremati kao artefakt ili GitHub Release s checksumom, kako build ne bi ovisio o trenutnoj dostupnosti portala.

### 5.5 Tehnički, organizacijski i pravni preduvjeti (za kriterij arhitekture)

- **Tehnički:** statički web (bilo koji HTTP poslužitelj); za osvježavanje Python 3.12 i Node 24; za AI tekst llama.cpp i model od 4,6 GB, bez GPU-a.
- **Organizacijski:** MF godišnje objavljuje financijske izvještaje JLP(R)S-a u stabilnom formatu; MPUDT može dodati naš DCAT katalog kao izvor za harvest na data.gov.hr ili nam dati račun izdavača za `package_create`; JLS-ovi mogu ugraditi karticu (`/#/embed`).
- **Pravni:** Otvorena dozvola (NN 67/17) s izjavama o izvoru i označenim izmjenama; odricanje da ocjena nije službena; EUPL-1.2 i CC BY 4.0; nema osobnih podataka (agregati na razini JLS-a, bez kolačića i analitike, a OpenFreeMap ne koristi kolačiće [P]), pa nije potreban GDPR banner; označavanje AI teksta; za preuzimanje u javnom sektoru usklađenost s pristupačnošću (WCAG 2.1 AA; Zakon o pristupačnosti mrežnih stranica… NN 17/19 [N: nije provjereno u ovom istraživanju]). Zato paleta mora biti prilagođena daltonistima, a karta mora imati tablični ekvivalent.

---

## 6. Plan rada i procjena napora

Pretpostavka: jedan developer s AI asistentom, dan od 8 do 10 sati. Ostali članovi paralelno rade dokumentaciju, video i QA (od četvrtka).

| Dio | Prioritet | Procjena (dev-dana) |
|---|---|---|
| Učvršćivanje ETL-a, šifrarnik ID-ova, pandera i pytest | P0 | 0,5 |
| Geo: WFS → mapshaper → spajanje 556 jedinica i 20 županija (dissolve) → susjedstvo i otoci | P0 | 0,5 |
| Statički API, OpenAPI 3.1, Scalar stranica | P0 | 0,4 |
| Frontend kostur (Vite, React, TS, Tailwind, shadcn, rute, pretraga) | P0 | 0,4 |
| Karta (choropleth, legenda, hover, klik, odabir pokazatelja i godine, pričuvni stil) | P0 | 0,6 |
| Profil JLS (ocjena, trendovi, objašnjenje pokazatelja, blizanci i usporedba) | P0 | 0,8 |
| Polish, pristupačnost, Playwright i screenshotovi | P0 | 0,6 |
| **Ukupno P0** | | **3,8** |
| AI objašnjenja (činjenice, prompt, verifikator, noćni batch, prikaz izvora) | P1 | 0,8 (+ noć) |
| Simulator spajanja (višestruki odabir uz susjedstvo, TS port formula, test paritetnosti, procjena uštede) | P1 | 0,8 |
| Ekonomija razmjera i kNN blizanci | P1 | 0,4 |
| GitHub Actions (ETL, deploy, cron) i DCAT-AP s datapackage | P1 | 0,5 |
| **Ukupno P0 + P1** | | **≈ 6,3** |
| „Pitaj podatke” (Worker, DuckDB-WASM, zaštite, primjeri) | P2 | 1,0 |
| Rano upozoravanje (LightGBM + SHAP) | P3 | 1,0 |
| Dokumentacija i video (ostali članovi) | P0 | 1,5 osoba-dana |

**Raspored:**
- **Pon 3.11.:** ETL, šifrarnik, geo pipeline; `llama-bench`; prvi prompt na 20 jedinica (E2B); frontend kostur.
- **Uto 4.11.:** karta i profil; paket činjenica i verifikator; slijepa usporedba (4.6); **noću batch E4B, prvi prolaz**.
- **Sri 5.11.:** blizanci, regresija, API i OpenAPI; početak simulatora. Odluka o modelu ili Workers AI prema postotku prolaza verifikatora.
- **Čet 6.11.:** simulator dovršen; regeneracija neuspjelih tekstova; CI deploy; tim počinje scenarij videa.
- **Pet 7.11.:** DCAT, polish, pristupačnost, Playwright. **Zamrzavanje funkcionalnosti u 20:00.** P2 samo ako je P1 gotov u četvrtak.
- **Sub 8.11.:** snimanje i montaža videa (OBS, Kdenlive); dokumentacija; samo ispravci grešaka.
- **Ned 9.11.:** završna provjera linkova i README-a; **slanje do podneva**, ne pred ponoć.

---

## 7. Plan B i plan C

**Točke odluke:**
- **Kraj ponedjeljka:** ako spajanje WFS geometrija s MF podacima nije gotovo, privremeno spajanje po normaliziranom nazivu i tablica ručnih iznimaka (CSV). Karta ide dalje, a šifrarnik se popravlja kasnije.
- **Kraj utorka:** ako karta i profil ne rade glatko, plan B za simulator.
- **Srijeda navečer:** ako verifikator propušta manje od 80 % tekstova, prijeći na Workers AI 26B-A4B ili na predloške za sve jedinice. Ne prikazivati AI tekst samo za dio jedinica.

**Plan B (isti stack, manji opseg):**
- objašnjenja iz Jinja2 predloška za sve jedinice, uz AI tekst samo ako je cijeli skup prošao provjeru;
- simulator s odabirom s popisa (combobox), bez ograničenja susjedstva, i ušteda kao jednostavna usporedba troška uprave po stanovniku s jedinicama slične veličine;
- bez cron osvježavanja (ručni deploy), DCAT kao jedna ručno pisana JSON-LD datoteka;
- karta u ECharts `geo` bez podloge ako MapLibre pravi probleme.

**Plan C (samo ako React ne radi do utorka navečer):** Streamlit (Apache-2.0) nad istim `jls.json`, s istim ETL-om i API datotekama. Lošiji UX i ovisnost o poslužitelju (Community Cloud uspava aplikaciju), pa je to krajnja mjera.

---

## 8. Glavni rizici

| Rizik | Vjerojatnost | Ublažavanje |
|---|---|---|
| E4B na 7,6 GB RAM-a swapa ili je prespor | srednja | E2B; Workers AI 26B-A4B; batch preko dvije noći uz nastavak |
| LLM izmišlja brojke ili krivo deklinira nazive | srednja | verifikator, ponovno generiranje, predložak, ljudski pregled 50 tekstova |
| Spajanje naziva MF ↔ WFS ↔ DZS (dvojezični istarski nazivi, „Sv.”) | visoka | šifrarnik po OIB-u i RPJ-u, CSV ručnih iznimaka, test da je spojeno 556 + 20 jedinica |
| Otočne općine nemaju kopnene susjede | sigurno | ručne veze (mostovi, isti otok) u `susjedstvo.json`, dokumentirano |
| Portal ili izvor nedostupan tijekom builda ili ocjenjivanja | niska | statički web ne ovisi o izvorima; cache sirovih datoteka s checksumom |
| Nestabilne verzije paketa (duckdb-wasm `latest` je dev build) | srednja | fiksirati verzije, `package-lock.json`, `requirements.txt` s `==` |
| Zadani Python 3.10 ne podržava najnovije pakete | sigurno | `py -3.12` venv i 3.12 u CI-ju |
| Tumačenje pravila o vlasničkom AI asistentu | niska | jasna izjava u dokumentaciji, upit organizatoru, build samo s OSS-om |
| Prazno polje licence kod nekih CKAN skupova (WFS popisa) | srednja | izjava prema Otvorenoj dozvoli; upit DGU-u ili DZS-u |
| Ocjenjivači gledaju samo dokumentaciju i video | sigurno [P] | zamrzavanje u petak, cijela subota za video i dokumentaciju; screenshotovi iz Playwrighta |
| OpenFreeMap nema SLA | niska | pričuvni prazni stil, atribucija u videu („OpenFreeMap © OpenMapTiles Data from OpenStreetMap” [P]) |
| Kvota Workers AI (P2) potrošena | niska | unaprijed izračunati primjeri, poruka „pokušajte sutra”, alternativa WebLLM |

---

## 9. Nacrt za dokumentaciju: „Korišteni alati i licence” (spremno za lijepljenje)

> ### Korišteni alati, biblioteke i licence
>
> Rješenje „Fiskalna karta JLS” razvijeno je i radi isključivo uz softver otvorenog koda. Izvorni kod objavljen je na [github.com/…] pod licencom **EUPL-1.2** (Javna licencija Europske unije v. 1.2). Izvedeni podaci (pokazatelji, ocjene, šifrarnik, generalizirane granice) objavljeni su pod licencom **CC BY 4.0**, uz obvezu navođenja izvornih tijela javne vlasti (vidi „Izvori podataka”). Cijelo rješenje može se izgraditi i pokrenuti samo alatima s ovog popisa (upute u README.md).
>
> **Obrada podataka (Python 3.12, PSF licenca)**
>
> | Alat | Namjena | Licenca |
> |---|---|---|
> | pandas | obrada tablica | BSD-3-Clause |
> | openpyxl | čitanje XLSX izvještaja Ministarstva financija | MIT |
> | DuckDB | SQL i Parquet izvoz | MIT |
> | httpx | pozivi CKAN API-ja i OGC WFS servisa | BSD-3-Clause |
> | pydantic, jsonschema | sheme i validacija API-ja | MIT |
> | pandera, pytest | validacija podataka i testovi | MIT |
> | GeoPandas, Shapely, pyogrio, pyproj | prostorni podaci | BSD-3-Clause / MIT |
> | libpysal | susjedstvo jedinica (simulator spajanja) | BSD-3-Clause |
> | mapshaper | generalizacija granica, TopoJSON | MPL-2.0 |
> | statsmodels | regresija ekonomije razmjera | BSD-3-Clause |
> | scikit-learn | statistički blizanci (kNN) | BSD-3-Clause |
> | rdflib, pySHACL | DCAT-AP katalog i validacija | BSD-3-Clause / Apache-2.0 |
> | Jinja2 | predlošci teksta | BSD-3-Clause |
>
> **Web aplikacija**
>
> | Alat | Namjena | Licenca |
> |---|---|---|
> | React, Vite, React Router | aplikacija i build | MIT |
> | TypeScript | tipovi | Apache-2.0 |
> | Tailwind CSS, shadcn/ui, Radix UI | sučelje | MIT |
> | Lucide | ikone | ISC |
> | MapLibre GL JS | interaktivna karta | BSD-3-Clause |
> | Apache ECharts | grafikoni | Apache-2.0 |
> | topojson-client | geometrija | ISC |
> | Turf.js | spajanje poligona | MIT |
> | Fuse.js | pretraga | Apache-2.0 |
> | Scalar API Reference | dokumentacija API-ja | MIT |
> | Vitest | testovi | MIT |
> | Playwright | testovi | Apache-2.0 |
> | Inter | font | SIL OFL 1.1 |
> | [DuckDB-WASM] | [ako se koristi] | MIT |
>
> **Umjetna inteligencija u rješenju**
> - **Gemma 4 E4B-it** (Google DeepMind), licenca **Apache 2.0**, pokreće se lokalno pomoću **llama.cpp** (MIT). Model piše objašnjenja ocjena razumljivim jezikom. Sve brojke računa naš kod, a deterministički verifikator provjerava da se svaka brojka u tekstu podudara s podacima. Tekstovi koji ne prođu provjeru zamjenjuju se predloškom. Svaki tekst je u aplikaciji označen kao AI-generiran.
> - [Ako se koristi] **Gemma 4 26B-A4B-it** (Apache 2.0) izvodi se preko usluge Cloudflare Workers AI (vlasnička usluga, besplatni plan) za funkciju „Pitaj podatke”. Model vraća samo SQL upit, koji se provjerava i izvršava lokalno u pregledniku (DuckDB-WASM), pa brojke u odgovoru uvijek dolaze iz podataka. Ista funkcija može raditi s bilo kojim OpenAI-kompatibilnim poslužiteljem (npr. vlastiti llama.cpp).
> - Statističke metode: k-najbližih susjeda (scikit-learn), OLS regresija (statsmodels).
>
> **AI alati korišteni u razvoju (nisu dio rješenja)**
> - **Claude Code** (Anthropic; vlasnički softver) korišten je kao asistent za programiranje i pisanje dokumentacije. Sav kod pregledao je i integrirao tim. Rješenje ne ovisi o tom alatu. Prema uvjetima korištenja pružatelja, prava na generirane izlaze pripadaju korisniku.
> - [navesti i druge, npr. ChatGPT ili Copilot, ako su korišteni]
>
> **Usluge**
> - GitHub (repozitorij, GitHub Actions, GitHub Pages): hosting i automatsko osvježavanje podataka.
> - OpenFreeMap: kartografska podloga. Podaci © OpenStreetMap contributors (ODbL), © OpenMapTiles. Podloga je zamjenjiva, a aplikacija radi i bez nje.
> - Video: OBS Studio (GPL-2.0), Kdenlive (GPL-3.0).
>
> **Izvori podataka** (popuniti iz istraživanja o podacima)
>
> | Skup podataka | Izdavač | Pristup | URI | Licenca | Zadnja izmjena |
> |---|---|---|---|---|---|
> | Financijski izvještaji JLP(R)S (PR-RAS, RAS-funkcijski, Bilanca) 2019.–2025. | Ministarstvo financija | HTTP preuzimanje [ili CKAN] | [URL] | [Otvorena dozvola ili navesti] | [datum] |
> | Popis stanovništva 2021., stanovništvo po gradovima/općinama | Državni zavod za statistiku | data.gov.hr CKAN API v3 | [CKAN URI] | Otvorena dozvola | [datum] |
> | Kućanstva – ukupno na razini gradova/općina iz Popisa stanovništva 2021. INSPIRE (granice 556 JLS) | Državna geodetska uprava / DZS | OGC WFS 2.0 (INSPIRE) | https://transformiraj.nipp.hr/ows/services/org.14.b8096c46-3962-421f-baf8-918a45735eed_wfs | izjava prema Otvorenoj dozvoli | [datum] |
>
> Izjava o izvoru: „Sadrži informacije Ministarstva financija, Državnog zavoda za statistiku i Državne geodetske uprave u skladu s Otvorenom dozvolom (https://data.gov.hr/otvorena-dozvola/). Podaci su izmijenjeni: izračunati su financijski pokazatelji i ocjene, a granice su generalizirane i spojene. Ocjene su izračun autora i nisu službena ocjena tijela javne vlasti.”

---

## 10. Što je provjereno, a što pretpostavljeno

**Provjereno u ovom istraživanju [P]:**
- licence i verzije svih paketa iz tablica (PyPI, npm i GitHub API, 2026-11-02);
- licence modela (HF API `cardData.license`); Gemma 4 pod Apache-2.0 (i preusmjeravanje stranice licence na `ai.google.dev/gemma/apache_2`);
- EU klauzula u Llama 3.2 AUP;
- EuroEval hrvatska ljestvica (podaci od 2026-10-27);
- veličine GGUF datoteka i Ollama manifesta;
- modeli u WebLLM 0.2.87;
- llama.cpp opcije (`--reasoning`, `json_schema`, `cache_prompt`) i Windows buildovi;
- Workers AI cijene, besplatna kvota, Gemma 4 26B-A4B dostupna na besplatnom planu, OpenAI-kompatibilan endpoint i JSON Mode;
- limiti GitHub Pagesa i Cloudflarea;
- CORS: CKAN ne šalje zaglavlje, GitHub Pages šalje `*`, WFS reflektira Origin;
- data.gov.hr CKAN 2.9.9 s ckanext-dcat i harvesterima te DCAT-AP izlaz;
- WFS s 556 poligona, GeoJSON i veličina 196 MB;
- WFS za Upravne jedinice je isključen;
- uvjeti Otvorene dozvole;
- OpenFreeMap uvjeti i atribucija; pravila OSM tile usluge;
- održavanje Observable Frameworka;
- uvjeti GitHub Actions cron-a;
- Anthropic Consumer Terms o vlasništvu izlaza;
- hardver i softver laptopa;
- citati iz Pravila i Javnog poziva.

**Nije provjereno ili je procjena [N, Procjena]:**
- brzine generiranja na ovom laptopu (izmjeriti `llama-bench`-om);
- stvarna tečnost hrvatskog teksta (EuroEval ne mjeri generiranje; potrebna slijepa usporedba);
- točan parametar za isključivanje reasoninga na Workers AI za Gemma 4 26B-A4B;
- oblik AST-a iz `json_serialize_sql` u DuckDB-WASM 1.32.0;
- primjenjivost čl. 50 AI Acta na ovaj prototip i točan naziv i broj NN zakona o pristupačnosti;
- izvor i licenca MF podataka 2019.–2025. (pokriva istraživanje o podacima);
- podrška alata za OpenAPI 3.2.

---

## Izvori

- Pravila Datathona (PDF u repozitoriju); Javni poziv: https://data.gov.hr/uploads/images/2026-10-23/1792757323727_javnipozivdatathonportalaotvorenihpodatakasaizmjenomrokaprijave.pdf
- Otvorena dozvola: https://data.gov.hr/otvorena-dozvola/
- EuroEval, hrvatska ljestvica: https://euroeval.com/leaderboards/croatian
- Gemma 4 model card i licenca: https://huggingface.co/google/gemma-4-E4B-it, https://ai.google.dev/gemma/docs/gemma_4_license
- Llama 3.2 Use Policy: https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/USE_POLICY.md
- OSI o licenci Llame: https://opensource.org/blog/metas-llama-2-license-is-not-open-source
- EUPL 1.2, hrvatski tekst: https://interoperable-europe.ec.europa.eu/sites/default/files/custom-page/attachment/eupl_v1.2_hr.pdf
- llama.cpp server README: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- Workers AI cijene: https://developers.cloudflare.com/workers-ai/platform/pricing/; OpenAI kompatibilnost: https://developers.cloudflare.com/workers-ai/configuration/open-ai-compatibility/
- Cloudflare Pages limiti: https://developers.cloudflare.com/pages/platform/limits/; Workers limiti: https://developers.cloudflare.com/workers/platform/limits/
- GitHub Pages limiti: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- GitHub Actions okidači (schedule): https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- OpenFreeMap: https://openfreemap.org/; OSM Tile Usage Policy: https://operations.osmfoundation.org/policies/tiles/
- Observable Framework issue #2045: https://github.com/observablehq/framework/issues/2045
- Anthropic Consumer Terms: https://www.anthropic.com/legal/consumer-terms
- DCAT-AP: https://github.com/SEMICeu/DCAT-AP/releases; data.gov.hr DCAT: https://data.gov.hr/ckan/catalog.ttl
