# 13 Prediktori gospodarskog razvoja JLS: postoje li i vrijedi li ih graditi (5.11.2026., noć)

Oznake: **[V]** provjereno (uživo, u primarnom izvoru ili izračunom na našim podacima), **[P]** procjena ili zaključak, **[N]** nije nađeno.

Sve skripte i preuzete datoteke su u scratchpadu, ne u repozitoriju (popis u §8.3). Računalo se nad kopijom `data/build/` od 5.11. u 0:25, prije noćnog online builda.

## 1. Sažetak i preporuka

**Preporuka: ODBACITI prognozu razvoja kao novu funkciju.** Ne gradimo karticu "Izgledi" ni oznaku "jedinica u padu". Razlozi:

1. **Razvoj je vrlo postojan, pa je predviđanje uglavnom "bit će kao i dosad".** Indeks razvijenosti 2018. i 2024. imaju Spearmanovu korelaciju 0,965. Dvije trećine jedinica (325 od 556) ostale su u istoj skupini razvijenosti. [V]
2. **Model sa svih 36 prediktora ne nadmašuje naivni model tamo gdje bi bio zanimljiv.** Kod rasta dohotka 2022.-2025. naivni model ("siromašniji rastu brže") ima R² izvan uzorka 0,31, a pun model 0,27. Kod pada fiskalne ocjene pun model ima AUC 0,69. To znači da su od 5 jedinica koje bi označio kao rizične, 3 lažna uzbuna. [V]
3. **Jedino gdje model jasno pomaže je broj stanovnika** (R² 0,47 → 0,69). Dobitak dolazi od dvije stvari koje već prikazujemo: neto migracije i turizma. Turistička mjesta rastu doseljavanjem (Novalja +18 %), a ostala se prazne. [V] Nema tu ničeg što karta već ne pokazuje.
4. **Komunikacijski rizik je velik, a dobitak u bodovima malen.** Prognoza "Bogdanovci će izgubiti stanovnike" za konkretnu općinu traži obrazloženje i intervale. Do zamrzavanja u subotu u 20 h to ne stignemo pošteno napraviti. [P]

**Što bi ipak vrijedilo, malo i bez prognoze (izborno, oko 4 h, samo ako ostane vremena u četvrtak):** redak "Razvojni put: indeks razvijenosti 2018. → 2024." na pregledu jedinice, iz dva službena PDF-a MRRFEU. To je činjenica, ne prognoza. Paketi činjenica za AI se ne mijenjaju (§6).

**Što svakako napisati:** jednu rečenicu u dokumentaciji ("Daljnji razvoj") i u metodologiji: "Ne prognoziramo razvoj. Provjerili smo: razvoj je postojan, a fiskalni pokazatelji ga ne predviđaju bolje od prošlog trenda." To je pošten i provjeren zaključak, a žiri cijeni kad tim zna zašto nešto nije napravio. [P]

---

## 2. Ciljna varijabla: što je "razvoj"

| Kandidat | Pokrivenost | Godine | Slabosti | Ocjena |
|---|---|---|---|---|
| **Promjena indeksa razvijenosti** (MRRFEU) | 556/556 u izdanjima 2013., 2018. i 2024. [V] | 2018.: podaci 2014.-2016.; 2024.: podaci 2020.-2022. [V] | Samo PDF. Izdanja svakih 5-6 godina, pa imamo jednu promjenu (2018. → 2024.). Metoda i ljestvica se mijenjaju: Civljane (171 stanovnik) skaču s 37,8 na 85,0 bodova, ali ostaju u I. skupini. To je šum male jedinice, ne razvoj. | dobra za opis, ne za prognozu |
| **Rast dohotka po stanovniku 2022.-2025.** (Porezna uprava) | 556/556 [V] | 4 godine, 2022. u kunama (preračunato 7,5345) [V] | Samo 3 godine promjene. Porezna reforma 2023./2024. (ukidanje prireza, veći osobni odbitak) mijenja neto. Zato sam koristio **dohodak prije poreza** (bruto − doprinosi). Medijan rasta je 58 % nominalno [V], pa razlike među jedinicama čine mali dio. | srednja |
| **Promjena broja stanovnika 31.12.2021. → 31.12.2025.** (DZS procjene) | 556/556 [V] | Niz 2011.-2025. iz XLSX-a "Gradovi i općine u statistici" [V] | Procjena, ne popis. Od 2021. temelji se na Popisu 2021., a do 2020. na Popisu 2011. (lom u nizu). Strani radnici ulaze kroz migraciju. 63 % jedinica gubi stanovnike, medijan −2,3 % [V]. | najbolja |
| **Promjena fiskalne ocjene 2021. → 2025.** (naš `results.parquet`) | 556/556 [V] | Bodovi 2021. su prozor 2019.-2021., bodovi 2025. prozor 2023.-2025., dakle bez preklapanja [V] | To nije gospodarski razvoj, nego zdravlje proračuna. Jako se vraća prema prosjeku: Ervenik je 2021. imao 46 bodova, a 2025. 99. 123 jedinice pale su za ocjenu, 159 ih je porasle [V]. | korisna za "rano upozorenje" |

Primjer: **Pag** je 2021. imao 3.156 stanovnika, 2025. 3.358 (+6,4 %). Dohodak prije poreza po stanovniku rastao je 55 % (log 0,437). Ocjena je s 4 porasla na 5, a skupina razvijenosti pala sa 7 na 6. Tri cilja govore tri različite priče o istom gradu. [V]

---

## 3. Prediktori

Prediktori su mjereni **do 2021.** (iznimke su označene), a ishodi su 2021./2022. → 2025.

| Prediktor | Izvor | Godine | Licenca | Pristup | Status |
|---|---|---|---|---|---|
| Broj stanovnika, gustoća, dobna struktura (0-14, 65+) | DZS Popis 2021. (WFS) | 2021. | otvorena | API (WFS), već u buildu | [V] |
| Trend stanovništva 2011.-2021. i 2016.-2020., prirodni prirast i neto migracija 2016.-2021. | DZS "Gradovi i općine u statistici" | 2011.-2025. | `open-license` | datoteka XLSX, već u buildu (samo 2025.); PxWeb ima 2011.-2024. | [V] |
| Indeks razvijenosti 2024. i 6 sastavnica (dohodak, izvorni prihodi, nezaposlenost, kretanje stanovništva, starenje, obrazovanost) | MRRFEU | podaci 2020.-2022. | nije navedena | PDF, u buildu samo indeks i skupina | [V] |
| Indeks razvijenosti 2018. i 6 sastavnica | MRRFEU, PDF za JLS (1,2 MB, 9 str.) | podaci 2014.-2016. | nije navedena | PDF; `pypdf` čita svih 556 redaka, spojeno 556/556 | [V] |
| Indeks razvijenosti 2013. | MRRFEU, PDF | podaci 2010.-2012. | nije navedena | PDF (pomoćni agent: odgovara, 12 str.); nisam parsirao | [V] dostupnost |
| Nezaposlenost po JLS | HZZ "Statistika on-line" | 2004.-2026. | - | OLAP sučelje ima samo dimenziju **županija**. Po JLS postoji samo kao sastavnica indeksa razvijenosti (prosjek 3 godine) | [N] po JLS |
| Novi poslovni subjekti po sjedištu | Sudski registar API v3.0.4 | trenutno + povijest | uvjeti pri registraciji | REST, OpenAPI odgovara (HTTP 200), svi podaci traže OAuth2 registraciju. **Nisam registrirao račun.** | [V] da postoji, [N] podaci |
| Obrti | Obrtni registar (pretrazivac-obrta.gov.hr) | - | - | samo pretraživač, bez skupnog preuzimanja; na portalu samo Zagreb | [N] po JLS |
| Obrtnici kao zamjena: broj osoba s dohotkom od obrta | Porezna uprava (već u buildu) | 2022.-2025. | otvorena | datoteka, već u buildu | [V] |
| EU projekti OPKK 2014.-2020. (ESIF po korisniku) | MRRFEU, portal | stanje 31.5.2023. | `open-license` | XLSX 3,9 MB; 331 JLS s barem jednom operacijom | [V] |
| EU sredstva u proračunu (konto 638), kapitalni rashodi (4), investicijska stopa, vlastiti prihodi, dug, trošak uprave, udio pomoći | MF PR-RAS i Bilanca (već u buildu) | 2019.-2021. (prosjek) | nije navedena | datoteka | [V] |
| Fiskalna ocjena 2021. | naš izračun | 2019.-2021. | - | - | [V] |
| Turizam (noćenja po stanovniku), građevinske dozvole | DZS PxWeb (već u buildu) | 2021. (prva godina u buildu; 2021. je još pod COVID-om) | otvorena | API | [V] |
| Prometna dostupnost | - | - | - | Nema otvorenog skupa po JLS (vrijeme putovanja). Zamjena: zračna udaljenost od Zagreba i od najbližeg od 4 velika grada, iz koordinata u šifrarniku | [N] skup, [V] zamjena |
| Otok, obalna županija | naš `geo.py` | - | - | već u buildu | [V] |
| Otvorenost podataka (CKAN), revizije DUR-a | portal, revizija.hr | **mjereno 2026.** ili mješovito | - | već u buildu | **Nisu korišteni**: mjereni su nakon ishoda, pa bi "predviđali" unatrag |

---

## 4. Literatura (ukratko)

Pomoćni agent je pretražio izvore. [V] znači da je stranicu ili PDF otvorio, [S] samo sažetak iz pretrage.

**Što predviđa lokalni rast**

1. **Glaeser, Scheinkman i Shleifer (1995)**, gradovi u SAD-u 1960.-1990. Rast dohotka i stanovništva bio je veći gdje je početna obrazovanost bila veća, a manji gdje su bili veća nezaposlenost i udio industrije. Javna potrošnja (osim kanalizacije) nije bila povezana s rastom. [V]
2. **Gennaioli i sur. (2013)**, 1.569 regija u 110 zemalja. Ljudski kapital je "od presudne važnosti" za razlike u razvijenosti regija. [V]
3. **Abreu, de Groot i Florax (2005)**, meta-analiza oko 600 procjena konvergencije. "Legendarnih 2 % godišnje" nije konstanta. Početna razina je uvijek prva kontrola u modelu rasta. [V]
4. **Khachiyan i sur. (2022)**, satelitske snimke SAD-a. Razinu dohotka i stanovništva predviđaju s R² 0,85-0,91, a promjenu kroz desetljeće samo s 0,32-0,46. **Razina se lako predviđa, rast teško.** To je točno ono što vidimo i mi. [V]

**Rano upozorenje za fiskalne poteškoće općina**

5. **Antulov-Fantulin, Lagravinese i Resce (2021)**, 7.795 talijanskih općina 2009.-2016., ishod je stečaj općine (*dissesto*). Strojno učenje predviđa izvan uzorka dobro. Zemljopisno područje je važnije od mnogih financijskih pokazatelja, a od financijskih najviše govore manjak i dug. [V, sažetak]
6. **Piermarini, Sudoso i Piccialli (2023)**, Italija, 39.520 opažanja i samo 416 slučajeva poteškoća. Logistička regresija radi jednako dobro kao XGBoost. Hvata sve slučajeve, ali je preciznost oko 14 %: na 1 pravu uzbunu dolazi 6 lažnih. Dio "lažnih" ipak padne u poteškoće unutar 4 godine. [V, preprint]
7. **Chen, Ren, Zha i Zhao (2025)**, 994 gradova i općina u državi New York, ishod je manjak veći od 3 %. AUC: logistička regresija 0,64, slučajne šume 0,84. Najjači prediktor je prošlogodišnji manjak. [V, prezentacija, nije recenzirano]
8. **Sustavi bodovanja, ne prognoze:** NY Comptroller Fiscal Stress Monitoring System [S], Michigan (Kloha, Weissert i Kleine 2005; sami autori kažu da sustav bolje *definira* poteškoće nego što ih *predviđa*) [S], austrijski KDZ Quicktest (5 omjera, 0-100 bodova, ocjene 1-5) [V] i slovački INEKO (dug, servis duga, tekući saldo, dospjele obveze; 0-6) [V]. Nijedan ne objavljuje točnost predviđanja. Naša ocjena je u istoj obitelji.

**Hrvatska**

9. **Marcelić (2015)**, *Revija za socijalnu politiku* 22(3), i **Perišić i Wagner (2015)**, *Financijska teorija i praksa* 39(2). Kritike indeksa razvijenosti: indeks nagrađuje proračunske prihode i kretanje stanovništva (tipično za obalu) više nego ljudski razvoj. Ima multikolinearnost i stršeće vrijednosti, pa autori predlažu intervale umjesto točke. [S] / [V]
10. **IJF i EIZ:** Bajo i Bronić (2007), *FTP* 31(1): kriteriji izravnanja nisu uzimali u obzir fiskalni kapacitet [S]. **Rad EIZ-a ili IJF-a koji predviđa razvoj po JLS iz otvorenih podataka nisam našao.** [N]

Pouka iz literature: (a) razina se predviđa, promjena slabo; (b) obrazovanost i početna razina su najpostojaniji prediktori; (c) sustavi ranog upozorenja imaju AUC oko 0,65-0,85 i nisku preciznost; (d) službeni sustavi (NY, KDZ, INEKO) boduju stanje i ne tvrde da prognoziraju.

---

## 5. Empirijska provjera

### 5.1 Metoda [V]

- **Uzorak:** 556 gradova i općina (bez županija).
- **Ciljevi:** `Y_stan` (promjena stanovnika 2021. → 2025.), `Y_dohodak` (log rast dohotka prije poreza po stanovniku 2022. → 2025., stanovnici iz procjene iste godine), `Y_bodovi` (bodovi 2025. − bodovi 2021.).
- **Binarne inačice:** najgorih 20 % po stanovništvu ili dohotku, te pad ocjene (22 % jedinica).
- **Modeli po cilju**, zapisani prije prvog pokretanja:
  - N1 naivni: prošli trend stanovništva; razina dohotka 2022. uz kratki trend; bodovi 2021.;
  - N2 samo indeks razvijenosti;
  - M1 ridge regresija sa svih 36 prediktora;
  - M2 gradient boosting sa svih 36;
  - za binarne: logistička regresija N1, N2 i L2 logistička sa svih 36.
- **Unakrsna provjera:**
  - 5 dijelova × 10 ponavljanja (nasumično);
  - **izostavi jednu županiju** (21 skupina). Ta je strože, jer susjedne općine nalikuju jedna drugoj, pa nasumična podjela precjenjuje točnost.
- Mjere su R² i AUC na predviđanjima izvan uzorka.
- **Broj modela:**
  - 21 specifikacija unaprijed (R4);
  - 13 dodano nakon prvih rezultata, kad je stigao PDF indeksa 2018. (R6, R7), označeno u skriptama;
  - ukupno 34. p-vrijednosti nisam računao.

### 5.2 Rezultati: regresija (R² izvan uzorka) [V]

| Cilj | N1 naivni | N2 samo indeks | M1 ridge (36) | M2 boosting (36) |
|---|---|---|---|---|
| Stanovništvo 2021.-2025. | 0,47 / 0,45 | 0,48 / 0,46 | **0,69 / 0,66** | 0,68 / 0,67 |
| Dohodak 2022.-2025. | **0,31 / 0,30** | 0,16 / 0,16 | 0,27 / 0,22 | 0,24 / 0,22 |
| Fiskalni bodovi 2021.-2025. | 0,29 / 0,28 | 0,06 / 0,06 | **0,32 / 0,32** | 0,28 / 0,25 |

Prvi broj: 5 × 10 nasumično, drugi: izostavljena županija. Raspršenje između ponavljanja je 0,003-0,02.

### 5.3 Rezultati: rano upozorenje (AUC izvan uzorka) [V]

| Ishod | N1 naivni | N2 samo indeks | M1 logit (36) | Preciznost u gornjih 20 % rizika (M1) |
|---|---|---|---|---|
| Najgorih 20 % po stanovništvu | 0,90 | 0,90 | 0,90 | 70 % |
| Najgorih 20 % po dohotku | **0,83** | 0,72 | 0,76 | 47 % |
| Pad ocjene 2021. → 2025. | 0,60 | 0,66 | **0,69** | 37 % (osnovna stopa 22 %) |

AUC 0,5 je bacanje novčića, a 1,0 savršeno.

- Kod stanovništva pun model ne dodaje ništa naivnom (0,90 = 0,90).
- Kod dohotka je lošiji od naivnog.
- Kod pada ocjene je najbolji, ali slab: 63 % označenih su lažne uzbune.

### 5.4 Odakle dolazi dobitak kod stanovništva [V]

| Model | R² (nasumično / po županijama) |
|---|---|
| D1 prošli trend (2016.-2020., 2011.-2021.) | 0,47 / 0,45 |
| D2 + neto migracija i prirodni prirast 2016.-2021. | 0,59 / 0,59 |
| D3 + noćenja po stanovniku 2021. | 0,66 / 0,66 |
| svih 36 (M1) | 0,69 / 0,66 |

- Tri varijable (migracija, prirast, turizam) daju gotovo sve.
- Raspodjela po turizmu, medijan promjene 2021.-2025.:
  - jedinice s malo turizma: −4,8 % (prirodno −3,0 %, migracija −1,7 %);
  - jedinice s puno turizma: **+4,3 %** (prirodno −2,5 %, migracija **+6,8 %**).
- Primjeri:
  - Novalja je imala ravan trend 2016.-2020. (−0,6 %), a 2021.-2025. +18 %;
  - Bogdanovci (bez turizma) 1.551 → 1.427, −8 %.
- Mali uzorci su bučniji. Za jedinice ispod 2.000 stanovnika (37 % jedinica) R² je 0,51, a iznad 2.000 je 0,77.

### 5.5 Pomažu li fiskalni pokazatelji (ulaganja, EU novac, dug)? [V]

Ridge, prvo naivni model, pa naivni uz 9 fiskalnih varijabli (investicijska stopa, udio EU, kapitalni rashodi i konto 638 po stanovniku, OPKK po stanovniku, vlastiti prihodi, neto dug, trošak uprave, udio pomoći):

| Cilj | naivni | + fiskalni blok | samo fiskalni blok |
|---|---|---|---|
| Stanovništvo | 0,47 | 0,61 | 0,45 |
| Dohodak | 0,31 | 0,31 | 0,14 |
| Fiskalni bodovi | 0,29 | 0,31 | 0,03 |

- Kod dohotka fiskalni pokazatelji ne dodaju ništa.
- Kod stanovništva pomažu, ali kao **zamjena za bogatstvo i turizam**, ne kao uzrok. Vlastiti prihodi su visoki u turističkim mjestima, a udio pomoći u siromašnima.
- Investicijska stopa i udio EU sredstava su čak **negativno** povezani s rastom stanovništva (Spearman −0,26 i −0,22). Siromašne općine dobivaju više pomoći za ulaganja.
- EU projekti OPKK nisu povezani ni s čim (|ρ| ≤ 0,06).
- **Iz naših podataka ne smijemo reći "ulaganja vode razvoju".** [V] za korelacije, [P] za tumačenje.

### 5.6 Test kroz vrijeme (pravi "out-of-time") [V]

- **Model:** naučen na razdoblju A (dohodak iz indeksa 2018. → 2024., dakle 2014.-2016. → 2020.-2022.), sa 6 sastavnica indeksa 2018. kao prediktorima.
- **Primjena:** na razdoblje B (2022. → 2025.), sa sastavnicama indeksa 2024.
- **Rezultati:**
  - u razdoblju A objašnjava 67 % (unutar uzorka);
  - u razdoblju B korelacija s ishodom je 0,38, dakle r² 0,14;
  - samo razina dohotka daje isto (0,38).
- Svih 6 sastavnica ne dodaje ništa razini: jedino što se prenosi kroz vrijeme je "siromašniji rastu brže".
- Prošli trend dohotka (A) korelira s rastom u B samo 0,30, a sam objašnjava 3 % (R² 0,03).

### 5.7 Zaključak provjere [P]

- **Stanovništvo:** predvidljivo, ali iz prošlog trenda, migracije i turizma. To već prikazujemo kao kontekst.
- **Dohodak:** jedini stabilan signal je konvergencija. Pun model se prenauči.
- **Fiskalna ocjena:** vraća se prema prosjeku; rano upozorenje ima AUC 0,69. To je ispod talijanskih i njujorških rezultata (0,84-0,86 sa slučajnim šumama na 10 godina podataka), a mi imamo 7 godina i jedno "razdoblje" ishoda.
- Nijedan rezultat nije dovoljno jak da bi opravdao prognozu za imenovanu općinu.

---

## 6. Prijedlog za proizvod

### 6.1 Što NE raditi

- **Kartica "Izgledi" s prognozom stanovništva, dohotka ili ocjene:** odbaciti (razlozi u §1, brojke u §5).
- **Rano upozorenje "rizik pada ocjene":** odbaciti. S AUC 0,69 i 63 % lažnih uzbuna to bi bila nepoštena oznaka.
- U AI tekst se ništa ne dodaje, pa se **paketi činjenica ne mijenjaju** i rok petak 17 h nije ugrožen.

### 6.2 Izborno: "Razvojni put" (samo ako ostane vremena u četvrtak)

Redak na pregledu jedinice, u postojećem bloku konteksta: "Indeks razvijenosti: 2018. **93,0** (II. skupina) → 2024. **93,4** (II. skupina)" (Bogdanovci). Uz to bilješka da je metoda ista (6 pokazatelja) i da su podaci 2014.-2016. i 2020.-2022.

- **Što korisnik dobiva:**
  - načelnik vidi je li se jedinica pomaknula u odnosu na državu;
  - novinar dobiva usporedivu činjenicu;
  - ministarstvo dobiva provjeru postojanosti svog indeksa.
- **Bodovi:** malo. "Povezivanje izvora" je već na 5 (doc 10). Drugo izdanje istog izvora ne mijenja ocjenu [P]. Inovativnost i utjecaj se ne mijenjaju.
- **Datoteke** (kad bi se radilo):
  - `pipeline/units.py` ili novi `pipeline/razvoj.py`: dohvat PDF-a kroz `sources.py` (provenance) i parsiranje s `pypdf`. Regex iz `r5_ir2018.py` daje 556/556.
  - `pipeline/kontekst.py`: polja `indeks_razvijenosti_2018`, `razvojna_skupina_2018`.
  - `pipeline/openapi.py`: shema.
  - `tests/test_api.py` i test za 556/556.
  - `web/` redak u bloku konteksta.
  - `docs/`: popis izvora.
- **Trošak:** oko 4 h (parser i provenance 1,5 h, API i testovi 1 h, sučelje 1 h, dokumentacija 0,5 h). [P]
- **Preporučeni prioritet: nizak.** Ako četvrtak ima važnije popravke iz doc 10 (karta na mobitelu, prijelazi), oni idu prvi.

### 6.3 Što svakako (15 min)

- U dokumentaciju za predaju, odjeljak "Daljnji razvoj": "Prognozu razvoja smo testirali (doc 13). Razvoj je postojan, pa prognoza malo dodaje. Kad DZS i MRRFEU objave nove podatke (npr. indeks iduće izdanje, HZZ po JLS), model se može ponovno provjeriti."
- U videu, ako ima mjesta: jedna rečenica "testirali smo i odbacili prognozu, jer ne bi bila poštena". [P]

---

## 7. Rizici

**Etički i komunikacijski**

- Oznaka "jedinica u padu" za Civljane (144 stanovnika 2025.) ili Bogdanovce je stigma koja može djelovati kao samoispunjavajuće proročanstvo: manje ulagača, više iseljavanja. [P]
- Model ne zna razlog: Novalja raste zbog turizma i stranih radnika, a pad u Banovini dio je posljedica potresa 2020. [P]
- Literatura (§4, br. 6) pokazuje da i dobri modeli imaju 6 lažnih uzbuna na 1 pravu.

**Statistički**

- Imamo jedno razdoblje ishoda (2021./22. → 2025.). Ne znamo vrijedi li isti model za 2025. → 2029.
- Dohodak 2022. ulazi i u prediktor i u nazivnik ishoda. Šum u njemu stvara lažnu konvergenciju (dio R² 0,31). Uz razinu iz neovisnog izvora (indeks) R² pada na 0,13. [V]
- Male jedinice su bučne: Civljane imaju indeks 37,8 → 85,0 bez stvarne promjene.
- 556 jedinica i 36 prediktora: ridge je dobro regulariziran, ali boosting već pokazuje prenaučenost (lošiji od ridgea kod dohotka i bodova).
- Prostorna sličnost: rezultati po županijama su do 0,05 lošiji od nasumičnih, pa nasumična podjela malo precjenjuje točnost. [V]
- Procjene DZS-a nisu popis. Lom 2020./2021. (prijelaz s Popisa 2011. na Popis 2021.) ulazi u trend 2011.-2021.

**Vremenski**

- Zamrzavanje je u subotu u 20 h, a paketi činjenica za AI moraju biti gotovi do petka u 17 h.
- Prognoza bi tražila i objašnjenje u sučelju, i intervale, i provjeru u testovima. To je realno 8-12 h. [P]
- Izborni "Razvojni put" (4 h) ne dira pakete.

---

## 8. Izvori

### 8.1 Podaci [V]

| Skup | Izdavatelj | Poveznica |
|---|---|---|
| Gradovi i općine u statistici (XLSX, Tab-2. i Tab-3., 2011.-2025.) | DZS | https://podaci.dzs.hr/media/bz5hplcj/gradovi-u-statistici.xlsx |
| Vrijednosti indeksa razvijenosti i pokazatelja, JLS, 2018. (PDF) | MRRFEU | https://razvoj.gov.hr/UserDocsImages//O%20ministarstvu/Regionalni%20razvoj/indeks%20razvijenosti//Vrijednosti%20indeksa%20razvijenosti%20i%20pokazatelja%20za%20izra%C4%8Dun%20indeksa%20razvijenosti_jedinice%20lokalne%20samouprave.pdf (HTTP 200, 1.198.920 B) |
| Indeks razvijenosti 2013., JLS (PDF) | MRRFEU | https://razvoj.gov.hr/UserDocsImages//O%20ministarstvu/Regionalni%20razvoj/indeks%20razvijenosti/Dosada%C5%A1nji/2013//Vrijednosti%20indeksa%20razvijenosti%20na%20lokalnoj%20razini%202013..pdf (provjerio pomoćni agent) |
| Indeks razvijenosti 2024. (PDF) | MRRFEU | https://razvoj.gov.hr/UserDocsImages/O%20ministarstvu/Regionalni%20razvoj/indeks%20razvijenosti/Vrijednosti%20indeksa%20razvijenosti%20i%20pokazatelja%20za%20izrac%CC%8Cun%20indeksa%20razvijenosti.pdf (HTTP 200, 316.625 B). Pazi: u nazivu je rastavljeno "c" + kvačica (`c%CC%8C`); isti URL sa složenim `%C4%8D` vraća 404 [V] |
| Popis operacija OPKK 2014.-2020. (stanje 31.5.2023.) | MRRFEU, portal | https://data.gov.hr/ckan/dataset/popis-operacija-financiranih-u-okviru-programa-konkurentnost-i-kohezija-2014-2020 |
| Statistika on-line (nezaposlenost samo po županijama) | HZZ | https://statistika.hzz.hr/Statistika.aspx?tipIzvjestaja=1 |
| Sudski registar API (OpenAPI, OAuth2) | MPUDT | https://sudreg-data.gov.hr/api/javni/dokumentacija/open_api |
| Pretraživač obrta (bez skupnog preuzimanja) | MINGO | https://pretrazivac-obrta.gov.hr/ |
| Već u buildu: MF PR-RAS i Bilanca, Porezna uprava (dohodak), DZS PxWeb, Popis 2021. | | vidi `data/raw/sources.json` |

CKAN pretrage `obrt`, `nezaposlenost`, `hzz`, `poduzetnick`, `dostupnost` (5.11.) nisu dale nijedan nacionalni skup po JLS. [V]

### 8.2 Literatura

1. Glaeser, E., Scheinkman, J., Shleifer, A. (1995). Economic Growth in a Cross-Section of Cities. *Journal of Monetary Economics* 36: 117-144. https://econpapers.repec.org/RePEc:nbr:nberwo:5013
2. Gennaioli, N., La Porta, R., Lopez-de-Silanes, F., Shleifer, A. (2013). Human Capital and Regional Development. *QJE* 128(1): 105-164. https://www.nber.org/papers/w17158
3. Abreu, M., de Groot, H., Florax, R. (2005). A meta-analysis of β-convergence: the legendary 2%. *Journal of Economic Surveys* 19(3): 389-420. https://econpapers.repec.org/RePEc:bla:jecsur:v:19:y:2005:i:3:p:389-420
4. Khachiyan, A. i sur. (2022). Using Neural Networks to Predict Microspatial Economic Growth. *AER: Insights* 4(4): 491-506. https://ideas.repec.org/p/nbr/nberwo/29569.html
5. Antulov-Fantulin, N., Lagravinese, R., Resce, G. (2021). Predicting bankruptcy of local government: A machine learning approach. *JEBO* 183: 681-699. https://doi.org/10.1016/j.jebo.2021.01.014
6. Piermarini, C., Sudoso, A., Piccialli, V. (2023). Predicting municipalities in financial distress: a machine learning approach enhanced by domain expertise. arXiv:2302.05780. https://arxiv.org/abs/2302.05780
7. Chen, Ren, Zha, Zhao (2025). Can Machine Learning Algorithms Better Help Predict Fiscal Stress in Local Governments? Brookings Municipal Finance Conference. https://www.brookings.edu/wp-content/uploads/2025/07/2c_Can-Machine-Learning-Algorithms-Better-Help-Predict-Fiscal-Stress-in-Local-Governments.pdf
8. NY State Comptroller, Fiscal Stress Monitoring System Manual (2022). https://www.osc.ny.gov/files/local-government/fiscal-monitoring/pdf/system-manual.pdf ; Kloha, P., Weissert, C., Kleine, R. (2005). *Public Administration Review* 65(3): 313-323; KDZ-Quicktest Leitfaden v2.0: https://www.stadt-salzburg.at/fileadmin/user_upload/04013/beilage_4_kdz-quicktest_leitfaden.pdf ; INEKO 2025: https://www.hospodarenieobci.sk/files/vystupy/analyza_miest_2025.pdf
9. Marcelić, S. (2015). Kritička analiza hrvatskog indeksa razvijenosti. *Revija za socijalnu politiku* 22(3): 309-333. https://doi.org/10.3935/rsp.v22i3.1237 ; Perišić, A., Wagner, V. (2015). Development index: analysis of the basic instrument of Croatian regional policy. *Financijska teorija i praksa* 39(2): 205-236.
10. Bajo, A., Bronić, M. (2007). *Financijska teorija i praksa* 31(1). https://hrcak.srce.hr/file/18859

### 8.3 Skripte i datoteke (scratchpad, ne commitaju se)

Mapa: `C:\Users\marsi\AppData\Local\Temp\claude\0ce3bc54462bc6b1\8198ca19-6a8e-4a31-aada-d817ed1a2e2f\scratchpad\R\`

- `r1_dzs_niz.py`: DZS XLSX → niz 2011.-2025. po JLS (koristi parser iz `pipeline/dzs_xlsx.py`, samo čitanje)
- `r2_opkk.py`: popis operacija OPKK
- `r3_skup.py`: tablica 556 × 51 (prediktori i ishodi) → `data/skup.parquet`
- `r4_modeli.py`: 21 unaprijed zapisana specifikacija → `out_r4.txt`, `out_regresija.csv`, `out_klasifikacija.csv`, `out_spearman.csv`
- `r5_ir2018.py`: PDF indeksa 2018. → `data/ir2018.csv` (556/556)
- `r6_vrijeme.py`: postojanost indeksa, test kroz vrijeme, raščlamba stanovništva → `out_r6.txt`
- `r7_fiskalni_blok.py`: doprinos fiskalnih varijabli → `out_r7.txt`
- Preuzeto u `raw/`: `opkk/`, `razvoj2018/`, `ckan/`, `hzz/`; kopije iz repoa u `raw/dzs/`, `raw/porezna/`, `raw/razvoj2024/`
