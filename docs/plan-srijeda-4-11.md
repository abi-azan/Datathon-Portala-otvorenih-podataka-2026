# Plan za srijedu 4.11.2026. (rafinirano 3.11. u 8:45)

Plan su sastavile noćna smjena i dvije neovisne procjene: ETL, podaci i AI, te frontend i UX. Uzete su u obzir i Fable preporuke iz `docs/noc-3-11.md` ("Fable, 8:00"). **PLAN.md nije mijenjan.** Ovo je radni plan za jedan dan, a odluke O1-O8 su na korisniku.

Oznake:
- **[S]** može raditi subagent sam;
- **[K]** treba korisnika (odluka, push, pristup);
- **[S+K]** subagent priprema, korisnik potvrđuje.

Kriterij gotovosti za svaki zadatak s kodom: `pytest` prolazi, a za web i `tsc`, `oxlint` i `npm run build`. Uz to vrijedi kriterij naveden kod zadatka.

## Odluke za korisnika (ujutro, prije svega ostalog)

| # | Odluka | Prijedlog | Zašto je važno |
|---|---|---|---|
| O1 | AI model i prikaz | **Gemma 4 12B.** Jedinice koje ne prođu provjeru dobivaju predložak, s jasnom oznakom na profilu. Treba izmijeniti rečenicu iz PLAN §5 "AI tekst se ne prikazuje samo za dio jedinica". | Uz 85 % prolaza oko 85 jedinica dobiva predložak. Bez izmjene pravila AI tekst se ne bi smio prikazati nikome. |
| O2 | Gdje računa simulator | **Unaprijed izračunati** sve povezane skupine od 2-4 jedinice unutar županije, razdijeljene po jedinici. | Statična stranica ne može zvati Python. Prenošenje metodologije u TypeScript znači dvije metodologije. |
| O3 | Sitnice za `merge()` | samo ista županija; bez županija i Zagreba; vrsta = grad ako je u skupini barem jedan grad; pravilo 1 se primjenjuje po članici prije zbroja | Pravilo 1 je nelinearno. Bez dogovora spoj može "otkriti" dospjele obveze kojih nema. |
| O4 | Rezovi (Fable) | rezati MCP, spopt/klizač (Karta reforme pohlepnim pravilom, prag 5.000), blizance i procjenu izravnanja (samo napomena); dva alternativna prikaza karte ostaviti samo ako stane sat posla | Oslobađa 1,5-2 dana za video, deploy i simulator |
| O5 | Tablica umjesto karte | zadano abecedno, filter po županiji i vrsti, rang samo unutar skupine | Tablica sortirana po bodovima je rang-lista (PLAN §6) |
| O6 | Push i Pages | spojiti `noc-3-11` u `main`, pushati, Settings → Pages → "GitHub Actions"; **ukloniti tjedni cron do objave rezultata** | Workflow radi samo na `main`. Pages nije uključen (provjereno: API vraća 404). |
| O7 | Tekst ograde i primjer | npr. "Ocjena je izračun iz javnih podataka, nije službena ocjena Ministarstva financija ni DUR-a."; primjer za video, npr. Sveta Marija ili Povljana | Ograda mora biti na stranici prije javnog URL-a |
| O8 | Popis skupova i licence | potvrditi popis (W8) i izjavu o MF podacima (nema licence, ponovna uporaba prema ZPPI); CC BY 4.0 za naše podatke zapisati u repo | Obavezno u predaji; Fable je našao da CC BY 4.0 nigdje ne piše |

## Zadaci po redoslijedu

### Jutro: prije pusha (paralelno, različite datoteke)

| # | Zadatak | Tko | Ulaz → izlaz | Kriterij gotovosti | Ovisi o | Trajanje |
|---|---|---|---|---|---|---|
| W1 | **Ispravak pokvarenog naziva datoteke** u `prras_long` ("01 Zagrebaƒka.xlsx", CP852 iz ZIP-a) | [S] | `pipeline/mf.py` → ispravni nazivi u `prras_long.parquet` | test: nazivi radnih knjiga sadrže "Zagrebačka"; rebuild prolazi | - | 1 h |
| W2 | **Rezerva za CI**: ulaz `snapshot` u workflowu (preskače ETL), ponavljanje u `sources.ckan()` (502), uklanjanje `schedule`, zaključane verzije (`requirements.lock` ili `==`) | [S+K] | `.github/workflows/deploy.yml`, `pipeline/sources.py`, `requirements.txt` | workflow YAML se parsira; `ckan()` ponavlja 3× s pauzom (test); korisnik potvrđuje commitanje snimke API-ja | O6 | 1,5 h |
| W3 | **Ograda, "što je ovo", "probaj primjer"** na naslovnici, uz ocjenu na profilu i u footeru | [S+K] | `Home.tsx`, `Profile.tsx`, `Layout.tsx` | tekst iz O7 vidljiv na sva tri mjesta; snimka 1440 px | O7 (može s privremenim tekstom) | 1 h |
| W4 | **Push i prvi CI run** | [K] | spajanje grane, Pages | stranica na `https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/` se otvara, karta i profil rade, bez grešaka u konzoli | W2, W3, O6 | 15 min + run 20-30 min |

### Dan: AI i podaci

| # | Zadatak | Tko | Ulaz → izlaz | Kriterij gotovosti | Ovisi o | Trajanje |
|---|---|---|---|---|---|---|
| W5 | **Potvrdni AI test v6**: 20 *novih* jedinica, samo 12B | [S+K] | `explain.py` (novi seed, isključeni OIB-ovi iz `kaggle/results/*`), metadata samo s 12B i `kernel_sources` na test bilježnicu | ≥ 16/20 `source=="ai"` + ručni pregled jezika, upisano u `research/06` kao v6; ako je ispod 16, vratiti korisniku (26B ili Claude) | O1 | 1,5 h + oko 0,1 h GPU-a |
| W6 | **Batch za 576 jedinica i integracija** | [S+K] | `explain.py --kaggle-batch` (paketi kao Kaggle dataset ili u dva dijela), nastavak nakon prekida (preskače gotove OIB-ove) → `data/ai/objasnjenja-2025.json` (`meta`: model, GGUF, llama.cpp commit, sha256 prompta; `tekstovi`: `{oib: {tekst, pack_sha256, pokusaja}}`); `publish.explanation()` uzima AI tekst ako `pack_sha256` odgovara i `verify` prolazi, inače predložak; polje `model` u OpenAPI | `test_api`: barem 80 % profila ima `izvor=="ai"`; nakon batcha `facts.py`, `verify.py` i prompt se zamrzavaju | W5 | 2,5 h + 2,5-3 h Kaggle preko noći |
| W7 | **`wide.parquet` i `merge()`** | [S] nakon O2, O3 | `build.py` sprema `data/build/wide.parquet` (p_* i b_* po jedinici i godini); `pipeline/merge.py`: zbroj sa `sum(min_count=1)`, pravilo 1 po članici, `methodology.evaluate_unit` bez izmjena, rang u postojećoj skupini | testovi: spoj jedne jedinice = `results.parquet`; simetričnost; Sveta Marija + susjed ne dobiva lažni DO | O2, O3 | 4-5 h |
| W8 | **Popis skupova podataka** kao jedan izvor istine | [S+K] | `data/reference/skupovi.csv` (naziv, izdavatelj, URL, licenca, način pristupa, uloga) iz `sources.json` + ručno (DGU ATOM, indeks razvijenosti, DUR, OpenFreeMap/OSM, Gemma na Kaggle Models) → `publish.py` ga objavljuje u API-ju; isti popis ide u README | svaki izvor koji kod koristi je na popisu, a ništa nekorišteno nije; korisnik potvrđuje | O8 | 1-1,5 h |

### Dan: frontend (prvo W9, ostalo poslije zbog istih datoteka)

| # | Zadatak | Tko | Ulaz → izlaz | Kriterij gotovosti | Ovisi o | Trajanje |
|---|---|---|---|---|---|---|
| W9 | **Prerada `GradeMap` i lijeno učitavanje** | [S] | `GradeMap` dobiva props (`colorBy`, `selectable`, `selected`, `onSelect`) i učitava se preko `React.lazy`; header se ne lomi na 375 px | početni JS < 400 KB (profil ne učitava MapLibre); 375 i 768 px bez vodoravnog pomicanja; snimke preko `build` i `preview` | - | 3 h |
| W10 | **Tablica kao alternativa karti i tipkovnica** | [S] | `UnitTable.tsx` (prekidač Karta/Tablica), strelice na odabiru godine, vidljiv fokus | sve dostupno Tabom; Lighthouse pristupačnost ≥ 95 | W9, O5 | 3-4 h |
| W11 | **Ugovori za četvrtak** (bez implementacije): JSON za provenijenciju brojki (`jedinice/<slug>/izvor.json`: formula, godine, ulazi `[{konto, godina, iznos, datoteka, list, redak}]`) i `MergeResult` za simulator | [S] | dokument `docs/ugovori-api.md` + nacrt shema u `openapi.py` | dva subagenta u četvrtak mogu raditi paralelno bez pitanja | W1, W7 | 1 h |

### Tim (paralelno, nisu developeri)

- **Scenarij videa v1** prema PLAN §10, s jedinicom iz O7. Tko snima glas i tko montira?
- **Tekstovi za građane:** rječnik pojmova i oblačići za pet sastavnica (side-quest 5).
- **Lektura:** 17 tekstova iz `kaggle/results/gemma_test_v5_e4b_12b.json` (12B) i 10 pravila stila (side-quest 9).

## Prenosi se na četvrtak i petak

- **Četvrtak:**
  - vidljiva provjera brojki (J, prema ugovoru iz W11; klik vodi na formulu i tablicu ulaza, ne na jednu ćeliju);
  - sučelje simulatora (K, ruta `#/simulator?j=a,b`);
  - AI tekstovi u profilu sa značkom modela (M);
  - ušteda na upravi (medijan po razredu veličine umjesto regresije, ako se O4 prihvati).
- **Petak:**
  - Karta reforme (pohlepno pravilo, prag 5.000, unaprijed izračunato);
  - stranice Izvori i Metodologija (`metodologija.json` iz `methodology.py`, prompt i verifikator javno);
  - README s arhitekturom;
  - snimke zaslona.

## Rizici

- **Memorija na laptopu** je oko 1-1,5 GB slobodno. Pregled u pregledniku radi jedan subagent u isto vrijeme, preko `build` i `preview`.
- **Prvi CI run:** mfin.gov.hr i WFS (196 MB) mogu biti spori, a CKAN zna vratiti 502. Rezerva je W2.
- **Batch skripta** sa 576 ugrađenih paketa imat će oko 1 MB, a ograničenje Kaggle pusha nije poznato.
- **Nakon batcha** svaka promjena `facts.py` tiho prebacuje profile na predložak (provjera `pack_sha256`). Test iz W6 to hvata.
- **Svaki zadatak koji dira `Home.tsx` ili `GradeMap.tsx`** čeka W9.
