# Video (najviše 3 minute): scenarij v1

Nacrt noćne smjene od 3.11., na temelju PLAN §10 ("Svjedodžba za vašu općinu", vrhunac "Spoji pa vidi"). Pravila traže da video obuhvati 7 elemenata; tablica na dnu provjerava je li svaki pokriven.

Naracija ima oko 400 riječi, što je oko 2:50 uz smirenu brzinu (oko 140 riječi u minuti). Brojke su iz trenutnog builda (2025.) i treba ih provjeriti prije snimanja.

**Odluke prije snimanja:**
1. **Jedinica u priči:** zasad Povljana. Može biti i jedinica koju netko iz tima stvarno poznaje.
2. **Tko govori:** ljudski glas je bolji od sintetiziranog.
3. **Simulator i Karta reforme** (kadrovi 4-5) snimaju se tek kad budu gotovi (petak). Do tada ide rezervni kadar.

---

## 0:00-0:22 Problem

**Kadar:** karta Hrvatske, 556 jedinica zasvijetli jedna po jedna. Zatim kadar Excel tablice Ministarstva financija (PR-RAS, tisuće redaka).

**Naracija:**
> Hrvatska ima 576 općina, gradova i županija. Više od dvjesto općina ima manje od dvije tisuće stanovnika. Svaka godišnje predaje financijske izvještaje, ali oni završe u tablicama s tisućama redaka. Je li vaša općina financijski stabilna? Odgovor postoji, samo ga nitko nije izračunao za sve.

## 0:22-0:40 Kome služi i što je Fiskalna karta

**Kadar:** naslovnica Fiskalne karte, pa polako prema legendi.

**Naracija:**
> Fiskalna karta je za građane, novinare, vijećnike i ministarstvo. Svaka jedinica dobiva ocjenu od jedan do pet, iz službenih podataka i uz usporedbu sa sličnima. Ovo nije rang-lista ni službena ocjena. Mjeri financijsku održivost, a ne kvalitetu upravljanja.

## 0:40-1:25 Ana traži svoju općinu (svjedodžba)

**Kadar:** pretraga, upisuje se "povlj"; zatim svjedodžba Općine Povljana.

**Naracija:**
> Ana živi u Povljani na Pagu. Upiše ime i dobije svjedodžbu: ocjena dva, pod pritiskom. Prošle godine bila je pet. Zašto? Ocjenu najviše spuštaju dospjele neplaćene obveze: milijun i četrdeset šest tisuća eura, gotovo polovina godišnjih rashoda. Kod sličnih općina medijan je dva posto.

**Kadar:** "Ukratko" s oznakom "AI tekst · N/N brojki provjereno"; klik na brojku otvara izvor (konto, godina, datoteka Ministarstva).

**Naracija:**
> Kratko objašnjenje piše otvoreni jezični model, ali brojke ne smišlja on. Svaku brojku izračuna program, a zatim provjeri da je u tekstu točna. Klik na broj pokazuje odakle je.

**Kadar:** trend 2019.-2025. uz medijan skupine; upozorenja.

**Naracija:**
> Uz ocjenu su pet sastavnica, sedam godina trenda i usporedba sa sličnim općinama.

*Rezerva dok nema klika na broj:* zadržati se na oznaci provjere i retku sastavnice s brojkom.

## 1:25-2:15 Spoji pa vidi (simulator i Karta reforme)

**Kadar:** simulator. Na karti se odaberu Povljana i susjedni Pag (most i otok su već povezani u podacima). Prikaz prije i poslije: ocjena, stanovnici, ušteda na upravi kao raspon.

**Naracija:**
> Hrvatska raspravlja o spajanju općina, ali bez brojki. Ovdje se može probati. Odaberete susjede i odmah vidite zajedničku svjedodžbu i iskren raspon uštede na općoj upravi, od nule do gornje granice.

**Kadar:** Karta reforme. Prag od 5.000 stanovnika i karta koja prelazi s 556 na N jedinica.

**Naracija:**
> Karta reforme pokazuje scenarij u kojem se, unutar svake županije, susjedne jedinice spajaju dok ne dosegnu pet tisuća stanovnika. To je scenarij za raspravu, ne prijedlog granica.

*Rezerva ako simulator ne bude gotov:* svjedodžba susjedne jedinice i tekst "simulator: u izradi". Taj dio se tada skraćuje, a dio o arhitekturi produljuje.

## 2:15-2:45 Podaci i arhitektura

**Kadar:** shema iz README-a (izvori, ETL, statični API, web), zatim `openapi.json` i stranica s popisom skupova podataka.

**Naracija:**
> Podatke uzimamo izravno s izvora: financije s Ministarstva financija, stanovništvo i granice preko DZS-ova INSPIRE servisa, a otvorenost jedinica preko API-ja Portala otvorenih podataka. Svako preuzimanje bilježimo s vremenom i otiskom datoteke. Sve se izračuna u GitHub Actionsu i objavi kao otvoreni API s OpenAPI opisom. Nema poslužitelja ni baze, pa ga može preuzeti bilo koja institucija.

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
2. Pretraga "povlj" i svjedodžba Povljane (ocjena, sastavnice, trend).
3. "Ukratko" s oznakom provjere; klik na broj (kad bude gotov).
4. Simulator Povljana + Pag (kad bude gotov).
5. Karta reforme s pragom 5.000 (kad bude gotova).
6. Shema arhitekture iz README-a (prepisati u vektorsku sliku).
7. `openapi.json` i `docs/skupovi-podataka.md` u pregledniku.
8. Repozitorij na GitHubu (README).

## Alati (otvoreni)

- OBS Studio za snimanje.
- Kdenlive za montažu.
- Audacity za glas.
- Glazba bez glazbe ili pod licencom CC0.

Sve treba navesti u dokumentaciji (navedeno je u `THIRD_PARTY_LICENSES.md`).

U svakom kadru s kartom mora se vidjeti natpis "OpenFreeMap © OpenMapTiles Data from OpenStreetMap" u kutu karte. MapLibre ga sažme u gumb "i" čim se karta pomakne, pa ga prije snimanja treba otvoriti klikom na "i" ili ga dopisati u montaži. To traže OpenFreeMap i ODbL za video i snimke zaslona.
