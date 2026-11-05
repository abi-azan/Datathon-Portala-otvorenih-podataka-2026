# Video (najviše 3 minute): scenarij v3

Scenarij prema PLAN §10 (vrhunac "Spoji pa vidi"). Pravila traže da video obuhvati 7 elemenata; tablica na dnu provjerava je li svaki pokriven.

- **v2 (4.11. noću):** simulator, Karta reforme i klik na brojku postoje, pa su rezervni kadrovi maknuti.
- **v3 (5.11. noću):** naracija skraćena s oko 400 na 338 riječi (žiri: govoriti sporije), uz nove kadrove: meko pretapanje boja u animaciji godina, kontekst s oznakom "uživo s API-ja DZS-a", kartica "Fiskalno izravnanje" (Samobor), isticanje spojenih i prekidač "Prikaži samo spojene" na Karti reforme te kadar MCP servera. Ispravljena je rečenica o upravi Paga (jaz od 1,4 mil. € je zbroj obje članice: Pag 1,15 mil. €, Povljana 0,25 mil. €). Sve brojke provjerene su prema API-ju iz online builda od 5.11. (tablica u `docs/noc-5-11.md`, N5).

Uz smirenu brzinu (oko 130 riječi u minuti) govor traje oko 2:35, pa ostaje oko 20 s za stanke i prijelaze. Video mora biti ispod 3:00.

**Odluke prije snimanja:**
1. **Jedinica u priči:** zasad Povljana. Može biti i jedinica koju netko iz tima stvarno poznaje.
2. **Tko govori:** ljudski glas je bolji od sintetiziranog.
3. **Brojke** treba ponovno provjeriti na stranici uživo, nakon pusha u petak (stupac "vrijednost" u tablici N5).

**Kadrovi koji se smiju snimiti tek nakon regeneracije AI tekstova (petak 6.11.):** oznaka [nakon regeneracije]. To su kadar "Ukratko" s AI tekstom Povljane i oznakom "AI tekst · Gemma 4 31B · N/N brojki provjereno". Do tada Povljana pokazuje "Predložak · 9/9". U pilotu v9 Gemma je za Povljanu napisala tekst s 15 brojki i rečenicom konteksta (`docs/research/06-gemma-test.md`).

---

## 0:00-0:20 Problem

**Kadar:** naslovnica, klik na "Pokreni 2019.–2025.". Boje se meko prelijevaju iz godine u godinu (pretapanje), kamera polako ide prema Zadru i Pagu. Zatim kratki kadar Excel tablice Ministarstva financija (PR-RAS, tisuće redaka).

**Naracija:**
> Hrvatska ima 576 općina, gradova i županija. Više od dvjesto općina ima manje od dvije tisuće stanovnika. Svaka godišnje predaje izvještaje koji završe u tablicama s tisućama redaka. Je li vaša općina financijski stabilna? Odgovor postoji, samo ga nitko nije izračunao za sve.

## 0:20-0:33 Kome služi i što je Fiskalna karta

**Kadar:** naslovnica, pa polako prema legendi.

**Naracija:**
> Fiskalna karta je za građane, novinare, vijećnike i ministarstvo. Svaka jedinica dobiva ocjenu od jedan do pet, iz službenih podataka i uz usporedbu sa sličnima. Mjeri održivost proračuna, a ne kvalitetu upravljanja.

## 0:33-1:15 Ana traži svoju općinu (pregled jedinice)

**Kadar:** pretraga, upisuje se "povlj"; zatim pregled Općine Povljana: ocjena 2, 39,9 boda, "Prošle godine 5 · vrlo stabilno".

**Naracija:**
> Ana živi u Povljani na Pagu. Otvori pregled svoje općine: ocjena dva, nestabilno. Lani je bila pet. Ocjenu spuštaju dospjele neplaćene obveze: milijun i četrdeset šest tisuća eura, gotovo pola godišnjih rashoda. Kod sličnih općina medijan je dva posto.

**Kadar [nakon regeneracije]:** "Ukratko" s oznakom "AI tekst · Gemma 4 31B · N/N brojki provjereno". Klik na "1.045.908 €" otvara "Kako je izračunato": DO = 23 D + 24 D + 26 D, s ćelijama LU324 i MA324 na listu 2025 Bilance i rashodima poslovanja iz `13 Zadarska.xlsx`, redak 156.

**Naracija:**
> Kratko objašnjenje piše otvoreni jezični model, ali brojke ne smišlja on. Program ih izračuna i provjeri svaku. Klik na broj vodi do retka u datoteci Ministarstva financija.

**Kadar:** kartica "Stanovništvo i gospodarstvo" na pregledu Povljane, uz oznaku "2021.–2024. uživo s API-ja DZS-a" (broj stanovnika +7,7 % od 2021., 726 u 2025.). Zatim 3 s kartica "Fiskalno izravnanje" Grada Samobora: "Niža stopa poreza: 18 % i 27 % (dopušteno do 22 % i 32 %)", uz najviše stope oko 6,8 mil. € godišnje više.

**Naracija:**
> Uz ocjenu je kontekst koji u nju ne ulazi, a broj stanovnika stiže uživo s API-ja Državnog zavoda za statistiku.

## 1:15-2:05 Spoji pa vidi (simulator i Karta reforme)

**Kadar:** s pregleda Povljane "Simuliraj spajanje sa susjedima", pa klik na Pag na karti (`#/simulator?j=05738,03166`). Ploča prije i poslije: ocjena 5 i "9. od 21 u skupini gradovi 2.000-5.000", tablica u eurima, poruka "Dug ne nestaje spajanjem…", ušteda "0 – 18.045 € godišnje" i okvir "Jaz koji postoji i bez spajanja: 1.400.511 €".

**Naracija:**
> O spajanju općina raspravlja se bez brojki. Ovdje se može probati. Povljana i Pag zajedno dobivaju ocjenu pet. Ali dug ne nestaje: milijun i sto šezdeset tisuća eura ostaje, sada petnaest posto rashoda. Ušteda od veličine je mala, do osamnaest tisuća eura godišnje.

**Kadar:** Karta reforme (`#/reforma?prag=5000`), klizač s 2.500 na 5.000 pa na 10.000. Spojene jedinice kratko zasvijetle i dobiju tamni obrub, vidljiv i na karti cijele države; brojka "555 → 239". Klik na prekidač "Prikaži samo spojene", pa klik na skupinu "Pag + Nin + Vrsi + Kolan + Povljana" (ocjena 5).

**Naracija:**
> Karta reforme spaja najmanje jedinice unutar županije dok ne dosegnu pet tisuća stanovnika. Od 555 općina i gradova ostaje 239. Ušteda na upravi je do trideset šest milijuna eura godišnje, a državni poticaj sto šezdeset osam milijuna. To je scenarij za raspravu, ne prijedlog granica.

## 2:05-2:42 Podaci i arhitektura

**Kadar:** shema iz README-a (izvori, ETL u CI-ju, statični API, web, MCP, Kaggle), zatim stranica "Metodologija i podaci" (tablica skupova), `openapi.json` i `dcat.jsonld`. Zatim **8-10 s MCP servera** (`docs/mcp.md`, primjer 2): u MCP klijentu (npr. Claude Desktop ili MCP Inspector) pitanje "Što bi bilo da se Povljana spoji s Pagom?", vidljiv poziv `scenarij_spajanja`, odgovor "ocjena 5 (83,6 boda), ušteda 0 do 18.044,8 € godišnje" s poveznicom na simulator.

**Naracija:**
> Podatke uzimamo izravno s izvora: Ministarstvo financija, DZS preko INSPIRE i PxWeb servisa, Porezna uprava i Portal otvorenih podataka preko CKAN API-ja. Svako preuzimanje bilježimo s otiskom datoteke. Sve se izračuna u GitHub Actionsu i objavi kao otvoreni API s OpenAPI opisom i katalogom DCAT-AP. Iste brojke AI asistenti dobivaju preko MCP servera.

## 2:42-2:58 Korist i daljnji razvoj

**Kadar:** naslovnica, pa poveznica na repozitorij.

**Naracija:**
> Građanin u minuti razumije stanje svoje općine, a ministarstvo dobiva alat za raspravu o reformi. Sljedeći korak: Ministarstvo financija objavljuje ove izvještaje na Portalu, a Fiskalna karta se osvježava sama. Kod i podaci su otvoreni.

---

## Provjera obaveznih elemenata (pravila natjecanja)

| Element | Gdje |
|---|---|
| Problem | 0:00-0:20 |
| Ciljni korisnici | 0:20-0:33 |
| Izvori podataka | 2:05-2:42 (i 0:00 za MF, 1:05 za DZS uživo) |
| Funkcionalnosti | 0:33-2:05 |
| Arhitektura | 2:05-2:42 |
| Vrijednost za korisnika | 2:42-2:58 (i kroz priču o Ani) |
| Daljnji razvoj | 2:42-2:58 |

## Popis kadrova za snimanje

Snima se zaslon 1920×1080, preglednik bez traka i kursor uvećan.

1. Naslovnica i animacija godina ("Pokreni 2019.–2025.", s pretapanjem boja).
2. Pretraga "povlj" i pregled Povljane (ocjena, sastavnice, trend).
3. **[nakon regeneracije]** "Ukratko" s oznakom provjere; klik na "1.045.908 €" i ploča "Kako je izračunato" za dospjele obveze.
4. Kartica "Stanovništvo i gospodarstvo" Povljane s oznakom "uživo s API-ja DZS-a" (prije snimanja provjeriti da se oznaka pojavi; DZS nakon desetak brzih upita vraća HTTP 429, a tada se prikazuje spremljena kopija bez oznake).
5. Kartica "Fiskalno izravnanje" Grada Samobora (niža stopa poreza).
6. Simulator Povljana + Pag, ulaz preko poveznice s pregleda jedinice.
7. Karta reforme: klizač 2.500 → 5.000 → 10.000, isticanje spojenih, "Prikaži samo spojene", klik na skupinu Paga.
8. Shema arhitekture iz README-a (dijagram mermaid; za video prepisati u vektorsku sliku).
9. Stranica "Metodologija i podaci", `openapi.json` i `dcat.jsonld` u pregledniku.
10. MCP klijent s pitanjem o Povljani i Pagu (`docs/mcp.md`, primjer 2).
11. Repozitorij na GitHubu (README).

## Alati (otvoreni)

- OBS Studio za snimanje.
- Kdenlive za montažu.
- Audacity za glas.
- Glazba bez glazbe ili pod licencom CC0.
- MCP Inspector (Apache-2.0) za kadar MCP servera, ako se ne koristi Claude Desktop.

Sve treba navesti u dokumentaciji (navedeno je u `THIRD_PARTY_LICENSES.md`). Ako se za kadar MCP-a koristi Claude Desktop, on je vlasnički alat i treba ga dodati u README, odjeljak "Korišteni AI alati".

U svakom kadru s kartom mora se vidjeti natpis "OpenFreeMap © OpenMapTiles Data from OpenStreetMap" u kutu karte. MapLibre ga sažme u gumb "i" čim se karta pomakne, pa ga prije snimanja treba otvoriti klikom na "i" ili ga dopisati u montaži. To traže OpenFreeMap i ODbL za video i snimke zaslona.
