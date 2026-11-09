# 10 — Pogled žirija: kako Fiskalna karta izgleda ocjenjivaču

Datum: 4.11.2026. navečer. Gledan je lokalni build s `main` (7 commita ispred objavljene stranice), poslužen s `npx vite preview` na portu 4180. Pregledano je u pregledniku bez prozora (gstack browse) na 1280 px i 375 px. Snimke su u lokalnoj radnoj mapi `jury/` i nisu u repozitoriju.

Uloga: član žirija koji otvori poveznicu, klika 3 do 5 minuta i pogleda video od 3 minute. Zanima ga koliko je rješenje tehnički i vizualno dojmljivo, a ne pravni detalji.

Kratki zaključak: proizvod je gotov, brz i bez grešaka u konzoli. Dizajn je uredan i ozbiljan, kao novinska grafika. Najjači trenuci su klik na brojku u AI tekstu i simulator spajanja. Najslabiji su to što se promjena na Karti reforme na razini cijele države ne vidi, što se godine na karti mijenjaju bez prijelaza i što na mobitelu karta dolazi tek na trećem ekranu. Procjena je 50 od 60 bodova, dakle točno na pragu za nagradu. S popravcima iz odjeljka 3 realno je 53 do 55.

---

## 1. Prvih 30 sekundi

Što žiri vidi (`jury/01-home-desktop.png`):

- Naslov "Kako stoje financije tvoje općine?", dvije rečenice objašnjenja, pretraga i karta Hrvatske u plavoj i crvenoj. Karta se učita za oko 1,7 s lokalno. Odmah je jasno o čemu se radi.
- Prijelaz mišem daje karticu s imenom, županijom, stanovnicima, ocjenom i bodovima (`jury/02-home-hover.png`). Klik vodi na svjedodžbu. To je dobro.
- Tri prikaza (ocjena, trošak uprave, pomoći u prihodima) mijenjaju paletu u ljubičastu (`jury/04-home-trosak.png`, `jury/05-home-pomoci.png`). Lijep dodatak koji žiri vjerojatno neće sam naći, jer je ispod pretrage i izgleda kao filter.
- Tablica kao alternativa karti radi i ima filtre (`jury/06-home-table.png`).

Što je zbunjujuće ili ravno:

- **Legenda i godine su ispod pregiba.** Na 1280×800 vidi se samo vrh legende. Gumb "Pokreni 2019.–2025." je 170 px ispod ruba ekrana. Žiri koji ne skrola ne zna da postoji vremenska animacija.
- **Animacija godina mijenja boje bez prijelaza.** Svakih 1,1 s karta "preskoči" u novu godinu (`web/src/pages/Home.tsx:44`, `web/src/components/GradeMap.tsx:206-216` boji preko `setFeatureState`, što MapLibre ne animira). Na videu to izgleda kao treperenje, ne kao priča.
- **Karta ne daje "aha" bez klika.** Hrvatska je većinom tamnoplava (302 jedinice s ocjenom 5). Pogled na kartu kaže "sve je dobro", a priča projekta je u crvenim točkama. Nema ništa što oko odmah povuče prema Povljani ili Vrhovinama.
- **Naslovnica nema nijednu brojku koja bi iznenadila.** Rečenica "U jedinicama s ocjenom 1 ili 2 živi 168.899 stanovnika" je dobra, ali skrivena na dnu legende. Isto vrijedi za "13.353 unaprijed izračunate kombinacije spajanja" i "svaka brojka vodi do retka u Excelu Ministarstva", koje se nigdje na naslovnici ne spominju.
- **Na mobitelu (375 px) karta dolazi tek nakon naslova, pretrage, prikaza, legende i godina**, otprilike na trećem ekranu (`jury/20-m-home-full.png`). Nema horizontalnog prelijevanja, ništa se ne raspada, ali prvi dojam na telefonu je tekst, ne karta. To je već zapisano kao otvoreni zadatak.

---

## 2. Procjena bodova po kriteriju

| Kriterij | Max | Procjena | Obrazloženje |
|---|---|---|---|
| Izvedivost: radi, spremno za uporabu | 10 | **9** | Sve stranice rade, nema grešaka u konzoli ni na jednoj od pet ruta, učitavanje je brzo, dubinske poveznice (`#/simulator?j=…`, `#/reforma?prag=…&s=…`) rade. Jedan bod manje jer objavljena stranica trenutno nije ova verzija i jer žiri na mobitelu dobiva slabiji doživljaj. |
| Dojam: UI/UX | 10 | **8** | Dosljedan, miran dizajn, dobra tipografija, ocjene uvijek s riječju, dobra kartica na prijelaz mišem. Odbijam dva boda: prijelazi na karti ne postoje, Karta reforme na razini države izgleda isto prije i poslije pomicanja klizača (`jury/14-reforma-10000-during.png` i `jury/14-reforma-10000.png` su identični), stranica "Metodologija" je zid teksta od 2.300 riječi (`jury/16-metodologija-full.png`), a gornji lijevi dio svjedodžbe ima velik prazan prostor (`jury/08-profile-povljana-top.png`). |
| Video | 10 | **7** (projekcija) | Scenarij videa pokriva svih sedam obaveznih elemenata i ima dobru priču (Ana u Povljani, "Spoji pa vidi"). Rizik je gustoća: 400 riječi u 2:50 je brzo za hrvatski. Bez prijelaza na karti i bez vidljive promjene na Karti reforme dva ključna kadra neće biti dojmljiva. Ocjenu dižu samo stvarni kadrovi, vidi odjeljak 5. |
| Otvoreni podaci izravno preko API-ja | 5 | **3** | Žiri vidi CKAN API i DZS WFS u tablici skupova i u `izvori.json`. Ali jezgra (MF) su XLSX datoteke, a u pregledniku se uživo ne zove nijedan javni API. Natjecanje izričito boduje API više od datoteka, i to je drugi kriterij za izjednačenje. Jedan poziv uživo iz preglednika (DZS PxWeb, CORS radi, `docs/research/09` §2.2) dignuo bi ovo na 4. |
| Smisleno povezivanje više izvora | 5 | **5** | MF (tri skupa) + DZS Popis + DZS granice + DGU šifrarnik + indeks razvijenosti + CKAN katalog + DUR revizije + tablica izravnanja, sve spojeno po OIB-u, RKP-u i šifri. Nova vrijednost je očita: ocjena, simulator, Karta reforme. |
| Relevantnost za izazov C | 5 | **5** | Učinkovito upravljanje i javne financije doslovno. Simulator spajanja je tema koja je trenutno u javnoj raspravi. |
| Utjecaj / korist | 5 | **4** | Građanin, novinar i ministarstvo dobivaju nešto što danas ne postoji. Jedan bod manje jer svjedodžba nije "prenosiva": nema slike za podijeliti, nema ugradive kartice, a to je najkraći put do stvarne uporabe. |
| Inovativna uporaba napredne tehnologije (AI) | 5 | **4** | Otvoreni model na besplatnom GPU-u, uz provjeru svake brojke i klik do ćelije u Excelu, je bolji obrazac nego bilo koji "chat nad podacima". Ali žiri to vidi tek na svjedodžbi, kao oznaku "11/11 brojki provjereno" i malu kućicu na prijelaz mišem (`jury/24-profile-number-hover.png`). Nema trenutka gdje AI "radi pred očima". MCP server ili vidljiva lista provjere digli bi ovo na 5. |
| Arhitektura: standardi, integracija, preduvjeti | 5 | **5** | OpenAPI 3.1, DCAT-AP, šifrarnik s tri ključa, zapis provenijencije svakog preuzimanja, CI koji sve ponovno izračuna, preduvjeti (pravni, organizacijski, tehnički) napisani u README-u. Teško je tražiti više. |
| **Ukupno** | **60** | **50** | Na pragu. Svaki bod iz odjeljka 3 je bod sigurnosti. |

---

## 3. Top 10 poboljšanja, po bodovima na sat

Procjene sati su za jednog razvojnog programera s AI asistentom. Prvi zadatak nije "poboljšanje", nego uvjet da žiri uopće vidi ovo što sam gledao.

### 1. Push na `main`, uspješan deploy i jedna slika na vrhu README-a (1 h)

- **Što:** gurnuti sedam lokalnih commita, dočekati zeleni CI, provjeriti objavljenu stranicu na mobitelu i desktopu. U README iznad "Što radi" staviti jednu snimku naslovnice (ili kratki GIF od 5 s: pretraga "povlj" pa svjedodžba). Žiri koji prvo otvori GitHub vidi sliku prije koda.
- **Kriterij:** Izvedivost (bez ovoga žiri gleda verziju bez tablice, bez novog simulatora i bez poticaja), Dojam +0,5.
- **Datoteke:** `README.md`, `docs/snimke/`.
- **Rizik:** CI radi puni ETL (preuzima s mfin.gov.hr). Ako je MF stranica spora, build padne, a Pages ostane na staroj verziji. Pokrenuti ručno dovoljno rano, ne u nedjelju navečer.

### 2. Karta reforme: promjena koja se vidi iz cijele države (2 h)

- **Što:** danas su spojene jedinice označene bijelom crtom od 1,4 px, a stare granice bijelom od 0,4 px (`web/src/components/ReformMap.tsx:117-119`). Na zoomu cijele države to se ne razlikuje od obične karte (`jury/13-reforma-5000-top.png` i `jury/14-reforma-10000.png`). Tek zoom na Zadar pokaže što se dogodilo (`jury/18-reforma-zoom-zadar.png`). Prijedlog: (a) obrub spojenih jedinica tamniji i deblji (npr. `#0b0b0b` 1,2 px, stare granice bijele 0,3 px), (b) pri promjeni praga spojene jedinice na 600 ms zasvijetle (fill-opacity 0,4 → 0,94 već postoji u `fillOpacity`, samo je prekratko i ne razlikuje spojene od nespojenih), (c) gumb "Prikaži samo spojene" koji nespojene potamni na 25 %, isto kao `dim` u GradeMap-u. Primjer: na pragu 5.000 Pag + Nin + Vrsi + Kolan + Povljana treba izgledati kao jedna velika tamnoobrubljena jedinica i bez zumiranja.
- **Kriterij:** Dojam +1, Video +0,5 (ovo je vrhunac scenarija, "555 → 239").
- **Datoteke:** `web/src/components/ReformMap.tsx`, `web/src/pages/Reforma.tsx`.
- **Rizik:** mali. Paziti da hover i klik na skupinu ostanu usklađeni s novim slojem.

### 3. Prijelaz boja na karti pri promjeni godine (2 h)

- **Što:** MapLibre animira `fill-color` kad se postavi preko `setPaintProperty`, ali ne animira `feature-state`. Umjesto `setFeatureState({g})` po jedinici (`GradeMap.tsx:206-216`), u GeoJSON svojstva pri učitavanju upisati `g2019`…`g2025` (podaci su već u `jedinice.json`) i mijenjati izraz `['match', ['get', 'g' + year], …]` uz `fill-color-transition: {duration: 500}`. Isto za tri prikaza. Animacija "Pokreni 2019.–2025." tada postaje mekani prijelaz, a ne treptanje. Primjer koji se vidi: Povljana 2023. tamnoplava, 2024. svjetloplava, 2025. crvena, i to se prelije.
- **Kriterij:** Dojam +0,5, Video +0,5 (uvodni kadar).
- **Datoteke:** `web/src/components/GradeMap.tsx`, `web/src/components/mapStyle.ts` (`gradeFill`, `sequentialFill`).
- **Rizik:** `feature-state` se i dalje koristi za hover, selected i dim; ne dirati to. Provjeriti da prijelaz ne usporava hover.

### 4. Jedan javni API uživo iz preglednika, s vidljivom oznakom (3 do 4 h)

- **Što:** na svjedodžbi dodati redak "Stanovnici 31.12.2024. (procjena DZS-a)" koji preglednik dohvati izravno s `web.dzs.hr/PXWeb/api/v1/hr/…/SP31_2.px` (POST, json-stat2, CORS radi, `docs/research/09` §2.2). Uz broj ide značka "dohvaćeno uživo s DZS-a u 14:32" i poveznica na skup na data.gov.hr. U ETL-u unaprijed napraviti `api/v1/dzs-px.json` (šifra → redni broj u PxWeb tablici), tako da preglednik radi jedan mali upit. Ako poziv padne (429 ili mreža), prikazati vrijednost iz builda s oznakom "iz spremnika". Primjer: Pag 3.352 (2024.) uz Popis 3.175 (2021.), Novalja +15 %.
- **Kriterij:** API +1 (3 → 4), to je kriterij za izjednačenje. Video dobiva kadar "ovo se upravo sad povlači s DZS-a".
- **Datoteke:** `pipeline/` novi mali modul za mapiranje, `pipeline/publish.py`, `web/src/pages/Profile.tsx`, `web/src/lib/data.ts`, `data/reference/skupovi.csv`.
- **Rizik:** PxWeb ograničava brzinu (429) i može biti nedostupan dok žiri gleda. Zato obavezno rezervna vrijednost i oznaka. Ne mijenjati metodologiju (po stanovniku ostaje Popis 2021.).

### 5. AI trenutak koji se vidi: lista provjere i bogatija kućica (2 h)

- **Što:** oznaka "AI tekst · Gemma 4 31B · 11/11 brojki provjereno" postaje gumb. Klik otvori popis: svaka od 11 brojki, kvačica, naziv činjenice i izvor (konto, ćelija). Kućica na prijelaz mišem (`web/src/components/Sources.tsx:252-275`) već kaže "Iz paketa činjenica" i sastavnicu; dodati i ćeliju (npr. "Bilanca 2025, LU324 + MA324") da prvi pogled već pokaže vezu s Excelom. Uz to jedna rečenica ispod teksta: "Model nije smio izmisliti nijednu brojku. Tekst koji ne prođe provjeru zamjenjuje predložak (11 od 576 jedinica)."
- **Kriterij:** Inovacija +0,5, Video +0,5 (kadar "11/11" koji se rasklopi je jasan i brz).
- **Datoteke:** `web/src/components/Sources.tsx`, `web/src/pages/Profile.tsx`. Podaci već postoje u `jedinice/<slug>.json` (`provjera`).
- **Rizik:** nikakav za podatke; samo prikaz.

### 6. Svjedodžba: silueta jedinice i ključne činjenice u praznom prostoru (2 h)

- **Što:** gornji lijevi dio svjedodžbe ima oko 150 px praznog prostora ispod naslova (`jury/08-profile-povljana-top.png`, `jury/17-profile-zupanija.png`). Tamo staviti malu SVG siluetu jedinice iz `geo/jls.topo.json` (topojson-client već je u bundleu, `ReformMap.tsx:6`) sa susjedima u sivoj boji, plus tri ili četiri brojke u nizu: stanovnici, površina, trošak uprave po stanovniku, otok/obala. Primjer: Povljana kao mali obris na Pagu, uz "669 stanovnika · 38,4 km² · 688 € uprava po stanovniku".
- **Kriterij:** Dojam +0,5. Svjedodžba postaje "slika", što pomaže i videu i README-u.
- **Datoteke:** `web/src/pages/Profile.tsx`, nova mala komponenta.
- **Rizik:** TopoJSON je 596 KB i već se učitava za kartu; na profilu je to dodatni zahtjev. Prihvatljivo, ali lijeno učitati.

### 7. Mobitel i naslovnica: karta odmah, legenda i godine sklopive (1 h)

- **Što:** na širini ispod 1024 px kartu staviti odmah ispod pretrage, a legendu i godine iza "Legenda i godine" (details/summary). Na desktopu legendu sažeti tako da gumb "Pokreni 2019.–2025." uđe u prvi ekran na 1280×800 (danas je 170 px prenisko). To je već zapisano kao otvoreni zadatak.
- **Kriterij:** Dojam +0,5, Izvedivost +0,5 (žiri koji otvori poveznicu na telefonu).
- **Datoteke:** `web/src/pages/Home.tsx` (redoslijed blokova u gridu, `order-*` klase).
- **Rizik:** mali.

### 8. Naslovnica s brojkama koje iznenade i značkom "povučeno s API-ja" (1,5 h)

- **Što:** ispod pretrage traka s četiri brojke iz `jedinice.json` i `metodologija.json`: "576 jedinica · 7 godina · 168.899 ljudi živi u jedinici pod pritiskom · 13.353 scenarija spajanja". Uz to mala značka "Podaci: MF 24.7.2026. · DZS WFS · CKAN API 2.11.2026." koja vodi na "Metodologija i podaci". Stranicu "Metodologija i podaci" podijeliti na kartice (Pokazatelji, Pravila, AI, Simulator, Podaci) umjesto jednog dugog toka; postojeći skok-linkovi na vrhu su dobar početak, ali ispod njih je zid.
- **Kriterij:** Dojam +0,5, API +0,5 (žiri vidi "API" bez traženja).
- **Datoteke:** `web/src/pages/Home.tsx`, `web/src/pages/Methodology.tsx`.
- **Rizik:** nema.

### 9. Svjedodžba za podijeliti: PNG kartica (4 h)

- **Što:** u ETL-u (Pillow ili matplotlib) za svaku jedinicu nacrtati karticu 1200×630: ime, ocjena s riječju, bodovi, pet sastavnica kao trake, "Fiskalna karta · podaci MF 2025.". Objaviti kao `api/v1/kartice/<slug>.png` i staviti gumb "Preuzmi svjedodžbu (PNG)" i "Kopiraj poveznicu". Načelnik ili novinar to može objaviti isti dan. Primjer: kartica Povljane s crvenom "2 pod pritiskom" i trakom dospjelih obveza na nuli.
- **Kriterij:** Utjecaj +0,5, Dojam +0,5. Ovo je i kadar za video ("svjedodžba koju možete podijeliti").
- **Datoteke:** novi `pipeline/kartice.py`, `pipeline/publish.py`, `pipeline/openapi.py`, `web/src/pages/Profile.tsx`.
- **Rizik:** fontovi u CI-ju (Public Sans je u repozitoriju? ako nije, dodati OFL datoteke). 576 slika po 40 KB je 23 MB, prihvatljivo. Og:image po jedinici ne radi s hash rutama, pa to ne obećavati.

### 10. MCP server i kadar od 10 sekundi (5 do 6 h)

- **Što:** read-only MCP server (MCP Python SDK, MIT) s četiri alata nad statičnim API-jem: `pronadi_jedinicu`, `svjedodzba`, `usporedi`, `scenarij_spajanja`. U videu kadar s bilo kojim MCP klijentom otvorenog koda: pitanje "Koja je ocjena Povljane i što bi dalo spajanje s Pagom?", odgovor s našim brojkama. U README dva reda za pokretanje.
- **Kriterij:** Inovacija +1 (4 → 5), Arhitektura ostaje 5, ali je "integracija s AI asistentima" tada demonstrirana, a ne obećana.
- **Datoteke:** novi `mcp/server.py`, `README.md`, `THIRD_PARTY_LICENSES.md`.
- **Rizik:** vrijeme. Žiri ga ne može isprobati na stranici, samo u videu i u repozitoriju. Ako se radi, raditi ga zadnje, u subotu, i samo ako su 1 do 8 gotovi. Nije uvjet za 50 bodova.

Gdje se ne slažem s pretpostavkama tima:

- **"Mobitel nije prioritet" (PLAN §6).** Žiri će poveznicu dobiti e-mailom i vrlo vjerojatno je prvi put otvoriti na telefonu. Zadatak 7 je jedan sat i vrijedi ga napraviti.
- **"Naslovnica nije rang-lista"** je ispravno politički, ali naslovnici fali bilo kakav kontrast. Rješenje nije rang-lista nego brojke koje iznenade (zadatak 8) i karta na kojoj se crvena vidi.
- **Novi podatkovni slojevi iz `research/09`** (dohodak Porezne uprave, lokalne stope) su dobri za proizvod, ali žiri ih u tri minute neće zamijetiti. Ako se bira jedan, neka bude DZS PxWeb uživo (zadatak 4), jer jedini mijenja ocjenu kriterija API.
- **3D ili vremenska animacija kao "wow"** ne preporučujem. Pravi prijelaz boja (zadatak 3) daje isti učinak u dva sata bez rizika.

---

## 4. Što maknuti ili sakriti

- **"Metodologija i podaci"** (`jury/16-metodologija-full.png`): 2.300 riječi u jednom toku, formule u monospaceu, pravni odlomci o ZPPI-ju i Pravilniku NN 67/17. Žiri koji klikne na tu stranicu izgubi se. Kartice ili sklopivi odjeljci; tablica skupova s oznakama "API" na vrh, pravni tekst iza "Licence i pravna osnova".
- **Simulator, donja polovica** (`jury/12-simulator-pag-povljana-full.png`): blokovi "Fiskalno izravnanje" i "Poticaj države" imaju po dva odlomka sitnog zakonskog teksta (čl. 8. i 9., NN 88/2022, NN 152/25). Ostaviti iznos i jednu rečenicu, ostalo iza "Kako se računa".
- **Svjedodžba, "Kriterij od 10 % za pomoći iz državnog proračuna"** u bloku dodatnih pokazatelja: "Zaključak Vlade od 16.4.2026." je pravni detalj čiji status ni PLAN nije siguran (§3.3 Z5). Premjestiti u "Upozorenja i napomene" kao jednu rečenicu, ili sakriti dok se ne potvrdi.
- **Karta reforme, padajući izbornik "Spojene jedinice (140)"**: obični `<select>` sa 140 dugih naziva. Ako žiri ne klikne na kartu, ovo je jedini put do skupine i djeluje sirovo. Pretraga kao na naslovnici, ili barem sortiranje po županiji s grupama.
- **Prazan prostor na vrhu svjedodžbe** (zadatak 6).
- **Dno naslovnice:** odlomak "Ocjena nije rang-lista…" i podnožje s pravnom izjavom o Otvorenoj dozvoli su u redu, ali na mobitelu su to još dva ekrana teksta prije kraja. Podnožje skratiti na jedan redak s poveznicom.
- **Konzola:** ni na jednoj stranici nisam vidio grešku ni upozorenje aplikacije. Jedini 404 bio je moja greška (otvorio sam `/Datathon-…/` putanju na lokalnom posluživanju, a `base` je relativan). Upozorenja "GPU stall due to ReadPixels" dolaze od preglednika bez prozora, ne od koda.
- **Nedostaje, a žiri bi mogao tražiti:** sortiranje tablice po ocjeni ili bodovima. Namjerna odluka, ali bar sortiranje po stanovnicima ne bi narušilo načelo "nije rang-lista".

---

## 5. Wow trenuci za video (redom)

Scenarij v2 je dobar; ovo su kadrovi koji ga nose, s onim što treba biti na ekranu i što se govori. Govoriti sporije: 330 riječi umjesto 400.

1. **0:05, karta diše.** Naslovnica, klik "Pokreni 2019.–2025." s mekim prijelazom (zadatak 3). Boje se prelijevaju sedam puta, kamera polako zumira prema Zadru i Pagu. *"Hrvatska ima 576 općina, gradova i županija. Svaka predaje izvještaje. Nitko ih nije pročitao za sve."* (`jury/01-home-desktop.png`, `jury/19-home-zoom-zadar.png`)
2. **0:35, svjedodžba.** Upis "povlj", padajući popis s crvenom "2 pod pritiskom" (`jury/07-home-search.png`), klik, svjedodžba Povljane: 39,9 bodova, 177. od 202, prošle godine 5 (`jury/08-profile-povljana-top.png`). *"Povljana na Pagu: ocjena dva. Lani pet. Zašto?"*
3. **0:55, AI koji ne smije izmisliti.** Miš na "49,4 %", kućica "Iz paketa činjenica" (`jury/24-profile-number-hover.png`), klik, otvori se "Kako je izračunato": DO = 23 D + 24 D + 26 D, ćelije LU324 i MA324 u listu 2025 Bilance, redak 156 u `13 Zadarska.xlsx` (`jury/09-profile-number-click.png`). *"Tekst piše otvoreni model na besplatnom GPU-u. Brojke računa program i provjeri svaku. Klik vodi do retka u datoteci Ministarstva."* Ovo je najjači kadar i treba mu dati 20 sekundi.
4. **1:25, Spoji pa vidi.** Sa svjedodžbe "Simuliraj spajanje sa susjedima", klik na Pag na karti, karta se približi otoku, pojave se čipovi "Pag 5 · Povljana 2 → 5" i žuti okvir "Dug ne nestaje spajanjem: 1.159.775 € ostaje, 15,1 % umjesto 49,4 %" (`jury/12-simulator-pag-povljana-full.png`). *"Spojene dobivaju pet. Ali dug ne nestaje. Ušteda od veličine je do 18 tisuća eura."*
5. **1:55, Karta reforme.** Klizač 2.500 → 5.000 → 10.000, brojač "555 → 370 → 239 → 147", karta zumirana na Zadarsku županiju tako da se spajanja vide (`jury/18-reforma-zoom-zadar.png`, nakon zadatka 2 i iz cijele države). Klik na skupinu Paga: sedam članica, 93,7 bodova (`jury/15-reforma-pag-group-full.png`). *"Scenarij, ne prijedlog granica. Ušteda na upravi do 36 milijuna, poticaj države 168 milijuna godišnje."*
6. **2:25, stroj iza.** Tri brza reza po 4 s: `izvori.json` s ETag-om i sha256, `openapi.json` u pregledniku, `dcat.jsonld`, zeleni GitHub Actions. Ako postoji zadatak 4: značka "dohvaćeno uživo s DZS-a". Ako postoji zadatak 10: MCP klijent s pitanjem o Povljani. *"CKAN API, DZS WFS, Ministarstvo financija. Sve se izračuna u CI-ju i objavi kao otvoreni API i DCAT katalog. Nema poslužitelja."*

U svakom kadru s kartom mora se vidjeti natpis OpenFreeMap / OpenStreetMap (već zapisano u scenariju videa).

---

## 6. Rizici za predaju

1. **Objavljena stranica je starija od `main`.** Ako se ne pusha i CI ne prođe, žiri ocjenjuje verziju bez tablice, novog simulatora i poticaja. Najveći pojedinačni rizik.
2. **Tjedni cron pada na dan predaje.** `.github/workflows/deploy.yml` ima `cron: "17 4 * * 1"`, ponedjeljak 04:17 UTC. 9.11.2026. je ponedjeljak. Build će se pokrenuti sam u 5:17 ujutro na dan slanja. Ako MF u međuvremenu zamijeni datoteke, brojke na stranici više neće odgovarati videu; ako mfin.gov.hr ne odgovori, build pada (stara verzija ostaje, ali bez provjere). Preporuka: isključiti `schedule` prije zamrzavanja u subotu i ponovno ga uključiti nakon objave rezultata.
3. **Vanjske ovisnosti u pregledniku:** OpenFreeMap pločice (karta ima rezervu bez podloge, `mapStyle.ts` `BLANK`), a nakon zadatka 4 i DZS PxWeb (obavezno rezervna vrijednost). Žiri gleda u bilo koje doba.
4. **Veličina po županiji u simulatoru:** `simulator/zup-02.json` ima 1,9 MB, `zup-13.json` 1,6 MB. GitHub Pages ih gzipa, ali na slabom Wi-Fiju prvi klik na kartu u simulatoru može trajati nekoliko sekundi bez vidljivog signala. Dodati "Učitavam scenarije županije…" ako već nema.
5. **Žiri na telefonu** vidi tri ekrana teksta prije karte (zadatak 7).
6. **Jedanaest jedinica ima predložak umjesto AI teksta.** Pošteno je označeno, ali ako žiri slučajno klikne na jednu od njih, vidi "predložak". Provjeriti da Zagreb, Split i primjeri s naslovnice (Sveta Marija, Povljana) imaju AI tekst.
7. **Brojke u videu moraju biti iz istog builda kao objavljena stranica.** Scenarij to već kaže; nakon svake promjene u `pipeline/` ponovno provjeriti 1.045.908 €, 49,4 %, 18.045 €, 555 → 239.
8. **Video bez naracije ljudskim glasom ili preko 3:00** gubi bodove; scenarij je na rubu (2:50). Skratiti tekst, ne ubrzavati govor.

---

## Dodatak: što je pregledano

| Snimka | Sadržaj |
|---|---|
| `jury/01-home-desktop.png`, `01-home-desktop-full.png` | naslovnica 1280 px, prvi ekran i cijela |
| `jury/02-home-hover.png` | kartica na prijelaz mišem (Zadar) |
| `jury/03-home-anim-mid.png` | animacija godina u tijeku (2021.) |
| `jury/04-home-trosak.png`, `05-home-pomoci.png` | prikazi "Trošak uprave" i "Pomoći u prihodima" |
| `jury/06-home-table.png` | tablica s filtrima |
| `jury/07-home-search.png` | pretraga "povlj" |
| `jury/08-profile-povljana-top.png`, `08-profile-povljana-full.png` | svjedodžba Povljane |
| `jury/09-profile-number-click.png` | klik na "1.045.908" otvara "Kako je izračunato" |
| `jury/10-profile-kako-izracunato.png`, `10b-…-2.png` | izračun servisa duga s ulaznim retcima |
| `jury/11-simulator-empty.png`, `12-simulator-pag-povljana-top.png`, `12-…-full.png` | simulator prazan i Pag + Povljana |
| `jury/13-reforma-5000-top.png`, `13-…-full.png`, `14-reforma-10000-during.png`, `14-reforma-10000.png` | Karta reforme, prag 5.000 i 10.000 |
| `jury/15-reforma-pag-group.png`, `15-…-full.png` | skupina Paga sa 7 članica |
| `jury/16-metodologija-top.png`, `16-…-full.png` | stranica metodologije |
| `jury/17-profile-zupanija.png` | svjedodžba Zadarske županije |
| `jury/18-reforma-zoom-zadar.png`, `19-home-zoom-zadar.png` | zum na Zadar, reforma i naslovnica |
| `jury/20-m-home.png`, `20-m-home-full.png`, `21-m-profile.png`, `22-m-simulator.png`, `22-…-full.png`, `23-m-reforma.png` | mobitel 375 px |
| `jury/24-profile-number-hover.png` | kućica "Iz paketa činjenica" na "49,4 %" |

Rute: `#/`, `#/jedinica/opcina-povljana`, `#/jedinica/zadarska-zupanija`, `#/simulator`, `#/simulator?j=05738,03166`, `#/reforma?prag=5000`, `#/reforma?prag=10000`, `#/metodologija`. Ni na jednoj nije bilo greške u konzoli. Horizontalno prelijevanje na 375 px: nema (scrollWidth 375). Učitavanje naslovnice lokalno: 1,7 s do `load`.
