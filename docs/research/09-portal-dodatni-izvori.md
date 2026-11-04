# 09 — Portal otvorenih podataka: dodatni izvori za Fiskalnu kartu

Datum istraživanja: 2026-11-04. Svrha: na data.gov.hr pronaći nacionalne skupove koji pokrivaju (gotovo) svih 576 jedinica, imaju ključ za naš šifrarnik i mogu se ugraditi za pola dana do dan rada. Ne ponavljam ono što već koristimo (`docs/skupovi-podataka.md`) ni ono što je opisano u `research/04`, osim kad sam izvor sada stvarno izbrojio.

| Oznaka | Značenje |
|---|---|
| **[V]** | Provjereno 4.11.2026.: resurs dohvaćen, pokrivenost izbrojena spajanjem s `data/build/units.csv`. |
| **[P]** | Naša prosudba ili izračun. |
| **[N]** | Nije provjereno. |

Pokrivenost je uvijek izbrojena, ne procijenjena. "556/556" znači svih 556 općina i gradova. Županije (20) navodim posebno.

---

## 1. Sažetak

1. **Najbolji novi izvor: Porezna uprava, "Neto dohodak stanovništva po općinama/gradovima" 2022.-2025.** Pokriva svih 556 jedinica i 20 županija, a ažuriran je 16.10.2026. Daje dohodak, porez i broj osoba po vrsti dohotka. Prvi put dobivamo porezni kapacitet stanovnika, a ne samo proračuna. Primjer: neto dohodak u Pagu je 9.574 € po stanovniku, a medijan svih jedinica 7.814 €. Povezivanje s PR-RAS-om radi: Zagreb knjiži 94 % poreza koji plate njegovi stanovnici. Trud: 3-4 h.
2. **DZS PxWeb API (procjene stanovništva, migracije, turizam, građevinske dozvole).** Svih 556 jedinica, pravi API s CORS-om. Turizam i dozvole imaju i DGU šifru u kodu. Daje stanovništvo nakon 2021. (do 31.12.2024.) i turizam za "statističke blizance" iz PLAN-a §3.5. Za bodove "API" ovo je najjači dodatak. Trud: 4 h za klijent i stanovništvo, plus 2 h za turizam i dozvole.
3. **Porezna uprava, lokalne porezne stope 2025./2026.** Ključ je DGU šifra, pa se 556/556 spaja bez ijednog naziva. Pokazuje koliko jedinica ne koristi zakonski porezni prostor: 123 od 552 imaju nižu stopu od dopuštene, među njima Split, Rijeka i Osijek. To se izravno veže na naš izračun izravnanja (kapacitet se računa uz najvišu stopu). Trud: 2-3 h.
4. Slijede četiri slabija kandidata, svaki s jasnim rizikom: DZS "Gradovi u statistici" (vrtići i zaposleni, ali samo datoteka), izvješća o provedbi ZPPI-a (575/576 po OIB-u, ali bez licence i izvan portala), popis operacija OPKK (331 JLS po OIB-u, ali stanje 2023.) i registar birača (556/556 preko datastore SQL-a, ali skroman dobitak).
5. **Što nisam našao:** nezaposlenost po JLS, komunalna društva s vlasnikom i iznosom duga, javnu nabavu po naručitelju i EU sredstva 2021.-2027. Na portalu za to nema ujednačenog nacionalnog skupa (§3).

---

## 2. Uži popis (rangirano)

### 2.1 Porezna uprava: Neto dohodak stanovništva po općinama/gradovima prebivališta, 2022.-2025. [V]

| | |
|---|---|
| Izdavatelj | Porezna uprava (Ministarstvo financija) |
| Skup | https://data.gov.hr/ckan/dataset/https-porezna-uprava-gov-hr-hr-porez-na-dohodak-4763-4763 (naslov "Porez na dohodak") |
| Resurs | https://data.gov.hr/ckan/dataset/bdbde39b-18b5-47f5-9066-4d73c33b0fcf/resource/f0b05b72-fcab-4597-9e59-e172f90cf506/download/pk_neto-dohodak-stanovnistva-2022_2025-30_9_26-1.xlsx |
| HTTP / format | 200, XLSX, 1.543.628 B; šalje `ETag` i `Last-Modified: 16 Oct 2026`, pa radi uvjetni GET iz `sources.py` |
| Pristup | Datoteka u CKAN spremištu portala, bez datastorea. URL treba čitati iz `package_show`, jer se ime datoteke mijenja sa svakim izdanjem (`-1`, `-5`). |
| Licenca | `open-license` (Otvorena dozvola); `metadata_modified` 2026-10-16 |
| Godine | listovi `2025 EUR`, `2024 EUR`, `2023 EUR`, `2022 HRK` (2022. je u kunama) |
| Pokrivenost | **556/556 JLS** po (šifra županije iz "13 - ZADARSKA ŽUPANIJA", naziv velikim slovima): 555 točno, 1 uz normalizaciju. Uz to 20 redaka "UKUPNO ŽUPANIJA", dakle **576/576**. Isto vrijedi za sve četiri godine. |

Svaka jedinica ima 9 redaka. Osam ih je po vrsti dohotka (zaposlenici iz JOPPD-a, umirovljenici, obrt, paušalisti, kapital, drugi dohodak, imovina, "povremeni rad - imovina"), a deveti je "UKUPNO OPĆINA". Stupci su broj osoba, bruto, doprinosi, dohodak, porez i neto. U retku UKUPNO broj osoba je broj različitih osoba: u Bedenici 1.013, a zbroj po vrstama je 1.280.

Uzorak (list `2025 EUR`):

```
13 - ZADARSKA ŽUPANIJA | PAG | IZ JOPPD - ZAPOSLENICI   | 2164 | 24835370.05 | 4788068.03 | 20047301.95 | 1800703.52 | 18244547.56
13 - ZADARSKA ŽUPANIJA | PAG | POVREMENI RAD - IMOVINA  | 1087 | 0           | 0          | 0           | 694476.98  | 0
13 - ZADARSKA ŽUPANIJA | PAG | UKUPNO OPĆINA            | 4198 | 35467565.92 | 4813069.31 | 32812207.88 | 3197794.81 | 30398826.56
```

**Provjera povezivanja s PR-RAS-om [V/P].** Usporedio sam konto 611 u PR-RAS-u 2025. (porez na dohodak koji jedinica knjiži) sa stupcem "Porez" za stanovnike te jedinice. Spojilo se svih 556 jedinica.
- Omjer je u medijanu 0,643 (p10 0,546, p90 0,706). Pag ima 0,713, a Bedenica 0,633.
- Zagreb ima 0,942. To odgovara zbroju gradskog i županijskog udjela u porezu na dohodak (74 % + 20 %) [N: udjele potvrditi u čl. 5. Zakona o financiranju JLP(R)S].
- Moguće objašnjenje nižeg omjera kod ostalih jedinica su povrati iz godišnjeg obračuna [P].
- Dva izvora dakle govore istu priču, a podatak Porezne uprave je ono što jedinica "ima na raspolaganju" prije podjele.

**Što omogućuje [P]:**
- **Profil:** neto dohodak po stanovniku. U Pagu je 9.574 €, a medijan jedinica 7.814 €. Raspon ide od 3.195 € (Ervenik) do 16.113 € (Funtana), uz nazivnik iz Popisa 2021. Prikazuje se i udio mirovina u dohotku.
- **Turizam u kućanstvima:** redak "povremeni rad - imovina" po našem čitanju je paušal od iznajmljivanja turistima [N]. U Pagu ga plaća 1.087 osoba.
- **Simulator:** zbroj dohotka članica daje dohodak po stanovniku spojene jedinice, a dohodak se može staviti uz kapacitet iz tablice izravnanja.
- **Karta reforme:** sloj dohotka po stanovniku.
- **AI:** nova činjenica u paketu (verifikator je provjerava kao i ostale brojke).

**Trud:** 3-4 h. Treba parser za četiri lista (2022. preračunati po 7,53450), redak u `skupovi.csv`, shemu u `openapi.py` i test zbroja: zbroj UKUPNO OPĆINA po županiji mora biti jednak retku UKUPNO ŽUPANIJA.

**Rizici:**
- Ključ su nazivi bez šifre. Spajanje radi za 556/556, ali dupli nazivi (Otok, Privlaka, Sveta Nedelja) moraju ići preko županije.
- Dohodak se vodi po prebivalištu, a ne po stvarnom stanovanju. Visoke vrijednosti u Novom Vinodolskom i Mošćeničkoj Dragi mogu biti umirovljenici s prijavljenim prebivalištem uz more [P].
- Struktura se mijenja: 2022.-2023. postoji redak "DOHODAK OD OSIGURANJA", a stupac je "Porez + prirez". Od 2024. stupac je samo "Porez".
- Uz skup postoji i datoteka `dohodak-po-jls-i-razredima-2023-2024-3.xlsx` (broj obveznika po poreznom razredu). Manje je važna i ima drugačiji raspored.

### 2.2 DZS PxWeb: procjene stanovništva, migracije, rođeni i umrli po JLS [V]

| | |
|---|---|
| Izdavatelj | Državni zavod za statistiku |
| Skup na portalu | "Stanovništvo", https://data.gov.hr/ckan/dataset/stanovni-tvo (resurs `pc-axis` vodi na PxWeb) |
| API | `https://web.dzs.hr/PXWeb/api/v1/hr/Stanovništvo/Procjene stanovništva/SP31_2.px`: GET daje metapodatke, a POST upit vraća `json-stat2`. Šalje `Access-Control-Allow-Origin: *`, pa ga i preglednik može zvati uživo. |
| Licenca | `open-license`; `metadata_modified` 2026-11-03 |
| Tablice | `SP31_2` procjena stanovništva 31.12., 2001.-2024. (ažurirano 27.11.2025.); `SM31` doseljeni i odseljeni u 8 kategorija, 2011.-2024.; `SV131` živorođeni, 2014.-2024.; `SV331` umrli, 2011.-2024. |
| Pokrivenost | **556/556** po (županija iz retka zaglavlja, naziv). 548 točno, 7 dvostrukih naziva sa županijom u zagradi, npr. "Otok (Vukovarsko-srijemska županija)", i 1 bez crtice ("Malinska Dubašnica"). Šifre nema: vrijednosti su redni brojevi 0-576. Grad Zagreb je jedan redak, "GRAD ZAGREB". |

Uzorak (`SP31_2`, svega, 31.12.):

```
Novalja            2021: 3722   2022: 3824   2023: 4051   2024: 4285
Pag                2021: 3156   2022: 3176   2023: 3238   2024: 3352
REPUBLIKA HRVATSKA 2021: 3862305 ...                      2024: 3874350
```

`SM31` 2024.: Pag ima 255 doseljenih i 115 odseljenih, Bedenica 35 i 31.

**Što omogućuje [P]:**
- **Profil:** promjena stanovništva 2021.-2024. (Novalja +15 %, Pag +6 %) i neto migracija. PLAN §3.4 traži promjenu stanovništva, a sad je imamo i nakon Popisa.
- **Karta reforme i simulator:** demografski trend članica i spojene jedinice.
- **Metodologija:** po stanovniku se danas računa s Popisom 2021. Prelazak na procjenu za istu godinu promijenio bi pokazatelje, pa to treba odlučiti posebno. Za početak bih procjenu prikazivao samo kao kontekst.

**Trud:** 3-4 h za generički PxWeb klijent (cache, ponovni pokušaj, spajanje po zaglavlju županije). Isti klijent zatim služi za §2.4.

**Rizici:**
- PxWeb ograničava brzinu. Nakon desetak brzih poziva vraća HTTP 429, pa treba pauza od 2-5 s i cache u `data/raw`.
- Procjena za 2025. još nije u PxWebu. Ima je DZS-ova datoteka iz §2.5.
- Putanje sadrže razmake i dijakritike, pa ih treba URL-enkodirati.

### 2.3 Porezna uprava: Usporedba poreznih stopa prema odlukama JLS (2025./2026.) [V]

| | |
|---|---|
| Izdavatelj | Porezna uprava |
| Skup | https://data.gov.hr/ckan/dataset/https-porezna-uprava-gov-hr-hr-odluke-jls-4009 |
| Resursi | Porez na dohodak 2026.: [`tablica-poreznih-stopa-...-2026-godinu-1.xlsx`](https://data.gov.hr/ckan/dataset/3c19c044-4cc4-42f1-ac97-29286a2bf305/resource/3c80d05a-3104-4f26-ad27-9ddb63d39070/download/tablica-poreznih-stopa-godinjeg-poreza-na-dohodak-za-2026-godinu-1.xlsx). Usporedba 2025./2026.: [`stope_poreza_na_dohodak_usporedba-2025-i-2026.xlsx`](https://data.gov.hr/ckan/dataset/3c19c044-4cc4-42f1-ac97-29286a2bf305/resource/a33cb1d7-969f-498f-9e9d-0d6eddd9cd87/download/stope_poreza_na_dohodak_usporedba-2025-i-2026.xlsx), ima i datastore. Porez na potrošnju 2026., porez na nekretnine 2025./2026. i paušalni porez po JLS i naselju 2026. Sve vraća HTTP 200 i XLSX, ukupno oko 400 KB. |
| Pristup | Datoteke. Usporedba ima `datastore_active=true`: `datastore_search_sql` vraća 556 redaka s nazivom i bez mojibakea, ali bez šifre. |
| Licenca | `open-license`; `metadata_modified` 2026-04-15, resursi 6.2.2026. |
| Pokrivenost | **556/556 po DGU šifri** (stupac "Šifra grada/općine" = naša šifra bez vodećih nula, npr. 19 = 00019 Andrijaševci) za porez na dohodak, potrošnju i nekretnine. Nijedan naziv se ne razlikuje. |

Uzorak (2026.):

```
Rbr. | Šifra | Ime        | Uplatni račun         | NN     | Niža stopa | Viša stopa | Stupanje na snagu
1.   | 19    | ANDRIJAŠEVCI | HR1910010051700112008 | 157/23 | 0.2       | 0.3        | 1.1.2024.
8.   | 86    | BAŠKA      | HR6510010051700812005 | 143/23 | 0.15       | 0.25       | 1.1.2024.
9.   | 94    | BAŠKA VODA | HR7110010051700912001 | 151/23 | 0.17       | 0.27       | 1.1.2024.
```

**Nalaz [V/P].** Nižu stopu za 2026. usporedio sam s najvišom dopuštenom stopom iz MF-ove tablice izravnanja (stupac "MAX NIŽA STOPA", `izravnanje.parse_mf`). Moje brzo spajanje našlo je tu stopu za 552 jedinice.
- Na maksimumu je 429 jedinica, a ispod njega 123: 105 gradova i 18 općina.
- Primjeri: Split 21,5 % (najviše 22 %), Rijeka, Osijek, Zadar i Velika Gorica 20 % (najviše 22 %), Karlovac 19 %. Baška je na zakonskom minimumu, 15 % i 25 %.
- Porez na potrošnju: 477 jedinica ima 3 %, a 42 ga ne naplaćuju.
- Porez na nekretnine: 385 jedinica prepušta naplatu Poreznoj upravi, a 171 ga naplaćuje same.

**Što omogućuje [P]:**
- **Profil:** "porezni napor", tj. koliko jedinica koristi zakonski prostor. Kontekst, ne ocjena: niža stopa je politički izbor, ne slabost.
- **Simulator i izravnanje:** MF računa kapacitet uz najvišu stopu (`research/07`). Jedinica s nižom stopom zato ne dobiva izravnanje za porez koji sama ne naplaćuje. To se može objasniti na profilu, a za spojenu jedinicu može se prikazati stopa koja bi vrijedila.
- **Povezivanje s §2.1:** iz dohotka i stope može se procijeniti koliko poreza jedinica ne naplaćuje. Treba raspodjela po razredima, pa je to dodatni korak.

**Trud:** 2-3 h, jer je ključ šifra, a gornja granica je već u `izravnanje.parse_mf`.

**Rizici:**
- Gornja granica ovisi o statusu: općina 20 %, grad 21 %, sjedište županije ili grad iznad 35.000 stanovnika 22 %, Zagreb 23 %. Treba je čitati iz MF-ove tablice, ne iz pretpostavke.
- Datastore nema šifru, a ima dvostruke nazive (Otok, Privlaka, Sveta Nedelja). Za spajanje treba XLSX.
- Porez na nekretnine ponegdje je upisan kao tekstualni raspon ("3,60 do 4,50"). Paušal je po naseljima i ulicama (1.444 retka).
- Stope su iz odluka, a ne iz ostvarenja.

### 2.4 DZS PxWeb: turizam (BS_TU19) i gradnja (PX14, PX15, PX6, PX7) po JLS [V]

| | |
|---|---|
| Izdavatelj | Državni zavod za statistiku |
| Skupovi na portalu | "Turizam", https://data.gov.hr/ckan/dataset/proizvodnja-orani-nih-usjeva-u-tonama (slug je pogrešan, naslov je "Turizam"); "Građevinarstvo", https://data.gov.hr/ckan/dataset/gradevinarstvo. Oba `open-license`, `metadata_modified` 2026-10-15. |
| API | `.../Turizam/Dolasci i noćenja turista u komercijalnim smještajnim objektima/BS_TU19.px` (2021.-2025., 14 pokazatelja, ažurirano 20.2.2026.); `.../Građevinarstvo/Građevinske dozvole/PX14.px` (dozvole po broju, površini i volumenu, 2014.-2025., ažurirano 3.9.2026.), `PX15.px` (stanovi u dozvolama); `.../Završene zgrade i stanovi/PX6.px` i `PX7.px` (2013.-2025.) |
| Pokrivenost | **556/556 po DGU šifri ugrađenoj u kod**: BS_TU19 `HR0203` + `00833`, PX14 `01` + `1` (gradovi) ili `2` (općine) + `01015`. Nijedan naziv se ne razlikuje. |

Uzorak (BS_TU19, 2025.):

```
Novalja  | stalne postelje 25726 | noćenja 1890591 | noćenja na 100 stanovnika 51374.8
Pag      | stalne postelje 10814 | noćenja  776716 | noćenja na 100 stanovnika 24463.5
Bedenica | stalne postelje    19 | noćenja       – | –
```

PX14, broj zgrada s izdanom dozvolom: Novalja 91 (2024.) i 44 (2025.), Pag 31 i 41, Bedenica 1 i 2. Prazno ("–") je 2024. kod 59 jedinica, a 2025. kod 41.

**Što omogućuje [P]:**
- **Blizanci i kontekst:** turizam po stanovniku je u PLAN-u §3.5 kao varijabla blizanaca, ali nije ugrađen. Uz to objašnjava visoke prihode turističkih jedinica (Novalja).
- **Gradnja:** dozvole su znak ulaganja i mogu se staviti uz komunalni doprinos u PR-RAS-u (skupina 653).
- **Karta:** slojevi intenziteta turizma i gradnje.

**Trud:** oko 2 h za obje tablice uz klijent iz §2.2.

**Rizici:**
- Ista ograničenja brzine kao u §2.2.
- BS_TU19 pokriva samo komercijalni smještaj.
- Dozvole ne znače dovršenu gradnju; za to su PX6 i PX7.

### 2.5 DZS: Statistika u nizu, "Gradovi i općine u statistici" (XLSX) [V]

| | |
|---|---|
| Izdavatelj | Državni zavod za statistiku |
| Skup | https://data.gov.hr/ckan/dataset/statistika-u-nizu-gradovi-u-statistici |
| Resurs | https://podaci.dzs.hr/media/bz5hplcj/gradovi-u-statistici.xlsx: HTTP 200, 3.258.710 B, `Last-Modified: 16 Oct 2026`. CKAN za resurs navodi 2.3.2023., ali URL je stalan, a sadržaj se ažurira. |
| Pristup | Datoteka |
| Licenca | `open-license`; `metadata_modified` 2026-04-15 |
| Pokrivenost | **556/556** po (županija, naziv); jedan naziv treba normalizirati ("Zlatar-Bistrica" je kod nas "Zlatar Bistrica"). Provjereno za Tab-2, Tab-4 i Tab-8. |
| Sadržaj | 16 tablica, među njima:<br>- **Tab-2:** procjene stanovništva 2011.-2025. (godinu dalje od PxWeba) i prirodno kretanje;<br>- **Tab-4:** zaposleni u pravnim osobama na dan 31.3., 2011.-2025.;<br>- **Tab-8:** dječji vrtići (broj ustanova, djece i zaposlenih) po pedagoškoj godini, od 2011./12. do 2025./26.;<br>- **Tab-9:** osnovne škole. |

Uzorak (Tab-8, 2025./26.: ustanova, djeca, zaposleni; Tab-4: zaposleni 2024. i 2025.):

```
Novalja   vrtići 2 | djeca 196 | zaposleni 40    zaposleni u pravnim osobama 1268 → 1593
Pag       vrtići 1 | djeca 119 | zaposleni 26    zaposleni u pravnim osobama  848 → 1140
Bedenica  vrtića nema (–)                        zaposleni u pravnim osobama  447 →  480
```

**Što omogućuje [P]:**
- **Vrtići:** pedagoške godine 2025./26. vrtić ima 494 jedinice, a u vrtićima je ukupno 158.685 djece. To je jedini ujednačen nacionalni podatak o vrtićima po JLS koji sam našao. Registar MZO-a ima samo poštansko mjesto (§3).
- **Zaposlenost:** stopa zaposlenosti 2025. (zaposleni po prebivalištu prema radno sposobnom stanovništvu).
- **Stanovništvo:** procjena za 2025. kao nadopuna §2.2.

**Trud:** 4-5 h. Zaglavlja imaju više redaka, a svaka tablica ima drugačiji raspored.

**Rizici:**
- Ovo je datoteka, ne API.
- Tab-4 ima lom serije: fusnota za 2025. kaže da su podaci "prema mjestu prebivališta". Bistra skače s 981 na 2.837 zaposlenih, a Zagreb pada s 374.386 na 345.016. Do 2024. je, po svemu sudeći, mjesto rada [N].
- Za Tab-8 nisam provjerio broji li se vrtić po sjedištu ili po objektu [N].

### 2.6 Povjerenik za informiranje: izvješća tijela javne vlasti o provedbi ZPPI-a (2025.) [V]

| | |
|---|---|
| Izdavatelj | Povjerenik za informiranje |
| Skup | https://data.gov.hr/ckan/dataset/kumulativna-izvjesca-tijela-javne-vlasti-o-provedbi-zakona-o-pravu-na-pristup-informacijama |
| Resurs na portalu | "CSV" s `datastore_active=true` vodi na HTML stranicu, a datastore sadrži HTML te stranice (2.397 redaka). Neupotrebljivo. |
| Stvarna datoteka | https://pristupinfo.hr/wp-content/uploads/2026/03/2025.xlsx: HTTP 200, 6.151.287 B, `Last-Modified: 11 Mar 2026`. Ista stranica ima godine 2015.-2024. |
| Licenca | U CKAN-u nije navedena (`license_id` prazan). Osnova bi bila ista kao za MF (ZPPI, Otvorena dozvola) [P]. |
| Pokrivenost | **575/576 po OIB-u**. OIB je spremljen kao broj, pa treba dodati vodeće nule do 11 znamenki. Nedostaje samo Općina Raša. |
| Sadržaj | 5.280 tijela i 264 stupca: zahtjevi preneseni, zaprimljeni, riješeni u roku i izvan roka, način rješavanja, žalbe itd. Ima i stupce "Djelatnost", "Osnivač" i "Status". |

Uzorak (ukupno zaprimljenih zahtjeva u 2025.):

```
Grad Zagreb      485
Grad Pag          15
Grad Novalja      12
Općina Bedenica    3      (29 jedinica nije zaprimilo nijedan zahtjev)
```

**Što omogućuje [P]:**
- **Sloj otvorenosti:** uz broj skupova na portalu dodaje stvarnu potražnju za informacijama (zahtjevi na 1.000 stanovnika) i udio riješenih u roku.
- **Društva u vlasništvu jedinica:** popis sadrži 577 trgovačkih društava kojima je osnivač "jedinica lokalne ili područne samouprave" (npr. "6. maj d.o.o.", Umag; komunalne usluge). Vlasnik nije naveden, samo sjedište (279 mjesta), pa to može biti samo naznaka, a ne pripisivanje duga.

**Trud:** oko 3 h. Čitanje lista traje oko minutu, jer je formatiran do 1.047.799 redaka.

**Rizici:**
- Licenca nije navedena.
- Datoteka nije na portalu (portal samo upućuje na stranicu), pa za bodove "portal i API" ne pomaže.
- Podatke prijavljuju sama tijela.

### 2.7 MRRFEU: Popis operacija Programa "Konkurentnost i kohezija 2014.-2020." [V]

| | |
|---|---|
| Izdavatelj | Ministarstvo regionalnoga razvoja i fondova EU |
| Skup | https://data.gov.hr/ckan/dataset/popis-operacija-financiranih-u-okviru-programa-konkurentnost-i-kohezija-2014-2020 |
| Resurs | https://data.gov.hr/ckan/dataset/4a50b669-6076-436e-a722-c090ba59c8ce/resource/6b4f95d3-b347-41b0-aae3-a117aecb4c6d/download/popis-operacija-opkk-31.5.2023.xlsx: HTTP 200, XLSX, 3.897.433 B |
| Licenca | `open-license`; resurs od 7.11.2023., stanje 31.5.2023. |
| Pokrivenost | Po OIB-u korisnika (stupac "Identifikacijski broj korisnika", list "CUT OFF 31.05.2023"): **331/556 JLS i 20/20 županija** su korisnici. To je 1.267 operacija s 974,8 mil. € iz ESI fondova. Jedinice bez projekta nisu u popisu, pa je za njih vrijednost 0. |

Uzorak:

```
Osječko-baranjska županija   60 operacija   ESIF 23.964.355 €
Grad Zagreb                  51 operacija   ESIF 82.309.552 €
Grad Novalja                  4 operacije   ESIF  8.122.266 €   (Pag: 0)
```

**Što omogućuje [P]:** na profilu "EU projekti iz OPKK-a (broj, iznos)" uz našu oznaku "EU projekt" (konto 638), kao dokaz s imenom projekta.

**Trud:** 1,5-2 h (ključ je OIB).

**Rizici:**
- Samo jedan program: nema Programa ruralnog razvoja (iz kojeg općine najčešće dobivaju novac), NPOO-a ni razdoblja 2021.-2027.
- Stanje je iz 2023. i ne ažurira se.
- Iznosi su ugovoreni, ne isplaćeni.

### 2.8 MPUDT: Registar birača, broj birača po adresi (13.5.2026.) [V]

| | |
|---|---|
| Izdavatelj | Ministarstvo pravosuđa, uprave i digitalne transformacije |
| Skup | https://data.gov.hr/ckan/dataset/registar-biraca-broj-biraca |
| Resurs | `bb_po_adresi_13_05_2026.csv`: HTTP 200, 79.570.791 B. Preveliko za preuzimanje, ali je u datastoreu (1.014.364 retka). |
| Pristup | **API (CKAN `datastore_search_sql`)**. `GROUP BY` portal blokira: veza se odmah prekida, pet pokušaja. `DISTINCT`, `SUM` i `WHERE` rade. Zato: 1 upit za 556 parova (županija, općina), pa 556 upita sa `SUM`. Ukupno 51 s. |
| Licenca | `open-license`; `metadata_modified` 2026-05-14 |
| Pokrivenost | **556/556** po (županija, naziv), nakon ispravka mojibakea u nazivu županije (`ZAGREBAÈKA` → ZAGREBAČKA, `Æ` → Ć). |

Uzorak (zbroj `BROJ_BIRACA`; u zagradi Popis 2021.):

```
Grad Pag          3.056   (3.175 stanovnika)
Grad Novalja      3.665   (3.680)
Općina Bedenica   1.071   (1.266)
```

Ukupno je 3.600.345 birača, od toga 3.557.000 na adresama sa statusom "VAŽEĆA". Omjer birača i stanovnika najviši je u Obrovcu (1,57), Viru (1,42) i Okrugu (1,42), a najniži u Erveniku (0,69).

**Što omogućuje [P]:** svjež broj punoljetnih osoba s prijavljenim prebivalištem (2026.) i signal "prijavljeni, ali ne žive tu". U Viru su to vikendaši, u Obrovcu iseljeni. Dobar je i kao demonstracija API-ja, ali sadržajno skroman dodatak.

**Trud:** 2-3 h.

**Rizici:**
- Birači nisu stanovnici.
- Mojibake u nazivima.
- Blokada `GROUP BY` znači 556 poziva po izgradnji.
- Ime datoteke sadrži datum, pa se resurs vjerojatno zamjenjuje.

---

## 3. Odbačeno

| Skup (izdavatelj) | Razlog |
|---|---|
| Dječji vrtići (MZO), https://data.gov.hr/ckan/dataset/djecji-vrtici | 885 pravnih osoba (svibanj 2025.), samo adresa i poštansko "Mjesto", bez šifre JLS i osnivača. Po nazivu mjesta pripisuje se 822 od 885. Bolji je Tab-8 iz §2.5. |
| Registar proračunskih i izvanproračunskih korisnika, Tablica 2 (MF) | 3.229 subjekata (JLS i njihovi vrtići, knjižnice, škole) s OIB-om, ali bez stupca "nadležna jedinica". Korisnika nije moguće pouzdano pripisati jedinici. |
| ESIF krediti za javnu rasvjetu (HBOR) | Oko 55 jedinica, stanje 16.1.2023. Krediti su već u Bilanci. |
| Popis JLS u minski sumnjivom prostoru (MPŠR) | 58 jedinica, datoteka iz 2018. |
| Financiranje komunalnog gospodarstva (MGIPU) | 2014.-2017.; `mgipu.hr` prekida vezu (mrtav link). |
| Podaci o financiranju udruga (Ured za udruge) | 2004.-2017., zastarjelo. |
| e-Građani statistika (MPUDT) | Samo po županijama. |
| Slobodna radna mjesta (HZZ) | Samo po županijama (XML). **Nezaposlenosti po JLS na portalu nema.** |
| Kaznena djela (MUP) | Po policijskim upravama. |
| Rezultati lokalnih izbora (DIP) | ZIP samo za 2013., 2017. i 2021.; 2025. nije na portalu. Izlaznost bi bila samo kontekst. |
| Kupoprodaje nekretnina (Porezna uprava) | Samo po županijama. |
| Registar godišnjih financijskih izvještaja (FINA) | Resurs "CSV" je stranica za prijavu (HTML, 200), kao što je već bilo poznato. |
| Informacije o ugovorenim koncesijama (FINA) | Datastore sadrži HTML obrasca, kao što je već bilo poznato. |
| Kumulativna izvješća ZPPI (Povjerenik), resurs na portalu | Datastore je HTML stranice. Upotrebljiva je samo datoteka s pristupinfo.hr (§2.6). |
| Lokacije ordinacija PZZ (HZZO) | `hzzo-net.hr/hackathon/...` se ne spaja (timeout). |
| Popis mjesnih odbora u općinama (Povjerenik) | Stanje 1.7.2018. |
| Statistička izvješća REGOS | Samo nacionalni zbrojevi (prijave, dob, uplate). |
| DZS PxWeb "Zaposlenost i plaće", "Strukturne poslovne statistike" | Prošao sam cijelo stablo: nema tablica po gradovima i općinama, samo po djelatnosti. |
| Sudski registar API (izvan portala) | Specifikacija v3.0.4 nema osnivače ni članove društva (provjereno u `open_api`), pa ne daje komunalna društva po vlasniku. Broj poduzeća po `sifra_opcine` je moguć, ali traži OAuth registraciju; ključa u `secrets.txt` nema [N]. |
| Središnji registar državne imovine (MPUDT, API) | Državna imovina, ne imovina jedinica. |
| Pojedinačni proračuni, planovi nabave i registri ugovora jedinica | Svaka jedinica ima svoj format, nije ujednačeno (kao što je navedeno u zadatku). |

---

## 4. Kako sam pretraživao

1. **Cijeli katalog:** `package_search?q=*:*&rows=1000&start=0..3000`, 4 poziva, 3.969 skupova. Spremio sam naslov, organizaciju, licencu, `metadata_modified`, oznake i resurse (format, `datastore_active`, URL).
2. **Nacionalni izdavatelji:** izbacio sam organizacije `grad-*`, `opcina-*` i `*zupanij*` i pregledao sve skupove ostalih: DZS (105), MUP (114), DGU (87), MPUDT (34), Porezna uprava (19), MF (10), HZZ (4), FINA (4), MZO (5), MRRFEU (1), HBOR, APPRRR, Povjerenik za informiranje, Ured za udruge, DIP, HZZO, REGOS, HAKOM i druge.
3. **Ključne riječi** (bez dijakritika, u naslovu, opisu i oznakama, samo nacionalni izdavatelji): `opcin`, `gradov`, `jls|jlp|lokaln.*samouprav`, `komunal`, `vrtic`, `nezaposl`, `borav`, `turist`, `potpor|subvenc`, `fond|eu projekt|europsk`, `nabav`, `porez|prirez`, `2021.*2027|operacij|esif|ruraln`.
4. **DZS PxWeb:** iz skupova DZS-a slijedio sam poveznice na PxWeb i prošao stabla `Stanovništvo`, `Građevinarstvo`, `Zaposlenost i plaće`, `Strukturne poslovne statistike` i `Popis poljoprivrede 2020` (`GET /PXWeb/api/v1/hr/<baza>/...`). Tražio sam naslove s "grad"/"općin". Za svaku nađenu tablicu dohvatio sam metapodatke i jedan POST upit.
5. **Provjera:** HEAD ili GET svakog resursa (status, veličina, `Last-Modified`), za datastore `datastore_search?limit=` i `datastore_search_sql` (`COUNT`, `SUM`, `DISTINCT`). Spajanje s `data/build/units.csv` radio sam po DGU šifri, OIB-u ili (županija, naziv) u tom redoslijedu. Nazivi su bez dijakritika, bez prefiksa "Grad"/"Općina", a bez crtice tek u drugom koraku.
6. **Zamke:**
   - `package_search` s dijakritikom u `q` i dalje vraća 502; pretraživao sam lokalnu kopiju kataloga.
   - `datastore_search_sql` s `GROUP BY` portal prekida (connection reset).
   - PxWeb vraća 429 pri brzim pozivima.

Skripte su u `C:\Users\marsi\AppData\Local\Temp\claude\0ce3bc54462bc6b1\dbe8e456-a2b2-437a-9ae9-d8ca042d957a\scratchpad\portal-skripte\`:
- alati: `ck.py`, `catalog.py`, `grep_cat.py`, `show.py`, `pxtree.py`, `pxmeta.py`, `pxquery.py`, `match.py`;
- analize: `an_dohodak.py`, `an_check611.py`, `an_stope.py`, `an_stope2.py`, `an_px.py`, `an_gus.py`, `an_zppi.py`, `an_opkk.py`, `an_biraci2.py`.

Preuzeto je u `...\scratchpad\portal\`, svaki izvor u svojoj mapi. Kod u `pipeline/`, `web/` i `tests/` nije mijenjan.
