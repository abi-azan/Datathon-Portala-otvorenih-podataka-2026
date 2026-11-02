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
- `pipeline/build.py` is an exploratory draft that implements the v1 indicators, not v2. It joins all 576 units across MF PR-RAS, Bilanca and DZS Popis 2021.
- When building starts, add build/run/test commands and an architecture overview here.

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
- Ministry of Finance local-budget data (PR-RAS, RAS-funkcijski, Bilanca) is on mfin.gov.hr only, not on the portal, and has no stated licence. Overdue liabilities (`dio 23/24/26 D`) exist only in the 2025 Bilanca. The MF national aggregate for functional classes in 2025 is incomplete, so validate per unit instead.
- The default `python` is 3.10. Use `py -3.12` for packages that need a newer Python.
- Known dead or unusable sources, despite being listed on the portal: the AIK "Poslovne zone u RH" JSON (403), the MGIPU contract-register CSVs (unreachable), FINA RGFI (tagged CSV but actually a login page), and FINA "Informacije o ugovorenim koncesijama" (its datastore holds the HTML/JS of a search form, not concession records). Check that any source is live before building on it.

## Environment gotchas (Windows)

- `python -I` ignores `PYTHONIOENCODING`, and the console is cp1252, so printing Croatian characters crashes. Call `sys.stdout.reconfigure(encoding="utf-8")` and open files with `encoding="utf-8"`.
- `.gstack/` holds gstack browser logs and ignores itself. Don't commit it.
