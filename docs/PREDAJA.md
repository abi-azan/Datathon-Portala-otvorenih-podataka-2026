# Predaja rješenja: provjera i nacrt e-maila (nacrt 6.11.2026.)

**Rok: ponedjeljak 9.11.2026. u 24:00**, samo elektroničkom poštom na **open.data@mpudt.hr**. Rješenje predano nakon roka ili bez video prezentacije ne ocjenjuje se (Pravila, odjeljak VIII). Rang-liste se objavljuju najkasnije 17.11.2026., a konferencija je 23.11.2026. u Zagrebu.

Ovaj dokument je nacrt. E-mail se **ne šalje** dok ga tim ne pregleda. Mjesta u uglatim zagradama popunjava tim.

## 1. Što predaja mora sadržavati (Pravila, odjeljci III i VIII)

Iz `docs/pravila-datathona.pdf`:

1. **Izvorni kod ili poveznica na javni repozitorij** (npr. github.com). Objava pod licencom slobodnog softvera otvorenog koda boduje se; izbor licence je na timu (odjeljak X).
2. **Tehnička i projektna dokumentacija**, uključujući **opis tehničke arhitekture** i **popis korištenih skupova podataka s izvorima**.
3. Dokumentacija mora navesti **sve korištene skupove podataka, njihove izdavatelje i poveznice na izvore** (odjeljak III).
4. **Demo materijali**, npr. poveznica na radni prototip i snimke zaslona.
5. **Video prezentacija rješenja u primjeni, do 3 minute**, koja obuhvaća: opis problema, ciljne korisnike, korištene izvore podataka, funkcionalnosti, tehničku arhitekturu, korisničku vrijednost i mogućnosti daljnjeg razvoja (7 elemenata).
6. **Alati, biblioteke i komponente otvorenog koda, uključujući AI alate, smiju se koristiti ako ne krše licence i ako su navedeni u dokumentaciji** (odjeljak VIII).
7. Rješenje se razvija **softverom otvorenog koda** (odjeljak III).
8. Podaci: **otvoreni podaci javnog sektora**, prednost imaju podaci s Portala; drugi javni izvori smiju se koristiti ako dozvola to dopušta. **Izvor se obavezno navodi** prema Pravilniku NN 67/17 (odjeljak III).
9. Ako je rješenje veće od ograničenja e-maila, šalje se **poveznica dostupna najmanje do objave rezultata** (odjeljak VIII).
10. Rješenje je izvorno djelo tima; sudionici jamče da ne krši prava trećih osoba (odjeljci VIII i X).

## 2. Tablica provjere

| Zahtjev | Gdje je ispunjen | Stanje |
|---|---|---|
| Izvorni kod, javni repozitorij | https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026 (javan od 3.11., odluka 15) | djelomično: `origin/main` je `25c589c` (4.11.); rad od 4.11. poslijepodne čeka push u petak, nakon regeneracije AI tekstova |
| Licenca otvorenog koda | `LICENSE` (EUPL-1.2, kod), `LICENSE-DATA.md` (CC BY 4.0, podaci koje projekt proizvodi) | gotovo |
| Tehnička i projektna dokumentacija | **`docs/DOKUMENTACIJA.pdf`** (10 stranica, poredano po kriterijima žirija, s prilogom svih skupova podataka; izvor je `docs/DOKUMENTACIJA.md`, PDF radi `python -m pipeline.dokumentacija` i ispis iz preglednika); `README.md` (što radi, podaci, metodologija, arhitektura, pokretanje, API, MCP, daljnji razvoj, licence, AI alati); `docs/PLAN.md` (projektni plan i odluke); `docs/research/` (istraživanja i provjere); stranica "Metodologija i podaci" (`#/metodologija`) | gotovo; tim i mentor upisani 8.11.; prije slanja upisati članove i poveznicu na video, pa ponovno ispisati PDF |
| Opis tehničke arhitekture | `docs/DOKUMENTACIJA.pdf`, odjeljak 7 (shema `docs/arhitektura.svg`, standardi, tablica "Povezivanje s postojećim javnim sustavima", preduvjeti: tehnički, organizacijski, pravni); `README.md`, odjeljak "Arhitektura" (ista shema i moduli ETL-a) | gotovo |
| Popis svih skupova podataka s izdavateljem i poveznicom | `docs/skupovi-podataka.md` (generira `python -m pipeline.publish` iz `data/reference/skupovi.csv`; 34 korištena skupa, s licencom i načinom pristupa); isto u API-ju kao `api/v1/skupovi.json`, a zapis svakog preuzimanja u `api/v1/izvori.json` | gotovo; generira se pri svakom buildu |
| Demo: poveznica na radni prototip | https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/ (GitHub Pages) | uživo je verzija od 6.11. navečer (`55f1ed1`, zeleni CI); provjereno 576 od 576 AI tekstova |
| Demo: snimke zaslona | `docs/snimke/`: `naslovnica.png`, `pregled-jedinice.png`, `simulator.png`, `karta-reforme.png` (1440×900; iste su u PDF-u) | sve četiri su sa stranice uživo (naslovnica 6.11., ostale tri 8.11., ista objavljena verzija `6dc14d6`) |
| Video do 3 min sa 7 elemenata | `docs/video-scenarij.md` (v4: natpis na ekranu za svaki od 7 elemenata, 327 riječi, tablica provjerenih brojki); slike `docs/video/01-naslov.png`, `02-izvori.png`, `04-kraj.png` i shema `docs/arhitektura.svg`; titlovi `docs/video/titlovi.srt` | scenarij, slike i titlovi gotovi; snima i govori tim; poveznica na video još ne postoji |
| Popis AI alata i knjižnica s licencama | `README.md`, odjeljak "Korišteni AI alati"; `THIRD_PARTY_LICENSES.md` (web, ETL, alati u izgradnji i AI dijelu, video, usluge) | gotovo |
| Softver otvorenog koda | `THIRD_PARTY_LICENSES.md`: sve knjižnice su otvorenog koda (MIT, BSD, Apache-2.0, ISC, PSF, MPL-2.0; copyleft samo GEOS LGPL-2.1 i text-unidecode); u proizvodu samo otvoreni model (Gemma 4, Apache-2.0) | gotovo |
| Navođenje izvora (atribucija) | `LICENSE-DATA.md` (izjava o izvoru prema Otvorenoj dozvoli), `docs/skupovi-podataka.md` (dokaz licence i datum zadnje izmjene), podnožje i stranica "Metodologija i podaci", natpis OpenStreetMap/OpenFreeMap na svakoj karti | gotovo; u videu otvoriti natpis karte ("i") ili ga dopisati u montaži |
| Podaci s Portala, i to preko API-ja | Svaki izvor koji ima upotrebljiv API čita se preko njega: CKAN API (katalog i sloj otvorenosti; datoteke Porezne uprave pronalaze se preko `package_show`), DZS INSPIRE WFS i DZS PxWeb, ukupno 9 skupova kroz tri servisa. Sva tri zovu se i uživo iz preglednika (ploča "Podaci preko API-ja" na `#/metodologija?o=podaci`; Portal i DZS na pregledu jedinice). Datoteke (23) ostaju samo gdje API ne postoji: MF i DUR objavljuju samo Excel i PDF, a jedina tablica Porezne uprave s DataStore API-jem ima 10.198 praznih redaka od 10.754. Popis u README-u, odjeljak "Podaci", i u PDF-u, odjeljak 4 | gotovo |
| Poveznica dostupna do objave rezultata | repozitorij i stranica su javni; video [poveznica, npr. YouTube "unlisted" ili repozitorij] | otvoreno: odabrati gdje je video |

## 3. Gdje žiri vidi kriterije (za tijelo e-maila)

| Kriterij | Gdje se vidi |
|---|---|
| Izvedivost | radni prototip na GitHub Pagesu, 576 jedinica, testovi u CI-ju |
| Dojam (UI/UX) | naslovnica s kartom, pregled jedinice, simulator, Karta reforme, mobilni prikaz |
| Otvoreni podaci preko API-ja | svaki izvor koji ima upotrebljiv API čita se preko njega: CKAN API, DZS WFS i PxWeb (9 skupova; sva tri servisa i uživo iz preglednika, vidi `#/metodologija?o=podaci`); datoteke samo gdje API ne postoji, uz zapis preuzimanja u `izvori.json` |
| Povezivanje izvora | sedam tijela javnog sektora (MF, DZS, Porezna uprava, DUR, DGU, MRRFEU, Portal), spojeno po OIB-u, RKP-u i službenoj šifri jedinice |
| Relevantnost za izazov C | fiskalna održivost svih JLP(R)S, simulator spajanja i Karta reforme |
| Utjecaj | građani, novinari, vijećnici, Ministarstvo financija i MPUDT |
| Inovativnost | AI tekst s vidljivom provjerom svake brojke (otvoreni model), MCP server za AI asistente |
| Arhitektura i interoperabilnost | statični API (OpenAPI 3.1), katalog DCAT-AP, stabilni ključevi (OIB, RKP, DGU), tablica povezivanja s postojećim javnim sustavima, preduvjeti navedeni (PDF, odjeljak 7) |

## 4. Nacrt e-maila (ne šalje se)

**Prima:** open.data@mpudt.hr
**Predmet:** Datathon Portala otvorenih podataka 2026 – rješenje za izazov C – Fiskalna karta JLS – tim Begovi mušketiri

**Tijelo:**

> Poštovani,
>
> u ime tima Begovi mušketiri dostavljamo rješenje za izazov C (Gospodarstvo i učinkovito upravljanje): **Fiskalna karta JLS**.
>
> Fiskalna karta daje ocjenu financijske stabilnosti od 1 do 5 za svih 576 općina, gradova i županija, iz izvještaja Ministarstva financija i otvorenih podataka DZS-a, Porezne uprave, Državnog ureda za reviziju i Portala otvorenih podataka. Uz ocjenu su usporedba sa sličnim jedinicama, simulator spajanja susjednih jedinica i Karta reforme. Kratko objašnjenje piše otvoreni jezični model (Gemma 4), a program provjerava svaku brojku u tekstu i pokazuje odakle dolazi.
>
> - **Radni prototip:** https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/
> - **Javni repozitorij (kod EUPL-1.2, podaci CC BY 4.0):** https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026
> - **Video prezentacija (do 3 min):** [poveznica]
> - **Tehnička i projektna dokumentacija:** u privitku (`DOKUMENTACIJA.pdf`, poredana po kriterijima ocjenjivanja) i u repozitoriju: https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026/blob/main/docs/DOKUMENTACIJA.md
> - **Popis korištenih skupova podataka s izdavateljima i poveznicama:** https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026/blob/main/docs/skupovi-podataka.md
> - **Otvoreni API:** https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/api/v1/openapi.json (OpenAPI 3.1) i katalog DCAT-AP `api/v1/dcat.jsonld`
> - **Popis AI alata i licenci:** README, odjeljak "Korišteni AI alati", i `THIRD_PARTY_LICENSES.md`
>
> U privitku su tehnička i projektna dokumentacija (PDF) i snimke zaslona. Sve poveznice bit će dostupne najmanje do objave rezultata.
>
> Članovi tima: [ime i prezime, visoko učilište], … Mentor: doc. dr. sc. Stjepan Begušić, Fakultet elektrotehnike i računarstva Sveučilišta u Zagrebu.
>
> Srdačan pozdrav,
> [ime i prezime voditelja tima]

**Privici** (ukupno ispod ograničenja e-maila, inače samo poveznice):
1. `docs/DOKUMENTACIJA.pdf` (oko 1,6 MB).
2. Četiri snimke zaslona iz `docs/snimke/` (naslovnica, pregled Povljane, simulator Pag + Povljana, Karta reforme 5.000).
3. Video samo kao poveznica (datoteka je prevelika za e-mail).

## 5. Na dan predaje i prije njega

| Kada | Što |
|---|---|
| pet 6.11. do 17 h | regeneracija AI tekstova (batch oko 4,2 h), uvoz, testovi zeleni lokalno |
| pet 6.11. | push na `main`, zeleni CI, provjera stranice uživo (naslovnica, Povljana, simulator, reforma) |
| sub 7.11. do 20 h | ~~isključiti tjedni cron~~ (gotovo 6.11.), zamrzavanje |
| ned 8.11. | **ponovno snimiti naslovnicu za README** i ostale snimke zaslona sa stranice uživo; provjeriti brojke u videu prema API-ju uživo (`docs/video-scenarij.md`, tablica u `docs/dnevnik/noc-5-11.md`) |
| ned 8.11. | snimiti i montirati video (ispod 3:00, ljudski glas), objaviti i dobiti poveznicu |
| pon 9.11. | završni commit (README: poveznica na video, datum; `docs/PREDAJA.md`: stanje "gotovo"), oznaka (tag) `predaja-2026-11-09` |
| pon 9.11. | poslati e-mail iz odjeljka 4 s popunjenim mjestima, najkasnije nekoliko sati prije 24:00; sačuvati potvrdu primitka |
| nakon slanja | ne mijenjati `main` do objave rezultata (17.11.), da stranica odgovara videu |

## 6. Izjava korisnika (do nedjelje 8.11.)

**Odluka 8.11.:** izjave nema, jer rješenje još nema stvarnih korisnika. Mjesto u uglatim zagradama u `docs/DOKUMENTACIJA.md` je obrisano; tekst ispod ostaje kao nacrt za vrijeme nakon natjecanja.

Kriterij "Utjecaj i korist za zajednicu" nosi 5 bodova. Jedna rečenica stvarnog korisnika u dokumentaciji i videu vrijedi više od našeg opisa koristi. Poruku treba poslati na 3 do 5 adresa: vijećnik ili pročelnik za financije u općini koju netko iz tima poznaje, lokalni novinar, netko iz udruge koja prati proračune. Dovoljan je jedan odgovor.

Nacrt poruke (šalje član tima, sa svog računa):

> Poštovani,
>
> studenti smo [visoko učilište] i za Datathon Portala otvorenih podataka napravili smo Fiskalnu kartu: ocjenu financijske održivosti proračuna svih općina, gradova i županija, iz izvještaja Ministarstva financija.
>
> Pregled za [naziv jedinice]: [poveznica na pregled jedinice]
>
> Možete li ga pogledati pet minuta i odgovoriti na dva pitanja?
> 1. Jesu li brojke točne i je li objašnjenje razumljivo?
> 2. Biste li ovakav pregled koristili, i za što?
>
> Ako se slažete, jednu Vašu rečenicu naveli bismo u dokumentaciji, s imenom i funkcijom ili bez njih, kako želite.
>
> Hvala unaprijed,
> [ime i prezime]

Odgovor ide u `docs/DOKUMENTACIJA.md`, odjeljak 9, na mjesto označeno uglatim zagradama, i kao natpis u videu u dijelu "Korisnička vrijednost". Navodi se samo uz pisano dopuštenje. Ako odgovora nema, mjesto u uglatim zagradama treba obrisati prije ispisa PDF-a.
