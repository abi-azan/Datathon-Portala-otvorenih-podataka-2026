# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Student team entry for the **Datathon Portala otvorenih podataka 2026** (organizer: MPUDT), challenge **C: Gospodarstvo i učinkovito upravljanje** (economy and efficient governance). The team prefers economics/finance topics and communicates in Croatian.

Chosen idea (2026-10-29): **Fiskalna karta JLS + dashboard**, a fiscal health map of all 576 local and regional self-government units with peer comparison and a merger simulator.

- **The plan is `docs/PLAN.md` (v2, 2026-11-02).** It holds the methodology (0-100 score with KDZ/INEKO anchors, displayed as 5 = best), the scope, the stack and the schedule. Supporting research is in `docs/research/00-04`.
- The user confirmed the plan on 2026-11-02 (PLAN.md §11), including the innovation package (Karta reforme, visible number verification, MCP server as SHOULD) and the cuts from an independent review. Building can start.
- LLM texts are generated on a free Kaggle GPU (Gemma 4, Apache-2.0), driven through the official Kaggle MCP server (`https://www.kaggle.com/mcp`). Tools used: `save_notebook` (takes `machine_shape`, `model_data_sources`, `dataset_data_sources`), `get_notebook_session_status`, `download_notebook_output`, `get_accelerator_quota`, `upload_dataset_file`.
  - Auth: OAuth through `/mcp` did not work. The server is registered in local scope with an `Authorization: Bearer KGAT_…` header. The token lives in `secrets.txt`, which is gitignored; never print it or commit it. Without auth every call returns "Unauthenticated".
  - GPU quota is 30 h per week and resets Saturday 00:00 UTC (checked 2026-11-02).
  - Kaggle Models `google/gemma-4` has GGUF variants `gemma-4-e4b-it-qat-q4_0-gguf`, `gemma-4-12b-it-qat-q4_0-gguf`, `gemma-4-26b-a4b-it-qat-q4_0-gguf` and `gemma-4-31b-it-qat-q4_0-gguf`. Attach them as a model data source instead of downloading from Hugging Face. The exact source-string format is not yet confirmed.

## Build and test

```
py -3.12 -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pipeline.build             # fetch sources (conditional GET) and build, ~2-4 min
.venv/Scripts/python -m pipeline.build --offline   # reuse data/raw
.venv/Scripts/python -m pytest -q tests            # all tests
.venv/Scripts/python -m pytest -q tests/test_methodology.py::test_flags   # one test
```

`tests/test_data.py` runs against `data/build/`, so build first; it is skipped when the build is missing. The build needs Node.js on PATH, because the geo step runs `npx -y mapshaper@0.6.102`.

## Architecture (ETL)

- `pipeline/sources.py` downloads every source and logs the URL, time, ETag, sha256 and CKAN metadata in `data/raw/sources.json`. That log is the provenance record for the "Izvori" page.
- `pipeline/mf.py` parses the MF workbooks.
  - PR-RAS goes into a long table that keeps workbook, sheet and Excel row for every value. The product uses these to show where a number comes from.
  - Bilanca gives one wide row per unit and year.
  - PR-RAS parsing takes about 2 min. It is cached in `data/build/prras_long.parquet`, keyed on the ZIP's sha256.
- `pipeline/units.py` builds the šifrarnik for 576 units: OIB, RKP, 5-digit DGU code (`Z01`-`Z20` for counties), name, county and slug.
  - PR-RAS sheet names are matched to Bilanca names within each county.
  - The OIB is then looked up in `data/reference/jls_master.csv`. That file is curated, holds 556 JLS, and was built from the DGU ATOM boundaries, the development index and an island flag.
- `pipeline/population.py` reads Popis 2021 from the DZS WFS.
- `pipeline/geo.py` reads the 556 unit polygons from the DZS WFS. It computes the official area, Queen neighbours with shared border length, an island flag and sea links. It also writes `data/build/geo/jls.topo.json` (layers `jls` and `zupanije`, simplified to 4% with mapshaper through `npx`) and `susjedi.json`.
  - Sea links connect the land components of a county, shortest gap first. The merger simulator and Karta reforme stay inside one county, so every county graph has to be connected.
  - Island units are those with no land path to Zagreb or Konavle (Konavle is in the Dubrovnik exclave beyond Neum).
  - `jls_master.csv` no longer holds area, island flag or neighbour count; they come from this step.
- `pipeline/openness.py` builds the openness layer.
  - It pages through all portal datasets with CKAN `package_search` (about 4,000 datasets, 4 calls) and maps each publishing organization to a unit.
  - It matches names without diacritics, because the portal writes "Konjšćina" and MF writes "KONJŠČINA". A county suffix such as "(ZD)" settles duplicate names like Privlaka.
  - Per unit it records the number of datasets, the last update, the machine-readable share and a link to the newest budget dataset.
- `pipeline/methodology.py` holds PLAN §3 as pure functions: auxiliary quantities, windowed indicators I1-I5, 0-100 scores, grades, four weight scenarios, flags Z1-Z4 and context measures. It also holds the two overdue-liability rules, decided 2026-11-03 (background in `docs/research/05`):
  - A loan reported as entirely overdue, while its principal is repaid at 3% a year or more, does not count toward DO. The unit gets the quality note `kredit_iskazan_kao_dospio`.
  - DO ≥ 30% of operating spending caps points at 39.9, so the grade is at most 2. `bodovi_bez_ogranicenja` keeps the uncapped points.
- `pipeline/facts.py`, `verify.py` and `explain.py` produce the AI explanation (PLAN §5).
  - Facts are pre-formatted Croatian strings. Python picks the story: the weakest component, the strengths and the comparison with the peer median.
  - The verifier fails a text when it contains a number not in the facts, or a grade other than this year's or last year's. A failed text is retried with feedback, at most twice, and then the template is used.
  - `verify.py` uses only the standard library, because it is embedded verbatim in the Kaggle script.
- `kaggle/gemma_runner.py` is a template. `python -m pipeline.explain --kaggle-test N` embeds the number check, the prompt code and N fact packs into `kaggle/gemma_test.py`.
  - Push and run with `KAGGLE_API_TOKEN=<from secrets.txt> .venv/Scripts/kaggle kernels push -p kaggle`, using the Kaggle CLI 2.x (pip `kaggle` and `six`). The token must never be printed.
  - The Kaggle user is `albertmari`. The notebook builds llama.cpp from source with `-DCMAKE_CUDA_ARCHITECTURES=75` for the T4 and serves the model with `llama-server --jinja`.
  - The model source string is `google/gemma-4/gguf/gemma-4-e4b-it-qat-q4_0-gguf/2`. The files are `gemma-4-E4B_q4_0-it.gguf` (5.2 GB) and an mmproj.
  - Re-check a downloaded output with `python -m pipeline.explain --check <gemma_test_output.json>`.
- `pipeline/build.py` orchestrates the steps above and writes `data/build/units.csv`, `results.parquet`, `results.json` and `geo/`.

Source documents:
- Rules: `1792415200857_praviladatathonfinal.pdf` (in repo)
- Javni poziv (deadlines, challenge description, scoring): https://data.gov.hr/uploads/images/2026-10-23/1792757323727_javnipozivdatathonportalaotvorenihpodatakasaizmjenomrokaprijave.pdf
- Competition page: https://data.gov.hr/-datathon_portala_otvorenih_podataka2026

## Hard constraints

- **Submission deadline: 09.11.2026 24:00**, by email to open.data@mpudt.hr. Late or video-less submissions are not scored.
- The submission must contain: source code or a public repo link, technical and project documentation (including an architecture description and a **list of every dataset used with its publisher and source link**), demo materials (prototype link, screenshots), and a **video of up to 3 min**. The video must cover the problem, target users, data sources, features, architecture, user value and further development.
- Open-source software only. AI tools and libraries are allowed but must respect their licenses and be **listed in the documentation**.
- Data must be public-sector open data, with data.gov.hr preferred. Other public sources are allowed if their license permits it. Attribution is mandatory.
- A public GitHub repo with an open-source license is scored.

## Scoring (max 60): what to optimize for

| Criterion | Pts |
|---|---|
| Izvedivost: working prototype, ready to use | 10 |
| Dojam: UI/UX | 10 |
| Video presentation | 10 |
| Open data used **directly via APIs** (scores higher than downloaded files) | 5 |
| Meaningfully linking multiple sources into new value | 5 |
| Relevance to challenge C | 5 |
| Impact / benefit to users | 5 |
| Innovative use of advanced tech (AI, etc.) | 5 |
| Architecture: interoperable standards, integration with existing public systems, technical/organizational/legal prerequisites stated | 5 |

Tie-breakers: Izvedivost first, then open data use. The organizer may withhold a prize if no entry reaches 50 points. With about 12 days to build, favor a small, finished, polished scope over breadth.

## Data access (verified 2026-10-28)

- **CKAN API v3**, no key needed: `https://data.gov.hr/ckan/api/3/action/`. Example: `package_search?fq=theme:economy_and_finance&rows=1000&start=0` (1025 datasets; `rows` is capped at 1000, so page with `start`).
- `package_search` returns HTTP 502 when `q` contains Croatian diacritics (e.g. `stanovništvo`). Search with ASCII terms (`stanovnistvo`).
- `datastore_search?resource_id=...` only works for resources with `datastore_active=true` (206 of 2790 in the economy theme). Column headers there are often garbage from badly imported XLSX files.
- About 84% of economy datasets come from municipalities, cities and counties: budgets, procurement plans, contract registers. Mostly XLSX/PDF/XLS, each publisher with its own layout. Only about 107 are CSV and 50 are JSON.
- Working external APIs: Sudski registar REST API at `https://sudreg-data.gov.hr` (free registration; OpenAPI spec at `/api/javni/dokumentacija/open_api`), HNB exchange rates at `https://api.hnb.hr/tecajn-eur/v3`.
- Sudski registar API v3.0.4 uses OAuth2 client credentials (`/api/oauth/token`). It serves whole tables paged with `offset`/`limit` per `snapshot_id`: `/subjekti` (`datum_osnivanja`, `datum_brisanja`, `postupak`, `glavna_djelatnost` as an NKD code), `/sjedista` (`sifra_opcine`, `naziv_opcine`; DGU code lists are not included), `/postupci` (bankruptcy and liquidation), `/gfi` (which annual financial reports were filed and when), `/promjene`. It covers companies only, not obrti.
- CKAN responses carry no CORS header, so a browser can't call the portal API directly. API use has to happen in the ETL or CI.
- Municipal boundaries plus Census 2021 population per unit: the DZS INSPIRE WFS at `transformiraj.nipp.hr` (556 polygons, GeoJSON, CORS enabled). The DGU "Upravne jedinice INSPIRE" ATOM ZIP is the fallback with an explicit Otvorena dozvola licence. The DGU WFS is disabled. Exact URLs are in `docs/research/04-podaci-granice-i-varijable.md`.
  - Polygons come from `su-vector:AreaStatisticalUnit` (`config.WFS_BOUNDARIES`), about 196 MB in 20 s. The service sends no ETag, so every online build downloads it again.
  - GeoJSON output is always lon/lat, whatever `SRSNAME` says. The feature `id` is `StatisticalUnit_<code>`, `areaValue` is m², and the names are mojibake, so names come from the register.
  - Borders are topologically clean: tolerances of 0.5 m and 5 m give the same 1,360 Queen pairs. Areas add up to 56,561.75 km², against the DZS figure of 56,561.5.
- Ministry of Finance local-budget data (PR-RAS, RAS-funkcijski, Bilanca) is on mfin.gov.hr only, not on the portal, and has no stated licence.
- Overdue liabilities exist in every Bilanca year from 2019 to 2025. 2025 labels the columns `dio 23 D` / `dio 23 N`. Earlier years label both columns `dio 23`, and only the second header row says "- dospjele" or "- nedospjele" (verified 2026-11-02; this corrects an earlier note that they exist only for 2025).
- MF level 22 is the unit's own budget without its budget users: account 367 (transfers to own budget users) is still in 3.
  - RAS-funkcijski leaves 367 out, so the control sum R1 = 3 + 4 − 367 holds for each unit.
  - Every PR-RAS sheet has a column-numbering row under the header (1, 2, 3, …). Its "3" is not account 3, so skip it.
- Unit sums of accounts 6 and 3 match the national sheet "SVEUKUPNO OPĆ_GRAD_ŽUPANIJA" in workbook 22 to within 1 € for every year.
- The default `python` is 3.10. Use `py -3.12` for packages that need a newer Python.
- State Audit Office (DUR) reports, used for the audit-opinion layer (verified 2026-11-03):
  - The list is HTML at `https://www.revizija.hr/izvjesca/10?pojamIzvjesce=&godinaID=<id>&page=N`, 40 items per page. Year ids: 2026=3164, 2025=3035, 2024=2901, 2023=2810, 2022=2686, 2021=1465, 2020=1275, 2019=1276.
  - Links are Windows-style backslash paths under `/UserDocsImages`. The folder names say the unit type (OPCINE/GRADOVI/ZUPANIJE, or JLPRS/OPĆINE in 2020-2021). Skip follow-up checks (PROVJER*, PPNNP), budget users, companies and summary reports.
  - The PDFs are text. The opinion (bezuvjetno/uvjetno/nepovoljno mišljenje, or suzdržavanje) is found by regex. The publication year is not the audited year.
  - About 330 of 576 units have at least one financial audit since 2019. Name matching has to handle bilingual Istrian names and "DJ" for "Đ".
- Known dead or unusable sources, despite being listed on the portal: the AIK "Poslovne zone u RH" JSON (403), the MGIPU contract-register CSVs (unreachable), FINA RGFI (tagged CSV but actually a login page), and FINA "Informacije o ugovorenim koncesijama" (its datastore holds the HTML/JS of a search form, not concession records). Check that any source is live before building on it.

## Environment gotchas (Windows)

- `python -I` ignores `PYTHONIOENCODING`, and the console is cp1252, so printing Croatian characters crashes. Call `sys.stdout.reconfigure(encoding="utf-8")` and open files with `encoding="utf-8"`.
- `.gstack/` holds gstack browser logs and ignores itself. Don't commit it.
