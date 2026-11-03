# Fiskalna karta JLS: plan projekta (v2, 2.11.2026.)

Datathon Portala otvorenih podataka 2026, izazov C (Gospodarstvo i učinkovito upravljanje). Predaja je **9.11.2026. (ponedjeljak)**; ciljamo slanje do 12 h.

Ovaj plan nadograđuje v1, koji je tim potvrdio 29.10. Temelji se na validaciji podataka i na četiri istraživanja u `docs/research/`:

| Dokument | Sadržaj |
|---|---|
| `00-validacija-podataka.md` | Provjera podataka i pretpostavki (vlastiti izračun) |
| `01-metode-financijskog-zdravlja.md` | Metode mjerenja i preporučena metodologija, 59 izvora |
| `02-postojeca-rjesenja-i-funkcije.md` | Postojeća rješenja, prioriteti funkcija, UX načela, video |
| `03-tehnologija-i-licence.md` | Pravila, stack, licence, LLM, arhitektura, procjena napora |
| `04-podaci-granice-i-varijable.md` | Granice, strukturne varijable, URL-ovi, popis skupova podataka |

---

## 0. Što se promijenilo u odnosu na v1

1. **Ocjena:** umjesto stepenica 1-5 i običnog prosjeka koristi se klizna ljestvica 0-100 s pragovima preuzetima iz austrijskog KDZ-a i slovačkog INEKO-a, uz pondere i analizu osjetljivosti.
2. **Kapitalne pomoći izlaze iz tekućih prihoda.** Inače operativni saldo napuhuju EU projekti. Validacija je pokazala da bi bez toga 70% jedinica dobilo najbolju ocjenu.
3. **Višegodišnji prozor:** godine se ponderiraju 4-3-2-1 (kao INEKO), jer se ocjena za jednu godinu mijenja kod 40-62% jedinica.
4. **Smjer ocjene je kao u školi: 5 je najbolje**, uvijek uz opisnu riječ.
5. **Crvene zastavice** prema Zakonu o proračunu odvojene su od ocjene.
6. **Statistički blizanci:** svaka jedinica se uspoređuje s 10 strukturno najsličnijih jedinica, uz osnovne skupine po veličini.
7. **Simulator** procjenjuje uštede samo na općoj upravi, kao raspon s tri sloja, uz procjenu promjene fiskalnog izravnanja po zakonskoj formuli. Ukupna ušteda se ne obećava.
8. **Odustajemo od modela strojnog učenja za ranu uzbunu.** Jedinice u Hrvatskoj ne mogu u stečaj, pa nema oznake na kojoj bi se model učio. Umjesto toga koristimo pravila (zastavice) i blizance.
9. **Granice i stanovništvo dolaze iz DZS-ova INSPIRE WFS servisa** (pravi API): 556 poligona i Popis 2021. Rezervni izvor je DGU ATOM paket pod Otvorenom dozvolom.
10. **Dospjele obveze postoje za sve godine 2019.-2025.** (ispravak 2.11. navečer, ETL v1). U Bilanci 2019.-2024. stupci se zovu samo `dio 23`, a "dospjele"/"nedospjele" piše u drugom retku zaglavlja; validacija je to previdjela. I5 zato ulazi u cijeli povijesni niz.

---

## 1. Cilj, korisnici, poruka

**Problem:** 576 jedinica lokalne i područne samouprave, reforma spajanja bez ijednog stvarnog spajanja (cilj NPOO-a bio je 20% stvarno i 40% funkcionalno spojenih) i financijski podaci zakopani u Excel tablicama Ministarstva financija s 1.157 redaka po jedinici. U Hrvatskoj **ne postoji** javna ocjena financijskog zdravlja svih jedinica ni simulator spajanja (potvrđeno istraživanjem 02).

**Poruka:** "Svjedodžba za svaku općinu i alat koji pokazuje što bi spajanje sa susjedima značilo u brojkama."

| Korisnik | Što dobiva |
|---|---|
| MPUDT i Ministarstvo financija | Podlogu za reformu, ranu uzbunu (zastavice), otvoreni API i DCAT katalog za data.gov.hr |
| Načelnici, vijećnici, pročelnici | Svjedodžbu, usporedbu sa sličnima, simulator, ugradivu karticu |
| Novinari, građani, istraživači | Kartu, objašnjenja običnim jezikom, preuzimanje podataka |

**Napomena u aplikaciji:** ocjenjuje se **financijska održivost**, a ne kvaliteta upravljanja. (Rečenica "Ocjena nije službena" maknuta je 4.11., jer se podrazumijeva.)

---

## 2. Podaci

Cijeli popis skupova podataka u formatu za predaju je u `04` §6.

| Izvor | Sadržaj | Pristup | Uloga |
|---|---|---|---|
| Ministarstvo financija, PR-RAS + RAS-funkcijski 2019.-2025. (razina 22) | Prihodi, rashodi, funkcije, broj zaposlenih | XLSX/ZIP s mfin.gov.hr (uvjetni GET s ETag-om) | Jezgra |
| Ministarstvo financija, Bilanca 2019.-2025. | OIB, RKP, dug, novac, dospjele obveze (sve godine), akumulirani rezultat | XLSX | Jezgra, ključ OIB |
| DZS, INSPIRE WFS (transformiraj.nipp.hr) | 556 poligona i Popis 2021. po jedinici | **OGC WFS API, GeoJSON** | Karta, stanovništvo, susjedstvo |
| DGU, Upravne jedinice INSPIRE (ATOM) | 556 JLS, 21 županija, naselja; Otvorena dozvola | ZIP/GML | Rezerva, broj naselja, otoci |
| data.gov.hr (CKAN API) | DZS Popis 2021. i 2011., Porezna uprava stope 2026., MPUDT popis JLS | **CKAN API** | Stanovništvo, kontekst, vrsta jedinice |
| DZS, PxWeb API | Turizam (noćenja, kreveti), službena površina | **API** | Statistički blizanci |
| razvoj.gov.hr i NN 3/2024 | Indeks razvijenosti i skupine I-VIII | PDF (parsiran, 556/556) | Skupine, kontekst |
| Ministarstvo financija, fiskalno izravnanje 2018.-2027. | Kapacitet, iznosi po jedinici | XLSX | Simulator (izravnanje) |
| NN 13/2026, NN 24/2019 | Decentralizirane funkcije, brdsko-planinska područja | Narodne novine | Oznake usporedivosti |
| Državni ured za reviziju (revizija.hr) | Izvješća o financijskim revizijama jedinica: mišljenje (bezuvjetno, uvjetno, nepovoljno, suzdržano) i poveznica na PDF | HTML popis po godini (`/izvjesca/10?godinaID=…&page=N`) + tekst PDF-a | Sloj vjerodostojnosti uz ocjenu (SHOULD, odluka 3.11.) |

**Ključevi:** OIB je primarni ključ, uz RKP (Ministarstvo financija) i peteroznamenkasti službeni kod jedinice (DGU i DZS, isti kod je i u Sudskom registru). Objavljujemo **šifrarnik OIB ↔ RKP ↔ kod ↔ naziv ↔ županija** kao zaseban interoperabilni rezultat. Spajanje po nazivu je testirano za svih 576 jedinica, uz 3 ručna aliasa.

**Licence:** Otvorena dozvola RH s izjavom o izvoru i označenim izmjenama. Za podatke Ministarstva financija licenca nije navedena. Rizik i ublažavanje su u §9.

---

## 3. Metodologija (v2)

Detalji i izvori su u `01` §2. Pondere i pragove kalibriramo jednom, prije pregledavanja rang-liste. Nakon toga se ne diraju bez zapisa u ovaj dokument.

### 3.1 Pomoćne veličine

| Oznaka | Definicija |
|---|---|
| KP | Kapitalne pomoći i donacije u razredu 6: 6312, 6322, 6324, 6332, 6342, 6352, 6362, 6382, 6632 (konta potvrđena u podacima) |
| PO | Tekući (operativni) prihodi = 6 − KP |
| OS | Operativni saldo = PO − 3 |
| ND | Neto dug = max(0, 26 + 25 − 11) |
| SD | Servis duga = 341 + 342 + 54 (refinanciranje se neutralizira kad je 84 velik u istoj godini) |
| ZO | Zakonska osnovica (približno, čl. 121.): prihodi prethodne godine − 63 + fiskalno izravnanje − 663 |
| DO | Dospjele obveze = 23 D + 24 D + 26 D (sve godine), uz pravilo 1 ispod |

**Pravilo 1, kredit iskazan kao cijeli dospio** (odluka 3.11., `research/05`). 26 D se ne ubraja u DO kad vrijede oba uvjeta:
- stanje kredita (26) je veće od 10.000 €, a 26 D je barem 90% od 26;
- otplata glavnice (54) u godini t je barem 3% stanja kredita na kraju godine t−1. Novi kredit (početno stanje 0) uvjet zadovoljava. Za 2019., kad nema prethodne godine, uzima se stanje na kraju godine t.

Jedinica tada dobiva oznaku kvalitete `kredit_iskazan_kao_dospio`, a profil prikazuje i iskazani i ispravljeni DO. Ako se kredit ne otplaćuje (Povljana), 26 D ostaje u DO. Za 2025. pravilo pogađa 26 jedinica, a ranijih godina 21-67.

### 3.2 Ocjenjivani pokazatelji

Bodovi se računaju linearnom interpolacijom između pragova, na ljestvici 0-100.

| # | Pokazatelj | Formula | Pragovi (vrijednost → bodovi) | Ponder |
|---|---|---|---|---|
| I1 | Operativni saldo | OS / PO | ≤ −10% → 0; 5% → 50; ≥ 20% → 100 | 20 |
| I2 | Slobodni saldo | (OS − 54) / PO | ≤ −5% → 0; 0% → 24; 5% → 44; 10% → 64; 15% → 84; ≥ 20% → 100 | 20 |
| I3 | Godine otplate neto duga | ND / ponderirani OS (∞ ako je OS ≤ 0 uz dug) | 0 → 100; 3 → 84; 7 → 64; 12 → 44; 25 → 24; ≥ 35 → 0 | 15 |
| I4 | Servis duga | SD / ZO(t−1) | 0% → 100; 5% → 84; 10% → 64; 15% → 44; **20% → 24**; ≥ 30% → 0 | 15 |
| I5 | Dospjele obveze | DO / 3 | ≤ 0,5% → 100; 15% → 50; ≥ 30% → 0 | 30 |

- **Prozor:** I1, I2 i I4 računaju se kao omjer ponderiranih zbrojeva za godine t..t−3 (ponderi 4-3-2-1). I3 je stanje na kraju godine t prema ponderiranom OS-u. I5 je jednogodišnji (stanje na kraju godine t prema rashodima poslovanja te godine). Na početku niza prozor je kraći (2019. ima jednu godinu); broj godina u prozoru se prikazuje.
- **Ukupno:** ponderirani zbroj 0-100 pretvara se u ocjenu: ≥ 80 → **5 "vrlo stabilno"**, 60-80 → **4 "stabilno"**, 40-60 → **3 "umjereno"**, 20-40 → **2 "pod pritiskom"**, < 20 → **1 "ozbiljan pritisak"**.
- **Pravilo 2, gornja granica zbog dospjelih obveza** (odluka 3.11.). Ako je I5 ≥ 30%, bodovi se ograničavaju na 39,9, pa je ocjena najviše 2 "pod pritiskom". Isto vrijedi u sva četiri scenarija pondera.
  - Razlog: na 30% S5 već daje 0, ali ostali pokazatelji mogu donijeti do 70 bodova. Bez pravila je 12 jedinica s DO ≥ 30% dobilo ocjenu 4.
  - Ograničavaju se i bodovi, ne samo ocjena, kako bi se ocjena, rang i percentil slagali. Neograničeni bodovi čuvaju se u `bodovi_bez_ogranicenja` i prikazuju u razradi s napomenom.
  - Za 2025. pravilo spušta 16 jedinica na ocjenu 2.
  - Raspodjela 2025. s oba pravila (5/4/3/2/1): 306/149/68/43/10.
- **Povijesni niz (2019.-2024.)** računa se istom metodom, sa svih pet pokazatelja. U grafikonima se uz to prikazuju i jednogodišnje vrijednosti.
- **Osjetljivost:** ocjena se računa u četiri scenarija pondera (osnovni, jednaki, sličan KDZ-u, sličan INEKO-u). Jedinica dobiva značku "ocjena stabilna" ili "ocjena osjetljiva na pretpostavke".
- **Kalibracija:** ako je više od 50% jedinica u jednom razredu, ili ako neki pokazatelj gotovo svima daje 100, to se obrazlaže kao stvarno stanje (npr. mnoge općine nemaju dug). Pragovi se ne krivotvore.

### 3.3 Crvene zastavice (ne ulaze u bodove)

| Zastavica | Uvjet | Uporište |
|---|---|---|
| Z1 Preneseni manjak | Neto manjak (9222 − 9221) > 5% PO | Čl. 37. Zakona o proračunu |
| Z2 Blizu zakonskog limita | (SD + DO) / ZO > 20% | Čl. 121. |
| Z3 Uzastopni operativni deficit | OS < 0 dvije godine zaredom | Praksa rejting agencija |
| Z4 Malo gotovine | Novac (11) < mjesečni rashodi poslovanja | NY OSC |
| Z5 Vladin kriterij od 10% (ako je donesen) | Manjak bez EU sredstava > 10% prihoda bez EU sredstava | Nacrt zaključka Ministarstva financija od 16.4.2026., status treba provjeriti |

Prikaz: "bez zastavica", "1-2: pojačano praćenje", "3 i više: strukturni rizik".

### 3.4 Kontekst (prikazuje se, ne ocjenjuje)

- **Ovisnost o pomoćima:** udio tekućih pomoći (bez fiskalnog izravnanja) i udio ukupnih pomoći.
- **Vlastiti prihodi i porezni kapacitet po stanovniku:** od 2024. postoji prekid serije zbog ukidanja prireza.
- **Trošak opće uprave po stanovniku:** funkcija 01 bez 017 i 018. Djelatnici u upravi na 1.000 stanovnika.
- **Investicijska stopa, samofinanciranje, akumulirani rezultat.**
- **Struktura jedinice:** indeks i skupina razvijenosti, promjena stanovništva 2011.-2021., otok/obala, brdsko-planinsko područje, decentralizirane funkcije.

### 3.5 Usporedne skupine i statistički blizanci

- **Skupine:** općina, grad, veliki grad (35.000+ stanovnika), županija, Grad Zagreb (zaseban). Razredi veličine: do 2.000, 2.000-5.000, 5.000-10.000, 10.000-35.000, 35.000+ stanovnika. Svaka skupina mora imati barem 15 jedinica.
- **Blizanci:** za svaku jedinicu traži se 10 najbližih jedinica iste vrste prema strukturnim varijablama:
  - log broja stanovnika i promjena 2011.-2021.,
  - indeks razvijenosti,
  - log površine ili gustoće naseljenosti,
  - broj naselja,
  - turizam po stanovniku,
  - otok/obala.

  Financijske varijable se namjerno ne koriste. Prikaz: "u 72. percentilu među svojih 10 blizanaca".
- **Rang** se prikazuje samo unutar skupine i uvijek s nazivnikom (npr. #12/84).

### 3.6 Posebni slučajevi

- **Županije:** isti pokazatelji, percentil samo među 20 županija, uz napomenu da pragovi nisu kalibrirani za regionalnu razinu.
- **Grad Zagreb:** normativna ocjena bez usporedne skupine.
- **Oznake na profilu:** EU projekt (638 > 10% od 6), potresi 2020. (Zagreb, Sisačko-moslavačka), mala jedinica (manje od 1.000 stanovnika), refinanciranje, nedostaju podaci.

### 3.7 Provjere točnosti (u testovima)

1. Zbroj jedinica jednak je zbirnim tablicama Ministarstva financija za razrede 6 i 3. Funkcije se provjeravaju po jedinici, jer je zbirna tablica Ministarstva za 2025. nepotpuna.
2. Zbroj stanovnika jednak je 3.871.833.
3. Za svaku jedinicu zbroj funkcija (R1) jednak je 3 + 4 − 367 (tolerancija 1%). Funkcijska klasifikacija ne broji prijenose vlastitim proračunskim korisnicima (367).
4. Ručna provjera pet jedinica prema njihovim godišnjim izvještajima i usporedba s IJF-ovim tablicama.
5. Pregled 10 najviših i 10 najnižih ocjena po skupini.

---

## 4. Simulator spajanja

1. **Odabir:** 2-4 jedinice koje se međusobno dodiruju i pripadaju istoj županiji. Susjedstvo se računa iz poligona (Queen, `pipeline/geo.py`): 1.360 parova, od kojih se 9 dodiruje samo u točki. Otoci se ne dodaju ručno nego jednim pravilom: unutar svake županije kopnene komponente spajaju se vezom preko mora između dviju najbližih jedinica, od najkraće udaljenosti prema duljoj, dok županija ne postane povezana. Tako nastaje 17 veza. To su redom mostovi i trajektni pravci (Krk-Kraljevica 0,4 km, Vir-Privlaka 0,4 km, Slivno-Ston 2,1 km, Dubrovnik-Mljet 5,7 km, Korčula-Lastovo 11,1 km). U sučelju se označavaju kao "veza preko mora".
2. **Zbirni profil (činjenice):** tokovi, stanja i stanovnici se zbrajaju, a ocjena i zastavice ponovno računaju. Prikazuje se usporedba prije i poslije.
3. **Ušteda samo na općoj upravi (01 bez 017 i 018), u tri sloja:**
   - **Strukturni jaz (gornja granica):** stvarni zbirni trošak umanjen za očekivani trošak za veličinu spojene jedinice. Očekivani trošak dolazi iz krivulje razmjera: log-log regresija unutar vrste, uz kontrolu površine, naselja, razvijenosti i obale, s predikcijskim intervalom.
   - **Realističan raspon:** 0% do oko 10% zbirnog troška uprave (Danska i Nizozemska ≈ 0; Brandenburg −4% uprave kod prisilnih spajanja; Izrael −9% ukupno). Za dobrovoljna spajanja vrijedi donji dio raspona.
   - **Troškovi tranzicije:** navode se, ali se ne kvantificiraju.
4. **Fiskalno izravnanje po zakonskoj formuli** (procjena): kapacitet je petogodišnji prosjek poreza na dohodak po stanovniku; referentna vrijednost ovisi o vrsti jedinice. Simulator pokazuje kad spajanje smanjuje izravnanje.
5. **Upozorenja:** iznad oko 10.000 stanovnika dodatna ušteda se ne očekuje. Alternativa je funkcionalno spajanje ili zajedničke službe. Postoji i nefinancijska cijena (zastupljenost).
6. **Uporište u našim podacima** (validacija §7): elasticitet troška uprave po stanovniku je −0,41 unutar općina; medijan je 390 €/stanovniku ispod 1.000 stanovnika i 196 € za 2.500-5.000; jedinice ispod 2.500 stanovnika imaju strukturni jaz od oko 41 mil. € godišnje (gornja granica).
7. **Tekst u sučelju:** "Procijenjeni potencijal uštede na općoj upravi: 0 – X € godišnje. Gornja granica temelji se na usporedbi sa sličnim jedinicama; u praksi se ostvari tek dio, osobito kod dobrovoljnih spajanja."

---

## 5. Inovacija i AI

| Element | Zašto je novo ili vrijedno | Status |
|---|---|---|
| Prva javna ocjena svih 576 jedinica s otvorenom metodologijom i kodom | Ne postoji u Hrvatskoj (IJF ocjenjuje transparentnost, ne financije) | MUST |
| Prvi hrvatski simulator spajanja s ocjenom prije i poslije | Moldavski AmalgaSim ima samo transfere | MUST |
| **Karta reforme** (max-p regionalizacija, `spopt`, BSD-3) | Algoritam unutar svake županije spaja susjedne jedinice dok svaka ne dosegne prag stanovnika (2.500 / 5.000 / 10.000). Klizač mijenja prag, a karta animirano prelazi s 556 na N jedinica. Uz kartu: broj jedinica, stanovnici kojih se tiče, raspon uštede na upravi, ocjene prije i poslije, promjena izravnanja. Klik na spojenu jedinicu otvara njezinu svjedodžbu. Računa se unaprijed u Pythonu, istom funkcijom spajanja kao simulator. Prikazuje se kao scenarij, ne kao prijedlog granica. | MUST |
| **AI objašnjenje uz provjeru brojki** | Python računa sve brojke, a model samo piše tekst oko njih. Provjera zahtijeva da svaki broj u tekstu postoji u ulaznim podacima. Ako ne prođe, tekst se generira ponovno (najviše 2 puta), a onda se koristi predložak. **Provjera je vidljiva:** oznaka "AI tekst · 11/11 brojki provjereno", a klik na broj pokazuje konto, godinu i izvornu datoteku. Ovaj obrazac nismo našli ni u jednom alatu. | MUST |
| **MCP server** ("DCAT za portale, MCP za AI asistente") | Read-only server nad statičnim API-jem (pretraga, profil, usporedba, scenarij spajanja). Bilo koji AI asistent odgovara na pitanja o jedinicama našim brojkama. Otvoreni standard. | SHOULD, cilj je da uđe; uvjet: Karta reforme i vidljiva provjera gotove do čet navečer |
| Statistički blizanci (k-NN na strukturnim varijablama) | Pošteniji kontekst od skupina po veličini | SHOULD |
| Značka stabilnosti ocjene (četiri scenarija pondera) | Pristup iz JRC/OECD priručnika za kompozitne indekse | SHOULD |
| Strojno provjerljiv "kriterij od 10%" | Izravna veza s politikom Ministarstva financija | Samo ako se potvrdi da je donesen |
| AI čita proračune jedinica s portala (30 jedinica, ukupni iznosi 2024., točnost prema podacima Ministarstva) | Najjača poruka za organizatora, ali ne hrani proizvod | Subotnji bonus |
| ~~Kontrafaktualni prikaz "što ako"~~ | Rez nakon Fable reviewa 2.11. | Odbačeno |
| ~~"Pitaj podatke" (text-to-SQL)~~ | Statična stranica ne smije sadržavati API ključ, a model u pregledniku traži veliko preuzimanje | Odbačeno |
| ~~Model strojnog učenja za ranu uzbunu~~ | Nema oznake distresa; Italija ima oko 40.000 opažanja, a mi oko 4.000 | Odbačeno |

**Model i izvođenje (odluka 2.11.):**
- Primarno: **Gemma 4 E4B-it** (Apache-2.0) na llama.cpp (MIT) u Kaggle bilježnici na besplatnom GPU-u (laptop nije dovoljno jak). Bilježnicu pokrećemo i nadziremo iz razvojnog okruženja preko službenog **Kaggle MCP servera** (`save_notebook` s GPU-om, status sesije, preuzimanje izlaza). Bilježnica je u repozitoriju.
- `explain.py` radi s bilo kojim pružateljem (jedna funkcija); prompt i verifikator su isti.
- Claude API je razvojni alat: ocjenjuje gramatiku i padeže prvih 20 tekstova i pomaže u doradi prompta.
- **Sri navečer odluka:** ako manje od 80% Gemma tekstova prođe provjeru uz pristojan hrvatski, prvo veći model (Gemma 4 26B-A4B na 2×T4, samo ako je potrebno), a zatim Claude u batch načinu, uz iskreno navođenje kao AI alata u izgradnji. Gemma bilježnica i uzorak Gemma tekstova ostaju u repozitoriju kao otvoreni put.
- Padeži: paket činjenica sadrži naziv jedinice u potrebnim padežima.
- Tekstovi se generiraju za 576 jedinica, za zadnju godinu. AI tekst se ne prikazuje samo za dio jedinica; inače predložak za sve. Prompt i verifikator su javni na stranici metodologije, a tekst je označen kao AI.

---

## 6. Proizvod: opseg

Prioriteti su iz `02` §5.

**MUST**
1. **Profil kao svjedodžba:** ocjena 5-1 s riječi, pet komponenti kao trake uz medijan sličnih, sedmogodišnji trendovi (linija jedinice i linija medijana sličnih), zastavice, oznaka kvalitete podataka, AI objašnjenje s vidljivom provjerom brojki, sloj otvorenosti s portala.
2. **Karta 576 jedinica:** pretraga "Pronađi svoju općinu", odabir godine i tri prikaza (ocjena, trošak uprave po stanovniku, udio tekućih pomoći), vremenska animacija 2019.-2025. Paleta sigurna za daltoniste. **Naslovnica nije rang-lista.**
3. **Slične jedinice:** skupina i blizanci, rang samo unutar skupine i uvijek s nazivnikom.
4. **Simulator spajanja** (§4): ručni odabir susjeda; isti izračun spajanja kao Karta reforme.
5. **Karta reforme** (§5).
6. **Metodologija i podaci:** formule, pragovi, popis svih skupova s izdavačem i poveznicom, licence, AI alati, ograničenja, značka "povučeno s data.gov.hr API-ja dana …".
7. **Otvoreni izlaz:** statični JSON/CSV API, OpenAPI 3.1, DCAT-AP katalog, šifrarnik ID-ova.
8. **Sloj otvorenosti (CKAN API):** broj skupova jedinice na data.gov.hr, zadnje ažuriranje, poveznica na proračun, strojna čitljivost (udio CSV/XLSX nasuprot PDF-u).

**SHOULD:** MCP server (§5); **sloj revizija DUR-a** (odluka 3.11.: za svaku jedinicu zadnje mišljenje revizije s godinom i poveznicom na izvješće, ili "nije revidirana od 2019."; ide nakon MUST-a); kriterij od 10% (Z5), samo ako je donesen; rječnik i oblačići; kontekst "što jedinica ne kontrolira"; kanal za prijavu greške.

**COULD:** ugradiva kartica (iframe); AI čita proračune s portala (subotnji bonus); dodatni slojevi (IJF transparentnost, Sudski registar); PDF svjedodžba; engleska verzija.

**Izbačeno 2.11. (Fable review):** zasebna usporedba 2-4 jedinice (simulator već pokazuje stanje prije); "što ako"; "Pitaj podatke"; prijedlog partnera (zamijenjen Kartom reforme); puni Playwright paket (umjesto njega ručna provjera svih poveznica u subotu).

**UX načela:**
- 5 je najbolje, uvijek uz riječ.
- Opisne kategorije ("pod pritiskom") umjesto moralnih ("loše").
- Bez imena gradonačelnika i stranaka.
- Uvijek usporedba sa sličnima i s vlastitom prošlosti.
- Progresivno otkrivanje: ocjena → komponente → formule → sirovi podaci.
- Iskreno o nesigurnosti.
- Pristupačnost (WCAG AA, tablica kao alternativa karti).
- Ciljni uređaj je laptop ili desktop (1366-1920 px). Mobitel nije prioritet (odluka 2.11.); stranica se na njemu samo ne smije raspasti.

---

## 7. Arhitektura i stack

Detalji, licence provjerene u registrima i nacrt odjeljka "Korišteni alati i licence" su u `03`.

```
IZVORI: CKAN API (data.gov.hr) · DZS INSPIRE WFS · DZS PxWeb API · Ministarstvo financija XLSX (ETag)
        │  GitHub Actions: tjedni cron + ručno pokretanje
        ▼
ETL (Python 3.12): fetch → build (pokazatelji, bodovi, zastavice) → geo (mapshaper, susjedstvo)
                   → model (krivulja razmjera, blizanci) → publish (JSON API, OpenAPI, DCAT-AP)
        │                     ▲ jednokratno: explain.py (Gemma 4 na Kaggle GPU-u, pružatelj zamjenjiv) → verify.py
        │                     ▲ scenariji: Karta reforme (spopt max-p po županijama, pragovi stanovnika)
        ▼
GitHub Pages (statično, 0 €): React SPA (karta, profil, simulator, Karta reforme)
                              /api/v1/* (JSON, CSV, TopoJSON) · catalog.jsonld → harvest na data.gov.hr
MCP server (read-only, čita /api/v1) → AI asistenti
```

| Sloj | Izbor | Licenca |
|---|---|---|
| ETL | Python 3.12 (`py -3.12`), pandas, openpyxl, duckdb, pandera, pytest | BSD-3 / MIT |
| Geo | geopandas, libpysal, spopt, mapshaper | BSD-3 / MPL-2.0 |
| Model | statsmodels, scikit-learn | BSD-3 |
| Frontend | React, Vite, TypeScript, Tailwind, shadcn/ui, MapLibre GL + OpenFreeMap, ECharts | MIT / Apache-2.0 / BSD-3 |
| AI | llama.cpp, Gemma 4 E4B-it na Kaggle GPU-u (Kaggle MCP za pokretanje); Claude API samo kao razvojni alat i rezerva | MIT / Apache-2.0 |
| MCP | MCP Python SDK | MIT (provjeriti) |
| Objava | GitHub Pages, GitHub Actions, OpenAPI 3.1, DCAT-AP 3.0.1 | — |
| Naše licence | Kod EUPL-1.2 (ima službeni hrvatski tekst), podaci CC BY 4.0 | — |

**API kriterij:** preglednik ne može izravno zvati CKAN API jer ne šalje CORS zaglavlje. Zato se API koristi u ETL-u, a dokaz je stranica "Izvori" (endpoint, vrijeme, `metadata_modified`, hash), logovi GitHub Actionsa i kadar u videu. DZS WFS podržava CORS i može se pozvati uživo. Priču o podacima vodimo s CKAN API-jem (uključujući sloj otvorenosti), WFS-om i PxWebom. U dokumentaciji, kao organizacijski preduvjet, preporučujemo da Ministarstvo financija objavljuje PR-RAS, RAS-funkcijski i Bilancu na data.gov.hr.

---

## 8. Raspored (danas je ponedjeljak 2.11.)

| Dan | Razvoj | Ostali (tim) |
|---|---|---|
| **Pon 2.11.** (noć) | Istraživanje, validacija, ovaj plan ✔ | — |
| **Uto 3.11.** | ETL v1 (fetch preko CKAN API-ja i WFS-a, šifrarnik, metodologija v2, testovi); sloj otvorenosti (CKAN); geo pipeline i susjedstvo; Kaggle bilježnica i test Gemme na 20 jedinica; kostur frontenda | — |
| **Sri 4.11.** | Karta i profil; paket činjenica i verifikator; AI batch na Kaggleu. **Navečer odluka o modelu.** | — |
| **Čet 5.11.** | Blizanci, krivulja razmjera, statični API i OpenAPI; funkcija spajanja; scenariji Karte reforme (spopt) | **Scenarij videa gotov** |
| **Pet 6.11.** | Simulator i Karta reforme u sučelju; vidljiva provjera brojki; MCP server (uvjetno); stranica metodologije; CI deploy | Dokumentacija (popis skupova, alati) |
| **Sub 7.11.** | DCAT, vremenska animacija, dorada, pristupačnost, ručna provjera svih poveznica, snimke zaslona. **Zamrzavanje funkcija u 20 h** | Testiranje s 2-3 vanjske osobe; **gruba montaža videa** |
| **Ned 8.11.** | Samo ispravci grešaka | Završna montaža videa (OBS, Kdenlive), samo popravci |
| **Pon 9.11.** | Završna provjera poveznica i README-a | **Slanje e-maila do 12 h** |

**Točke odluke:**
- **Uto navečer:** ako geometrija i podaci Ministarstva financija nisu spojeni po kodu, privremeno se spaja po nazivu (radi za 576/576).
- **Sri navečer:** ako karta i profil ne rade glatko, simulator ide u plan B: odabir s popisa i jednostavna usporedba.
- **Sri navečer (AI):** ako manje od 80% Gemma tekstova prođe provjeru uz pristojan hrvatski: veći Gemma model ako je potrebno, zatim Claude (§5).
- **Čet navečer:** ako Karta reforme ne radi, ostaje jedan unaprijed izračunat prag (5.000) bez klizača. MCP server ulazi samo ako su Karta reforme i vidljiva provjera gotove.

**Plan B / C:** u `03` §7. Krajnja mjera je Streamlit nad istim ETL-om.

---

## 9. Rizici i otvorena pitanja

| Rizik | Ublažavanje |
|---|---|
| Podaci Ministarstva financija nemaju navedenu licencu i nisu na portalu | Izjava o izvoru; javni podaci prema Zakonu o pravu na pristup informacijama; upit organizatoru |
| AI asistent za kodiranje je vlasnički alat | **Riješeno 2.11.:** pravila dopuštaju AI alate uz navođenje u dokumentaciji. Claude Code se navodi kao razvojni alat koji nije dio rješenja; rješenje se gradi isključivo otvorenim kodom. Upit organizatoru se ne šalje. |
| Dospjele obveze jedinice same prijavljuju | Ponder 30 ostaje (presedan INEKO), uz analizu osjetljivosti i ručnu provjeru ekstremnih vrijednosti |
| Mapiranje konta (341, 25, 663, udio za decentralizirane funkcije) | Provjera u Računskom planu i u izvatku; testovi |
| Razina 22 je proračun same jedinice, bez proračunskih korisnika (potvrđeno: konto 367 je u rashodima) | Napomena: vrtići, knjižnice i sl. ulaze samo kroz prijenose (367); Z006 broji samo tijela uprave |
| Skriveni dug u komunalnim društvima nije u podacima | Napomena na stranici metodologije |
| Politička osjetljivost | Bez rang-lista na naslovnici i bez imena; jezik "održivosti"; ograda |
| Hrvatski jezik i padeži u tekstovima modela | Nazivi u padežima u paketu činjenica; Claude ocjenjuje uzorak od 20 jedinica; odluka u srijedu (§5) |
| Broj "~24% u funkcionalnom spajanju" nije potvrđen | U videu i dokumentaciji citirati službeni izvor ili govoriti samo o cilju (40%) i stvarnom spajanju (0). Potvrditi ili izbaciti prije snimanja. |
| Kriterij API-ja: jezgra podataka je XLSX izvan portala | Priču voditi s CKAN API-jem, WFS-om i PxWebom; preporuka Ministarstvu financija u dokumentaciji (§7) |
| Vremenski budžet: procjena za MUST bila je 6,3 dana, ostaje oko 5 | Rezovi iz §6; jedna funkcija spajanja za simulator i Kartu reforme |
| Karta reforme je politički osjetljiva | "Scenarij, ne prijedlog granica"; uvijek uz raspon stvarnih ušteda; ograda i u videu |

---

## 10. Video (≤ 3 min)

Okvir je **"Svjedodžba za vašu općinu"**, a vrhunac **"Spoji pa vidi"**:

| Vrijeme | Sadržaj |
|---|---|
| 0:00-0:25 | Problem: 576 jedinica, reforma bez spajanja, podaci u Excelu |
| 0:25-1:25 | Ana traži svoju općinu: svjedodžba, "komentar razrednika" (AI) s klikom na provjereni broj, usporedba s "razredom" (blizanci) |
| 1:25-2:15 | "Spoji pa vidi": tri susjedne općine u simulatoru, zatim Karta reforme: klizač na 5.000 stanovnika, karta prelazi s 556 na N jedinica, iskren raspon uštede |
| 2:15-2:50 | Arhitektura: CKAN API → izračun → otvoreni API; DCAT za portale, MCP za AI asistente (kratki kadar asistenta); daljnji razvoj |
| 2:50-3:00 | Poziv: alat za javnu raspravu o reformi |

---

## 11. Odluke (potvrđeno 2.11.)

Korisnik je 2.11. potvrdio plan i nalaze Fable reviewa (neovisni pregled modelom Claude Fable 5.1).

1. Ocjena 0-100 s pragovima KDZ-a i INEKO-a i ponderima 20/20/15/15/30, prikazana kao 5 (najbolje) do 1 s riječima.
2. Glavna ocjena za 2025. (prozor 2022.-2025.); povijesni niz istom metodom (dospjele obveze postoje za sve godine, ispravak 2.11.).
3. Simulator: ušteda samo na općoj upravi, raspon u tri sloja, plus procjena fiskalnog izravnanja.
4. Bez modela strojnog učenja za ranu uzbunu; umjesto toga zastavice i blizanci.
5. Stack: React + MapLibre + ECharts, Python ETL, GitHub Pages, Gemma 4 na Kaggle GPU-u.
6. Licence: kod EUPL-1.2, podaci CC BY 4.0.
7. ~~Upit organizatoru o AI asistentu~~ **Odlučeno 2.11.:** AI za kodiranje smijemo koristiti, navodi se u dokumentaciji, upit se ne šalje.
8. **Prihvaćeno 2.11.: sloj otvorenosti preko CKAN API-ja.** Za svaku jedinicu: broj skupova na data.gov.hr, datum zadnjeg ažuriranja i poveznica na njezine proračune na portalu. Provjera 2.11.: na portalu objavljuje oko 262 od 576 jedinica (159 općina, oko 90 gradova, 13 županija). Procjena: pola dana.
9. **Prihvaćeno 2.11.: paket inovacija.** Karta reforme i vidljiva provjera brojki (MUST), MCP server (SHOULD, cilj je da uđe), vremenska animacija. Detalji u §5 i §6.
10. **Prihvaćeno 2.11.: AI hibrid.** Gemma 4 na Kaggleu primarno; veći model samo ako je potrebno; Claude kao razvojni alat i rezerva uz odluku u srijedu navečer.
11. **Prihvaćeno 2.11.: rezovi i slijepe točke iz Fable reviewa** (§6, §8, §9).
12. **Prihvaćeno 3.11.: sloj revizija DUR-a (SHOULD).**
    - Provjera izvora 3.11.: popis izvješća je HTML, po 40 stavki po stranici, a putanja PDF-a kaže vrstu i naziv jedinice.
    - PDF-ovi su tekstualni. Mišljenje se iz njih čita regularnim izrazom (8/8 na uzorku 2019.-2025.).
    - Pokrivenost: od 2019. barem jednu financijsku reviziju ima oko 330 od 576 jedinica (314 spojeno odmah, ostatak su dvojezični nazivi i "DJ" za "Đ").
    - Godina objave nije revidirana godina; revidirana se čita iz teksta.
13. **Prihvaćeno 3.11.: objava.** GitHub Pages + GitHub Actions (ETL → testovi → build → statični API → deploy), bez poslužitelja i baze. AI tekstovi se generiraju na Kaggleu i commitaju, CI ih samo kopira. Uvjet: repozitorij mora biti javan (besplatni Pages).
14. **Prihvaćeno 3.11.: pravila za dospjele obveze** (`research/05`, §3.1 i §3.2). Ugrađeno u `pipeline/methodology.py` i pokriveno testovima.
    - Pravilo 1: kredit iskazan kao cijeli dospio, a redovno otplaćivan, ne ulazi u DO i dobiva oznaku kvalitete.
    - Pravilo 2: DO ≥ 30% rashoda poslovanja daje ocjenu najviše 2.
15. **Odlučeno 3.11.:** repozitorij postaje javan odmah. Ime ostaje.
