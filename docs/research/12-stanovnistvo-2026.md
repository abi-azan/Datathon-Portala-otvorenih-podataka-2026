# 12 Stanovništvo: najsvježiji podaci po JLS (stanje 4.11.2026.)

Oznake: **[V]** provjereno uživo ili u primarnom izvoru, **[P]** zaključak, **[N]** nije pronađeno.

Sve sirove datoteke i skripte su u scratchpadu agenta F (`.../scratchpad/F/raw`, `.../scratchpad/F/scripts`), ne u repozitoriju.

## 1. Sažetak

- **Podataka o broju stanovnika po JLS za 2026. nema.** DZS ih nije objavio i neće ih objaviti do 2027. [V]
- **Najsvježija službena brojka je procjena DZS-a za 31.12.2025.** Objavljena je 30.9.2026., ali samo u XLSX datoteci "Gradovi i općine u statistici". PxWeb je još na 2024. [V]
- **DZS PxWeb dobiva 2025. tek 30.11.2026.** Tada stižu i procjene, i rođeni i umrli, i migracije po JLS. To je nakon roka predaje 9.11. [V] (Kalendar objavljivanja 2026.)
- XLSX se za 2021.-2024. **potpuno poklapa s PxWebom**: 0 razlika u 11.116 ćelija (556 JLS, 5 pokazatelja, 4 godine). Demografska jednadžba (promjena = rođeni − umrli + doseljeni − odseljeni) vrijedi u svih 2.224 jedinica-godina. [V]
- Registar birača (13.5.2026.) jedini je izvor po JLS s datumom u 2026. Kao zamjena za broj stanovnika nije dobar: ne broji strance ni djecu, a broji iseljene. Pag: birača je 2,4 % manje nego 2021., a DZS procjenjuje 6,4 % više stanovnika. [V]

**Preporuka:**
1. **Opcija A, ako tim ima oko 4 sata do 9.11.:** procjenu za 31.12.2025. i prirodno kretanje i migracije za 2025. uzeti iz XLSX-a, samo za godine koje PxWeb još nema. PxWeb ostaje glavni izvor i ide uživo. Oznaka na kartici: "Procjena DZS-a, 31.12.2025.".
2. **Inače opcija B:** ništa ne mijenjati i na kartici napisati da DZS 2025. objavljuje 30.11.2026. Kada izađe, sve se pokupi samo: tjedni CI build i poziv iz preglednika.
3. Ne prikazivati ništa kao "2026." Birače, ako ih uopće uvodimo, prikazati kao poseban podatak, ne kao trend stanovništva.
4. Popis 2021. ostaje baza za pokazatelje po stanovniku, kako je tim odlučio.

## 2. Pitanje 1: procjene DZS-a za 31.12.2025.

### 2.1 PxWeb uživo (4.11.2026.) [V]

GET metapodataka na `https://web.dzs.hr/PXWeb/api/v1/hr/Stanovništvo/...`. Pauza između poziva je bila 3 s, a 429 nije stigao.

| Tablica | Sadržaj | Godine u metapodacima | DZS "updated" |
|---|---|---|---|
| `SP31_2` | procjena 31.12. po JLS | 2001.-**2024.** | 27.11.2025. |
| `SM31` | doseljeni i odseljeni po JLS | 2011.-**2024.** | 27.11.2025. |
| `SV131` | živorođeni po JLS | 2014.-**2024.** | 25.11.2025. |
| `SV331` | umrli po JLS | 2011.-**2024.** | 25.11.2025. |
| `SP22_2` | procjena 31.12. po županijama | 2001.-**2024.** | 25.11.2025. |

U mapi "Procjene stanovništva" nema druge tablice po JLS. Tamo su samo `SP21_1`, `SP22_2`, `SP23_1`, `SP24_2` (županije) i `SP31_2`. [V]

### 2.2 Prva priopćenja za 2025. [V]

| Priopćenje | Objavljeno | Razina | Što kaže |
|---|---|---|---|
| STAN-2026-1-1 Prirodno kretanje u 2025. | 17.7.2026. | RH, županije, **gradovi i općine** | 32.479 živorođenih, 50.007 umrlih. 43 JLS imaju pozitivan prirodni prirast, a 509 JLS i Grad Zagreb negativan. |
| STAN-2026-2-1 Migracija u 2025. | 17.7.2026. | RH, županije | 56.665 doseljenih iz inozemstva (70,3 % stranci), 37.485 odseljenih |
| STAN-2026-3-1 Procjena stanovništva u 2025. | 4.9.2026. | RH, županije | **sredina 2025.**: 3.874.993, Grad Zagreb 777.744 |

Procjena u priopćenju je za sredinu godine i samo po županijama. Za JLS se procjenjuje samo stanje 31.12.

### 2.3 XLSX "Gradovi i općine u statistici" [V]

- URL: `https://podaci.dzs.hr/media/bz5hplcj/gradovi-u-statistici.xlsx` (stalan URL, sadržaj se mijenja).
- Zaglavlja: `Last-Modified: 16.10.2026.`, ETag postoji, a uvjetni GET vraća 304. CORS-a nema, ali za ETL ne treba.
- Licenca je `open-license` (CKAN `statistika-u-nizu-gradovi-u-statistici`).
- **Tab-2.** (procjena 31.12. i prirodno kretanje): stupci za procjenu 2011.-**2025.**, živorođene, umrle, sklopljene i razvedene brakove 2011.-**2025.** te Popis 2011. i 2021.
  - Fusnota 2: "Procjene broja stanovnika od 2021. do 2025. izračunane su na temelju podataka Popisa 2021."
- **Tab-3.** (doseljeni i odseljeni): 2011.-**2025.**, 8 stupaca po godini (ukupno, ista županija, druga županija, inozemstvo, za doseljene i odseljene).
- Ima 556 redaka, svih 556 se spaja na naš šifrarnik po (županija, naziv) s `pxweb.name_key`. Grad Zagreb je jedan redak. Redaka za županije nema. Županija je zbroj svojih JLS, a to točno vrijedi i u PxWebu za 2024. (razlika 0 u svih 20 županija).
- Isti podaci o migraciji 2001.-2025. su i u `stanovnistvo-pregled-po-gradovima-i-opcinama.xlsx` (Last-Modified 30.9.2026., 25 listova, jedan po godini). [V]

**Usporedba s PxWebom** (`data/build/dzs.parquet`, 2021.-2024.) [V]:

```
stanovnici_procjena  2.224 ćelija, 0 razlika
zivorodeni           2.220 ćelija, 0 razlika
umrli                2.224 ćelija, 0 razlika
doseljeni            2.224 ćelija, 0 razlika
odseljeni            2.224 ćelija, 0 razlika
jednadžba stanovništva 2022.-2025.: 0 odstupanja u 556 x 4
zbroj 556 JLS: 2024. 3.874.350 (= PxWeb RH), 2025. 3.876.002
```

Zbrojevi rođenih i umrlih za 2025. jednaki su priopćenju (32.479 i 50.007). Za 3 JLS rođenih 2025. nema, nego stoji "-", što znači nula.

**Uzorak** (procjena 31.12.; Popis 2021. u zagradi):

| JLS | 2021. | 2022. | 2023. | 2024. | **2025.** | 2021.→2025. |
|---|---|---|---|---|---|---|
| Grad Pag (3.175) | 3.156 | 3.176 | 3.238 | 3.352 | **3.358** | +6,4 % |
| Općina Bogdanovci (1.545) | 1.551 | 1.497 | 1.460 | 1.423 | **1.427** | −8,0 % |
| Grad Zagreb (767.131) | 766.824 | 768.624 | 772.122 | 777.359 | **778.184** | +1,5 % |

Kretanje u 2025. (na 1.000 stanovnika Popisa 2021., kako računa `kontekst.py`):

| JLS | rođeni | umrli | prirodni prirast | doseljeni | odseljeni | neto migracija |
|---|---|---|---|---|---|---|
| Pag | 21 | 49 | −28 (−8,8) | 190 | 156 | +34 (+10,7) |
| Bogdanovci | 12 | 18 | −6 (−3,9) | 67 | 57 | +10 (+6,5) |
| Grad Zagreb | 7.036 | 8.608 | −1.572 (−2,0) | 21.675 | 19.278 | +2.397 (+3,1) |

Primjer: Pag 2024. ima 3.352 stanovnika. Uz 21 − 49 + 190 − 156 = +6 dolazi do 3.358 u 2025.

U 2025. raste 230 JLS, a pada 315. Od 2021. do 2025. raste 203 JLS, a pada 353. [V]

### 2.4 Kada DZS objavljuje (Kalendar objavljivanja 2026.) [V]

| Datum | Objava | Razina |
|---|---|---|
| 30.9.2026. (srijeda) | Gradovi i općine u statistici: Stanovništvo, procjena i prirodno kretanje, 2025. | gradovi, općine |
| 30.9.2026. | Gradovi i općine u statistici: doseljeno i odseljeno stanovništvo, 2025. | gradovi, općine |
| 30.9.2026. | Stanovništvo, pregled po gradovima i općinama, 2025. | RH, županije, JLS |
| **30.11.2026. (ponedjeljak)** | **PC-AXIS baze: Procjene stanovništva, Migracije stanovništva, Vitalna statistika (Rođeni, Umrli), 2025.** | RH, županije, **gradovi, općine** |

Program publiciranja 2026. (31.12.2025.) navodi iste datume. Lani je PxWeb ažuriran 25. i 27.11.2025., pa se obrazac ponavlja. [V]

**Odgovor:** procjena za 31.12.2025. je objavljena, ali samo u XLSX-u (30.9.2026.). U PxWebu nije. Isto vrijedi za rođene, umrle i migracije 2025. U PxWeb sve stiže 30.11.2026.

## 3. Pitanje 2: drugi izvori s brojkama za 2025. i 2026.

| Izvor | Postoji po JLS? | Datum | Pristup | Licenca | Usporedivost |
|---|---|---|---|---|---|
| DZS XLSX (§2.3) | da, 556/556 | 31.12.2025. | datoteka, uvjetni GET | Otvorena dozvola | ista serija kao PxWeb [V] |
| Registar birača (MPUDT) | da, 556/556 | 13.5.2026. | CKAN datastore SQL (API), bez CORS-a | Otvorena dozvola | samo punoljetni državljani [V] |
| Porezna uprava, broj osoba s dohotkom | da, 576/576 | 2025. | datoteka (već je imamo) | Otvorena dozvola | nije stanovništvo [V] |
| MUP, prijavljeno prebivalište | ne | | | | [N] |
| HZZO, osigurane osobe | ne (samo RH) | prosjek 2025. | izvješće Vladi | | [N] po JLS |
| e-Građani (MPUDT) | ne (samo županije) | 3.11.2026. | CKAN | Otvorena dozvola | korisnici usluge, ne stanovnici [V] |

### 3.1 Registar birača [V]

- CKAN `registar-biraca-broj-biraca`, resurs `d3e8f75b-...`, 1.014.364 adresa, datastore radi. `SUM` s `WHERE` radi, a `GROUP BY` blokira portal (§2.8 u istraživanju 09). CKAN ne šalje CORS zaglavlje, pa preglednik ne može zvati portal izravno.
- **Postoje stariji izvaci.** CKAN `package_activity_list` pokazuje da se isti resurs mijenjao: 9.9.2021., 29.11.2022., 14.5.2024., 16.5.2025., 13.5.2026.
  - Izvaci iz 2021. i 2022. još su na `mpudt.gov.hr/UserDocsImages/dokumenti/Otvoreni podaci/` (HTTP 200, 78 MB i 80 MB, `Access-Control-Allow-Origin: *`).
  - Stari CKAN URL-ovi za 2024. i 2025. vraćaju današnju datoteku (Last-Modified 14.5.2026.), pa ta dva izvatka više nisu dostupna.
  - Izvadak od 9.9.2021. je samo devet dana nakon Popisa (31.8.2021.), pa je dobra početna točka.

Zbroj `BROJ_BIRACA` (svi statusi adrese):

| JLS | 9.9.2021. | 29.11.2022. | 13.5.2026. | promjena birača | DZS procjena 2021.→2025. |
|---|---|---|---|---|---|
| Pag | 3.131 | 3.084 | 3.056 | −2,4 % | +6,4 % |
| Bogdanovci | 1.525 | 1.484 | 1.441 | −5,5 % | −8,0 % |
| Grad Zagreb | 701.746 | 695.705 | 688.411 | −1,9 % | +1,5 % |
| svih 556 JLS | 2.989.331 | 2.959.844 | 2.911.934 | −2,6 % | +0,1 % |

Usporedba svih 556 JLS (promjena birača 9.9.2021.→13.5.2026. prema promjeni DZS-ove procjene 31.12.2021.→31.12.2025.):
- korelacija je 0,75, a smjer se slaže u 440 od 556 JLS (79 %);
- medijan apsolutne razlike je 2,2 postotna boda, a 90. percentil 7,6 p.b.;
- najveća odstupanja su tamo gdje dolaze strani radnici: Vrhovine (birači −8,8 %, DZS +34,5 %), Funtana (+0,8 % prema +32,6 %), Medulin, Novalja, Plitvička Jezera;
- u Bogdanovcima je birača (1.441) **više** od svih procijenjenih stanovnika (1.427). Omjer birača i stanovnika veći je od 1 u 167 JLS, a najveći je u Obrovcu (1,58) i Benkovcu (1,51).

**Zašto se razlikuje [P, uz V za definicije]:**
- Birači su samo punoljetni hrvatski državljani (i građani EU koji su se prijavili), s prijavljenim prebivalištem. Djece i stranaca iz trećih zemalja nema, a oni su 2025. bili 70 % doseljenih iz inozemstva (STAN-2026-2-1).
- Prebivalište nije uobičajeno mjesto stanovanja. Iseljeni koji nisu odjavili prebivalište ostaju u registru (Obrovac, Benkovac, Bogdanovci). DZS od Popisa 2021. broji po uobičajenom mjestu stanovanja (najmanje 12 mjeseci).
- Vikendaši i studenti često su prijavljeni ondje gdje ne žive.
- Starenje: kada mladi postanu punoljetni, birača raste i bez ikakve selidbe.

**Zaključak:** kao zamjena za trend stanovništva birači su loši baš tamo gdje je priča najzanimljivija (otoci, obala, strani radnici). Mogu biti poseban, jasno označen podatak: "punoljetni državljani s prijavljenim prebivalištem, 13.5.2026.".

### 3.2 Porezna uprava, broj osoba s dohotkom (`porezna_dohodak.parquet`, redak `ukupno`) [V]

| JLS | 2022. | 2023. | 2024. | 2025. |
|---|---|---|---|---|
| Pag | 3.747 | 3.890 | 4.123 | 4.198 |
| Bogdanovci | 1.248 | 1.248 | 1.265 | 1.334 |
| Grad Zagreb | 664.146 | 669.372 | 708.689 | 712.993 |

- Pag ima više osoba s dohotkom (4.198) nego stanovnika (3.358). Tu se broji svatko tko je u godini imao bilo kakav dohodak, uključujući najam (1.087 osoba u Pagu, istraživanje 09 §2.1) i povremeni rad.
- Između 2023. i 2024. Zagreb skače za 5,9 %, a stanovnika ima 0,7 % više. To izgleda kao lom serije nakon porezne reforme 2024. [P]
- Ovo nije mjera stanovništva. Ne koristiti za trend.

### 3.3 MUP, HZZO, ostalo

- **MUP, prijavljeno prebivalište po JLS:** na data.gov.hr nema (`package_search` za `prebivaliste` i `mup prebivaliste` ne daje ništa takvo). Ni na mup.gov.hr nisam našao objavu po JLS. MUP je izvor podataka o migraciji za DZS (STAN-2026-3-1, "Izvori podataka"), pa je DZS-ova serija već najbolja javna obrada tih podataka. [N]
- **HZZO:** po JLS nema ništa. Skup "Broj pacijenata po ordinaciji" na portalu je iz 2018. i ide po ordinaciji, a ne po prebivalištu. Izvješće o poslovanju za 2025. navodi prosječno 4.090.358 osiguranih osoba za cijelu RH, više nego stanovnika (3,87 milijuna). [N] po JLS
- **e-Građani:** korisnici po županiji prebivališta (CKAN `e-gradani-statistika`, 3.11.2026.). Nema JLS, a mjeri korištenje usluge. [V]
- **Mjesečno prirodno kretanje, privremeni podaci 2026.:** DZS ih objavljuje 30. u mjesecu, ali samo za RH. [V]
- **Lokalni izbori 2025.:** brojevi birača po JLS postoje u rezultatima DIP-a. Strojno čitljiv skup za sve JLS na portalu nisam našao, samo pojedinačne općine (npr. `lokalni-izbori-2025` Općine Starigrad). [N]

## 4. Pitanje 3: može li se pošteno prikazati išta "2026."?

- **Broj stanovnika za 2026. ne.** Nijedan službeni izvor nema stanovnike po JLS s datumom u 2026. [V]
- **Najnovija poštena godina je 31.12.2025.** (DZS, XLSX), za svih 556 JLS, za 20 županija kao zbroj i za Grad Zagreb.
  - Oznaka: "Procjena DZS-a, stanje 31.12.2025." Eurostat isti broj zove "1. siječnja 2026.", ali DZS piše 31.12., pa bih ostao uz DZS-ov zapis.
  - Prirodno kretanje i migracija: "2025.".
- **S datumom u 2026. mogu se prikazati:**
  - birači 13.5.2026., kao "punoljetni državljani s prijavljenim prebivalištem", odvojeno od stanovništva;
  - porezne stope 2026. (već ih imamo), koje nisu stanovništvo.
- Ako ostanemo samo na PxWebu, poštena godina do 30.11. je 2024., uz napomenu "DZS 2025. objavljuje 30.11.2026.".

## 5. Pitanje 4: preporuka i trud

### Opcija A: most iz XLSX-a za godine koje PxWeb nema (preporučeno, oko 4 h)

1. **`pipeline/pxweb.py` ili novi `pipeline/dzs_xlsx.py` (1,5 h).**
   - Čita Tab-2 (procjena, živorođeni, umrli) i Tab-3 (ukupno doseljeni i odseljeni) iz `gradovi-u-statistici.xlsx`.
   - Stupce traži po zaglavlju godine u retku 7 (Tab-2), odnosno 5 (Tab-3), a ne po fiksnom indeksu.
   - Spaja po (županija, naziv) postojećim `_match_county`. Županije računa kao zbroj JLS.
2. **Pravilo prednosti (0,5 h).**
   - Za svaku (tablicu, godinu) koju PxWeb ima vrijedi PxWeb. XLSX dodaje samo godine veće od zadnje godine u PxWebu.
   - Stupac `tablica` dobiva vrijednost npr. `GUS_TAB2`, da se na kartici vidi izvor.
   - 30.11. most sam nestaje, jer PxWeb tada ima 2025.
3. **Provjere u testu (0,5 h).**
   - XLSX i PxWeb moraju biti jednaki za sve zajedničke godine (danas 0 razlika).
   - Mora vrijediti jednadžba stanovništva.
   - Ako provjera padne, build ne koristi XLSX.
4. **`sources.py`, `skupovi.csv`, `izvori.json`, OpenAPI (0,5 h).** Uvjetni GET radi (304).
5. **Preglednik (0,5-1 h, obavezno uz A).** `PopulationEconomy.tsx` sada uzima živu seriju umjesto statičke čim živa ima barem dvije godine i prvu godinu (`isLive`). Uz opciju A živi PxWeb do 30.11. vraća 2021.-2024. i **potisnuo bi statičku 2025.**
   - Ispravak: spojiti obje serije po godini, PxWeb gdje postoji i statičku za ostale godine, ili uzeti živu samo kada joj je zadnja godina barem jednaka statičkoj.
   - Oznaku "uživo s API-ja DZS-a" prikazati samo kad živa serija daje zadnju godinu.

Rizik: XLSX je datoteka, ne API. Zato PxWeb ostaje glavni i živi izvor, a XLSX je samo most. To dobro zvuči i u dokumentaciji za kriterij "API".

### Opcija B: čekati DZS (0 h, ali 2025. stiže tek nakon roka)

- **Hoće li pipeline pokupiti 2025. sam?** Da. [V po kodu]
  - `build_query` uzima sve godine ≥ 2021 iz metapodataka, a `kontekst.py` traži `max()` godine.
  - Tjedni CI build ili ručni build nakon 30.11. dodaje 2025. bez promjene koda.
  - Prirodni prirast i migracija uzimaju "zadnju godinu koju imaju sve četiri tablice". DZS objavljuje sve četiri isti dan, pa je to u redu.
- **Hoće li to pokazati poziv iz preglednika?** Da, odmah 30.11., ali samo za broj stanovnika i sparkline. [V po kodu]
  - `live_query` šalje `Godina: all`, a `parseSeries` čita sve godine.
  - Medijan skupine, prirodni prirast i migracija ostaju statični do idućeg builda, najviše 7 dana. Za to vrijeme kartica bi pokazala promjenu 2021.-2025. uz medijan 2021.-2024.
  - Mali popravak: medijan prikazati s godinama, ili ga sakriti kad se živa i statička zadnja godina razlikuju (0,5 h).
- **Rizik [P]:** `parseSeries` provjerava samo kod područja (redni broj 0-576), ne i naziv. Ako DZS 30.11. preslaže retke, kartica bi tiho pokazala drugu jedinicu. Provjera naziva u odgovoru (`category.label[kod]`) uz naziv iz profila stoji 0,5 h.
- Žiri će stranicu vjerojatno otvoriti nakon 30.11. [P]. Tada bi i bez opcije A vidio 2025. uživo. Video i snimke zaslona ostaju na 2024.

### Opcija C: registar birača (2-3 h za 2026.; +1-2 h za usporedbu s 9.9.2021.)

Ne preporučujem ga za trend (§3.1). Ako se radi, neka bude jedan red na kartici: "Birača s prebivalištem (13.5.2026.): 3.056". Uz to ide napomena da su to punoljetni državljani, bez stranaca i djece. Za API bodove nije potreban, jer PxWeb već jest API.

### Ukupno

| Opcija | Trud | Što žiri vidi 9.11. | Nakon 30.11. |
|---|---|---|---|
| A | oko 4 h | 2025. (XLSX), uživo 2024. | PxWeb 2025., most se sam gasi |
| B | 0-1 h (popravci u pregledniku) | 2024. + napomena o 30.11. | 2025. uživo odmah, statično za ≤ 7 dana |
| C | 2-4 h | birači 2026., zbunjujuće | isto |

## 6. Izvori

- DZS PxWeb API v1, mape i metapodaci (GET 4.11.2026.): `https://web.dzs.hr/PXWeb/api/v1/hr/Stanovništvo/Procjene stanovništva` i tablice `SP31_2.px`, `SP22_2.px`; `.../Migracije/SM31.px`; `.../Vitalna statistika/Rođeni/SV131.px`; `.../Vitalna statistika/Umrli/SV331.px`. Licenca Otvorena dozvola (CKAN `stanovni-tvo`).
- DZS, Gradovi i općine u statistici (XLSX, Last-Modified 16.10.2026.): https://podaci.dzs.hr/media/bz5hplcj/gradovi-u-statistici.xlsx (CKAN `statistika-u-nizu-gradovi-u-statistici`)
- DZS, Stanovništvo, pregled po gradovima i općinama (XLSX, 30.9.2026.): https://podaci.dzs.hr/media/2gihgkfh/stanovnistvo-pregled-po-gradovima-i-opcinama.xlsx (CKAN `statistika-u-nizu-stanovni-tvo`)
- DZS, STAN-2026-3-1 Procjena stanovništva RH u 2025. (4.9.2026.): https://podaci.dzs.hr/media/ae2kgoad/stan-2026-3-1-procjena-stanovništva-republike-hrvatske-u-2025.pdf
- DZS, STAN-2026-1-1 Prirodno kretanje stanovništva RH u 2025. (17.7.2026.): https://podaci.dzs.hr/media/4vwbzvld/stan-2026-1-1-prirodno-kretanje-stanovništva-republike-hrvatske-u-2025.pdf
- DZS, STAN-2026-2-1 Migracija stanovništva RH u 2025. (17.7.2026.): https://podaci.dzs.hr/media/j21p3d5v/stan-2026-2-1-migracija-stanovništva-republike-hrvatske-u-2025.pdf
- DZS, Kalendar objavljivanja statističkih podataka za 2026. (PDF): https://dzs.gov.hr/services/publishing/calendar-of-statistical-data-issues-2026/2378
- DZS, Program publiciranja 2026.: https://dzs.gov.hr/UserDocsImages/dokumenti/Program%20publiciranja%202026.pdf
- DZS, DSBB kalendar za studeni 2026.: https://dzs.gov.hr/UserDocsImages/dokumenti/Dokumenti/11%20DSBB%20-%20kalendar%20studeni%202026.pdf
- MPUDT, Registar birača, broj birača po adresi: https://data.gov.hr/ckan/dataset/registar-biraca-broj-biraca (datastore `d3e8f75b-41cc-4e15-a3b6-c1cf3816c2bc`, 13.5.2026.); povijest izmjena: `package_activity_list`, `activity_data_show`
- MPUDT, stariji izvaci: https://mpudt.gov.hr/UserDocsImages/dokumenti/Otvoreni%20podaci/BB_po_adresi_09_09_2021.csv i `.../BB_po_adresi_29_11_2022.csv`
- MPUDT, e-Građani statistika: https://data.gov.hr/ckan/dataset/e-gradani-statistika
- Porezna uprava, Neto dohodak po općinama/gradovima prebivališta: lokalno `data/build/porezna_dohodak.parquet` (istraživanje 09 §2.1)
- HZZO, Izvješće o poslovanju za 2025. (Vlada RH, 171. sjednica, svibanj 2026.): https://vlada.gov.hr/UserDocsImages/2016/Sjednice/2026/Svibanj/171_sjednica_VRH/171%20-%2022%20Izvjesce.pdf (preko pretraživača, PDF nisam otvarao; brojka 4.090.358 je iz sažetka rezultata)
- Kod u repozitoriju: `pipeline/pxweb.py` (`build_query`), `pipeline/kontekst.py` (`live_query`, `indicators`), `web/src/lib/dzs.ts` (`parseSeries`), `web/src/components/PopulationEconomy.tsx` (`isLive`)
