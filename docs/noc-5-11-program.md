# Noćna smjena 5.11.2026. (od početka do 9:30): program

Ti si **voditelj** noćne smjene za projekt **Fiskalna karta JLS** (repo `C:\Users\marsi\Documents\FER\datathon`). Korisnik spava i ujutro pregledava. Radiš samostalno, od početka do **9:30**, prema ovom programu.
- **Ne postavljaj pitanja.** Sve što traži novu odluku zapiši u dnevnik pod "Odluke za korisnika" i nastavi sa sljedećim zadatkom.
- Pišeš na hrvatskom, u stilu `docs/noc-4-11.md`.
- Smiješ voditi **najviše 2 subagenta istovremeno**. Ima ih tri, u dva utora:
  - utor 1 je M (MCP server);
  - utor 2 je najprije R (istraživanje prediktora razvoja), a kad R završi, U (vizualni prijedlozi).

**Cilj noći**, sve na grani `noc-5-11`, testirano i opisano u dnevniku:
1. **MCP server** radi, ima testove i upute, i spreman je za kadar u videu. To je SHOULD iz PLAN §11, odluka 9; uvjet iz PLAN §6 (Karta reforme i vidljiva provjera brojki) je ispunjen.
2. **Online build** je prošao sa svim novim izvorima, dakle CI put je provjeren prije pusha.
3. **Code review** dnevnih izmjena je napravljen, a potvrđeni nalazi su ispravljeni.
4. **Dokumentacija za predaju** postoji u nacrtu (`docs/PREDAJA.md`, README), a **video scenarij v3** ima provjerene brojke.
5. **Pilot AI teksta** s novim pravilom konteksta (20 jedinica, Gemma 4 31B) je napravljen, ako ga korisnik u promptu nije isključio.
6. **Vizualni prijedlozi** su na grani, svaki kao zaseban commit, pa korisnik ujutro bira što ostaje.
7. **Istraživanje prediktora gospodarskog razvoja** (R) je gotovo u `docs/research/13-prediktori-razvoja.md`, s jasnom preporukom RAZVITI ili ODBACITI. Noćas se samo istražuje. Razvoj, ako ga korisnik odobri, ide u četvrtak preko dana.

## 0. Prvih 20 minuta

1. **Pročitaj:**
   - `CLAUDE.md`;
   - `docs/TODO.md`;
   - `docs/PLAN.md` §5 (MCP) i §11 (odluke);
   - `docs/research/10-pogled-zirija.md` §3-6;
   - `docs/research/11-porezi-razredi-oznake.md` §2.6;
   - `docs/video-scenarij.md`;
   - `docs/noc-4-11.md`, za stil dnevnika i primopredaje.
2. **Stanje na početku (5.11. oko 0:30):**
   - Lokalni `main` je na commitu s ovim programom i 5 commitova je ispred `origin/main`.
     - `origin/main` je `25c589c` (podatkovni slojevi). Ta je verzija uživo: CI je prošao 4.11. u 16:57 i trajao je 32 min.
     - Ono što je nastalo poslije, tj. kontekst na pregledu jedinice, izravnanje iz odluka MF-a, stanovništvo 2025., ikona i karte, nije pushano.
   - Testovi: **252 prolaze**. **Dva padaju i to je poznato:** `tests/test_api.py::test_ai_texts_cover_almost_every_profile` i `tests/test_verify.py::test_no_false_grade_claims_in_real_model_texts`. Padaju dok se AI tekstovi ne generiraju ponovno (petak). Svaki drugi pad je nov i treba ga riješiti.
   - Paketi činjenica promijenili su se kod 561 od 576 jedinica (izravnanje iz odluka MF-a, kontekst stanovništva i dohotka). Ti profili do petka prikazuju predložak. To je očekivano i nije greška.
   - GPU kvota: 5,6 h od 30 h potrošeno; obnavlja se 7.11. u 01:00 po našem vremenu. Zadnji puni batch trajao je 3,5 h.
   - Memorija laptopa: oko 2,7 GB slobodno od 7,6 GB.
3. **Pripremi okolinu:**
   - `git checkout main && git checkout -b noc-5-11` (bez `pull`: `origin/main` je iza lokalnog);
   - napravi dnevnik `docs/noc-5-11.md` s rasporedom i praznim odjeljkom "Primopredaja";
   - provjeri GPU kvotu (Kaggle MCP `get_accelerator_quota`) i memoriju (PowerShell `Get-CimInstance Win32_OperatingSystem`);
   - pokreni `.venv/Scripts/python -m pytest -q tests` i zapiši broj testova u dnevnik.
4. **Odmah pokreni subagente M i R** u pozadini (briefovi su u §4). Ne ovise ni o čemu.
   - **U kreće čim R završi**, očekivano oko 4:00.
   - Ako R u 4:30 još radi, pošalji mu poruku da preda ono što ima, pa pokreni U.

## 1. Pravila rada (bez iznimke)

- **Git:**
  - Sve ide na granu `noc-5-11`. Commit po zadatku. Smiješ `git push origin noc-5-11`, jer push grane ne pokreće deploy. Pushaj na svakom šefovskom krugu.
  - **`main` ne diraj, ne spajaj i ne pushaj.** Ne pokreći `/ship` ni `/land-and-deploy`. Ne mijenjaj `.github/workflows/` (cron se isključuje danju, s korisnikom).
  - Subagenti commitaju sami, svaki svoj zadatak, **samo s izričitim putanjama** (`git add <putanje>`). Nikad `git add -A` ni `git add .`, ni ti ni oni. Ako postoji `.git/index.lock`, pričekaj nekoliko sekundi i pokušaj ponovno.
- **Autor commita je uvijek korisnikov git identitet (abi-azan).** Nikad ne dodaj `Co-Authored-By` ni bilo kakav spomen Claudea kao autora, ni u commitu ni u PR-u. Strogo zabranjeno. Na primopredaji provjeri: `git log main..noc-5-11 --format='%an %ae%n%b' | grep -i -E "co-authored|claude"` mora biti prazno.
- **Tajne:**
  - Kaggle token iz `secrets.txt` nikad se ne ispisuje.
  - Uzima se ovako: `export KAGGLE_API_TOKEN="$(grep -o -m1 'KGAT_[A-Za-z0-9_-]*' secrets.txt)"`, a izlaz se maskira s `sed -E 's/KGAT_[A-Za-z0-9_-]+/***/g'`.
  - `secrets.txt` se ne čita ni ne commita.
- **Metodologija je zamrznuta:**
  - ne mijenjaju se `pipeline/methodology.py`, pragovi i ponderi, pravila u `facts.py` (pragovi konteksta `CONTEXT_POP_PP_PER_YEAR`, `CONTEXT_INCOME_REL`), `verify.py` ni prompt u `explain.py`;
  - jedina iznimka je jedna iteracija prompta u N3, pod uvjetima iz N3;
  - ako code review (N2) nađe grešku koja traži promjenu metodologije, zapiši je kao odluku za korisnika s prijedlogom i ne mijenjaj ništa;
  - za Belišće se ne radi posebno pravilo (odluka 5.11.);
  - Z5 (kriterij od 10 %) ostaje gdje je.
- **AI i GPU:**
  - **Nema punog generiranja** i nema uvoza u `data/ai/`. Puni batch je u petak, nakon zadnjih promjena.
  - GPU se noćas troši samo za pilot N3, najviše 1 h ukupno.
  - Model je **Gemma 4 31B-it QAT Q4_0**: `google/gemma-4/gguf/gemma-4-31b-it-qat-q4_0-gguf/2`.
- **Memorija i preglednik:**
  - Bez `npm run dev`. Pregled ide kroz `npx vite build --outDir <svoja mapa> --emptyOutDir` i `npx vite preview --outDir <ista mapa> --port <svoj port> --strictPort`, a server se gasi nakon pregleda.
  - Portovi: voditelj 4185, U 4188. M i R ne koriste preglednik.
  - **Istovremeno radi samo jedan headless preglednik:**
    - do početka U-a (oko 4:00) koristi ga voditelj (N9a);
    - dok U radi, koristi ga samo U;
    - nakon U-a opet voditelj (N8, N9b).
  - Svaki preglednik ima svoj daemon: prefiks `BROWSE_STATE_FILE=$S/browse-<ime>.json` (`$S` je scratchpad iz system prompta), a na kraju `$B stop` s istim prefiksom.
  - Samo gstack headless `$B` (`~/.claude/skills/gstack/browse/dist/browse`). **Nikad `mcp__claude-in-chrome__*`.**
- **Kriterij gotovosti za svaki zadatak s kodom:**
  - `.venv/Scripts/python -m pytest -q tests` prolazi, osim dva poznata AI testa;
  - za web još i `npx tsc -b --noEmit`, `npx oxlint` i `npx vite build` (u `web/`);
  - za sučelje snimka zaslona na 1280 px i 375 px, bez grešaka u konzoli i bez vodoravnog pomicanja stranice. Snimke za korisnika idu u `docs/snimke/noc-5-11-*.png`, kao prošle noći.
- **Riječi:** nikad "svjedodžba"; stranica jedinice je "pregled jedinice". U sučelju nema natpisa "procjena DZS-a".
- **Windows:**
  - `.venv/Scripts/python`. Kod ispisa hrvatskih znakova `sys.stdout.reconfigure(encoding="utf-8")`.
  - Kad heredoc u Bashu padne s "unexpected EOF", skriptu napiši alatom Write u `$S` i pokreni je s `PYTHONPATH=.`.
- **Iskreno izvještavanje:** što ne radi ili je preskočeno piše u dnevniku, s izlazom testa.

## 2. Raspored

Vremena vrijede uz početak oko 0:30. Ako počneš kasnije, pomakni sve osim dva fiksna roka:
- **pilot N3 mora krenuti najkasnije u 4:00**;
- **U staje u 8:00** i predaje ono što ima;
- **primopredaja je 9:00-9:30.**

| Vrijeme | Voditelj | Subagenti |
|---|---|---|
| 0:30-0:50 | §0 priprema | M i R kreću |
| 0:50-1:50 | **N1** online build i usporedba | M, R |
| 1:50-3:00 | **N2** code review dnevnih izmjena i ispravci | M, R |
| 3:00-3:30 | **N9a** QA prolaz cijele stranice (preglednik je slobodan) | M, R |
| 3:30 | **Šefovski krug 1** | |
| 3:30-4:00 | **N3** priprema i pokretanje pilota na Kaggleu (u pozadini) | M; R završava |
| 4:00-4:30 | **N11** pregled izvještaja R | M; **U kreće** |
| 4:30-5:30 | **N4** dokumentacija za predaju | M, U |
| 5:30-6:00 | **N5** video scenarij v3; preuzimanje i analiza pilota N3 | M, U |
| 6:00 | **Šefovski krug 2** | |
| 6:00-6:45 | **N6** pregled i uključivanje MCP servera (M) | U |
| 6:45-8:00 | rezerva: zaostaci, nalazi iz N2 i N9a (šalju se U-u), nacrt primopredaje | U, do 8:00 |
| 8:00 | **Šefovski krug 3** | |
| 8:00-8:30 | **N7** pregled prijedloga (U), commit po commit | |
| 8:30-9:00 | **N8** snimka naslovnice; **N9b** kratka završna provjera | |
| 9:00-9:30 | **N10 primopredaja** | |

Za fiksne točke postavi podsjetnike: šefovske krugove, 4:00 pilot i početak U-a, 8:00 kraj U-a i 9:00 primopredaju, npr. alatom CronCreate ako je dostupan. Između zadataka svejedno provjeri sat (`date`). Na Kaggle i na duge naredbe čekaj pozadinskom petljom (Bash `run_in_background`), bez uzastopnog ručnog provjeravanja.

## 3. Zadaci voditelja

### N1. Online build (provjera CI puta)

CI na pushu radi puni online build. Noćas se prvi put svi novi izvori dohvaćaju zajedno:
- DZS PxWeb (6 tablica, HTTP 429 nakon desetak brzih poziva);
- DZS XLSX "Gradovi i općine u statistici";
- Porezna uprava (dohodak, razredi, stope, potrošnja, nekretnine);
- tablice i odluke MF-a za izravnanje 2021.-2025.;
- tablica MF-a za 2027.

Bolje je da padne noćas nego u petak.

1. Spremi `data/build/results.parquet` i `data/raw/sources.json` u `$S/prije/`.
2. Pokreni `.venv/Scripts/python -m pipeline.build` (bez `--offline`) s izlazom u `$S/build-online.log` i izmjeri vrijeme. Zatim `python -m pipeline.publish` i testove.
3. **Usporedi i zapiši:**
   - koji su izvori promijenili sha256 u `sources.json`;
   - je li bilo `::warning::`, ponovnih pokušaja ili 429;
   - koliko se ocjena za 2025. promijenilo, s popisom;
   - promjene u brojkama koje koristi video: Povljana 39,9 bodova i ocjena 2, dospjele obveze 1.045.908 € i 49,4 %, Pag + Povljana, Karta reforme 555 → 239 na pragu 5.000, ušteda 0-36,1 mil. €.
4. **Ako build padne:**
   - ako je uzrok naš kod (parsiranje, ponovni pokušaj), ispravi ga, dodaj test i commitaj;
   - ako je izvor nedostupan, zapiši to kao rizik za CI s prijedlogom i nastavi s `--offline`.
5. **Gotovo:** zapis u dnevniku. Commitaju se samo ispravci koda (`data/raw` i `data/build` nisu u gitu).

### N2. Code review dnevnih izmjena

- **Opseg:** sve što je na grani, a nije na `origin/main` (`git diff origin/main...noc-5-11`), tj. sve od `25c589c`: rad agenata od 4.11. poslijepodne. Pokreni `/code-review high` nad tim rasponom; ako vještina gleda samo radnu kopiju, pregledaj raspon commitova izravno.
- **Posebno pogledaj:**
  - `pipeline/izravnanje_isplate.py` i njegov utjecaj na ZO i I4 u `methodology.py` (ulazi u ocjenu);
  - `pipeline/kontekst.py` i `pipeline/dzs_xlsx.py` (pravilo da PxWeb ima prednost, oznake "-" i "z");
  - pravila konteksta u `facts.py` i `verify.py`;
  - spajanje serije uživo i spremljene serije u `web/src/lib/dzs.ts`;
  - pretapanje boja u `GradeMap.tsx` i isticanje u `ReformMap.tsx`.
- **Ispravci:**
  - potvrđene nalaze u `pipeline/` i `tests/` ispravi odmah;
  - nalaze u web datotekama koje drži U pošalji U-u porukom (SendMessage), ili ih ispravi nakon što U završi (8:15-9:00);
  - nalaz koji traži promjenu metodologije ide u odluke za korisnika (§1).
- **Gotovo:** testovi, commit, a u dnevniku što je ispravljeno, a što nije i zašto.

### N3. Pilot AI teksta s pravilom konteksta (uvjetno, kreće najkasnije u 4:00)

**Preskoči ovaj zadatak ako u korisnikovom promptu piše "Pilot N3: NE".**

Svrha je provjeriti, prije punog batcha u petak, poštuje li Gemma 4 31B novo pravilo 8: jedna završna rečenica "Za kontekst, što ne ulazi u ocjenu: …", vrijednosti prepisane točno i bez povezivanja s ocjenom. To nije regeneracija, pa se ništa ne uvozi u `data/ai/`.

1. Uzorak od 20 jedinica, od kojih barem 10 ima kontekst u paketu (`"kontekst": true`).
   - `python -m pipeline.explain --kaggle-test 20 --fresh` bira uzorak sam (`pick_test_units`). Ako uzorak nema dovoljno jedinica s kontekstom, dodaj u CLI opciju za takav uzorak. To je promjena koda, a ne prompta, pa `prompt_sha256` ostaje isti.
   - CLI piše preko `kaggle/gemma_test.py`. Na grani je to u redu, pa novu verziju commitaj.
2. Bilježnica `albertmari/fiskalna-karta-jls-gemma-test` pokreće se iz privremene mape, kao v6 i v7 u `research/06`:
   - kopija `kaggle/kernel-metadata.json` u kojoj je `model_sources` samo 31B Q4_0 (gore);
   - push naredbom `.venv/Scripts/kaggle kernels push -p <mapa>`, s tokenom prema §1;
   - praćenje pozadinskom petljom svakih 60 s (`kaggle kernels status`).
   - **Budžet: najviše 1 h GPU-a ukupno.**
3. Preuzmi izlaz i pokreni `python -m pipeline.explain --check <izlaz>`.
4. Zapiši u `docs/research/06-gemma-test.md` kao "v9: pilot konteksta (31B)":
   - koliko tekstova prolazi provjeru, ukupno i među onima s kontekstom;
   - razloge odbijanja;
   - 5 primjera teksta, od kojih 3 s kontekstom;
   - trajanje i potrošen GPU.
5. **Ako među tekstovima s kontekstom prolazi manje od 80 %:**
   - smiješ **jednom** prilagoditi samo `RULES` ili `EXAMPLE` u `explain.py`, uz zapis zašto;
   - zatim pokreni drugi pilot, u istom budžetu od 1 h;
   - ako ni tada ne prođe barem 80 %, vrati prompt na prethodni (`git revert`) i zapiši odluku za korisnika s prijedlogom.
6. **Gotovo:** zapis u `research/06`, commit i stanje kvote u dnevniku.

### N4. Dokumentacija za predaju

1. Pročitaj pravila (`1792415200857_praviladatathonfinal.pdf` u repou, alatom Read sa stranicama) i zahtjeve iz CLAUDE.md, odjeljak "Hard constraints". Zapiši točan popis onoga što predaja mora sadržavati.
2. Napravi `docs/PREDAJA.md`:
   - **tablicu provjere** "Zahtjev | Gdje je ispunjen | Stanje" za:
     - izvorni kod i javni repozitorij s licencom otvorenog koda;
     - tehničku i projektnu dokumentaciju s opisom arhitekture;
     - **popis svih skupova podataka s izdavačem i poveznicom** (`docs/skupovi-podataka.md` se generira);
     - demo (poveznica na prototip, snimke zaslona);
     - video do 3 min sa 7 obaveznih elemenata;
     - popis AI alata i knjižnica s licencama;
     - navođenje izvora (atribuciju);
   - **nacrt e-maila** za open.data@mpudt.hr: predmet, tijelo, poveznice i popis privitaka. **Ne šalje se.**
   - popis onoga što treba napraviti ili osvježiti na dan predaje, npr. snimke 8.11., poveznicu na video i završni commit.
3. **README:** pregledaj i dopuni postojeće odjeljke "Arhitektura", "Licence" i "Korišteni AI alati".
   - U "Arhitektura" dodaj dijagram (mermaid): izvori (CKAN API, DZS WFS i PxWeb, MF, Porezna uprava, DUR) → ETL u CI-ju → statični API (OpenAPI 3.1, DCAT-AP) → web, MCP server i AI tekstovi na Kaggleu.
   - Popis AI alata mora biti potpun i istinit: Gemma 4 31B (Apache-2.0) preko llama.cpp (MIT) na Kaggleu; Claude Code (Anthropic) kao razvojni asistent; gstack kao alat za pregled u pregledniku. Provjeri licence.
   - Preduvjeti (tehnički, organizacijski, pravni) i daljnji razvoj: provjeri da postoje i da su točni.
   - Ne diraj odjeljak koji M dodaje za MCP. M piše u `docs/mcp.md`, a ti u README dodaješ samo poveznicu (N6).
4. **Gotovo:** commit (`docs/PREDAJA.md`, `README.md`).

### N5. Video scenarij v3

- U `docs/video-scenarij.md` **provjeri svaku brojku** prema trenutnom API-ju, nakon N1. U dnevnik zapiši tablicu "brojka | datoteka i polje | vrijednost | promijenjeno?".
- **Dodaj nove mogućnosti** gdje imaju smisla:
  - značka "uživo s API-ja DZS-a" na pregledu jedinice (kriterij API);
  - kartica "Fiskalno izravnanje" (npr. Samobor, niža stopa poreza);
  - isticanje i prekidač "Prikaži samo spojene" na Karti reforme;
  - pretapanje boja u animaciji godina;
  - kadar MCP servera, ako je N6 gotov.
- Naracija najviše oko 330 riječi (žiri: govoriti sporije), a video ispod 3:00. Tablica pokrivenosti 7 obaveznih elemenata ostaje i mora biti točna.
- Označi kadrove koji se smiju snimiti tek nakon regeneracije AI teksta: kadar s AI tekstom Povljane i "N/N brojki provjereno".
- **Gotovo:** commit.

### N6. MCP server: pregled i uključivanje (nakon izvještaja subagenta M)

- Pregledaj M-ov commit (`git show`) i pokreni testove, uključujući `tests/test_mcp.py`.
- Provjeri da je SDK u `requirements.txt` s fiksnom verzijom, jer CI radi `pip install -r requirements.txt`.
- Server pozovi sam, malom skriptom preko SDK klijenta: `pronadi_jedinicu("povljana")`, `pregled_jedinice` i `scenarij_spajanja` za Pag + Povljana.
- Dodaj u README kratak odjeljak "MCP server" s poveznicom na `docs/mcp.md` i redak u arhitekturi. Commit.
- **Ako M nije gotov do 7:30:** uključi ono što radi, a ostatak zapiši u primopredaju.

### N7. Vizualni prijedlozi: pregled (nakon izvještaja subagenta U)

- Za svaki U-ov commit:
  - pogledaj diff i snimke;
  - provjeri da ne kvari ništa drugo (testovi, `tsc`, build).
- Commit koji kvari nešto vrati s `git revert`, uz zapis.
- U primopredaji napravi tablicu "Prijedlog | Commit | Snimke | Preporuka (zadržati ili ne)", jer korisnik ujutro bira. Svaki commit se može vratiti zasebno.

### N8. Snimka naslovnice za README (nakon U)

- Build i preview (port 4185), naslovnica na 1280×800, nakon što se karta učita (pričekaj oko 5 s), u `docs/snimke/naslovnica.png`.
- Na vrh README-a, iznad "Što radi", stavi tu sliku s alt tekstom.
- U `docs/TODO.md` već piše da se snimka mora ponovno napraviti 8.11. Ostavi to tako.

### N9. QA cijele stranice (N9a u 3:00, N9b u 8:30)

**N9a (3:00-3:30, prije U-a), puni prolaz.**
- Rute na 1280 i 375 px:
  - `#/`;
  - 10 nasumičnih pregleda jedinica, uključujući Povljanu, Pag, Samobor, Grad Zagreb i jednu županiju;
  - `#/simulator` s 3 skupine;
  - `#/reforma` s pragovima 2.500, 5.000 i 10.000;
  - `#/metodologija`.
- Za svaku zapiši: greške u konzoli (bez WebGL upozorenja headless preglednika), `scrollWidth` i vrijeme učitavanja naslovnice.
- Sitnice u `pipeline/` ispravi odmah. Nalaze u `web/src/` daj U-u kao dodatni zadatak (porukom), ili ih zapiši.

**N9b (8:30-9:00, nakon U-a), kratka provjera:** 5 ruta na 1280 i 375 px, da U-ove izmjene nisu ništa pokvarile:
- `#/`;
- Povljana;
- Samobor;
- `#/simulator?j=05738,03166`;
- `#/reforma?prag=5000`.

### N11. Istraživanje prediktora razvoja: pregled (oko 4:00, nakon izvještaja R)

- Pročitaj `docs/research/13-prediktori-razvoja.md`.
- Provjeri 2-3 ključne tvrdnje:
  - ponovi jednu brojku empirijske provjere R-ovom skriptom iz `$S/R/`;
  - otvori jedan izvor.
- Provjeri da je preporuka (RAZVITI ili ODBACITI) obrazložena i da je trošak u satima realan za četvrtak.
- **Ne razvijaj ništa.** U primopredaju stavi sažetak:
  - preporuka;
  - što bi se gradilo i za koliko sati;
  - utječe li na pakete činjenica (tada mora biti gotovo do petka u 17 h);
  - glavni rizici.

### N10. Primopredaja (9:00-9:30)

Na vrh `docs/noc-5-11.md` ide sažetak, kao u `noc-4-11.md`:
- grana, broj commitova i autor (provjereno: bez Claudea), broj testova (uz dva poznata AI testa), stanje `tsc`, `oxlint` i builda;
- tablica "Područje | Što | Commit" za N1-N11, s jasnim "nije napravljeno" gdje treba;
- **brojke:**
  - online build: izvori koji su se promijenili, promjene ocjena;
  - pilot: X/20 prolazi, a od toga koliko s kontekstom; potrošen GPU i preostala kvota;
  - MCP: alati i testovi;
  - QA: rute;
- **istraživanje R:** preporuka RAZVITI ili ODBACITI, ključne brojke i prijedlog opsega za četvrtak (iz N11);
- **prijedlozi U** s preporukom (tablica iz N7);
- **Odluke za korisnika**, numerirane, svaka s prijedlogom;
- **kako preuzeti:**
  1. pregled `git diff main...noc-5-11`;
  2. `git checkout main && git merge --ff-only noc-5-11`;
  3. **push na `main` tek nakon regeneracije AI tekstova u petak.** CI pokreće testove, a dva AI testa padaju dok tekstovi ne budu novi, pa bi deploy pao i stranica ostala stara;
  4. cron u `deploy.yml` isključiti prije zamrzavanja; treba `gh` token s ovlašću `workflow`;
- **plan za četvrtak i petak:** odluke iz ove smjene; ako je istraživanje R odobreno, razvoj u četvrtak preko dana; zadnje promjene koje mijenjaju pakete do petka u 17 h; puni batch (3,5 h); uvoz, push i CI; subota rezerva i zamrzavanje u 20 h.

Na kraju zadnji `git push origin noc-5-11`. U 9:30 smjena staje.

## 4. Briefovi za subagente

Sva tri su Opus s effortom high. Istovremeno rade najviše dva: M cijelo vrijeme, a R pa U jedan za drugim. Daj im brief u cijelosti, uz `$S` iz svog system prompta. Svi rade na grani `noc-5-11` i commitaju sami, samo svoje putanje, a ti pushaš.

### Subagent M: MCP server (kreće u 0:50)

- **Cilj:** read-only MCP server "Fiskalna karta" nad našim statičnim API-jem (PLAN §5). Bilo koji AI asistent koji podržava MCP može odgovarati na pitanja o jedinicama našim brojkama, uz izvor.
- **Tehnika:**
  - službeni MCP Python SDK (`mcp` na PyPI): provjeri licencu (očekuje se MIT) i fiksiraj verziju koja radi s Pythonom 3.12 u `.venv`; dodaj je u `requirements.txt` (jedan redak);
  - transport stdio (FastMCP);
  - paket se zove `fiskalna_mcp/`, a **ne `mcp/`**, jer bi `mcp/` zasjenio SDK pri importu;
  - pokretanje: `.venv/Scripts/python -m fiskalna_mcp [--api <URL ili mapa>]`. Zadano je javni API `https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/api/v1/`, a mapa `web/public/api/v1` služi za testove i rad bez mreže. Odgovori se drže u memoriji, a upiti imaju vremensko ograničenje.
- **Alati** (nazivi i opisi na hrvatskom; izlaz je JSON koji zadržava poveznice na izvor):
  1. `pronadi_jedinicu(naziv, zupanija=None)`: pretraga bez dijakritika nad `jedinice.json`. Vraća slug, naziv, vrstu, županiju i ocjenu.
  2. `pregled_jedinice(jedinica, godina=None)`: ocjena, bodovi, sastavnice, usporedna skupina i rang, zastavice, kontekst (stanovništvo, dohodak, izravnanje), objašnjenje s oznakom AI ili predložak, poveznica na `#/jedinica/<slug>` i na `izvor.json`.
  3. `usporedi(jedinice)`: 2-5 jedinica jedna uz drugu, uz medijane skupina.
  4. `scenarij_spajanja(jedinice)`: traži skupinu u `simulator/zup-XX.json` (2-4 susjeda iz iste županije). Vraća stanje prije i poslije, raspon uštede, promjenu isplate izravnanja, poticaj i demografiju. Za nevaljanu kombinaciju daje jasnu poruku zašto (druga županija, ne graniče, Zagreb).
  5. `karta_reforme(prag, jedinica=None)`: sažetak `reforma/prag-N.json` (broj prije i poslije, ušteda, poticaj, preraspodjela izravnanja), a uz zadanu jedinicu i njezinu skupinu.
  6. `izvor_brojke(jedinica, pokazatelj)`: formula i ulazi s listom i retkom u datotekama MF-a, iz `izvor.json`.
  - Po izboru resurs `metodologija` (`metodologija.json`).
- **Pravila:**
  - server nikad ne izmišlja brojke; vraća samo podatke iz API-ja, s poveznicama;
  - riječ "svjedodžba" se ne koristi.
- **Testovi** u `tests/test_mcp.py`, preskaču se ako lokalni API ne postoji. Koriste klijent iz SDK-a u memoriji. Provjeravaju:
  - popis alata;
  - Povljanu: ocjena 2 i 39,9 bodova;
  - Pag + Povljana `05738,03166`: spojena ima ocjenu 5;
  - nevaljanu kombinaciju, koja vraća poruku umjesto greške;
  - pretragu bez dijakritika ("povljana", "osijek").
- **Dokumentacija** ide u `docs/mcp.md` (README ne dira, to radi voditelj):
  - što server radi i kako se pokreće;
  - primjer konfiguracije za MCP klijent (npr. Claude Desktop JSON);
  - naredba za MCP Inspector (`npx @modelcontextprotocol/inspector …`; provjeri točnu sintaksu i licencu);
  - za video, 2-3 primjera pitanja s očekivanim pozivima alata i odgovorima (kadar od 10 s).
  - Ako projekt negdje nabraja licence Python knjižnica, dodaj i SDK.
- **Ograničenja:**
  - smije mijenjati samo `fiskalna_mcp/`, `tests/test_mcp.py`, `requirements.txt` (jedan redak) i `docs/mcp.md`;
  - ne treba ni ne pokreće preglednik ni dev server;
  - ne dira `pipeline/`, `web/` ni `data/`.
- **Commit:** `git add fiskalna_mcp tests/test_mcp.py requirements.txt docs/mcp.md`, poruka na hrvatskom, bez spominjanja Claudea.
- **Vraća izvještaj od najviše 250 riječi:** verzija SDK-a i licenca, alati, testovi, naredba za pokretanje i otvorena pitanja.

### Subagent R: istraživanje prediktora gospodarskog razvoja (kreće u 0:50, rok 4:00)

- **Pitanje korisnika:**
  - Postoje li u otvorenim podacima pouzdani **prediktori gospodarskog razvoja** jedinica koje bi Fiskalna karta mogla pokazati?
  - Vrijedi li to graditi prije zamrzavanja u subotu u 20 h?
  - Noćas se samo istražuje. Sutra korisnik odlučuje razvija li se ili odbacuje, pa je odgovor "nije vrijedno" ili "nije moguće" jednako dobar kao "da", ako je dobro obrazložen.
- **Što istražiti:**
  1. **Što je "razvoj" i kako ga izmjeriti po jedinici** (ciljna varijabla). Kandidati:
     - promjena indeksa razvijenosti MRRFEU između izdanja (provjeri koja izdanja postoje po JLS i gdje);
     - rast neto dohotka po stanovniku 2022.-2025. (Porezna uprava, `data/build/porezna_dohodak.parquet`);
     - promjena broja stanovnika 2021.-2025. (`data/build/dzs.parquet`);
     - promjena ocjene fiskalne održivosti 2019.-2025. (`data/build/results.parquet`).

     Za svaki: pokrivenost, godine i slabosti.
  2. **Kandidati za prediktore po JLS**, s izvorom, godinama, licencom i načinom pristupa (API ili datoteka).
     - Ono što već imamo u `data/build/`:
       - kapitalna ulaganja, dug, EU sredstva (konto 638), trošak uprave i vlastiti prihodi (`wide.parquet`, `results.parquet`);
       - dobna struktura iz Popisa 2021. (`st_0_14`, `st_65_plus` u `units.csv`);
       - migracije, prirodni prirast, dozvole i turizam;
       - dohodak i udio mirovina;
       - otvorenost podataka (CKAN), revizije DUR-a, indeks razvijenosti, otok.
     - Novi izvori; za svaki provjeri da je živ:
       - nezaposlenost po JLS (HZZ);
       - novi poslovni subjekti po sjedištu (Sudski registar API traži registraciju; **ne registriraj račun**, samo zapiši);
       - EU projekti po JLS (MRRFEU popis operacija, `research/09` §2.7);
       - obrti;
       - prometna dostupnost.
     - Ne gradi novi dohvat u `pipeline/`.
  3. **Literatura**, ukratko i s izvorima, najviše 8-10, primarni gdje je moguće:
     - što predviđa lokalni gospodarski rast (ljudski kapital, demografija, dostupnost, ulaganja, institucije);
     - sustavi ranog upozorenja za fiskalne poteškoće općina (npr. SAD, Italija, slovački INEKO, austrijski KDZ);
     - hrvatski radovi EIZ-a i Instituta za javne financije.
  4. **Brza empirijska provjera**, samo u `$S/R/`, ne u repou. Na našim podacima izmjeri ima li ijedan kandidat stvarnu prediktivnu moć. Primjer: prediktori iz 2019.-2021. → ishod 2022.-2025. (rast dohotka po stanovniku, promjena stanovništva, pad ocjene).
     - Jednostavno i pošteno: korelacije, regularizirana ili logistička regresija s unakrsnom provjerom, R² ili AUC izvan uzorka.
     - **Uvijek usporedi s naivnim modelom**: samo prošli trend, ili samo indeks razvijenosti.
     - Bez lova na p-vrijednosti; zapiši koliko je modela isprobano.
  5. **Vrijednost za proizvod i žiri:**
     - kako bi to izgledalo u sučelju (npr. kartica "Izgledi" na pregledu jedinice, prikaz na karti, rano upozorenje);
     - što dobiva korisnik (načelnik, novinar, ministarstvo);
     - koji kriterij bodovanja diže (inovativnost, utjecaj, povezivanje izvora).
  6. **Rizici:**
     - etički i komunikacijski: oznaka "jedinica u padu" za konkretnu općinu;
     - statistički: malo godina, 556 jedinica, šum u malim jedinicama, prenaučenost;
     - vremenski: rok, zamrzavanje u subotu u 20 h, i paketi činjenica do petka u 17 h ako se išta dodaje u AI tekst.
- **Izlaz:** `docs/research/13-prediktori-razvoja.md`.
  - Na hrvatskom, jednostavnim riječima i kratkim rečenicama, bez dugih crtica (—). Svaki pojam objašnjen je primjerom iz naših podataka (npr. Pag, Bogdanovci).
  - Oznake: [V] provjereno, [P] procjena, [N] nije nađeno.
  - Struktura:
    1. sažetak s **preporukom: RAZVITI, s opsegom, ili ODBACITI, s razlogom**;
    2. ciljna varijabla;
    3. prediktori (tablica);
    4. literatura;
    5. empirijska provjera (metoda, brojke, usporedba s naivnim modelom);
    6. prijedlog za proizvod: ako RAZVITI, što točno, koje datoteke, trošak u satima za četvrtak i utječe li na pakete činjenica;
    7. rizici;
    8. izvori.
- **Ograničenja:**
  - read-only u repou, osim izvještaja;
  - skripte idu u `$S/R/`, a preuzete datoteke odvojeno u `$S/R/raw/`;
  - ne dira `pipeline/`, `web/`, `data/` ni testove;
  - **ne koristi preglednik**, nego WebSearch i `curl -sL`;
  - ne registrira račune i ništa ne šalje van;
  - PxWeb samo uz pauze od 2-5 s;
  - Python `.venv/Scripts/python`, uz `sys.stdout.reconfigure(encoding="utf-8")`.
- **Commit:** `git add docs/research/13-prediktori-razvoja.md`, poruka na hrvatskom, bez spominjanja Claudea. Skripte se ne commitaju; u izvještaju navedi njihova imena u scratchpadu.
- **Rok je 4:00.** Ako ne stigne sve, predaje ono što ima, s jasnim "nije napravljeno".
- **Vraća izvještaj od najviše 250 riječi:** preporuka, ključne brojke empirijske provjere, trošak razvoja i put do izvještaja.

### Subagent U: vizualni prijedlozi (kreće kad R završi, oko 4:00; tvrdi kraj u 8:00)

- **Cilj:** dojam sučelja, jer žiri boduje UI/UX i video (`docs/research/10-pogled-zirija.md`).
- **Zadaci 1-4 su prioritet, a 5-7 samo ako ostane vremena.** U 8:00 staje i predaje izvještaj s onim što je gotovo.
- Radi zadatke redom. **Svaki zadatak je zaseban commit** koji se može vratiti sam za sebe. Poruka počinje s "Prijedlog:", osim zadatka 1, koji je odobren ako stignemo.
- Za svaki zadatak napravi snimke prije i poslije na 1280 i 375 px, u `docs/snimke/noc-5-11-u<N>-*.png`, i zadrži ih u commitu.

1. **Vidljiva provjera AI teksta** (prijedlog 5 iz `research/10`):
   - oznaka "AI tekst · … · N/N brojki provjereno", odnosno "Predložak · …", postaje gumb koji otvara popis: svaka brojka, kvačica, naziv činjenice i izvor (konto ili ćelija);
   - kućica na prijelaz mišem u `Sources.tsx` dobiva i ćeliju;
   - jedna rečenica ispod teksta objašnjava da model nije smio izmisliti nijednu brojku.
   - Mora biti točno i za AI tekst i za predložak, jer do petka većina profila prikazuje predložak.
   - Podaci već postoje u `jedinice/<slug>.json` (`objasnjenje.provjera`, `cinjenice`).
2. **Naslovnica na mobitelu** (zadatak iz `docs/TODO.md` "UX zadaci za razmotriti", prijedlog 7):
   - ispod 1024 px karta dolazi odmah ispod pretrage, a legenda i godine su sklopive (`details`/`summary`);
   - na desktopu legenda je sažeta tako da gumb "Pokreni 2019.–2025." stane u prvi ekran na 1280×800.
3. **Sitnice na kartama** (agent C, 4.11.):
   - tamni obrub spojenih jedinica na malim otocima je pretežak, pa ga treba skalirati sa zumom ili veličinom;
   - na mobitelu ljepljivo zaglavlje prekriva natpis Karte reforme;
   - natpis na karti na 1280 px prekriva sjever Hrvatske.
4. **Ravnoteža stupaca na pregledu jedinice:** na desktopu je desni stupac ispod "Susjedi" prazan, a lijevi raste s novim karticama ("Stanovništvo i gospodarstvo", "Fiskalno izravnanje"). Uravnoteži raspored, a na mobitelu zadrži smislen redoslijed čitanja.
5. **Prijedlog:** u simulatoru zakonski odlomci u blokovima "Fiskalno izravnanje" i "Poticaj države" idu iza "Kako se računa". Vidljivi ostaju iznos i jedna rečenica.
6. **Prijedlog:**
   - naslovnica dobiva traku s 3-4 brojke izračunate iz podataka, ne upisane rukom (npr. "576 jedinica · 7 godina · 168.899 ljudi u jedinicama pod pritiskom · 13.353 scenarija spajanja");
   - stranica "Metodologija i podaci" dobiva kartice ili sklopive odjeljke umjesto jednog toka od 2.300 riječi, a postojeća sidra i poveznice nastavljaju raditi.
7. **Prijedlog, najniži prioritet:** u praznom prostoru lijevo od kartice s ocjenom na pregledu jedinice ide mali obris jedinice sa susjedima u sivoj boji, iz `geo/jls.topo.json`, učitan lijeno.

- **Ograničenja:**
  - smije mijenjati samo `web/src/` i `docs/snimke/noc-5-11-u*`;
  - ne dira `pipeline/`, podatke ni testove u Pythonu, mjesto Z5 ni riječi ("pregled jedinice", nikad "svjedodžba"; bez natpisa "procjena DZS-a");
  - poštuje `prefers-reduced-motion`, tipkovnicu i `aria` za gumbe i sklopive dijelove;
  - stil je postojeći (`Card`, `Eyebrow`, tokeni, `format.ts`).
- **Preglednik i memorija:**
  - jedini preglednik dok radi; `BROWSE_STATE_FILE=$S/browse-U.json`, a na kraju `$B stop`;
  - bez `npm run dev`; `npx vite build --outDir $S/dist-U --emptyOutDir` i preview na portu 4188; server se gasi nakon svakog pregleda, a na kraju se provjeri `netstat` da je port slobodan.
- **Prije svakog commita:** `npx tsc -b --noEmit`, `npx oxlint` i `npx vite build` u `web/`.
- **Commit:** `git add <web/src putanje> docs/snimke/noc-5-11-u<N>-*.png`.
- Voditelj ti može poslati nalaze iz code reviewa za datoteke koje držiš; ispravi ih kao zaseban commit.
- **Vraća izvještaj od najviše 300 riječi:** commit po commit (hash, jedan redak, snimke), što je preskočeno i zašto, i što je primijetio a nije popravljao.

## 5. Šefovski krugovi (3:30, 6:00, 8:00)

Svaki krug je kratak:
1. Gdje smo u odnosu na raspored? Stanje subagenata (M, R ili U) i stanje pilota.
2. Prolaze li testovi na grani? Je li radna kopija čista ili commitana? `git push origin noc-5-11`.
3. **Prioriteti:**
   - kad kasnimo, reže se ovim redom: U zadaci 7, 6, 5; N8; drugi pilot iz N3; N9a se svodi na 5 ruta;
   - N1, N2, N4, N6, N11 i primopredaja se ne režu.
4. Kratki zapis u dnevnik: što je gotovo, gdje je i što je otvoreno.

## 6. Kad nešto pođe po zlu

| Problem | Što napraviti |
|---|---|
| Online build padne na izvoru | zapis kao rizik za CI, nastavak s `--offline`; ispravak samo ako je uzrok naš kod |
| Kaggle push odbijen ili bilježnica ERROR | log preko `kaggle kernels output`, jedan ispravak; ako opet padne, N3 se zapisuje kao nije napravljen |
| Pilot troši više od 1 h GPU-a | prekini (`cancel_notebook_session` ili Kaggle CLI), uzmi djelomični izlaz |
| Test pada, a uzrok nije jasan za 20 min | vrati zadnju izmjenu (`git revert` ili `git checkout -- <datoteka>`), zapiši, sljedeći zadatak |
| Memorija ispod 1 GB | ugasi preview i preglednik; nikad dva preglednika odjednom |
| Subagent mijenja datoteku koju ne smije | ne pushaj taj commit; vrati ga (`git revert`) i zapiši |
| `.git/index.lock` | pričekaj, pa ponovno; nikad ne briši lock dok drugi proces radi |
| Odluka koja nije u PLAN §11 ni u ovom programu | ne donosi je; zapiši je s prijedlogom i nastavi |

## 7. Što noćna smjena ne radi

- `main`, deploy, postavke repozitorija i `.github/workflows/`.
- Puno generiranje AI tekstova i uvoz u `data/ai/`.
- Promjene metodologije, pragova konteksta i provjere; promjenu prompta osim jedne iteracije u N3.
- Posebno pravilo za Belišće i premještanje Z5.
- Razvoj prediktora razvoja u proizvodu: noćas samo istraživanje i analiza u scratchpadu (R).
- Slanje e-maila, objavu videa i bilo što izvan repozitorija, osim privatne Kaggle bilježnice za pilot.
- Brisanje ičega što nije sama napravila, i nadogradnju gstacka.
