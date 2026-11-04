# Video (najviše 3 minute): scenarij v2

Nacrt noćne smjene od 3.11., na temelju PLAN §10 (vrhunac "Spoji pa vidi"). **v2 (4.11. noću):** simulator, Karta reforme i klik na brojku sada postoje, pa su rezervni kadrovi maknuti, a brojke u kadrovima 4 i 5 su stvarne. Pravila traže da video obuhvati 7 elemenata; tablica na dnu provjerava je li svaki pokriven.

Naracija ima oko 400 riječi, što je oko 2:50 uz smirenu brzinu (oko 140 riječi u minuti). Brojke su iz trenutnog builda (2025.) i treba ih provjeriti prije snimanja.

**Odluke prije snimanja:**
1. **Jedinica u priči:** zasad Povljana. Može biti i jedinica koju netko iz tima stvarno poznaje.
2. **Tko govori:** ljudski glas je bolji od sintetiziranog.
3. **Brojke** su iz builda od 4.11. (2025.) i trebaju se ponovno provjeriti ako se build promijeni.

---

## 0:00-0:22 Problem

**Kadar:** karta Hrvatske, 556 jedinica zasvijetli jedna po jedna. Zatim kadar Excel tablice Ministarstva financija (PR-RAS, tisuće redaka).

**Naracija:**
> Hrvatska ima 576 općina, gradova i županija. Više od dvjesto općina ima manje od dvije tisuće stanovnika. Svaka godišnje predaje financijske izvještaje, ali oni završe u tablicama s tisućama redaka. Je li vaša općina financijski stabilna? Odgovor postoji, samo ga nitko nije izračunao za sve.

## 0:22-0:40 Kome služi i što je Fiskalna karta

**Kadar:** naslovnica Fiskalne karte, pa polako prema legendi.

**Naracija:**
> Fiskalna karta je za građane, novinare, vijećnike i ministarstvo. Svaka jedinica dobiva ocjenu od jedan do pet, iz službenih podataka i uz usporedbu sa sličnima. Ovo nije rang-lista. Mjeri financijsku održivost, a ne kvalitetu upravljanja.

## 0:40-1:25 Ana traži svoju općinu (pregled jedinice)

**Kadar:** pretraga, upisuje se "povlj"; zatim pregled Općine Povljana.

**Naracija:**
> Ana živi u Povljani na Pagu. Upiše ime i otvori se pregled njezine općine: ocjena dva, pod pritiskom. Prošle godine bila je pet. Zašto? Ocjenu najviše spuštaju dospjele neplaćene obveze: milijun i četrdeset šest tisuća eura, gotovo polovina godišnjih rashoda. Kod sličnih općina medijan je dva posto.

**Kadar:** "Ukratko" s oznakom "AI tekst · Gemma 4 31B · N/N brojki provjereno". Klik na "1.045.908 €" otvara "Kako je izračunato": DO = 23 D + 24 D + 26 D, s ćelijama LU324 i MA324 na listu 2025 Bilance i rashodima poslovanja iz `13 Zadarska.xlsx`, redak 156.

**Naracija:**
> Kratko objašnjenje piše otvoreni jezični model, ali brojke ne smišlja on. Svaku brojku izračuna program, a zatim provjeri da je u tekstu točna. Klik na broj pokazuje formulu i točan redak u datoteci Ministarstva financija.

**Kadar:** trend 2019.-2025. uz medijan skupine; upozorenja.

**Naracija:**
> Uz ocjenu su pet sastavnica, sedam godina trenda i usporedba sa sličnim općinama.

## 1:25-2:15 Spoji pa vidi (simulator i Karta reforme)

**Kadar:** s pregleda Povljane "Simuliraj spajanje sa susjedima", pa klik na Pag na karti (`#/simulator?j=05738,03166`). Ploča prije i poslije: ocjena 5 i "9. od 21 u skupini gradovi 2.000-5.000", tablica u eurima, poruka "Dug ne nestaje spajanjem…", ušteda "0 – 18.045 € godišnje" i okvir "Jaz koji postoji i bez spajanja: 1.400.511 €".

**Naracija:**
> Hrvatska raspravlja o spajanju općina, ali bez brojki. Ovdje se može probati. Povljana i Pag zajedno dobivaju ocjenu pet. Ali dug ne nestaje: milijun i sto šezdeset tisuća eura ostaje, samo je sada petnaest posto rashoda umjesto pola. Ušteda od veličine je mala, do osamnaest tisuća eura godišnje. Pag na upravu troši milijun i četiristo tisuća više od sličnih gradova, ali taj trošak postoji i bez spajanja.

**Kadar:** Karta reforme (`#/reforma?prag=5000`), klizač s 2.500 na 5.000 pa na 10.000; brojka "555 → 239"; klik na skupinu "Pag + Nin + Vrsi + Kolan + Povljana".

**Naracija:**
> Karta reforme pokazuje scenarij u kojem se, unutar svake županije, najmanje jedinice spajaju sa susjedima dok ne dosegnu pet tisuća stanovnika. Od 555 općina i gradova ostaje 239. Ušteda na upravi je do trideset šest milijuna eura godišnje. Vladin poticaj za takva spajanja stajao bi sto šezdeset osam milijuna godišnje, pet godina. To je scenarij za raspravu, ne prijedlog granica.

## 2:15-2:45 Podaci i arhitektura

**Kadar:** shema iz README-a (izvori, ETL, statični API, web), zatim stranica "Metodologija i podaci" (tablica skupova i značka "Povučeno s data.gov.hr API-ja"), `openapi.json` i `dcat.jsonld`.

**Naracija:**
> Podatke uzimamo izravno s izvora: financije s Ministarstva financija, stanovništvo i granice preko DZS-ova INSPIRE servisa, a otvorenost jedinica preko API-ja Portala otvorenih podataka. Svako preuzimanje bilježimo s vremenom i otiskom datoteke. Sve se izračuna u GitHub Actionsu i objavi kao otvoreni API s OpenAPI opisom i katalogom DCAT-AP, koji portal može preuzeti. Nema poslužitelja ni baze, pa ga može preuzeti bilo koja institucija.

## 2:45-3:00 Korist i daljnji razvoj

**Kadar:** naslovnica, pa poveznica na repozitorij.

**Naracija:**
> Građanin u minuti razumije stanje svoje općine. Ministarstvo dobiva alat za raspravu o reformi. Sljedeći korak je da Ministarstvo financija objavi ove izvještaje na Portalu otvorenih podataka. Tada se Fiskalna karta osvježava sama. Kod i podaci su otvoreni.

---

## Provjera obaveznih elemenata (pravila natjecanja)

| Element | Gdje |
|---|---|
| Problem | 0:00-0:22 |
| Ciljni korisnici | 0:22-0:40 |
| Izvori podataka | 2:15-2:45 (i 0:00 za MF) |
| Funkcionalnosti | 0:40-2:15 |
| Arhitektura | 2:15-2:45 |
| Vrijednost za korisnika | 2:45-3:00 (i kroz priču o Ani) |
| Daljnji razvoj | 2:45-3:00 |

## Popis kadrova za snimanje

Snima se zaslon 1920×1080, preglednik bez traka i kursor uvećan.

1. Naslovnica i animacija godina ("Pokreni 2019.-2025.").
2. Pretraga "povlj" i pregled Povljane (ocjena, sastavnice, trend).
3. "Ukratko" s oznakom provjere; klik na "1.045.908 €" i ploča "Kako je izračunato" za dospjele obveze.
4. Simulator Povljana + Pag, ulaz preko poveznice s pregleda jedinice.
5. Karta reforme: klizač 2.500 → 5.000 → 10.000 i klik na skupinu Paga.
6. Naslovnica s prekidačem "Prikaz na karti" (trošak uprave, tekuće pomoći), ako stane u vrijeme.
7. Shema arhitekture iz README-a (prepisati u vektorsku sliku).
8. Stranica "Metodologija i podaci", `openapi.json` i `dcat.jsonld` u pregledniku.
9. Repozitorij na GitHubu (README).

## Alati (otvoreni)

- OBS Studio za snimanje.
- Kdenlive za montažu.
- Audacity za glas.
- Glazba bez glazbe ili pod licencom CC0.

Sve treba navesti u dokumentaciji (navedeno je u `THIRD_PARTY_LICENSES.md`).

U svakom kadru s kartom mora se vidjeti natpis "OpenFreeMap © OpenMapTiles Data from OpenStreetMap" u kutu karte. MapLibre ga sažme u gumb "i" čim se karta pomakne, pa ga prije snimanja treba otvoriti klikom na "i" ili ga dopisati u montaži. To traže OpenFreeMap i ODbL za video i snimke zaslona.
