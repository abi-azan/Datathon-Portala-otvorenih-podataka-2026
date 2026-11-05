# Predaja rješenja: provjera i nacrt e-maila (nacrt 5.11.2026.)

**Rok: ponedjeljak 9.11.2026. u 24:00**, samo elektroničkom poštom na **open.data@mpudt.hr**. Rješenje predano nakon roka ili bez video prezentacije ne ocjenjuje se (Pravila, odjeljak VIII). Rang-liste se objavljuju najkasnije 17.11.2026., a konferencija je 23.11.2026. u Zagrebu.

Ovaj dokument je nacrt. E-mail se **ne šalje** dok ga tim ne pregleda. Mjesta u uglatim zagradama popunjava tim.

## 1. Što predaja mora sadržavati (Pravila, odjeljci III i VIII)

Iz `1792415200857_praviladatathonfinal.pdf`:

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
| Tehnička i projektna dokumentacija | `README.md` (što radi, podaci, metodologija, arhitektura, pokretanje, API, MCP, daljnji razvoj, licence, AI alati); `docs/PLAN.md` (projektni plan i odluke); `docs/research/` (istraživanja i provjere); stranica "Metodologija i podaci" (`#/metodologija`) | gotovo, osvježiti brojke na dan predaje |
| Opis tehničke arhitekture | `README.md`, odjeljak "Arhitektura" (dijagram mermaid i moduli ETL-a), uz preduvjete (pravni, organizacijski, tehnički) | gotovo |
| Popis svih skupova podataka s izdavateljem i poveznicom | `docs/skupovi-podataka.md` (generira `python -m pipeline.publish` iz `data/reference/skupovi.csv`; 34 korištena skupa, s licencom i načinom pristupa); isto u API-ju kao `api/v1/skupovi.json`, a zapis svakog preuzimanja u `api/v1/izvori.json` | gotovo; generira se pri svakom buildu |
| Demo: poveznica na radni prototip | https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/ (GitHub Pages) | uživo je verzija od 4.11.; nova verzija nakon pusha u petak i zelenog CI-ja |
| Demo: snimke zaslona | `docs/snimke/` (naslovnica u README-u: `docs/snimke/naslovnica.png`) | ponovno snimiti 8.11. (`docs/TODO.md`) |
| Video do 3 min sa 7 elemenata | `docs/video-scenarij.md` (v3, s tablicom pokrivenosti 7 elemenata) | scenarij gotov; snimanje nakon regeneracije AI tekstova; poveznica na video još ne postoji |
| Popis AI alata i knjižnica s licencama | `README.md`, odjeljak "Korišteni AI alati"; `THIRD_PARTY_LICENSES.md` (web, ETL, alati u izgradnji i AI dijelu, video, usluge) | gotovo |
| Softver otvorenog koda | `THIRD_PARTY_LICENSES.md`: sve knjižnice su otvorenog koda (MIT, BSD, Apache-2.0, ISC, PSF, MPL-2.0; copyleft samo GEOS LGPL-2.1 i text-unidecode); u proizvodu samo otvoreni model (Gemma 4, Apache-2.0) | gotovo |
| Navođenje izvora (atribucija) | `LICENSE-DATA.md` (izjava o izvoru prema Otvorenoj dozvoli), `docs/skupovi-podataka.md` (dokaz licence i datum zadnje izmjene), podnožje i stranica "Metodologija i podaci", natpis OpenStreetMap/OpenFreeMap na svakoj karti | gotovo; u videu otvoriti natpis karte ("i") ili ga dopisati u montaži |
| Podaci s Portala, i to preko API-ja | CKAN API (katalog i sloj otvorenosti; datoteke Porezne uprave pronalaze se preko `package_show`), DZS INSPIRE WFS, DZS PxWeb (u ETL-u i uživo iz preglednika); popis u README-u, odjeljak "Podaci" | gotovo |
| Poveznica dostupna do objave rezultata | repozitorij i stranica su javni; video [poveznica, npr. YouTube "unlisted" ili repozitorij] | otvoreno: odabrati gdje je video |

## 3. Gdje žiri vidi kriterije (za tijelo e-maila)

| Kriterij | Gdje se vidi |
|---|---|
| Izvedivost | radni prototip na GitHub Pagesu, 576 jedinica, testovi u CI-ju |
| Dojam (UI/UX) | naslovnica s kartom, pregled jedinice, simulator, Karta reforme, mobilni prikaz |
| Otvoreni podaci preko API-ja | CKAN API, DZS WFS i PxWeb (i uživo iz preglednika), zapis preuzimanja u `izvori.json` |
| Povezivanje izvora | MF + DZS + Porezna uprava + DUR + katalog portala, spojeni po OIB-u i šifri DGU |
| Relevantnost za izazov C | fiskalna održivost svih JLP(R)S, simulator spajanja i Karta reforme |
| Utjecaj | građani, novinari, vijećnici, Ministarstvo financija i MPUDT |
| Inovativnost | AI tekst s vidljivom provjerom svake brojke (otvoreni model), MCP server za AI asistente |
| Arhitektura i interoperabilnost | statični API (OpenAPI 3.1), katalog DCAT-AP, stabilni ključevi (OIB, RKP, DGU), preduvjeti navedeni |

## 4. Nacrt e-maila (ne šalje se)

**Prima:** open.data@mpudt.hr
**Predmet:** Datathon Portala otvorenih podataka 2026 – rješenje za izazov C – Fiskalna karta JLS – tim [naziv tima]

**Tijelo:**

> Poštovani,
>
> u ime tima [naziv tima] dostavljamo rješenje za izazov C (Gospodarstvo i učinkovito upravljanje): **Fiskalna karta JLS**.
>
> Fiskalna karta daje ocjenu financijske stabilnosti od 1 do 5 za svih 576 općina, gradova i županija, iz izvještaja Ministarstva financija i otvorenih podataka DZS-a, Porezne uprave, Državnog ureda za reviziju i Portala otvorenih podataka. Uz ocjenu su usporedba sa sličnim jedinicama, simulator spajanja susjednih jedinica i Karta reforme. Kratko objašnjenje piše otvoreni jezični model (Gemma 4), a program provjerava svaku brojku u tekstu i pokazuje odakle dolazi.
>
> - **Radni prototip:** https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/
> - **Javni repozitorij (kod EUPL-1.2, podaci CC BY 4.0):** https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026
> - **Video prezentacija (do 3 min):** [poveznica]
> - **Tehnička i projektna dokumentacija:** README u repozitoriju (arhitektura, preduvjeti, daljnji razvoj, AI alati) i `docs/PLAN.md`
> - **Popis korištenih skupova podataka s izdavateljima i poveznicama:** https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026/blob/main/docs/skupovi-podataka.md
> - **Otvoreni API:** https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/api/v1/openapi.json (OpenAPI 3.1) i katalog DCAT-AP `api/v1/dcat.jsonld`
> - **Popis AI alata i licenci:** README, odjeljak "Korišteni AI alati", i `THIRD_PARTY_LICENSES.md`
>
> U privitku su snimke zaslona i kratki opis rješenja u PDF-u. Sve poveznice bit će dostupne najmanje do objave rezultata.
>
> Članovi tima: [ime i prezime, visoko učilište], … Mentor: [ime i prezime].
>
> Srdačan pozdrav,
> [ime i prezime voditelja tima]

**Privici** (ukupno ispod ograničenja e-maila, inače samo poveznice):
1. 4-6 snimki zaslona iz `docs/snimke/` (naslovnica, pregled Povljane s provjerom brojki, simulator Pag + Povljana, Karta reforme 5.000, metodologija, mobilni prikaz).
2. Kratki opis u PDF-u (README izvezen u PDF, npr. `/make-pdf`), ako tim želi.
3. Video samo kao poveznica (datoteka je prevelika za e-mail).

## 5. Na dan predaje i prije njega

| Kada | Što |
|---|---|
| pet 6.11. do 17 h | regeneracija AI tekstova (batch oko 4,2 h), uvoz, testovi zeleni lokalno |
| pet 6.11. | push na `main`, zeleni CI, provjera stranice uživo (naslovnica, Povljana, simulator, reforma) |
| sub 7.11. do 20 h | isključiti tjedni cron u `deploy.yml` (pada u pon 9.11. u 04:17 UTC; treba `gh` token s `workflow`), zamrzavanje |
| ned 8.11. | **ponovno snimiti naslovnicu za README** i ostale snimke zaslona sa stranice uživo; provjeriti brojke u videu prema API-ju uživo (`docs/video-scenarij.md`, tablica u `docs/noc-5-11.md`) |
| ned 8.11. | snimiti i montirati video (ispod 3:00, ljudski glas), objaviti i dobiti poveznicu |
| pon 9.11. | završni commit (README: poveznica na video, datum; `docs/PREDAJA.md`: stanje "gotovo"), oznaka (tag) `predaja-2026-11-09` |
| pon 9.11. | poslati e-mail iz odjeljka 4 s popunjenim mjestima, najkasnije nekoliko sati prije 24:00; sačuvati potvrdu primitka |
| nakon slanja | ne mijenjati `main` do objave rezultata (17.11.), da stranica odgovara videu |
