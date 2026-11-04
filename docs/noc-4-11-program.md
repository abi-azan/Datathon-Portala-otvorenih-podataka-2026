# Noćna smjena 4.11.2026. (od početka do 9:30): program

Ti si noćna smjena za projekt **Fiskalna karta JLS** (repo `C:\Users\marsi\Documents\FER\datathon`). Korisnik spava i ujutro pregledava. Radiš samostalno, od početka do **9:30**, prema ovom programu.
- **Ne postavljaj pitanja.** Sve što traži novu odluku zapiši u dnevnik pod "Odluke za korisnika" i nastavi sa sljedećim zadatkom.
- Pišeš na hrvatskom, u stilu `docs/noc-3-11.md`.

**Cilj noći:**
1. Pravilo 1 je prošireno.
2. AI tekstovi Gemme 4 31B postoje za svih 576 jedinica i prikazuju se na profilima.
3. Simulator spajanja ima sučelje, uštedu na upravi i, ako prođe provjeru, fiskalno izravnanje.
4. Karta reforme ima izračun.

Sve je na grani `noc-4-11`, testirano i opisano u dnevniku.

## 0. Prvih 15 minuta

1. **Pročitaj:**
   - `CLAUDE.md`;
   - `docs/PLAN.md`: §3.1, §4, §5, §6 i posebno **§11, odluke 14-17** (odluke od 4.11. su obavezujuće);
   - `docs/plan-srijeda-4-11.md`;
   - `docs/research/05-dospjele-obveze-stvarna-prica.md`;
   - `docs/research/06-gemma-test.md` (v6 i v7);
   - `docs/research/01-metode-financijskog-zdravlja.md` §5 (simulator i izravnanje);
   - `docs/noc-3-11.md`, za stil dnevnika.
2. **Stanje na početku (4.11. oko 2 h):**
   - `main` je na `f06f3cc` ili novijem commitu s dokumentacijom.
   - Stranica je uživo na https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/.
   - 64 testa prolaze.
   - Simulator (`pipeline/merge.py`) već računa 13.353 skupine u `data/build/simulator/zup-XX.json` i objavljuje ih u `api/v1/simulator/`, ali bez uštede, bez izravnanja i bez sučelja.
   - GPU kvota: oko 27,9 h do 7.11. u 01:00 po našem vremenu.
3. **Pripremi okolinu:**
   - `git checkout main && git pull && git checkout -b noc-4-11`;
   - napravi dnevnik `docs/noc-4-11.md` (raspored i prazan odjeljak "Primopredaja");
   - provjeri GPU kvotu (Kaggle MCP `get_accelerator_quota`);
   - provjeri slobodnu memoriju (PowerShell `Get-CimInstance Win32_OperatingSystem`).
4. **Pokreni subagenta R** (zadatak N5, izravnanje) u pozadini odmah. Ne ovisi ni o čemu.

## 1. Pravila rada (bez iznimke)

- **Git:**
  - Commit po zadatku, na granu `noc-4-11`. Smiješ `git push origin noc-4-11`, jer push grane ne pokreće deploy.
  - **`main` ne diraj, ne spajaj i ne pushaj.** Ne pokreći `/ship` ni `/land-and-deploy`.
- **Autor commita je uvijek korisnikov git identitet (abi-azan).** Nikad ne dodaj `Co-Authored-By` ni bilo kakav spomen Claudea kao autora, ni u commitu ni u PR-u. Strogo zabranjeno.
- **Tajne:**
  - Kaggle token iz `secrets.txt` nikad se ne ispisuje.
  - Uzima se ovako: `export KAGGLE_API_TOKEN="$(grep -o -m1 'KGAT_[A-Za-z0-9_-]*' secrets.txt)"`, a izlaz se maskira s `sed -E 's/KGAT_[A-Za-z0-9_-]+/***/g'`.
  - `secrets.txt` se ne čita ni ne commita.
- **Zamrzavanje nakon N2:** kad se generiraju paketi za batch, sve što mijenja pakete činjenica je zamrznuto do kraja smjene:
  - datoteke: `pipeline/facts.py`, `verify.py`, `explain.py` (SYSTEM, RULES, EXAMPLE, `messages`, `feedback`), `methodology.py`, `units.py`, `mf.py`, `population.py`, `data/reference/*`;
  - **build samo s `--offline`**, jer online build može povući nove podatke MF-a i tiho promijeniti pakete.
  - Ako nešto od toga treba mijenjati, zapiši to kao odluku za korisnika.
- **Metodologija:** jedina dopuštena promjena je N1. Ostalo (pragovi, ponderi, prompt) se ne dira.
- **GPU:**
  - Noćas se troši samo za batch (N2/N8), najviše oko 6 h uključujući ponavljanje.
  - Bez novih A/B testova.
  - Model je **Gemma 4 31B-it QAT Q4_0** s Kaggle Models: `google/gemma-4/gguf/gemma-4-31b-it-qat-q4_0-gguf/2`.
- **Memorija laptopa** je oko 1,5 GB slobodno.
  - Bez `npm run dev`. Pregled ide kroz `npm run build` i `npx vite preview`, uvijek samo jedan preglednik odjednom, a server se gasi nakon pregleda.
  - Istovremeno najviše 2 subagenta.
- **Preglednik:** samo gstack `/browse` (headless `$B`). Nikad `mcp__claude-in-chrome__*`.
- **Kriterij gotovosti za svaki zadatak s kodom:**
  - `.venv/Scripts/python -m pytest -q tests` prolazi;
  - za web još i `npx tsc -b`, `npx oxlint` i `npm run build` (u `web/`);
  - za sučelje snimka zaslona na 1440 px bez grešaka u konzoli.
- **Windows:** `py -3.12` i venv. Kod ispisa hrvatskih znakova koristi `sys.stdout.reconfigure(encoding="utf-8")`.
- **Iskreno izvještavanje:** što ne radi ili je preskočeno, piše u dnevniku, s izlazom testa.

## 2. Raspored

Vremena vrijede uz početak oko 2:00. Ako počneš kasnije, pomakni sve osim dva fiksna roka:
- **batch mora krenuti najkasnije u 4:30**;
- **primopredaja je 9:00-9:30.**

| Vrijeme | Glavna smjena | Subagenti |
|---|---|---|
| 2:00-2:15 | §0 priprema | R kreće (N5) |
| 2:15-3:00 | **N1** pravilo 1 | R |
| 3:00-4:30 | **N2** batch kod i pokretanje na Kaggleu | R |
| 4:30-5:15 | **N3** AI tekst u API-ju i na profilu | R |
| 5:15 | **Šefovski krug 1** | |
| 5:20-6:00 | **N4** ušteda na upravi; `merge()` bez ograničenja veličine | R |
| 6:00-7:30 | **N6** sučelje simulatora | K kreće (N7) |
| 7:00 | **Šefovski krug 2** (batch, subagenti, prioriteti) | |
| 7:30-8:00 | **N5b** izravnanje u simulatoru (ako R prođe provjeru); **N9** code review | K |
| 8:00-8:45 | **N8** preuzimanje batcha, provjera i objava | |
| 8:45-9:00 | **Šefovski krug 3**; pregled i commit K; N10 samo ako je sve ostalo gotovo | |
| 9:00-9:30 | **Primopredaja** | |

**Za sve fiksne točke postavi podsjetnike** (šefovski krugovi, 8:00 batch i 9:00 primopredaja), npr. alatom CronCreate ako je dostupan. Između zadataka svejedno provjeri sat (`date`). Na Kaggle se čeka pozadinskom petljom (Bash `run_in_background`), bez uzastopnog ručnog provjeravanja.

## 3. Zadaci

### N1. Pravilo 1 za kredit u povlačenju (odluka 17)

- **Što:** `methodology.loan_reported_all_due_but_repaid` vraća `True` i kad je stanje kredita (`b_26`) veće od stanja prethodne godine (`prev["b_26"]`). Kredit se tada još povlači.
  - Uvjeti ostaju isti: kredit veći od `LOAN_ALL_DUE_MIN` i `b_26_D` barem `LOAN_ALL_DUE_SHARE` kredita.
  - Prva godina serije (nema `prev`) ne računa se kao povlačenje.
  - Zapiši konstantu ili komentar s pozivom na odluku 17.
- **Testovi:**
  - novi slučaj u `tests/test_methodology.py`;
  - u `tests/test_data.py`: kod Svete Marije 2023. ocjena više nije ograničena (`ogranicenje_do` je False), a `kredit_iskazan_dospio` je True.
- **Provjera nakon `build --offline`:**
  - **ocjene za 2025. su iste** (5/4/3/2/1 = 306/149/68/43/10);
  - u 2020.-2024. promijeni se oko 20 jedinica-godina, a oko 10 izgubi ograničenje (prijedlog iz `docs/noc-3-11.md`, 10:45);
  - prije commita zapiši stvarne brojke u dnevnik.
- **Ako se promijeni ijedna ocjena za 2025.:** vrati N1 (`git checkout -- pipeline/methodology.py`), zapiši nalaz kao odluku za korisnika i nastavi s N2 na postojećoj metodologiji. Batch ne smije kasniti zbog N1.
- **Dokumentacija:** kratki odjeljak "Proširenje 4.11." u `research/05` i rečenica u PLAN §3.1 uz pravilo 1.
- **Gotovo:** testovi prolaze, simulator je ponovno izračunat (build), commit.

### N2. Batch za 576 jedinica (W6, prvi dio)

- **Kod (`pipeline/explain.py`, zatim zamrzavanje):**
  - `pack_sha256(pack)`: sha256 od `json.dumps(pack, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`.
  - `--kaggle-batch`: paketi za svih 576 jedinica za `LAST_YEAR`, ugrađeni u Kaggle skriptu (isti runner `kaggle/gemma_runner.py`; po potrebi parametar za ime izlaza).
  - `--skip <izlaz.json>`: izostavlja OIB-e koji su već gotovi, za nastavak nakon prekida.
  - Uz skriptu se piše `data/ai/manifest-2025.json`: `{oib: pack_sha256}` i sha256 prompta (SYSTEM, RULES i EXAMPLE).
- **Bilježnica `albertmari/fiskalna-karta-jls-gemma-batch`:**
  - privatna, `machine_shape: NvidiaTeslaT4`, internet uključen;
  - `model_sources` je samo 31B Q4_0;
  - `kernel_sources: ["albertmari/fiskalna-karta-jls-gemma-test"]` (gotov llama-server, bez izgradnje od 30 min);
  - metadata spremi kao `kaggle/kernel-metadata-batch.json`.
- **Push:** iz privremene mape s `kernel-metadata.json` i skriptom (kao v6 i v7 u `research/06`), naredbom `.venv/Scripts/kaggle kernels push -p <mapa>`.
  - Ako push padne zbog veličine skripte, podijeli pakete na dva dijela (A/B, po 288) i pokreni ih jedan za drugim.
- **Praćenje:** pozadinska petlja svakih 60 s s `kaggle kernels status`, do COMPLETE, ERROR ili CANCEL.
  - Očekivano trajanje je oko 21 s po tekstu, dakle oko 3,4-3,8 h. Runner sprema izlaz nakon svake jedinice.
- **Ako padne:**
  - preuzmi djelomični izlaz, generiraj skriptu s `--skip` i pokreni novu verziju (najviše 2 puta);
  - ako 31B dvaput padne iz infrastrukturnih razloga (OOM, timeout), ostatak pokreni s 12B (`gemma-4-12b-it-qat-q4_0-gguf/2`), koji je rezerva prema README-u, i bilježi model po tekstu.
- **Gotovo:** batch se vrti, a commit sadrži kod, manifest i metadatu.

### N3. AI tekst u API-ju i na profilu (W6, drugi dio)

- **Uvoz:** `python -m pipeline.explain --import-batch <izlaz.json> [<izlaz2.json> ...]` piše `data/ai/objasnjenja-2025.json` (commita se):
  - `meta`: model, GGUF, Kaggle izvor modela, commit llama.cpp-a, sha256 prompta, bilježnica i vrijeme;
  - `tekstovi`: `{oib: {tekst, pack_sha256, pokusaja, izvor: "ai"|"neprovjereno", model}}`;
  - `pack_sha256` se uzima iz manifesta; uvoz upozori ako se trenutni paket razlikuje.
- **`publish.explanation()`** uzima AI tekst samo ako je `izvor=="ai"`, ako je `pack_sha256` jednak trenutnom paketu i ako `verify.verify(tekst, pack)` prolazi. Inače se koristi predložak.
  - Polja u profilu: `izvor` ("ai" ili "predlozak"), `model` i `provjera`. OpenAPI se dopunjuje.
- **Sučelje (`web/src/pages/Profile.tsx`):** oznaka "AI tekst · Gemma 4 31B · N/N brojki provjereno", a za predložak "Predložak · N/N brojki provjereno".
- **Test (`tests/test_api.py`):** ako `data/ai/objasnjenja-2025.json` postoji, barem 95 % profila ima `izvor=="ai"`; inače je test preskočen.
  - Dok batch traje, cijeli lanac isprobaj na izlazu v7 (`kaggle/results/gemma_test_v7_31b_q4_0_ud.json`, 20 jedinica) u privremenoj datoteci, ne u `data/ai/`.
- **Gotovo:** testovi prolaze, snimka profila s oznakom AI teksta, commit.

### N4. Ušteda na općoj upravi i `merge()` bez ograničenja (odluka 17)

- **U `pipeline/merge.py`** sažetak dobiva blok `usteda` za zadnju godinu:
  - `uprava_zbroj`: zbroj (01 − 017 − 018) članica, u €;
  - `medijan_pc`: medijan `uprava_pc` usporedne skupine spojene jedinice za tu godinu, iz `results.parquet`;
  - `ocekivano = medijan_pc × stanovnici`;
  - `strukturni_jaz = max(0, uprava_zbroj − ocekivano)`, tj. gornja granica;
  - `realno_do = min(0,10 × uprava_zbroj, strukturni_jaz)`;
  - `iznad_10000`: True kad spojena jedinica ima više od 10.000 stanovnika, uz upozorenje da se dodatna ušteda ne očekuje (`research/01` §5.4).
- **Tekst za sučelje** je iz `research/01` (prijedlog teksta ispod §5): "Procijenjeni potencijal uštede na općoj upravi: 0 – X € godišnje …".
- **`merge(data, oibs, max_members=MAX_MEMBERS)`:** `None` znači bez ograničenja (za Kartu reforme). `check` je i dalje obavezan za županiju, Zagreb i povezanost.
- **`python -m pipeline.merge --precompute`** ponovno piše `data/build/simulator/` bez cijelog builda.
- **Testovi:** `realno_do ≤ 0,1 × uprava_zbroj` i `realno_do ≤ strukturni_jaz`, jaz nikad nije negativan, a Povljana + Pag imaju smislen blok. OpenAPI shema `Spajanje` se dopunjuje.
- **Gotovo:** testovi, ponovni izračun, publish, commit. Odmah nakon toga može krenuti subagent K (N7).

### N5. Fiskalno izravnanje po zakonskoj formuli (subagent R, od 2:15)

**Brief za subagenta.** Daj mu ovo, plus pokazivače na datoteke:
- **Cilj:** `pipeline/izravnanje.py` s čistim funkcijama i provjerom.
- **Formula:** iz Zakona o financiranju jedinica lokalne i područne (regionalne) samouprave (NN 127/17 i izmjene), uz bilješke iz `research/01` §5.5 i PLAN §4.4:
  - puni iznos = (referentna vrijednost − kapacitet) × stanovnici;
  - kapacitet je višegodišnji prosjek poreza na dohodak po stanovniku;
  - referentne vrijednosti ovise o vrsti; za gradove se računa bez Zagreba.
- **Detalje provjeri u zakonu, ne u bilješkama.**
- **Izvor:** tablice fiskalnog izravnanja na mfin.gov.hr (PLAN §2: "fiskalno izravnanje 2018.-2027.", kapacitet i iznosi po jedinici). Prvo provjeri da je izvor živ.
  - Preuzimanje ide kroz `sources.fetch` (zapis provenijencije).
  - Novi redak ide u `data/reference/skupovi.csv` s licencom: MF prema ZPPI, uz uvjete Otvorene dozvole, kao za ostale podatke MF-a.
- **Provjera (obavezna):** formula na postojećim jedinicama mora reproducirati objavljene iznose MF-a za zadnju godinu u tablici, za **barem 90 % jedinica s odstupanjem do 5 %**.
  - Rezultat provjere i odstupanja (koje jedinice, zašto) idu u `docs/research/07-fiskalno-izravnanje.md`.
- **Procjena za spojenu jedinicu:**
  - kapacitet spojene = (Σ kapacitet × stanovnici) / Σ stanovnici;
  - referentna vrijednost je za vrstu spojene jedinice (grad ako je barem jedna članica grad);
  - izlaz: puni iznos spojene, zbroj punih iznosa članica i promjena.
  - Napomena: isplata je udio u godišnjem iznosu iz proračuna, pa je ovo puni iznos prema formuli.
- **Ograničenja za subagenta:**
  - ne mijenja `merge.py`, `methodology.py`, `facts.py`, `explain.py`, `verify.py` ni `web/`;
  - ne commita;
  - ne pokreće dev server ni preglednik;
  - vraća izvještaj s brojkama provjere.

**N5b (glavna smjena, oko 7:30):**
- **Ako je provjera prošla:** u sažetak simulatora dodaj blok `izravnanje` (puni iznos članica, spojene i promjena) i prikaz u sučelju s napomenom. Zatim precompute, testovi i commit.
- **Ako nije prošla:** sučelje pokazuje napomenu "Spajanje može smanjiti fiskalno izravnanje; procjena nije uključena jer formula ne reproducira objavljene iznose", a u dnevnik ide odluka za korisnika.

### N6. Sučelje simulatora (MUST)

- **Ruta i navigacija:** ruta `#/simulator`, stanje u URL-u `#/simulator?j=<sifra>,<sifra>`. Poveznica "Simulator spajanja" u izborniku postaje aktivna.
- **Odabir:**
  - `GradeMap` u načinu odabira (props `selectable`, `selected`, `onSelect` već postoje);
  - uz kartu je pretraga po nazivu, kao pristupačna alternativa odabiru mišem;
  - najviše 4 jedinice; datoteka `api/v1/simulator/zup-XX.json` učitava se lijeno, za županiju prve odabrane jedinice;
  - dopušteni sljedeći odabir su jedinice koje s trenutnim odabirom čine postojeći ključ u datoteci, a ostale su vidljivo onemogućene, uz razlog (druga županija, ne graniči).
- **Ploča "prije i poslije":**
  - članice (naziv, ocjena, stanovnici) i spojena jedinica (ocjena s riječi, bodovi, "9. od 21 u skupini gradovi 2.000-5.000", pet sastavnica);
  - **apsolutni iznosi u €** (dospjele obveze, uprava);
  - ušteda iz N4 kao raspon s tekstom;
  - izravnanje (N5b) ili napomena;
  - upozorenja (iznad 10.000 stanovnika, zastavice);
  - rečenica "Scenarij za raspravu, ne prijedlog granica";
  - poveznice na svjedodžbe članica i gumb "Počni ispočetka".
- **Primjer za razrjeđivanje** (Povljana + Pag):
  - Povljana sama ima ocjenu 2 i dospjele obveze od 1.045.908 € (49 % rashoda poslovanja).
  - Spojena s Pagom ima ocjenu 5, a dug od oko 1,16 mil. € ostaje i čini 15 % rashoda.
  - Kad udio dospjelih obveza padne, a iznos u € ne, sučelje mora reći: "Dug ne nestaje spajanjem, nego se raspoređuje na veći proračun."
- **Gotovo:**
  - snimke na 1440 px za Povljana + Pag i za skupinu od 3-4 jedinice;
  - na 375 px se stranica ne raspada;
  - u konzoli nema grešaka;
  - `tsc`, `oxlint` i build su čisti; commit.

### N7. Karta reforme: izračun (subagent K, nakon N4; MUST)

**Brief za subagenta:**
- **`pipeline/reforma.py`, pohlepno pravilo (odluka 17):**
  - unutar svake županije, bez županija i Grada Zagreba, ponavljaj: uzmi jedinicu (ili već spojenu skupinu) s najmanje stanovnika ispod praga i spoji je sa susjedom koji ima najmanje stanovnika;
  - kod izjednačenja odlučuje najniža šifra;
  - susjedi i veze preko mora su iz `susjedi.json`;
  - kraj je kad su sve skupine na pragu ili iznad, ili kad skupina nema više susjeda u županiji.
- **Pragovi:** 2.500, 5.000 i 10.000 stanovnika.
- **Rezultat:** skupina se računa kroz `merge.merge(data, oibs, max_members=None)`, s istom metodologijom i uštedom (N4).
- **Izlaz:** `data/build/reforma/prag-XXXX.json`:
  - zaglavlje: `prag`, `n_prije`, `n_poslije`, `stanovnika_u_spojenima`;
  - `jedinice`: sve jedinice nakon reforme, uključujući one koje se nisu spajale. Za svaku: `clanice` (šifre), naziv ("Pag + Povljana"), vrsta, stanovnici, ocjene članica prije, ocjena i bodovi poslije, ušteda.
  - `publish.py` ih kopira u `api/v1/reforma/`, a OpenAPI ih opisuje.
- **Testovi:**
  - svaka jedinica je u točno jednoj skupini;
  - skupine su povezane i unutar jedne županije;
  - svaka skupina je na pragu, osim kad je cijela povezana komponenta županije ispod praga;
  - dva pokretanja daju isti rezultat;
  - viši prag nikad ne daje više jedinica;
  - Zagreb i županije nisu u rezultatu.
- **Ograničenja:** ne mijenja `merge.py` (osim ako glavna smjena tako dogovori), metodologiju ni `web/`; ne commita; vraća izvještaj s brojem jedinica po pragu.

**Glavna smjena:** pregledaj diff, pokreni testove i commitaj.

### N8. Batch: preuzimanje, provjera i objava (oko 8:00)

1. Preuzmi izlaz: `kaggle kernels output albertmari/fiskalna-karta-jls-gemma-batch -p <mapa> --file-pattern '.*\.json$'`.
2. Pokreni `python -m pipeline.explain --check <izlaz>`, a zatim `--import-batch` u `data/ai/objasnjenja-2025.json`.
3. Pokreni `python -m pipeline.publish` i testove (očekuje se barem 95 % AI teksta).
4. Ručno pregledaj 20 nasumičnih tekstova (jezik, sadržaj) i zapiši nalaz u `research/06` kao "v8: batch 576".
5. Commit. Jedinice koje nisu prošle dobivaju predložak s oznakom (odluka O1).
6. **Ako batch u 8:45 još nije gotov:** uvezi ono što postoji (runner sprema djelomično), objavi, a ostatak zapiši u primopredaju. Bilježnica radi dalje, pa korisnik ujutro uvozi ostatak istom naredbom.

### N9. Code review (oko 7:30)

- `/code-review high` na `git diff main...noc-4-11`.
- Ispravi potvrđene nalaze, ponovi testove i u dnevnik zapiši što je ispravljeno, a što nije i zašto.

### N10. Karta reforme: sučelje (samo ako je sve ostalo gotovo)

- Ruta `#/reforma`, klizač s tri praga.
- Karta spaja geometrije članica na klijentu (`topojson-client` `merge` nad `geo/jls.topo.json`).
- Uz kartu: broj jedinica prije i poslije, stanovnici kojih se tiče i raspon uštede. Klik na skupinu otvara ploču sa spojenim rezultatom.
- Ako nema vremena, ovo je prvi zadatak za dnevnu smjenu.

## 4. Šefovski krugovi (5:15, 7:00, 8:45)

Svaki krug je kratak:
1. Gdje smo u odnosu na raspored? Stanje batcha (status, broj gotovih jedinica ako se vidi iz loga) i stanje subagenata.
2. Testovi na grani prolaze? Radna kopija je čista ili commitana? `git push origin noc-4-11`.
3. **Prioriteti:**
   - kad kasnimo, reže se ovim redom: N10, pa uljepšavanje N6, pa N5b (ostaje napomena);
   - N1, N2, N3, N8 i osnovni N6 se ne režu.
4. Kratki zapis u dnevnik: što je gotovo, gdje je i što je otvoreno.

## 5. Primopredaja (9:00-9:30)

Na vrh `docs/noc-4-11.md` ide sažetak, kao u `noc-3-11.md`:
- grana, broj commitova i autor (provjereno: bez Claudea), broj testova, stanje `tsc`, `oxlint` i builda;
- tablica "Područje | Što | Commit" za N1-N10, s jasnim "nije napravljeno" gdje treba;
- brojke:
  - N1: promjene po godinama;
  - batch: X/576 AI, potrošen GPU i preostala kvota;
  - simulator: broj skupina i primjer Povljana + Pag (prije i poslije, ušteda);
  - izravnanje: rezultat provjere;
  - Karta reforme: broj jedinica po pragu;
- **Odluke za korisnika** (numerirane, svaka s prijedlogom);
- **kako preuzeti:** pregled `git diff main...noc-4-11`, pa `git checkout main && git merge --ff-only noc-4-11 && git push`. Push pokreće CI i deploy, a korisnik to radi sam.
- **prvi zadaci za dnevnu smjenu**, prema plan-srijeda: Karta reforme UI ako nije gotova, vidljiva provjera brojki, tablica, video.

Na kraju zadnji `git push origin noc-4-11`. U 9:30 smjena staje.

## 6. Kad nešto pođe po zlu

| Problem | Što napraviti |
|---|---|
| Kaggle push odbijen (veličina) | dva dijela A/B (N2) |
| Bilježnica ERROR | pogledaj log (`kaggle kernels output` donosi i log), ispravi, pokreni s `--skip`; najviše 2 ponovna pokretanja, pa 12B za ostatak |
| Kvota GPU-a niža od očekivane | najprije batch; ništa drugo ne troši GPU |
| Test pada, a uzrok nije jasan za 20 min | `git stash` ili vraćanje zadnje izmjene, zapis u dnevnik, sljedeći zadatak |
| Memorija | ugasi preview i preglednik; nikad dva preglednika odjednom |
| Subagent mijenja datoteku koju ne smije | ne commitaj to; vrati datoteku i zapiši u dnevnik |
| Odluka koja nije u PLAN §11 ni u ovom programu | ne donosi je; zapiši je s prijedlogom i nastavi |

## 7. Što noćna smjena ne radi

- `main`, deploy i postavke repozitorija.
- Promjene metodologije osim N1, promjene prompta ili činjenica nakon N2, online build.
- MCP server, tablicu (dolazi kasnije), blizance (izbačeni), spopt.
- Nove GPU testove i nadogradnju gstacka.
- Brisanje ičega što nije sama napravila.
