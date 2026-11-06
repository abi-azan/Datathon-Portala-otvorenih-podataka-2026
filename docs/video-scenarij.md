# Video (najviše 3 minute): scenarij v4

Pravila traže da video obuhvati 7 elemenata: opis problema, ciljne korisnike, korištene izvore podataka, funkcionalnosti, tehničku arhitekturu, korisničku vrijednost i mogućnosti daljnjeg razvoja. Video nosi 10 od 60 bodova, a žiri ocjenjuje samo ono što je predano (kod, dokumentacija, demo, video).

- **v2 (4.11. noću):** simulator, Karta reforme i klik na brojku postoje, pa su rezervni kadrovi maknuti.
- **v3 (5.11. noću):** naracija skraćena s oko 400 na 338 riječi (govoriti sporije), novi kadrovi (pretapanje boja, "uživo s API-ja DZS-a", fiskalno izravnanje, MCP).
- **v4 (6.11. navečer):**
  - Svaki od 7 elemenata ima **natpis na ekranu istim riječima kao u pravilima**, da ga član žirija može odmah označiti.
  - Dio "Podaci i arhitektura" (prije 37 s s pet tema) podijeljen je na **Izvore podataka** i **Tehničku arhitekturu**.
  - Rečenica o API-ju je točnija: svaki izvor koji ima API čitamo preko njega (9 skupova kroz tri servisa), a datoteke ostaju samo gdje API-ja nema.
  - Gotove su četiri slike (`docs/video/`) i titlovi (`docs/video/titlovi.srt`).
  - Sve brojke ponovno su pročitane iz API-ja obrade od 6.11. (tablica na dnu).

Naracija ima 327 riječi. Uz oko 130 riječi u minuti govor traje 2:31, pa ostaje oko 25 s za stanke i prijelaze. **Video mora biti ispod 3:00.**

**Odluke prije snimanja:**
1. **Jedinica u priči:** Povljana. Može biti i jedinica koju netko iz tima stvarno poznaje, ali tada treba promijeniti brojke u naraciji.
2. **Tko govori:** ljudski glas. Sintetizirani glas žiri prepozna.
3. **Brojke** još jednom usporediti sa stranicom uživo na dan snimanja (tablica na dnu).

**Natpisi na ekranu:** mali natpis gore lijevo, 4 s na početku svakog dijela, bijela podloga 92 %, tekst `#0b0b0b`, font Public Sans 600. Riječi su točno ove: Problem · Ciljni korisnici · Funkcionalnosti · Izvori podataka · Tehnička arhitektura · Korisnička vrijednost · Daljnji razvoj.

---

## 0:00-0:20 Problem

**Natpis:** Problem

**Kadar:** 2 s slika `docs/video/01-naslov.png`. Zatim naslovnica, klik na "Pokreni" u traci s godinama iznad karte. Boje se meko prelijevaju iz godine u godinu, kamera polako ide prema Zadru i Pagu. Zatim kratki kadar Excel tablice Ministarstva financija (PR-RAS, tisuće redaka).

**Naracija:**
> Hrvatska ima 576 općina, gradova i županija. Više od dvjesto općina ima manje od dvije tisuće stanovnika. Njihovi godišnji izvještaji završe u tablicama s tisućama redaka. Je li vaša općina financijski stabilna? Odgovor postoji, samo ga nitko nije izračunao za sve.

## 0:20-0:36 Ciljni korisnici

**Natpis:** Ciljni korisnici

**Kadar:** naslovnica, pa polako prema legendi.

**Naracija:**
> Fiskalna karta je za građane, novinare, vijećnike i ministarstvo. Svaka jedinica dobiva ocjenu od jedan do pet, iz službenih podataka i uz usporedbu sa sličnima. Mjeri održivost proračuna, a ne kvalitetu upravljanja.

## 0:36-1:17 Funkcionalnosti: pregled jedinice

**Natpis:** Funkcionalnosti

**Kadar:** pretraga, upisuje se "povlj"; zatim pregled Općine Povljana: ocjena 2, 39,9 boda, "Prošle godine 5 · vrlo stabilno". Uz siluetu je traka "Ocjena po godinama" (2, 3, 2, 4, 5, 5, 2), pa se pad s pet na dva vidi bez pomicanja stranice.

**Naracija:**
> Ana živi u Povljani na Pagu. Otvori pregled svoje općine: ocjena dva, nestabilno. Lani je bila pet. Ocjenu spuštaju dospjele neplaćene obveze: milijun i četrdeset šest tisuća eura, gotovo pola godišnjih rashoda. Kod sličnih općina medijan je dva posto.

**Kadar:** "Ukratko" s oznakom "AI tekst · Gemma 4 31B · 15/15 brojki provjereno". Klik na "1.045.908 €" otvara izračun pokazatelja (gumb "Prikaži izračun"): DO = 23 D + 24 D + 26 D, s ćelijama LU324 i MA324 na listu 2025 Bilance i rashodima poslovanja iz `13 Zadarska.xlsx`, redak 156. Zatim 6 s kartica "Stanovništvo i gospodarstvo" s oznakom "2021.–2024. uživo s API-ja DZS-a" (bez naracije; o API-ju govori dio "Izvori podataka").

**Naracija:**
> Kratko objašnjenje piše otvoreni jezični model, ali brojke ne smišlja on. Program ih izračuna i provjeri svaku. Klik na broj vodi do retka u datoteci Ministarstva financija.

## 1:17-2:01 Funkcionalnosti: simulator i Karta reforme

**Kadar:** s pregleda Povljane "Simuliraj spajanje sa susjedima", pa klik na Pag na karti (`#/simulator?j=05738,03166`). Ploča prije i poslije: ocjena 5 i "9. od 21", tablica u eurima, poruka "Dug ne nestaje spajanjem…", ušteda "0 – 18.045 € godišnje".

**Naracija:**
> O spajanju općina raspravlja se bez brojki. Ovdje se može probati. Povljana i Pag zajedno dobivaju ocjenu pet. Ali dug ne nestaje: milijun i sto šezdeset tisuća eura ostaje, sada petnaest posto rashoda. Ušteda od veličine je mala, do osamnaest tisuća eura godišnje.

**Kadar:** Karta reforme (`#/reforma?prag=5000`), klizač s 2.500 na 5.000 pa na 10.000. Spojene jedinice kratko zasvijetle i dobiju tamni obrub; brojka "555 → 239". Klik na prekidač "Prikaži samo spojene", pa klik na skupinu "Pag + Nin + Vrsi + Kolan + Povljana" (ocjena 5).

**Naracija:**
> Karta reforme spaja najmanje jedinice unutar županije dok ne dosegnu pet tisuća stanovnika. Od 555 općina i gradova ostaje 239. Ušteda na upravi je do trideset šest milijuna eura godišnje, a državni poticaj sto šezdeset osam milijuna. To je scenarij za raspravu, ne prijedlog granica.

## 2:01-2:20 Izvori podataka

**Natpis:** Izvori podataka

**Kadar:** 5 s slika `docs/video/02-izvori.png` (sedam tijela, što je API, a što datoteka). Zatim stranica "Metodologija i podaci", odjeljak "Podaci": ploča "Podaci preko API-ja", na kojoj preglednik uživo pita Portal, DZS PxWeb i WFS i ispiše odgovore ("3.969 skupova u katalogu", "556 općina i gradova u sloju granica"; brojke prije snimanja pročitati sa stranice).

**Naracija:**
> Povezali smo podatke sedam tijela javnog sektora. Svaki izvor koji ima API čitamo preko njega, a stranica ta tri servisa pita i uživo. Izvještaji Ministarstva financija postoje samo kao Excel, pa svako preuzimanje bilježimo s otiskom datoteke.

## 2:20-2:40 Tehnička arhitektura

**Natpis:** Tehnička arhitektura

**Kadar:** 6 s shema `docs/arhitektura.svg` (izvori, obrada u GitHub Actionsu, otvoreni API, web, MCP). Zatim 3 s `openapi.json` i `dcat.jsonld` u pregledniku. Zatim **6 s MCP servera** (`docs/mcp.md`, primjer 2): u MCP klijentu pitanje "Što bi bilo da se Povljana spoji s Pagom?", vidljiv poziv `scenarij_spajanja` i odgovor "ocjena 5 (83,6 boda)".

**Naracija:**
> Sve se izračuna u GitHub Actionsu i objavi kao otvoreni API, s OpenAPI opisom i katalogom DCAT-AP. Poslužitelja i baze nema. Iste brojke AI asistenti dobivaju preko MCP servera.

## 2:40-2:57 Korisnička vrijednost i daljnji razvoj

**Natpis:** Korisnička vrijednost, a od rečenice "Sljedeći korak" natpis Daljnji razvoj

**Kadar:** naslovnica, zatim 4 s slika `docs/video/04-kraj.png` (adresa stranice, repozitorij, licence).

**Naracija:**
> Građanin u minuti razumije stanje svoje općine, a ministarstvo dobiva brojke za raspravu o reformi. Sljedeći korak: Ministarstvo financija objavljuje ove izvještaje na Portalu, a karta se osvježava sama. Kod i podaci su otvoreni.

---

## Provjera obaveznih elemenata (pravila natjecanja)

| Element iz pravila | Gdje | Natpis na ekranu |
|---|---|---|
| Opis problema | 0:00-0:20 | Problem |
| Ciljni korisnici | 0:20-0:36 | Ciljni korisnici |
| Funkcionalnosti | 0:36-2:01 | Funkcionalnosti |
| Korišteni izvori podataka | 2:01-2:20 (i kadar "uživo s API-ja DZS-a" u 1:10) | Izvori podataka |
| Tehnička arhitektura | 2:20-2:40 | Tehnička arhitektura |
| Korisnička vrijednost | 2:40-2:49 (i kroz priču o Ani) | Korisnička vrijednost |
| Mogućnosti daljnjeg razvoja | 2:49-2:57 | Daljnji razvoj |

## Što video pokazuje za ostale kriterije

| Kriterij | Kadar |
|---|---|
| Upotreba otvorenih podataka (API) | ploča "Podaci preko API-ja" s odgovorima uživo; oznaka "uživo s API-ja DZS-a" na pregledu jedinice |
| Povezivanje podataka | slika izvora (sedam tijela, ključevi OIB, RKP, šifra); simulator, koji spaja financije, granice i stanovništvo |
| Inovativnost | oznaka "15/15 brojki provjereno" i klik s brojke na redak u datoteci; MCP server |
| Izvedivost | sve se snima na javnoj stranici, bez montiranih prikaza |
| Dojam | karta s pretapanjem godina, pregled jedinice, simulator |

## Brojke u naraciji (obrada od 6.11.2026.)

| Rečenica | Vrijednost u API-ju | Datoteka |
|---|---|---|
| 576 općina, gradova i županija | 576 (428 općina, 128 gradova, 20 županija) | `jedinice.json` |
| više od dvjesto općina ispod dvije tisuće stanovnika | 202 | `jedinice.json` (`stanovnici`) |
| Povljana: ocjena dva, lani pet | 2 (39,9 boda), 2024.: 5 | `jedinice/opcina-povljana.json` |
| milijun i četrdeset šest tisuća eura, gotovo pola rashoda | 1.045.908 €, 49,4 % rashoda poslovanja | isto, `cinjenice` |
| medijan sličnih općina dva posto | 2,0 % | isto |
| 15/15 brojki provjereno | `objasnjenje.provjera.n_brojki` = 15 | isto |
| Povljana i Pag: ocjena pet | 5 (83,6 boda), 9. od 21 | `simulator/zup-13.json` |
| dug milijun i sto šezdeset tisuća eura, petnaest posto rashoda | 1.159.775 €, 15,1 % rashoda poslovanja | isto (`zadnja.DO`, `zadnja.I5`) |
| ušteda do osamnaest tisuća eura | 0 – 18.045 € | isto |
| od 555 ostaje 239 | 555 → 239 | `reforma/prag-5000.json` |
| ušteda do trideset šest milijuna, poticaj sto šezdeset osam | 36,1 mil. € i 168,5 mil. € | isto |
| sedam tijela javnog sektora | MF, DZS, Porezna uprava, DUR, DGU, MRRFEU, MPUDT (Portal) | `skupovi.json` |
| tri servisa | CKAN, PxWeb, OGC WFS: 9 skupova | `skupovi.json` |

## Popis kadrova za snimanje

Snima se zaslon 1920×1080, preglednik bez traka i kursor uvećan.

1. Naslovnica i animacija godina (gumb "Pokreni" iznad karte, s pretapanjem boja).
2. Pretraga "povlj" i pregled Povljane (ocjena, pokazatelji, traka ocjena po godinama).
3. "Ukratko" s oznakom provjere; klik na "1.045.908 €" i ploča s izračunom za dospjele obveze.
4. Kartica "Stanovništvo i gospodarstvo" Povljane s oznakom "uživo s API-ja DZS-a" (prije snimanja provjeriti da se oznaka pojavi; DZS nakon desetak brzih upita vraća HTTP 429, a tada se prikazuje spremljena kopija bez oznake).
5. Simulator Povljana + Pag, ulaz preko poveznice s pregleda jedinice.
6. Karta reforme: klizač 2.500 → 5.000 → 10.000, isticanje spojenih, "Prikaži samo spojene", klik na skupinu Paga.
7. Stranica "Metodologija i podaci", ploča "Podaci preko API-ja" s tri odgovora uživo (`#/metodologija?o=podaci`), zatim `openapi.json` i `dcat.jsonld` u pregledniku.
8. MCP klijent s pitanjem o Povljani i Pagu (`docs/mcp.md`, primjer 2).
9. Excel tablica Ministarstva financija (PR-RAS), 2 s.

Slike za montažu (1920×1080) su u `docs/video/`: `01-naslov.png`, `02-izvori.png`, `04-kraj.png`, a shema arhitekture je `docs/arhitektura.svg` (16:9). Izvorni SVG-ovi su uz njih, pa se tekst može promijeniti.

## Titlovi

`docs/video/titlovi.srt` sadrži cijelu naraciju, podijeljenu na retke do 42 znaka, s vremenima iz ovog scenarija. Nakon snimanja glasa vremena treba pomaknuti prema stvarnom govoru (Kdenlive: Titlovi → Uvezi titlove, pa povući rubove). Titlovi pomažu žiriju koji gleda bez zvuka.

## Alati (otvoreni)

- OBS Studio za snimanje.
- Kdenlive za montažu.
- Audacity za glas.
- Bez glazbe, ili glazba pod licencom CC0.
- MCP Inspector (Apache-2.0) za kadar MCP servera, ako se ne koristi Claude Desktop.

Sve treba navesti u dokumentaciji (navedeno je u `THIRD_PARTY_LICENSES.md`). Ako se za kadar MCP-a koristi Claude Desktop, on je vlasnički alat i treba ga dodati u README, odjeljak "Korišteni AI alati".

U svakom kadru s kartom mora se vidjeti natpis "OpenFreeMap © OpenMapTiles Data from OpenStreetMap" u kutu karte. MapLibre ga sažme u gumb "i" čim se karta pomakne, pa ga prije snimanja treba otvoriti klikom na "i" ili ga dopisati u montaži. To traže OpenFreeMap i ODbL za video i snimke zaslona.
