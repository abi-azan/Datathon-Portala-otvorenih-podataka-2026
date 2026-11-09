# 01 — Metode mjerenja financijskog zdravlja JLP(R)S i preporuka za Fiskalnu kartu JLS

Datum istraživanja: 2026-11-02. Svrha: odabrati metodu ocjene financijskog zdravlja za 576 jedinica (428 općina, 127 gradova + Grad Zagreb, 20 županija), 2019.–2025., na podacima MFIN-a (PR-RAS, Bilanca) i DZS-a (Popis 2011./2021.).

## Legenda oznaka pouzdanosti

| Oznaka | Značenje |
|---|---|
| **[V-n]** | Provjereno: pročitao sam primarni izvor n (ili njegov relevantni dio). |
| **[S-n]** | Samo sekundarno: sažetak pretrage, novinski članak ili reprodukcija; primarni izvor nisam otvorio. |
| **[P]** | Naša prosudba ili prijedlog, nije preuzeto iz izvora. |
| **[N]** | Nije provjereno; treba provjeriti prije korištenja. |

---

## 0. Sažetak

**Preporuka:** hibrid austrijskog **KDZ-Quickteste** [V-1] i slovačkog **INEKO "finančné zdravie"** [V-2][V-3], prilagođen hrvatskom zakonu o proračunu [V-26]:

1. Pet ocjenjivanih pokazatelja (zadržavamo strukturu vašeg nacrta), ali s **ispravljenim definicijama**: operativni prihodi **bez kapitalnih pomoći**, otplata **neto duga** (26 − 11), servis duga na **zakonskoj osnovici** iz čl. 121. Zakona o proračunu i dospjele obveze uključujući **24 D**.
2. Umjesto stepenica 1–5: **po dijelovima linearno bodovanje 0–100**, sa sidrištima preuzetima iz KDZ-a i INEKO-a (oba su dokumentirana i javna). Ukupna ocjena A–E prema **KDZ razredima bodova** (81–100 / 61–80 / 41–60 / 21–40 / ≤20) [V-1].
3. **Višegodišnje ponderiranje 4-3-2-1** (zadnja godina najteža), kao kod INEKO-a [V-2].
4. **Crvene zastavice** (signalni pristup, kao Italija/Michigan/NY) odvojene od bodova. Koriste hrvatske zakonske okidače: 20 % limit (čl. 121.), preneseni manjak (čl. 37.) i dvije uzastopne operativne godine u minusu.
5. Normativna ocjena (apsolutni pragovi) plus **relativni položaj** unutar usporedne skupine, a kao inovaciju **"statistički blizanci"** (k-NN na strukturnim, ne financijskim varijablama, po uzoru na CIPFA "nearest neighbours" [V-7][S-8]).

**Pet najvažnijih nalaza:**

1. **Kapitalne pomoći u razredu 6 iskrivljuju operativni saldo.** KDZ izričito oduzima kapitalne transfere (Bedarfszuweisungen) iz operativnog salda [V-1]. U nacrtu se (6−3)/6 "napuhuje" u godinama EU projekata. To je najvažniji ispravak.
2. **Hrvatsko fiskalno pravilo nije "servis duga / prihodi poslovanja".** Čl. 121. ograničava *ukupnu godišnju obvezu* (prosječni anuitet + jamstva + **dospjele obveze**) na 20 % prihoda prethodne godine **umanjenih za pomoći, donacije i udio poreza na dohodak za decentralizirane funkcije**. EU projekti i energetska učinkovitost su izuzeti [V-26]. Fiskalno izravnanje se za ovu svrhu **ne smatra** pomoći [V-27]. Mjerenje u nacrtu podcjenjuje opterećenje jedinica koje ovise o pomoćima.
3. **INEKO je gotovo identičan analog.** Isti izvor podataka (Ministarstvo financija), pet pokazatelja (dug, servis duga, tekući saldo, dospjele obveze, obveze >60 dana), težine 30/10/30/15/15, linearno bodovanje 0–6 i ponderi 4-3-2-1 [V-2][V-3]. To je najjače opravdanje za naš dizajn pred žirijem.
4. **Supervizirani ML za rano upozorenje nije realan.** JLS u Hrvatskoj ne mogu u stečaj [V-28], pa nema oznake "distresa". Talijanski radovi imaju ~40.000 opažanja i samo 416 pozitivnih slučajeva [V-45], a i tamo autori zadatak opisuju kao vrlo težak [S-44]. Naših 576×7 je dovoljno za indeks, percentile i krivulju ekonomije razmjera, ali ne za ML klasifikator.
5. **Uštede od spajanja su skromne i nesigurne.** Meta-analiza ne nalazi pad prosječnih troškova iznad otprilike 10.000 stanovnika [V-54]. Prisilna spajanja u Brandenburgu smanjila su administrativne rashode za oko 4 % (ukupne za oko 6 %), dobrovoljna manje i nerobusno [V-50]. Danska je pokazala nulti učinak na ukupne rashode [V-48]. Simulator treba prikazivati **raspon s donjom granicom 0**, ne "uštedu".

---

## 1. (a) Usporedba metoda

### 1.1 Ocjenjivački i nadzorni sustavi

| Sustav | Pokazatelji (sažeto) | Bodovanje / pragovi / težine | Transparentnost | Uklapanje s našim podacima |
|---|---|---|---|---|
| **KDZ-Quicktest (AT)**, "finanzwirtschaftlich" [V-1] | ÖSQ = (operativni saldo − kapitalni transferi BZ) / operativni rashodi; FSQ = (op. saldo − otplate − BZ) / (op. prihodi − BZ); EFQ = (op. + investicijski prihodi) / (op. + investicijski rashodi); VSD = (obveze − likvidna sredstva) / prosječni op. saldo; SDQ = (kamate + otplate) / porezni prihodi i pristojbe | Tablice od 25 koraka po pokazatelju. ÖSQ, FSQ i EFQ nose po 25 bodova, VSD i SDQ po 12,5, ukupno 100. Ukupno: 81–100 vrlo dobro, 61–80 dobro, 41–60 prosječno, 21–40 dovoljno, ≤20 nedovoljno. Ključni pragovi su u §1.3. | Visoka: formule i tablice objavljene, alat (Excel/Praxisplaner) komercijalan | **Vrlo dobro**: svi brojnici/nazivnici postoje u PR-RAS/Bilanci |
| **KDZ-Quicktest NEU** [V-1] | Dodaje NEQ (neto rezultat / rashodi, obračunski), NVQ (neto imovina / aktiva), SEQ (investicije / amortizacija) | 7 pokazatelja: FSQ 25, ostali po 12,5 | Visoka | Djelomično: nemamo amortizaciju i obračunski rezultat u našem izvatku [N] |
| **INEKO finančné zdravie (SK)** [V-2][V-3][V-4] | Ukupni dug / tekući prihodi prethodne god.; servis duga / tekući prihodi preth. god.; tekući saldo / tekući prihodi; dospjele obveze / tekući prihodi preth. god.; obveze >60 dana nakon dospijeća | Linearno 0–6. Dug 0 % → 6, 60 % → 3, ≥120 % → 0. Servis 0 → 6, 25 % → 3, ≥50 % → 0. Saldo ≤−10 % → 0, 5 % → 3, ≥20 % → 6. Dospjele 0 → 6, 15 % → 3, ≥30 % → 0. Obveze >60 dana: 0 → 6, a za (0; 3 %) pada s 3 na 0. **Težine 30/10/30/15/15.** Ponderi godina 4-3-2-1. Razredi: 0–1 vrlo loše … 5–6 izvrsno | Vrlo visoka: metodika javna, podaci MF SR | **Izvrsno**: isti tip podataka; nemamo samo podjelu dospjelih obveza po starosti (>60 dana) |
| **NY OSC Fiscal Stress Monitoring System (US)** [S-5][N-6] | Saldo fondova (50 b.), operativni deficiti 3 god. (10), gotovina (20), kratkoročni dug za likvidnost (10), fiksni troškovi (10) | 0 b. ako je slobodni saldo >10 % rashoda, ukupni saldo >20 %, gotovina >100 % mjesečnih rashoda, plaće <65 % prihoda, servis duga <10 %. Stres: ≥65 značajan, 55–64,9 umjeren, 45–54,9 podložan. Okolišni (ekonomski) pokazatelji ocjenjuju se zasebno | Visoka (priručnik javan, ali iza Cloudflarea) | Dobro: imamo 11 (gotovina), 9221/9222, 31, 342+54; nemamo kratkoročni dug zasebno [N] |
| **CIPFA Financial Resilience Index (UK)** [V-7] | Održivost rezervi, razina i promjena rezervi, kamate / neto rashodi, bruto vanjski dug, naknade / rashodi usluga, council tax / neto rashodi, rast iznad osnovice | **Relativan**: nema normativnih pragova ("tool takes no view on what is an acceptable level"). Usporedba sa **statističkim najbližim susjedima** ili svima istog tipa | Srednja (podaci javni, CIPFA ih ne daje) | Ideja "nearest neighbours" izravno primjenjiva; pokazatelji rezervi samo djelomično (9221/9222) |
| **Bertelsmann Kommunaler Finanzreport / Wegweiser Kommune (DE)** [S-9] | Kassenkredite (kratkoročni dug za likvidnost) p.c., Finanzierungssaldo p.c., porezi p.c., investicije, socijalni rashodi | Deskriptivno, bez kompozitne ocjene; Wegweiser je portal pokazatelja za općine od 5.000+ stanovnika | Visoka | Dobro kao kontekst; nema ocjene |
| **Brown 10-point test (US)** [V-10][S-11] | 10 omjera: prihodi p.c., udio pomoći, udio vlastitih poreza, rashodi p.c., operativni saldo / prihodi, saldo fonda / prihodi, pokriće obrtnog kapitala, dug / porezna osnovica, servis duga / prihodi, financiranost mirovina | Kvartili unutar razreda veličine: +2 / +1 / 0 / −1 po omjeru, ukupno −10 … +20 [S-11]. Maher i Nollenberger (2009) namjerno izostavljaju zbirni skor [V-10] | Visoka | Dobro (7 od 10 omjera izračunljivo); kvartilni pristup = naši percentili |
| **ICMA Financial Trend Monitoring System (US)** [N] | Desetci trendova (financijski, okolišni, organizacijski) | Bez zbirne ocjene, "warning trends" | Srednja | Kontekst; previše za 7 dana |
| **Kloha–Weissert–Kleine / Michigan (US)** [V-12][S-13] | 9 kategorija: rast stanovništva, realni rast porezne osnovice, velik pad osnovice, rashodi / osnovica, operativni deficit, prethodni deficiti, veličina salda fonda, deficiti fondova, dug / osnovica | 0/1 po pokazatelju, skala 0–10: **0–4 neutralno, 5–7 nadzor, 8–10 stres** | Visoka | Dobro za zastavice; promjena stanovništva iz popisa 2011./2021. |
| **Ohio Financial Health Indicators (US)** [S-14] | 17 pokazatelja iz financijskih izvještaja | Kritično / oprez / pozitivno. Stres ako ima ≥6 kritičnih ili ≥8 kritičnih + oprez. Mjerila iz petogodišnjih prosjeka svih gradova i županija | Srednja | Ideja: pragovi iz empirijske distribucije |
| **Rejting agencije (LRG)** [S-15][S-16][S-17] | Fitch: **payback = neto prilagođeni dug / operativni saldo** (primarni pokazatelj za "Type B"). Moody's: operativna marža, cash financing surplus, kamate / op. prihodi, dug / op. prihodi. S&P: 6 faktora, uključujući operativni saldo % op. prihoda i izravni dug % op. prihoda | Okidači u izvještajima Fitcha za pojedine izdavatelje: ~7,5×–10,5× [S-15]. Opća tablica razreda nije provjerena [N] | Niska do srednja (kriteriji djelomično iza paywalla) | Pokazatelji izračunljivi; pragovi nisu javni |
| **Italija, parametri deficitarnosti** [V-18][V-19] | P1 kruti rashodi (osoblje + dug + pokriće manjka) / tekući prihodi >48 %; P2 naplata vlastitih prihoda <22 %; P3 >0; P4 (kamate + glavnica) / tekući prihodi **>16 %**; P5 manjak na teret godine >1,2 %; P6 >1 %; P7 >0,6 % (izvanbilančni dugovi); P8 stopa naplate <47 % | **Strukturno deficitaran ako je ≥ polovica parametara deficitarna** (≥4/8). Pragovi su za općine; pokrajine i planinske zajednice imaju svoje | Vrlo visoka (pravni akt) | Dobro za ideju zastavica; P1 i P4 izračunljivi |
| **Portugal, Anuário Financeiro** [V-21] | 10 pokazatelja: likvidnost, op. rezultat, obveze / imovina, obveze p.c., pokriće rashoda, **prosječni rok plaćanja**, izvršenje salda, ukupni dug, izvršenje rashoda prema preuzetim obvezama, izravni porezi p.c. | Zbroj bodova (do ~1.900 b. za 10 pokazatelja); "zadovoljavajuće" ako ≥50 % [S-21]. Rangiranje po veličinskim razredima (veliki/srednji/mali) | Srednja (težine po pokazatelju nisu potvrđene) | Dobro; analogija s dospjelim obvezama |

### 1.2 Zakonska fiskalna pravila za lokalnu razinu (izvor kalibracije pragova)

| Zemlja | Pravilo | Status |
|---|---|---|
| **Hrvatska** | **Čl. 121. Zakona o proračunu (NN 144/21):** ukupna godišnja obveza ≤ **20 %** ostvarenih prihoda prethodne godine. U obvezu ulaze prosječni godišnji anuitet (krediti, zajmovi, vrijednosni papiri), jamstva, suglasnosti i **dospjele obveze iz zadnjeg izvještaja**. Prihodi se umanjuju za pomoći iz inozemstva i unutar općeg proračuna, donacije i dodatni udio poreza na dohodak za decentralizirane funkcije. Izuzeto: zaduživanje do prihvatljivog troška EU projekta i za energetsku učinkovitost. Kratkoročno zaduženje najviše 12 mjeseci (čl. 119.). Ako se preneseni manjak ne može podmiriti u godini, obvezan je **višegodišnji plan uravnoteženja (čl. 37.)**. Dodatna godišnja ograničenja propisuje zakon o izvršavanju proračuna (čl. 118.). | [V-26] |
| Hrvatska | Sredstva **fiskalnog izravnanja** su nenamjenska. Za pravila o zaduživanju **ne smatraju se pomoćima** (čl. 9. st. 3. Zakona o financiranju JLP(R)S). | [V-27] |
| Hrvatska | Nad JLP(R)S se **ne može provesti predstečajni ni stečajni postupak** (Stečajni zakon). Zato ne postoji pravna oznaka "bankrota". | [V-28] |
| Slovačka | Dug ≤ 60 % tekućih prihoda prethodne godine (sankcijski pojas od 50 %); servis duga ≤ 25 %. Režim ozdravljenja ako dospjele obveze prelaze 15 % prihoda ili postoji ijedna obveza neplaćena više od 60 dana (nulta tolerancija). | [V-2][V-4] |
| Češka | Dug ≤ 60 % prosjeka prihoda zadnje 4 godine. Višak se mora smanjivati najmanje 5 % godišnje, inače MF može zadržati dio poreznih prihoda. | [S-23] |
| Slovenija | Godišnja otplata ≤ 8 % ostvarenih prihoda prethodne godine (verzija iz 2008.). Novela ZFO-1E (2025.) mijenja čl. 10.b i definira "prezaduženost" kao prekoračenje limita za 5 %. Novu formulu nisam provjerio. | [S-24] |
| Estonija | Neto dug ≤ 60 % operativnih prihoda (do 100 % ovisno o sposobnosti samofinanciranja); operativni rezultat ne smije biti negativan. Izvori se ne slažu oko točne verzije. | [S-25] |
| Španjolska | Uz pozitivnu neto štednju i dug < 75 % tekućih prihoda zaduživanje je slobodno; 75–110 % traži odobrenje; negativna neto štednja ili dug > 110 % isključuje dugoročni kredit (ili traži plan sanacije). | [S-20] |
| Poljska | Čl. 243.: individualni pokazatelj duga. Servis duga u odnosu na tekuće prihode ograničen je prosjekom ranijih operativnih viškova (uz prihode od prodaje imovine od 2024.). Formula se mijenja od 2026.; nisam je provjerio. | [S-22] |

**Zaključak iz 1.2 [P]:** prag od 20 % u Hrvatskoj se poklapa s KDZ-ovom granicom "SDQ > 20 % = negativno" [V-1]. Zato sidrište "20 % = slaba ocjena" ima i zakonsko i stručno uporište.

### 1.3 Ključni detalji dvaju najbližih uzora

**KDZ-Quicktest** (Leitfaden 2.0, svibanj 2025.) [V-1]:
- Tumačenje: ÖSQ > 25 % je "vrlo pozitivno", a < 5 % "jasan znak upozorenja". FSQ < 0 znači da se tekuće poslovanje financira novim dugom. EFQ < 85 % više godina zaredom znači da treba odmah konsolidirati. VSD < 3 godine je izvrsno, > 25 godina loše. SDQ < 5 % je pozitivno, > 20 % negativno.
- Granice ocjena (ocjena 1 = najbolja), očitane iz tablica:

| Pokazatelj | Ocjena 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| ÖSQ | ≥25 % | 20–25 % | 15–20 % | 5–15 % | <5 % |
| FSQ | ≥15 % | 10–15 % | 5–10 % | 0–5 % | <0 % |
| EFQ | ≥110 % | 100–110 % | 95–100 % | 85–95 % | <85 % |
| VSD (godine) | <3 | 3–7 | 7–12 | 12–25 | ≥25 (0 bodova od 35) |
| SDQ | <5 % | 5–10 % | 10–15 % | 15–20 % | ≥20 % (0 bodova od 30 %) |

- Ako je operativni saldo ≤ 0, VSD je "praktički beskonačan" (KDZ ne dopušta negativne godine otplate). VSD se računa na **prosječnom** operativnom saldu.
- KDZ je 2025. revidirao skale za EFQ i SDQ, pa novi rezultati mogu odstupati od starijih.
- Leitfaden ne objavljuje formulu kojom se iz bodova računa "Gesamtnote" (primjer: 47,5 bodova daje ocjenu 3,16) [N].

**INEKO** [V-2][V-3][V-4]:
- Dug se boduje samo za zadnju godinu. Kod servisa duga i tekućeg salda prvo se uzme ponderirani prosjek **vrijednosti** (4-3-2-1), pa se on boduje. Kod dospjelih obveza i obveza >60 dana uzme se ponderirani prosjek **bodova**. Godine koje nedostaju preskaču se.
- Upozorenja iz same metodike: dug skriven u društvima kćerima i JPP projektima nije obuhvaćen. Podaci koje jedinice same unose ne moraju odgovarati njihovom knjigovodstvu.
- Rezultat za 2024. (gradovi): prosjek 4,26 od 6; 33 grada "izvrsno". INEKO dospjele obveze manje od 0,5 % prihoda smatra "minimalnima" [V-4].

---

## 2. (b) Preporučena metoda za Fiskalnu kartu JLS

### 2.1 Načela

1. **Normativno, ne samo relativno.** Ocjena A–E počiva na apsolutnim sidrištima (KDZ, INEKO, hrvatski zakon). Zato nije igra nultog zbroja: sve jedinice mogu biti "B", a godine se mogu uspoređivati. Relativni položaj (percentil u usporednoj skupini) prikazuje se **uz** ocjenu, kao kod Browna i CIPFA-e [P].
2. **Slijediti korake OECD/JRC priručnika** [V-42, sadržaj]: teorijski okvir → izbor pokazatelja → provjera korelacija → normalizacija → ponderiranje i agregacija → analiza nesigurnosti i osjetljivosti → razlaganje ocjene na pokazatelje.
3. **Sve ocjenjivano je omjer**, pa nema problema s inflacijom ni prelaskom na euro. Iznosi po stanovniku služe samo kao kontekst [P].

### 2.2 Pomoćne veličine

| Oznaka | Definicija (konta) | Napomena |
|---|---|---|
| **KP** (kapitalne pomoći i donacije u razredu 6) | Zbroj kapitalnih podskupina pomoći (tipično 63x2: 6312, 6322, 6332, 6342, 6362, 6382) + kapitalne donacije (6632) | [N] Točne šifre provjeriti u Računskom planu (Pravilnik o proračunskom računovodstvu i Računskom planu). Ako 4-znamenkasta konta nisu u izvatku, prikazati obje varijante i označiti godine kad 63 i 4 istodobno skoče [P]. |
| **PO** (operativni prihodi) | 6 − KP | Analogno KDZ-u, koji oduzima kapitalne transfere iz operativnog salda [V-1] |
| **OS** (operativni saldo, iznos) | PO − 3 | Razred 7 (prodaja imovine) je već izvan razreda 6, pa je jednokratni prihod od prodaje zemljišta isključen |
| **ND** (neto dug) | max(0, 26 + 25 − 11) | 25 (vrijednosni papiri) samo ako postoji [N]. KDZ i Fitch rade s neto dugom [V-1][S-15] |
| **SD** (servis duga) | 341 + 342 + 54 (+ glavnica vrijednosnih papira, ako se vodi zasebno) | [N] Provjeriti šifre 341 i otplate vrijednosnih papira. Ako se iste godine pojave velik primitak 84 i velika otplata 54, riječ je vjerojatno o refinanciranju: označiti ili isključiti [P] |
| **ZO** (zakonska osnovica, približno) | (6 [+7?]) − 63 + FI − 663 − (udio poreza na dohodak za decentralizirane funkcije, ako je prepoznatljiv), **iz prethodne godine** | FI = fiskalno izravnanje (6353 prema vašem mapiranju), vraća se jer se ne smatra pomoći [V-27]. Uključenost razreda 7 u "ukupne ostvarene prihode" [N] |
| **DO** (dospjele obveze) | 23 D + 24 D + 26 D (dospjeli dijelovi) | Nacrt nema **24 D** (dospjele obveze za nabavu nefinancijske imovine) [P] |

### 2.3 Ocjenjivani pokazatelji, sidrišta i težine

Bodovanje: **po dijelovima linearna interpolacija** između sidrišta, s rezanjem na krajevima (0–100). Sidrišta su preuzeta iz izvora, a u zagradi je trenutna logika nacrta.

| # | Pokazatelj | Formula | Sidrišta (vrijednost → bodovi) | Izvor sidrišta | Težina [P] |
|---|---|---|---|---|---|
| I1 | **Operativni saldo** (nacrt: (6−3)/6) | OS / PO | ≤ −10 % → 0; 5 % → 50; ≥ 20 % → 100 | INEKO, tekući saldo [V-2] | **20** |
| I2 | **Slobodni saldo nakon otplate** (nacrt: (6−3−54)/6) | (OS − 54) / PO | ≤ −5 % → 0; 0 % → 24; 5 % → 44; 10 % → 64; 15 % → 84; ≥ 20 % → 100 | KDZ FSQ, preračunato s 25 b. na 100 [V-1] | **20** |
| I3 | **Godine otplate neto duga** (nacrt: 26/(6−3)) | ND / ponderirani prosjek OS. ND = 0 → 0 god.; ND > 0 i OS ≤ 0 → ∞ | 0 → 100; 3 → 84; 7 → 64; 12 → 44; 25 → 24; ≥ 35 → 0 | KDZ VSD [V-1] | **15** |
| I4 | **Servis duga na zakonskoj osnovici** (nacrt: (342+54)/6) | SD / ZO(t−1) | 0 % → 100; 5 % → 84; 10 % → 64; 15 % → 44; **20 % (zakonski limit) → 24**; ≥ 30 % → 0 | KDZ SDQ [V-1] i čl. 121. [V-26] | **15** |
| I5 | **Dospjele obveze** (nacrt: (23D+26D)/3) | DO / 3 | ≤ 0,5 % → 100; 15 % → 50; ≥ 30 % → 0 | INEKO [V-2]; tolerancija 0,5 % prema INEKO-ovom "minimalnom" iznosu [V-4], primijenjena kao [P] | **30** |

**Obrazloženje težina [P]:** grupirano po dimenzijama, tekuća održivost nosi 40 (I1+I2), dug 30 (I3+I4), platna disciplina 30 (I5). KDZ daje 50 % bilancama [V-1], a INEKO 30 % saldu i 30 % dospjelim obvezama [V-2]. Dospjele obveze su izravan simptom nelikvidnosti i ulaze u hrvatski zakonski limit [V-26]. I1 i I2 su jako korelirani, pa im zajednička težina ne bi trebala prelaziti oko 40. **Težine nisu "istinite", nego izbor.** Zato je analiza osjetljivosti iz §2.9 obavezna.

**Ukupna ocjena:** zbroj ponderiranih bodova (0–100) → razred **A ≥ 80, B 60–80, C 40–60, D 20–40, E < 20**. Razredi su preuzeti iz KDZ-a (81–100 vrlo dobro … ≤20 nedovoljno) [V-1].

**Kalibracija [P]:** sidrišta su kalibrirana na austrijske i slovačke jedinice. Prije objave treba pogledati distribuciju ocjena po godinama. Ako je više od 50 % jedinica u jednom razredu, ili ako pojedini pokazatelj gotovo svima daje 100 bodova (vjerojatno I3/I4 jer mnoge hrvatske jedinice nemaju dug, [N] provjeriti), treba u dokumentaciji obrazložiti da je to stvarno stanje, a ne greška.

Skica implementacije:

```python
import numpy as np
ANCHORS = {
  "I1": ([-0.10, 0.05, 0.20], [0, 50, 100]),
  "I2": ([-0.05, 0.0, 0.05, 0.10, 0.15, 0.20], [0, 24, 44, 64, 84, 100]),
  "I3": ([0, 3, 7, 12, 25, 35], [100, 84, 64, 44, 24, 0]),        # godine; inf -> 0
  "I4": ([0, 0.05, 0.10, 0.15, 0.20, 0.30], [100, 84, 64, 44, 24, 0]),
  "I5": ([0.005, 0.15, 0.30], [100, 50, 0]),
}
WEIGHTS = {"I1": 20, "I2": 20, "I3": 15, "I4": 15, "I5": 30}
def score(ind, x):
    if ind == "I3" and np.isinf(x): return 0.0
    xs, ys = ANCHORS[ind]
    return float(np.interp(x, xs, ys))   # np.interp reže na krajevima
```

### 2.4 Višegodišnje usrednjavanje

- **Tokovi (I1, I2, I4):** ponderirani omjer zbrojeva za godine t, t−1, t−2, t−3 s ponderima **4-3-2-1**. INEKO usrednjava vrijednosti istim ponderima [V-2]. Omjer zbrojeva (Σwᵢ·brojnikᵢ / Σwᵢ·nazivnikᵢ) je stabilniji od prosjeka omjera kod malih općina [P].
- **I3:** neto dug na kraju godine t podijeljen s ponderiranim prosjekom OS. KDZ VSD je izričito na prosječnom saldu [V-1].
- **I5:** ponderirani prosjek **bodova** po godinama (4-3-2-1), kao INEKO [V-2].
- **Rub serije:** za 2019.–2021. prozor je kraći, pa se godine koje nedostaju preskaču kao kod INEKO-a [V-2]. U UI-u ocjene za 2019. i 2020. označiti kao "manje pouzdane (kraći prozor)" [P].
- U UI-u uz ocjenu prikazati i **jednogodišnje** vrijednosti, da korisnik vidi i šok i izglađeni trend [P].

### 2.5 Crvene zastavice (signalni pristup, ne ulaze u bodove)

Uzor: talijanski parametri (deficitarno ako je ≥ polovica pokazatelja loša) [V-18], Michigan 0–10 [V-12] i NY OSC [S-5].

| Zastavica | Uvjet | Uporište |
|---|---|---|
| Z1 Preneseni manjak | 9222 > 9221 i neto manjak > 5 % PO | Čl. 37. (višegodišnji plan uravnoteženja) [V-26]; prag 5 % je [P] |
| Z2 Blizu zakonskog limita | Procijenjena I4 (uz dodane DO u brojnik, kao u čl. 121.) > 20 % | [V-26] |
| Z3 Uzastopni operativni deficit | OS < 0 dvije godine zaredom | Rejting agencije se brinu kod dva uzastopna deficita ili deficita većeg od 5–10 % [V-10] |
| Z4 Rast dospjelih obveza | DO/3 raste 3 godine zaredom i > 5 % | Trend-pristup ICMA/Michigan; pragovi [P] |
| Z5 Niska gotovina | 11 < 1/12 × 3 (manje od mjesec dana operativnih rashoda) | NY OSC: gotovina / prosječni mjesečni rashodi, 0 bodova iznad 100 % [S-5] |

Prikaz: "0 zastavica / 1–2 pojačati praćenje / ≥3 strukturni rizik" [P].

### 2.6 Kontekstni pokazatelji (prikazuju se, ne ocjenjuju)

| Pokazatelj | Formula | Napomena |
|---|---|---|
| Ovisnost o pomoćima | (63 − FI)/6 i 63/6 | Brown ratio 2 [V-10] |
| Vlastiti prihodi p.c. | (61 + 64 + 65)/stanovnici | **Prekid serije 2024.:** ukinut prirez, jedinice same određuju stope poreza na dohodak (NN 114/23) [S-41] |
| Porezni kapacitet p.c. | 611/stanovnici (5-god. prosjek) | Približno logici fiskalnog izravnanja (5-godišnji prosjek poreza na dohodak p.c.) [V-27] |
| Trošak opće uprave p.c. | Funkcija 01 **bez 017 (javni dug) i 018 (transferi)**, ako je dostupno / stanovnici | Prema COFOG-u, 01 uključuje i transakcije javnog duga te transfere; inače se kamate broje dvaput [P/N] |
| Zaposleni na 1.000 st. | Z006 / stanovnici × 1000 | Svjetska banka koristi isti pokazatelj; maksimum 2018. Lovas 32,9 [V-30] |
| Investicijska stopa | 4 / (3 + 4) | |
| Samofinanciranje (EFQ) | (6 + 7)/(3 + 4) | KDZ EFQ, pragovi 85 / 100 / 110 % [V-1]; osjetljivo na vremenski raskorak EU projekata |
| Akumulirani rezultat | (9221 − 9222)/PO | |
| Razvojna skupina | Skupina I–VIII prema indeksu razvijenosti (NN 3/2024) | [S-29] |
| Promjena stanovništva | Popis 2021./2011. | Michigan: pad stanovništva je pokazatelj [V-12] |

### 2.7 Usporedne skupine i "statistički blizanci"

**Osnovne skupine (tip × veličina) [P]:**
- Tipovi: općina, grad, veliki grad (≥ 35.000 st., zakonski status [V-30, fn. 14]), županija, **Grad Zagreb (zaseban)**.
- Veličinski razredi za općine i gradove: < 2.000; 2.000–5.000; 5.000–10.000; 10.000–35.000; > 35.000. Prag 10.000 dolazi iz meta-analize [V-54], prag 35.000 iz zakona [V-30].
- Pravilo [P]: svaka ćelija ≥ 15 jedinica, inače spojiti susjedne razrede. Provjeriti na podacima.

**Statistički blizanci (inovacija) [P]:** za svaku jedinicu 10 najbližih jedinica istog tipa po standardiziranoj euklidskoj udaljenosti na **strukturnim** (egzogenim) varijablama: log(stanovnici 2021.), promjena stanovništva 2011.–2021., indeks/skupina razvijenosti, primorska ili otočna oznaka, log(površina ili gustoća) [N: izvor površine]. Financijske varijable se namjerno ne koriste, jer bi se uspoređivali "jednako loši". Uzor je CIPFA Nearest Neighbour Model, koji uspoređuje sa statistički najbližim vijećima (tipično 15) [V-7][S-8].

Prikaz: "Općina X je u 72. percentilu svojih 10 blizanaca; medijan blizanaca = …".

### 2.8 Jednokratni poremećaji

| Poremećaj | Učinak | Postupak |
|---|---|---|
| **EU projekti** | Kapitalne pomoći (63x2/638x) u razredu 6 napuhuju operativni saldo. Rashod je u 4, a prihod često u drugoj godini. Zaduživanje za predfinanciranje izuzeto je iz limita od 20 % [V-26] | KP isključen iz PO (§2.2); prozor 4-3-2-1; oznaka "EU projekt" kad je 638 > 10 % od 6 [P]; EFQ samo kao kontekst |
| **Potresi 2020.** (Zagreb, Sisačko-moslavačka) | Izvanredne pomoći i kapitalni rashodi; mogući pad prihoda | Oznaka "izvanredne okolnosti" za pogođene jedinice [P]; kapitalne pomoći su ionako isključene; prikazati baznu 2019. |
| **COVID-19 2020.** | Zajednički šok svima | Relativni položaj (percentil) to neutralizira; u grafikonu prikazati nacionalni medijan [P] |
| **Porezna reforma 2024.** | Ukidanje prireza i lokalne stope poreza na dohodak [S-41] | Napomena o prekidu serije za 611 i 61; omjeri ostaju usporedivi |
| **Refinanciranje** | Velik 54 i 84 iste godine narušava I2 i I4 | Zastavica; u I2/I4 koristiti 54 − min(54, 84) kad oba prelaze npr. 10 % PO [P] |
| **Prodaja imovine** | Jednokratni prihod u razredu 7 | Isključen iz I1/I2 po konstrukciji |
| **Inflacija 2022.–2023.** | Iznosi p.c. nisu usporedivi kroz vrijeme | Ocjene su omjeri; kontekst p.c. prikazati u stalnim cijenama ili kao omjer prema medijanu [P] |
| **Mali nazivnici** | Općine s nekoliko stotina stanovnika imaju jako volatilne omjere | Omjer zbrojeva (§2.4); oznaka "mala jedinica" ispod npr. 1.000 st. [P] |

### 2.9 Grad Zagreb i županije

- **Grad Zagreb** je istodobno grad i županija i financira decentralizirane funkcije. Zakon ga isključuje iz izračuna referentne vrijednosti za gradove kod fiskalnog izravnanja [V-27], a Svjetska banka ga u analizi zaposlenih isključuje kao outlier [V-30]. **Preporuka [P]:** dati mu normativnu ocjenu (omjeri su valjani), ali **bez usporedne skupine**. Prikazati trend i, informativno, usporedbu s četiri najveća grada uz jasnu napomenu.
- **Županije:** drukčija struktura (decentralizirane funkcije, veliki prijenosi). Ocjenjivati istim pokazateljima, ali percentil računati samo među 20 županija. Napomena da sidrišta nisu kalibrirana za regionalnu razinu [P].

### 2.10 Analiza osjetljivosti (JRC korak "uncertainty & sensitivity") [V-42 sadržaj; postupak P]

Izračunati ukupnu ocjenu u četiri scenarija težina:

| Scenarij | I1 | I2 | I3 | I4 | I5 |
|---|---|---|---|---|---|
| Osnovni | 20 | 20 | 15 | 15 | 30 |
| Jednake težine | 20 | 20 | 20 | 20 | 20 |
| "KDZ-like" | 25 | 25 | 12,5 | 12,5 | 25 |
| "INEKO-like" | 30 | 0 | 30 | 10 | 30 |

Za svaku jedinicu prikazati raspon ranga ili razreda kroz scenarije, kao oznaku "ocjena stabilna / osjetljiva na pretpostavke". Opcionalno peti scenarij su težine **"benefit of the doubt"** (DEA koja svakoj jedinici daje njoj najpovoljnije težine; R paket `Compind`) [S-43].

---

## 3. (c) Što dodati, promijeniti ili izbaciti iz nacrta

| Element nacrta | Preporuka | Razlog |
|---|---|---|
| Operativni saldo (6−3)/6 | **Promijeniti:** (6 − KP − 3)/(6 − KP) | Kapitalne pomoći napuhuju saldo; KDZ ih isključuje [V-1] |
| Slobodni saldo (6−3−54)/6 | Promijeniti isto; refinanciranje neutralizirati | Isto; KDZ FSQ [V-1] |
| Godine otplate 26/(6−3) | **Promijeniti:** neto dug (26 + 25 − 11) / prosječni OS; ∞ ako je OS ≤ 0 | KDZ VSD koristi neto i prosječni saldo [V-1]; Fitch neto prilagođeni dug [S-15] |
| Servis duga (342+54)/6 | **Promijeniti nazivnik** na zakonsku osnovicu iz prethodne godine; dodati 341 | Čl. 121. [V-26]; FI se vraća u osnovicu [V-27] |
| Dospjele (23D+26D)/3 | **Dodati 24 D**; tolerancija 0,5 % | Zakon broji sve dospjele obveze [V-26]; INEKO "minimalno" [V-4] |
| Pragovi 1–5 (stepenice) | **Zamijeniti** linearnim 0–100 sa sidrištima | Nema skokova na granici; KDZ ionako ima 25 finih koraka [V-1] |
| Jednak prosjek 5 ocjena | **Zamijeniti** težinama 20/20/15/15/30 + analiza osjetljivosti | I1 i I2 su korelirani; JRC preporučuje osjetljivost [V-42] |
| Višegodišnje usrednjavanje (nije definirano) | **Dodati** 4-3-2-1 | INEKO [V-2] |
| Akumulirani rezultat kao kontekst | **Ostaviti kao kontekst + zastavica Z1** | Zakonska posljedica (čl. 37.) [V-26] |
| Trošak uprave = 01 / stanovnici | **Promijeniti:** isključiti 017 i 018 ako postoje | COFOG 01 uključuje javni dug i transfere [P/N] |
| Usporedne skupine tip × veličina | **Zadržati + dodati** Zagreb zasebno, prag 35.000, blizance | [V-30][V-54][S-8] |
| (nema) | **Dodati** zastavice Z1–Z5 | Talijanski, NY i Michigan signalni pristup [V-18][V-12][S-5] |
| (nema) | **Dodati** napomenu o "skrivenom dugu" u komunalnim društvima | INEKO [V-2]; IJF [S-35] |
| (nema) | **Provjeriti razinu izvještaja** (proračun JLS ili konsolidirano s proračunskim korisnicima, npr. vrtićima) | Utječe na usporedivost 31 i Z006 [N] |
| Izbaciti | Ništa bitno. Ne dodavati pokazatelje koji traže podatke kojih nemamo (amortizacija, rezerviranja, porezna osnovica) | KDZ NEU traži obračunske podatke [V-1] |

---

## 4. (d) Dokazi o uštedama od spajanja i preporučeno uokvirivanje

### 4.1 Dokazi

| Reforma / studija | Metoda | Učinak | Pouzdanost |
|---|---|---|---|
| **Danska 2007.** (271 → 98 općina) — Blom-Hansen, Houlberg, Serritzlew 2014, AJPS | Kvazi-eksperiment: 239 spojenih, 32 kontrolne | "Considerable" učinci razmjera na **administrativne troškove po stanovniku**; točan postotak nisam dobio | [V-47] samo sažetak |
| Danska — Blom-Hansen i sur. 2016, APSR | DiD | **Nulti učinak** na rashode: uštede u nekim područjima poništene pogoršanjem u drugima; za većinu usluga veličina nije važna; uz to troškovi tranzicije | [V-48] sažetak |
| Danska — Houlberg 2011, SJPA | Administrativni troškovi i osoblje | Očekivane administrativne uštede "zasad nisu ostvarene". Potencijal je prije reforme bio **napuhan** u procesu legitimiranja reforme. Mjereno administrativnim osobljem, veće općine ne troše manje | [V-49] sažetak |
| **Njemačka, Brandenburg** — Blesse & Baskaran (WP 2013; RSUE 2016) | DiD, panel 1998.–2005. | Prisilna spajanja: **ukupni rashodi −6 %, administrativni −4 %, tekući −8 %** (log specifikacija). **Dobrovoljna:** manji i manje robusni učinci | [V-50] tekst WP-a |
| **Izrael 2003.** — Reingewertz 2012, JUE | DiD | Ukupni rashodi **oko −9 %**, bez pada razine usluga | [S-51] |
| **Nizozemska** 1997.–2011. — Allers & Geertsema 2016, JRS | Dinamički panel | Prema novinskom sažetku spajanje "ne donosi novac" | [S-52] rezultat nisam provjerio u radu |
| **Finska** — Moisio & Uusitalo 2013 | | Sekundarni izvori se ne slažu: nema značajnog učinka ili čak viši rashodi | [S-53] |
| **Japan** (Heisei spajanja) | Više studija | Mješovito: padaju troškovi skupština; ukupni rashodi privremeno rastu, kasnije umjeren pad | [S-57] |
| **Estonija** (spajanja prije 2017.) — Reiljan i sur. | Prije i poslije | Administrativni rashodi pali, ali i prihodi (manje državnih potpora) | [S-56] |
| Estonija 2017. | | 213 → 79 jedinica; poticaji 65 mil. EUR; ex-post procjenu uštede nisam našao | [S-56] |
| **Meta-analiza** — Gómez-Reino, Lago-Peñas, Martinez-Vazquez 2023, JRS | Meta-analiza | Konstantni do umjereno rastući prinosi; **nema pada prosječnih troškova iznad skromne veličine, često procijenjene na ~10.000 st.** | [V-54] sažetak |
| Pregled — Tavares 2018 | Pregled literature | Uštede su uglavnom ograničene na **opću upravu**; nema promjene kvalitete usluga; slabi kvaliteta lokalne demokracije | [V-30] citira |
| **Međuopćinska suradnja** (Češka, otpad) — Struk & Bakoš 2021 | Panel 2010.–2019. | Oko **−13,5 %** godišnjeg troška usluge | [V-30] citira |
| **Hrvatska** — Svjetska banka (Primorac) 2022 | Opisna analiza (PR-RAS 2018.) | "Ne postoje čvrsti kvantitativni dokazi". Broj zaposlenih ne raste proporcionalno sa stanovništvom (fiksni troškovi) | [V-30][V-31] |
| Hrvatska, NPOO | | Cilj do kraja 2026.: stvarno spajanje ≥ 20 % (111) i funkcionalno ≥ 40 % (222) JLS. **Nijedno stvarno spajanje.** Funkcionalno uglavnom kroz zajedničke vrtiće (10 gradova + 51 općina), knjižnice, komunalne redare. Isplaćeno 6,3 % planiranih poticaja 2022. i 22,3 % 2023. | [V-32][V-33] |

**Napomena:** vaš podatak "~24 % u funkcionalnom spajanju" nisam uspio potvrditi. Novi list (2024.) navodi 225 jedinica do 31. 10. 2024. [S]. Preporučam citirati točan službeni broj iz izvještaja MPUDT-a ili NPOO-a [N].

### 4.2 Što to znači za simulator spajanja [P]

1. **Ukupna ušteda ≠ administrativna ušteda.** Simulator smije procjenjivati uštedu **samo na općoj upravi** (01 bez 017/018). Danski ukupni učinak je nula [V-48], a Tavares i Svjetska banka uštede vide samo u upravi [V-30].
2. **Prikazati raspon s tri sloja:**
   - **Strukturni jaz (gornja granica):** zbroj stvarnih troškova opće uprave minus očekivani trošak za veličinu spojene jedinice, iz krivulje razmjera.
   - **Empirijski realističan raspon:** od 0 % do otprilike 10 % zbrojenog troška opće uprave. Donja granica dolazi iz Danske, Nizozemske i Finske. Gornja odgovara redu veličine iz Brandenburga (−4 % administracije kod prisilnih spajanja) i Izraela (−9 % ukupno). Za **dobrovoljna** spajanja realno donji dio raspona [V-50].
   - **Jednokratni troškovi tranzicije:** nisu kvantificirani; NPOO poticaji su zamišljeni da ih pokriju [V-31].
3. **Krivulju razmjera procijeniti ispravno:** log(01 p.c.) na log(stanovnici), unutar tipa, uz kontrolu za gustoću ili površinu, broj naselja, razvijenost i primorje. Izostavljene varijable precjenjuju potencijal (Houlberg: "napuhan" [V-49]). Jedna studija za Južnu Australiju nalazi da ekonomije razmjera nestaju kad se jedinice raslojavaju po gustoći naseljenosti [S-59]. Prikazati **predikcijski interval**, ne točku.
4. **Iznad ~10.000 stanovnika** simulator treba upozoriti da se dodatna ušteda ne očekuje [V-54].
5. **Fiskalno izravnanje izračunati po zakonskoj formuli [V-27].** Puni iznos = (referentna vrijednost − kapacitet) × stanovnici, gdje je kapacitet 5-godišnji prosjek poreza na dohodak p.c. pri najvišoj stopi, uključujući paušal od turizma. Referentna vrijednost za općine je prosjek svih općina uvećan za 50 %, za gradove prosjek svih gradova bez Zagreba. Iz te formule slijedi [P]:
   - Ako su obje jedinice ispod referentne vrijednosti, zbroj punih iznosa se ne mijenja (formula je linearna).
   - Ako je jedna iznad, kapacitet spojene jedinice raste i **izravnanje pada**.
   - Promjena statusa iz općine u grad mijenja referentnu vrijednost.
   - Isplata je udio u godišnjem iznosu iz proračuna, pa spajanje neznatno mijenja i udjele ostalih jedinica.
6. Izračunati i novi **limit od 20 %** na zbrojenoj osnovici, uz napomenu o harmonizaciji stopa poreza na dohodak nakon 2024. [S-41].
7. Prikazati **alternativu: funkcionalno spajanje / zajedničke službe** (dokaz: −13,5 % kod zajedničkog gospodarenja otpadom [V-30]) i **nefinancijsku cijenu** (manja zastupljenost i lokalna demokracija [V-30]).

**Prijedlog teksta za UI:** "Procijenjeni potencijal uštede na općoj upravi: 0 – X EUR godišnje. Gornja granica temelji se na usporedbi s jedinicama slične veličine. Studije reformi u Danskoj, Njemačkoj i Nizozemskoj pokazuju da se u praksi ostvari tek dio tog potencijala ili ništa, osobito kod dobrovoljnih spajanja."

---

## 5. (e) Izvedive inovacije za 7 dana

| Inovacija | Vrijednost za bodovanje | Napor | Rizik | Preporuka [P] |
|---|---|---|---|---|
| **Statistički blizanci** (k-NN, §2.7) | Velika (UX, "nova vrijednost") | 0,5–1 dan | Nizak; treba izvor površine [N] | **Da** |
| **Značka stabilnosti ocjene** (4 scenarija težina, §2.10) | Srednja (metodološka uvjerljivost) | 0,5 dana | Nizak | **Da** |
| **Pravila ranog upozorenja** (Z1–Z5 + strelica trenda) | Velika (relevantnost za MPUDT) | 0,5 dana | Nizak | **Da** |
| Krivulja razmjera s predikcijskim intervalom | Nužna za simulator | 0,5–1 dan | Srednji (specifikacija) | **Da** |
| Izravnanje u simulatoru po zakonskoj formuli | Velika (stručna vjerodostojnost) | 0,5–1 dan; aproksimacija iz 611 p.c. | Srednji: točan izračun MFIN-a traži podatke koje nemamo [N] | Da, kao "procjena" |
| **AI objašnjenje** (LLM pretvara izračunate brojke u kratak tekst po jedinici) | Velika za kriterij "napredne tehnologije" | 0,5–1 dan | Halucinacije → generirati unaprijed iz strukturiranih brojki i pregledati uzorak; navesti alat u dokumentaciji | Da, ako ostane vremena |
| Transparentna logistička "nowcast" vjerojatnost pada u D/E iduće godine | Srednja | 1 dan | Cirkularno (predviđa vlastiti indeks), mali broj događaja | Opcionalno, uz jasnu ogradu |
| Supervizirani ML (GBM/RF) za distres | Na papiru velika | 2+ dana | **Nema oznake distresa** [V-28]; 576×7 ≈ 4.000 opažanja, a talijanski ML ima ~40.000 opažanja i 416 pozitivnih [V-45]; drugdje ML pobjeđuje logit tek uz tisuće opažanja i resampling [V-46] | **Ne** |
| DEA/SFA učinkovitosti uprave | Akademski zanimljivo (hrvatske DEA studije postoje [S-40]) | 1–2 dana | Teško objasniti; slabi pokazatelji outputa | **Ne**; umjesto toga rezidual krivulje razmjera |

**Je li 576×7 dovoljno?** Za normativni indeks, percentile, blizance i presječnu krivulju razmjera (~556 općina i gradova po godini): **da**. Za superviziranu predikciju distresa: **ne**, jer nema oznake ni dovoljno događaja [P na temelju V-28, V-45].

---

## 6. Otvoreni rizici i provjere

1. **Mapiranje konta** (KP, 341, 25, 24 D, 663, 6353, udio poreza za decentralizirane funkcije) treba provjeriti u Računskom planu i u stvarnom izvatku [N].
2. **Razina izvještaja** (samo proračun ili konsolidirano s korisnicima) utječe na 31 i Z006 [N].
3. **Kvaliteta "dospjelih obveza":** jedinice same izvještavaju; I5 nosi najveću težinu. Provjeriti outliere ručno [P].
4. **Skriveni dug** u komunalnim društvima i ustanovama nije u bilanci JLS [V-2][S-35]. Moguće proširenje: povezati vlasništvo preko Sudskog registra (REST API na `sudreg-data.gov.hr`).
5. **Sidrišta su strana** (AT/SK). Kalibraciju na hrvatskoj distribuciji dokumentirati [P].
6. **Zakonska osnovica (ZO) je približna**: zakon koristi prosječni anuitet i jamstva, a mi stvarne isplate [V-26].
7. **Broj funkcionalno spojenih jedinica** (~24 %) nije potvrđen; izvori se razlikuju [V-32][S].
8. Učinak spajanja u Danskoj 2014. (točan postotak) i nizozemski rezultat nisam provjerio u punom tekstu [V-47][S-52].

---

## 7. (f) Izvori

1. KDZ – Zentrum für Verwaltungsforschung: *KDZ-Quicktest, Leitfaden Version 2.0* (Biwald, Hödl, Pichler), 07.05.2025. https://www.stadt-salzburg.at/fileadmin/user_upload/04013/beilage_4_kdz-quicktest_leitfaden.pdf (pročitano)
2. INEKO: *Metodika* (Hospodárenie obcí, krajov a ich organizácií). https://www.hospodarenieobci.sk/metodika (pročitano)
3. INEKO: *Čo je finančné zdravie*. https://www.hospodarenieobci.sk/financne-zdravie (pročitano)
4. INEKO: *Analýza hospodárenia miest 2025 (za rok 2024)*. https://www.hospodarenieobci.sk/files/vystupy/analyza_miest_2025.pdf (pročitano)
5. Town of Pound Ridge (NY): *NYS Comptroller's Office 2024 Fiscal Stress Report* (reprodukcija bodovanja OSC FSMS). https://www.townofpoundridge.gov/finance/nys-comptrollers-office-2024-fiscal-stress-report (pročitano; sekundarno)
6. NY Office of the State Comptroller: *Fiscal Stress Monitoring System – Interpreting the Lists*. https://www.osc.ny.gov/files/local-government/fiscal-monitoring/pdf/InterpretingLists.pdf (nije otvoreno, Cloudflare)
7. North Hertfordshire DC: *Appendix D – CIPFA Resilience Index results*. https://democracy.north-herts.gov.uk/documents/s21554/APPENDIX%20D%20-%20RESILIENCE%20INDEX.pdf (pročitano)
8. CIPFA: *Nearest Neighbour Model*. https://www.cipfa.org/services/nearest-neighbour-model ; LG Inform: *Display and comparison groups*. https://help.lginform.local.gov.uk/faqs/display-and-comparison-groups/display-and-comparison-groups (sažetak pretrage)
9. Bertelsmann Stiftung: *Kommunaler Finanzreport 2019*. https://bertelsmann-stiftung.de/fileadmin/files/BSt/Bibliothek/Doi_Publikationen/Finanzreport-2019-gesamt.pdf (sažetak pretrage)
10. Maher, C. S. & Nollenberger, K. (2009): *Revisiting Kenneth Brown's "10-Point Test"*, Government Finance Review, Oct 2009, 61–66. https://icma.org/sites/default/files/302051_GFRoct09KennethBrownUpdate.pdf (pročitano)
11. City of San Diego, Office of the City Auditor: *Fiscal Condition Highlights* (Brown bodovanje +2/+1/0/−1). https://www.sandiego.gov/sites/default/files/18-024_fiscal_condition_highlights.pdf (sažetak pretrage)
12. Michigan Senate Fiscal Agency: *Local Government Fiscal Indicator System*. https://sfa.senate.michigan.gov/Publications/Issues/LocalGovFiscalIndicatorSystem/LocalGovFiscalIndicatorSystem.pdf (pročitano djelomično)
13. Kloha, P., Weissert, C. S. & Kleine, R. (2005): *Developing and Testing a Composite Model to Predict Local Fiscal Distress*, Public Administration Review 65(3), 313–323. doi:10.1111/j.1540-6210.2005.00456.x (bibliografski zapis)
14. Pew Charitable Trusts (2017): *Ohio Seeks to Identify, Help Local Governments Headed for Distress*. https://www.pewtrusts.org/research-and-analysis/articles/2017/11/13/ohio-seeks-to-identify-help-local-governments-headed-for-distress (sažetak pretrage)
15. Fitch Ratings, izvještaji za izdavatelje (npr. Métropole de Lyon 2025.). https://www.grandlyon.com/fileadmin/user_upload/media/pdf/institution/budget/financement/20251219_notation-fitch-2025_en.pdf ; Nouvelle-Aquitaine 2022. https://nouvelle-aquitaine.fr/sites/default/files/2022-05/FitchRatings_rating_action_commentary_24052022.pdf (sažetak pretrage)
16. Moody's Local Brasil: *Regional and Local Governments Methodology*. https://moodyslocal.com.br/wp-content/uploads/2026/04/ML-BR-RLG-Methodology-EN.pdf (sažetak pretrage)
17. S&P Global Ratings (2024): *Comparative Statistics: Local and Regional Government Risk Indicators – Europe*. https://www.spglobal.com/ratings/en/research/articles/240919-comparative-statistics-local-and-regional-government-risk-indicators-europe-remains-resilient-13253197 (sažetak pretrage)
18. Ministero dell'Interno / MEF: *Decreto 4 agosto 2023, Allegato A – Parametri obiettivi 2022–2024*. https://dait.interno.gov.it/documenti/decreto-fl-04-08-2023-all-a.pdf ; decreto: https://dait.interno.gov.it/documenti/decreto-fl-04-08-2023.pdf (pročitano)
19. Decreto 28 dicembre 2018 (parametri 2019–2021, pravilo "almeno la metà"). https://www.moltocomuni.it/wp-content/uploads/decreto-del-28-dicembre-2018.pdf (pročitano djelomično)
20. Ministerio de Hacienda (ES): *Nota informativa sobre el régimen de endeudamiento 2024*. https://www.hacienda.gob.es/SGFAL/DGCFEL/Endeudamiento/Nota-Informativa-Endeudamiento-2024.pdf (sažetak pretrage)
21. e-konomista.pt: *Municípios com maior eficiência financeira* (popis 10 pokazatelja Anuária). https://www.e-konomista.pt/municipios-com-maior-eficiencia-financeira/ (pročitano) ; RTP: https://www.rtp.pt/noticias/economia/cerca-de-80-dos-municipios-com-eficiencia-financeira-pouco-saudavel-segundo-anuario_n1182664 (sažetak)
22. Standardy Prawa: art. 243 ustawy o finansach publicznych. https://standardyprawa.pl/akt/464/art/53095 (sažetak pretrage)
23. Ministerstvo financí ČR (2024): informacija o pravilu rozpočtové odpovědnosti. https://mfcr.cz/assets/attachments/2024-08-14_Info-106-99-MF-25524-2024-74.pdf (sažetak pretrage)
24. ZFO-1, čl. 10.b. https://www.racunovodstvo.net/zakonodaja/zfo/10b-clen ; ZFO-1E (Uradni list RS 2025). https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/2025-01-0586 (sažetak pretrage)
25. ERR News: *Tallinn could borrow €60 million…* https://news.err.ee/1609317111/tallinn-could-borrow-60-million-for-supplementary-budget ; CoR: *Estonia – Fiscal Powers*. https://portal.cor.europa.eu/divisionpowers/Pages/Estonia-Fiscal-Powers.aspx (sažetak pretrage)
26. *Zakon o proračunu* (NN 144/21 i izmjene), čl. 37., 57., 118.–124. https://www.zakon.hr/z/283/zakon-o-proracunu (pročitano)
27. *Zakon o financiranju jedinica lokalne i područne (regionalne) samouprave* (NN 127/17, 138/20, 151/22, 114/23), čl. 5., 8.–10. https://www.zakon.hr/z/411/zakon-o-financiranju-jedinica-lokalne-i-podru%C4%8Dne-%28regionalne%29-samouprave (pročitano)
28. *Stečajni zakon* (NN 71/15, 104/17, 36/22), odredba o predstečajnom i stečajnom dužniku. https://www.zakon.hr/z/160/Ste%C4%8Dajni-zakon (pročitano)
29. *Odluka o razvrstavanju jedinica lokalne i područne (regionalne) samouprave prema stupnju razvijenosti* (NN 3/2024). https://narodne-novine.nn.hr/clanci/sluzbeni/2024_01_3_60.html (sažetak pretrage)
30. World Bank (2022): *Municipal Mergers and Associations: International Experience and Reform Options for Croatia*. https://documents1.worldbank.org/curated/en/099005011212295606/pdf/P1752590b183650780bda60574556b25029.pdf (pročitano djelomično)
31. Svjetska banka (2022): *Spajanje i povezivanje općina: Međunarodna iskustva i mogućnosti reforme za Hrvatsku* (autor M. Primorac i sur.). https://documents1.worldbank.org/curated/en/099061423145030508/pdf/P1752590b0e14f05f0b6b20c4f8357171bf.pdf (pročitano djelomično)
32. Informator: *Rezultati dobrovoljnog spajanja općina i gradova*. https://informator.hr/strucni-clanci/rezultati-dobrovoljnog-spajanja-opcina-i-gradova (pročitano djelomično)
33. Novi list: *"Papir trpi sve, ne i praksa": Ideja dobrovoljnog spajanja općina i gradova doživjela je fijasko*. https://www.novilist.hr/novosti/papir-trpi-sve-ne-i-praksa-ideja-dobrovoljnog-spajanja-opcina-i-gradova-dozivjela-je-fijasko/ (pročitano)
34. IJF: *Osvrt 134 – objava za medije* (Bronić, Ott, Prijaković, Stanić). https://www.ijf.hr/files/file/press-materijal/Osvrt_134_objava-za-medije.docx ; IJF pregled proračuna 2021.–2022. https://repozitorij.ijf.hr/islandora/object/ijf:904/datastream/FILE0/view (sažetak pretrage)
35. IJF Newsletter 120 (zaduživanje preko trgovačkih društava i ustanova). https://www.ijf.hr/upload/files/file/newsletter/120.pdf (sažetak pretrage)
36. Bajo, A. & Bronić, M. (2007): *Assessments of the Effectiveness of the Croatian Fiscal Equalisation Model*, Financial Theory and Practice. https://ideas.repec.org/a/ipf/finteo/v30y2007i1p1-26.html (bibliografski)
37. Erjavec, N., Jakšić, S. & Mačkić, V. (2017), odrednice proračunskih ishoda JLP(R)S 2012.–2014. https://hrcak.srce.hr/hr/181677 (sažetak pretrage)
38. Rašić Bakarić, I., Šimović, H. & Vizek, M., ekonomske odrednice općina. https://hrcak.srce.hr/en/131536 (sažetak pretrage)
39. Jurlina Alibegović, D. & Slijepčević, S. (2013): *Can Local Governments in Croatia Cope with more Responsibilities?*, Lex localis. https://www.bib.irb.hr/633425 (sažetak pretrage)
40. Rabar, D. & Grbin, A., window DEA učinkovitost. https://hrcak.srce.hr/hr/clanak/330642 ; Hunjet, Neralić & Wendell (2015), CEJOR. https://econpapers.repec.org/article/sprcejnor/v_3a23_3ay_3a2015_3ai_3a3_3ap_3a675-686.htm (sažetak pretrage)
41. Crowe Hrvatska: *Sve što trebate znati o novom krugu porezne reforme za 2024.* https://www.crowe.com/hr/news/sve-sto-trebate-znati-o-novom-krugu-porezne-reforme-za-2024 (sažetak pretrage)
42. OECD/JRC (2008): *Handbook on Constructing Composite Indicators: Methodology and User Guide*. https://knowledge4policy.ec.europa.eu/sites/default/files/jrc47008_handbook_final.pdf ; https://publications.jrc.ec.europa.eu/repository/handle/JRC47008 (bibliografski zapis i sadržaj)
43. R paket *Compind* (Benefit-of-the-Doubt). https://cran.r-universe.dev/Compind/doc/manual.html (sažetak pretrage)
44. Antulov-Fantulin, N., Lagravinese, R. & Resce, G. (2021): *Predicting bankruptcy of local government: A machine learning approach*, JEBO 183, 681–699. https://www.research-collection.ethz.ch/entities/publication/f2ca7193-a3e7-4475-afa8-a2a14fdd6e55 (sažetak pretrage)
45. Piermarini, D., Sudoso, A. M. & Piccialli, V. (2023): *Predicting municipalities in financial distress: a machine learning approach enhanced by domain expertise*, arXiv:2302.05780. https://arxiv.org/abs/2302.05780 (pročitano djelomično)
46. Chen, C., Ren, C., Zha, Y. & Zhao, Y. (2025): *Can Machine Learning Algorithms Better Help Predict Fiscal Stress in Local Governments?* (Municipal Finance Conference). https://www.brookings.edu/wp-content/uploads/2025/07/2c_Can-Machine-Learning-Algorithms-Better-Help-Predict-Fiscal-Stress-in-Local-Governments.pdf (pročitano djelomično)
47. Blom-Hansen, J., Houlberg, K. & Serritzlew, S. (2014): *Size, Democracy, and the Economic Costs of Running the Political System*, AJPS 58(4), 790–803. https://ideas.repec.org/a/wly/amposc/v58y2014i4p790-803.html (sažetak)
48. Blom-Hansen, J., Houlberg, K., Serritzlew, S. & Treisman, D. (2016): *Jurisdiction Size and Local Government Policy Expenditure*, APSR 110(4), 812–831. https://ideas.repec.org/a/cup/apsrev/v110y2016i04p812-831_00.html (sažetak)
49. Houlberg, K. (2011): *Administrative economies of scale in local government in Denmark*, Scandinavian Journal of Public Administration. https://publicera.kb.se/sjpa/article/view/16195 (sažetak)
50. Blesse, S. & Baskaran, T. (2013/2016): *Do municipal mergers reduce costs? Evidence from a German federal state*, CEGE DP 176; RSUE 59, 54–74. https://wwwuser.gwdguser.de/~cege/Diskussionspapiere/DP176.pdf ; https://ideas.repec.org/p/zbw/cegedp/176r.html (pročitano djelomično)
51. Reingewertz, Y. (2012): *Do municipal amalgamations work? Evidence from municipalities in Israel*, JUE 72(2–3), 240–251. https://ideas.repec.org/a/eee/juecon/v72y2012i2p240-251.html (sažetak pretrage)
52. Allers, M. & Geertsema, J. B. (2016): *The effects of local government amalgamation on public spending, taxation, and service levels*, JRS 56, 659–682; WP: https://ideas.repec.org/p/gro/rugsom/14019-eef.html ; novinski sažetak: https://www.binnenlandsbestuur.nl/bestuur-en-organisatie/burgerparticipatie/bezuinigen-door-gemeentelijke-herindeling-is-drijfzand (sažetak pretrage)
53. Moisio, A. & Uusitalo, R. (2013): *The impact of municipal mergers on local public expenditures in Finland*, Public Finance and Management 13(3). https://pfm.spaef.org/article/1440/The-impact-of-municipal-mergers-on-local-public-expenditures-in-Finland (sažetak pretrage)
54. Gómez-Reino, J. L., Lago-Peñas, S. & Martinez-Vazquez, J. (2023): *Evidence on economies of scale in local public service provision: A meta-analysis*, Journal of Regional Science 63(4), 793–819. https://ideas.repec.org/a/bla/jregsc/v63y2023i4p793-819.html (sažetak)
55. Tavares, A. F. (2018): *Municipal amalgamations and their effects: a literature review*, Miscellanea Geographica 22(1), 5–15. https://ideas.repec.org/a/vrs/mgrsod/v22y2018i1p5-15n7.html (preko izvora 30)
56. Reiljan, Jaansoo & Ülper: *The impact of amalgamation on the financial sustainability of municipalities in Estonia*, Riigikogu Toimetised 29. https://rito.riigikogu.ee/en/previous-issues/no-29/the-impact-of-amalgamation-on-the-financial-sustainability-of-municipalities-in-estonia/ ; ERR: https://news.err.ee/638877/minister-estonia-s-administrative-reform-complete (sažetak pretrage)
57. *Evaluation of the fiscal effect on municipal mergers: Quasi-experimental evidence from Japanese municipal data*, RSUE 66 (2017). https://ideas.repec.org/a/eee/regeco/v66y2017icp132-149.html (sažetak pretrage)
58. Struk, M. & Bakoš, E. (2021), međuopćinska suradnja u gospodarenju otpadom (Južna Moravska). Citirano u izvoru 30 (fusnota 19).
59. University of New England, studija o ekonomijama razmjera u Južnoj Australiji po gustoći naseljenosti. https://rune.une.edu.au/web/handle/1959.11/26540 (sažetak pretrage; pripisivanje nalaza ovom zapisu nesigurno)
