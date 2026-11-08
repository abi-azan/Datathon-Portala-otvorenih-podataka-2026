# UX zadaci za razmotriti

- [x] Dodati poruku kada pretraga nema rezultata. (4.11., `fcfed3e`)
- [x] Tablica kao alternativa karti: abecedno, filteri po županiji i vrsti, rang samo unutar skupine. (4.11., `fcfed3e`)
- [ ] Postaviti pretragu i kartu kao glavni sadržaj; legendu i dodatne postavke učiniti sklopivima. (prijedlog 7 iz `research/10`, nije odobren)

# Dogovoreno 4.11. navečer (radi se od večeras)

- [x] Temelj: novi izvori u `skupovi.csv`, build, API, testovi.
- [x] P1: kartica "Stanovništvo i gospodarstvo" (osnovica Popis 2021., procjena samo za trend, bez natpisa "procjena DZS-a").
- [x] P2: broj stanovnika uživo s API-ja DZS-a, sa spremljenom kopijom kao rezervom.
- [x] P4: demografija u simulatoru i Karti reforme.
- [x] D1: neto dohodak po stanovniku i udio mirovina.
- [x] D4 + S2: kartica "Fiskalno izravnanje" (samo isplata); možda se kasnije makne.
- [x] Karta reforme vidljiva iz cijele države (prijedlog 2 iz `research/10`).
- [x] Meki prijelaz boja na karti pri promjeni godine (prijedlog 3).
- [x] Nova ikona i favicon: v3 (presavijena karta od šahovnice); korisnik je možda još promijeni.
- [ ] Sitnice s karte koje je agent primijetio: teški obrubi oko malih otoka, na mobitelu zaglavlje prekriva natpis Karte reforme, natpis na karti na 1280 px prekriva sjever.
- [x] Snimka naslovnice u README, nakon karte i ikone. (5.11. noću, `docs/snimke/naslovnica.png`; uključuje prijedloge U-a)
- [x] Nova snimka naslovnice za README (6.11., stranica uživo, 1440×900, nove boje ocjena). Ako se naslovnica još mijenja, snimiti ponovno 8.11.
- [x] AI tekstovi: ponovno generiranje 5.11. navečer, nakon UI sesije (Gemma 4 31B, `kaggle/results/gemma_batch_2025_31b_q4_0_v2.json`): **561 od 576** prolazi provjeru (550 iz prvog pokušaja), ostalih 15 ide na predložak. 253 teksta imaju rečenicu konteksta (stanovništvo, dohodak).
- [x] Tih 15 ponovno generirano 6.11. s konkretnijom porukom nakon odbijanja (`--kaggle-batch --neprovjereni`, `kaggle/results/gemma_batch_2025_31b_q4_0_v3_neprovjereni.json`): **576 od 576** prolazi provjeru (`26796a3`).
- [x] (riješeno 6.11. navečer, vidi dolje) Sitnica u AI tekstovima: **44 teksta** prepisuju medijan skupine doslovno, pa ispadne nespretno, npr. "uz medijan skupine od nedostaje 1,7 % tekućih prihoda" (Požeško-slavonska županija) ili "uz medijan skupine od viška 13,3 % tekućih prihoda" (Novi Golubovec). Nije netočno. Popravak traži promjenu paketa ili prompta, a time novi batch za svih 576 (oko 4 h na Kaggleu); ne isplati se prije predaje.

# UI sesija 5.11. popodne (lokalno, necommitano)

- [x] Nazivi ocjena 2 i 1: "nestabilno", "vrlo nestabilno" (PLAN §11, odluka 18); isti u pipelineu, API-ju, paketima, MCP-u i sučelju.
- [x] Naslovnica: h1 "Fiskalna karta" + opis; "Za početak" (Povljana, Pag i Povljana, Karta reforme; brojke iz podataka).
- [x] Legenda na karti (naslovnica, simulator, Karta reforme); na mobitelu traka ispod karte. Područje izvan Hrvatske izblijeđeno.
- [x] Trake pokazatelja obojene prema rasponu ocjene, crtica medijana skupine (`skupine.json` dobiva S1-S5) i "medijan N" uz bodove.
- [x] Graf kretanja bodova: vrijednosti napisane na točkama, dodir otvara detalje; oznake više ne odrezane.
- [x] Metodologija → Pet pokazatelja: četiri koraka, primjer Grad Split (iz API-ja), kartica po pokazatelju s pitanjem i ljestvicom, formule sklopljene.
- [x] Jezični pregled (`.gstack/ui-review/jezicni-pregled.md`) primijenjen; "sastavnica" → "pokazatelj", "financijska održivost proračuna", predložak u punim rečenicama.
- [ ] Jezik, čeka potvrdu tima: `Reforma.tsx` "Zadnji razred s dodatkom u Vladinoj odluci…" i `metodologija.py` "Zakonska osnovica je približna…" (što je točno približno).
- [ ] Mobitel: dodir na kartu odmah otvara pregled; prijedlog je da prvi dodir pokaže karticu s gumbom "Pregled →".

# Pregled očima žirija 6.11. popodne (lokalno, necommitano)

Pregledana je stranica uživo na 1440×900, 1366×768 i 390 px. Mobitel se po odluci ne dira.

- [x] AI tekst Grada Zagreba bio je najkraći od svih 576 (174 znaka, 3 brojke), a Zagreb je prvi primjer na naslovnici. Dodana provjera: uz najslabiji pokazatelj mora stajati i njegova vrijednost (`verify.states_value`). Nisu je prošla samo dva teksta, Grad Zagreb i Općina Blato; ponovno su generirani (batch v4, 291 s, `kaggle/results/gemma_batch_2025_31b_q4_0_v4_vrijednost.json`). **576 od 576** prolazi i novu provjeru. Predložak sada također navodi vrijednost.
- [x] Naslovnica na laptopu: prikaz na karti i godine su u traci iznad karte, pa je sve na prvom ekranu (1366×768, 1280×720, 1440×900). Gumb u traci glasi "Pokreni".
- [x] Karta reforme: nakon odabira skupine (karta ili popis) stranica skoči na karticu skupine, a karta ostaje vidljiva. Odabrana skupina ima crno-bijeli obrub. Pomicanje klizača ne pomiče stranicu.
- [x] Simulator: legenda na karti bez državnih brojki.
- [x] Pregled jedinice: "Kopiraj poveznicu" i "Podaci jedinice (JSON)" u gornjem redu.
- [x] Metodologija: odjeljak "MCP server za AI asistente" s primjerom iz API-ja; poveznica u podnožju.
- [x] README: maknuta zastarjela rečenica "Za 15 jedinica prikazuje se predložak".
- [x] Commit i push na `main` (`54fa05f`, `8b3fa6d`), zeleni CI.
- [ ] Mobitel, ako ostane vremena: u simulatoru s odabranim jedinicama karta je na 4.774. pikselu od 6.014, a na Karti reforme ispod svih brojki.

# Bodovi: API i UI/UX, 6.11. navečer

Procjena prije ovoga: oko 45 od 50 mogućih bez videa (API 4 od 5, dojam 8,5 od 10).

- [x] Kartica "Otvoreni podaci jedinice" pita Portal uživo: broj skupova i dan zadnje izmjene (CKAN `package_search`). Portal ne šalje CORS zaglavlje, pa se zove kao JSONP (`web/src/lib/portal.ts`). Ako ne odgovori ili vrati manje od 80 % spremljenog broja, ostaje brojka iz obrade. Na Portalu objavljuje 269 od 576 jedinica.
- [x] Metodologija → Podaci: ploča "Podaci preko API-ja" (9 od 32 izvora). Preglednik uživo pita Portal (broj skupova u katalogu), DZS PxWeb (zadnja godina procjene) i WFS (broj jedinica u sloju granica); uz svaki je poveznica "otvori poziv".
- [x] Pregled jedinice: traka "Ocjena po godinama" uz siluetu; ispod "Ukratko" jedna napomena umjesto dvije; izvori kartice "Stanovništvo i gospodarstvo" i izračun izravnanja sklopljeni iza jednog retka.
- [x] Simulator: poruka o dospjelim obvezama odmah ispod tablice; kriterij od 10 %, promjena stanovništva i izračun uštede sklopljeni.
- [x] Karta: legenda više ne prekriva otoke kod Zadra i Šibenika na 1280×720 i 1366×768 (`mapStyle.leftClear` računa lijevi odmak pri prvom prikazu).
- [x] Pristupačnost: axe (WCAG 2 A i AA) ne nalazi prekršaje na naslovnici, pregledu jedinice, simulatoru, Karti reforme i metodologiji.
- [x] Push na `main` (`55f1ed1`), zeleni CI, provjera uživo: 576 od 576 AI tekstova, Zagreb "4/4 brojki provjereno", tri API-ja odgovaraju iz preglednika, Rijeka "uživo s API-ja Portala". Prvi pokušaj objave (`8b3fa6d`) zapeo je na GitHub Pagesu 10 minuta i bio otkazan; novi commit je prošao.
- [x] Nova snimka naslovnice za README sa stranice uživo (1440×900).
- [ ] Nije napravljeno: tablica Porezne uprave preko DataStore API-ja. Jedina tablica koja ga ima (usporedba stopa 2025./2026.) u DataStoreu ima 10.754 retka, od toga 10.198 praznih, pa XLSX ostaje izvor.
- [x] ~~Utjecaj (bez koda): poslati poveznicu dvjema ili trima osobama (vijećnik, novinar, udruga) i jednu njihovu rečenicu staviti u dokumentaciju i video.~~ Odluka 8.11.: bez izjave korisnika.
- [ ] Video: probna snimka u subotu, da se vidi stane li 11 kadrova u 3 minute.

# Čeka odluku

- [x] Konto 6353: izravnanje se za 2021.-2025. uzima iz odluka MF-a (opcija a, `pipeline/izravnanje_isplate.py`); 18 ocjena raste, Z2 se gasi kod 33 jedinice.
- [x] S1: prikazano na pregledu 124 jedinice s nižom stopom, kratki tekst (`docs/research/11`).
- [x] Stanovništvo 31.12.2025.: iz DZS XLSX-a "Gradovi i općine u statistici" za godine koje PxWeb još nema (opcija A); PxWeb ima prednost čim objavi 2025.
- [x] Trend stanovništva i dohodak u paketu činjenica za AI (kontekst, 253 od 576 jedinica); generiranje kasnije.
- [x] Belišće knjiži izravnanje na 6352: bez posebnog pravila (odluka 5.11.), poznato ograničenje.
- [ ] Prijedlog 6 (silueta jedinice i brojke u praznom prostoru na vrhu pregleda jedinice).
- [ ] Prijedlog 5 (vidljiva provjera AI teksta): samo ako stignemo.
- [x] Push na `main` i isključivanje tjednog crona (6.11.; `deploy.yml` sada samo na push i ručno).
- [x] Kriterij od 10 %: samo redak u "Dodatni pokazatelji" (i blok u simulatoru), bez upozorenja, jer ga za 2025. po približnom izračunu ne zadovoljava 270 od 576 jedinica (odluka 5.11.).
- [ ] Zakonski tekst u simulatoru iza "Kako se računa".

- [ ] Prediktori gospodarskog razvoja: istraživanje u noćnoj smjeni 5.11. (`docs/research/13`), odluka RAZVITI ili ODBACITI u četvrtak.

# Sesija 6.11. navečer: bodovi žirija (grana `noc-6-11`, `main` nije diran)

Žiri ocjenjuje samo predano: kod, dokumentaciju, demo i video. Zato je večer otišla na ono što žiri čita i otvara.

- [x] **Karta bez WebGL-a.** MapLibre GL 6 traži WebGL 2 i bez njega baca grešku, pa je cijela stranica ostajala prazna. Sada se karta crta kao SVG iz istog TopoJSON-a (naslovnica, simulator, Karta reforme), a granica greške hvata i kasnije padove. Provjera na bilo kojem računalu: `?webgl=0` ispred `#` u adresi.
- [x] **Pregled svega što žiri može otvoriti:** 576 pregleda jedinica, po dvije skupine simulatora za svaku županiju i svih devet stanja Karte reforme, bez ijedne greške, i prije i nakon promjene činjenica; 73 poveznice u dokumentaciji rade.
- [x] **AI tekstovi pročitani uz činjenice.** Brojke su bile točne u svih 576, ali 164 teksta nisu bila dobra: 68 je kao najslabiji navodilo pokazatelj koji je ujedno jaka strana (Rovinj, 100 bodova), 67 je izgubilo riječ „ostaje” uz medijan dok jedinici „nedostaje” (Knin), 29 je imalo rečenicu „uz medijan skupine od nedostaje…”. Tri nova pravila u provjeri, određena poruka modelu, prompt isti. Piloti po 8 jedinica: v5 je dao 6 dobrih tekstova od 8, v6 je pao zbog greške u poruci modelu (ispravljeno, uz test koji je sada hvata), v7 je dao 8 od 8. Batch v8 (150 jedinica, 101 min) dao je 150 od 150: 10 iz prvog pokušaja, 138 iz drugog, 2 iz trećeg. **Svih 576 tekstova je AI i prolazi provjeru.**
- [x] **Dokumentacija za žiri:** `docs/DOKUMENTACIJA.pdf`, 10 stranica po devet kriterija, s prilogom svih 34 skupa. Shema `docs/arhitektura.svg`, tablica povezivanja s postojećim javnim sustavima, točnija rečenica o API-ju (svaki izvor koji ima upotrebljiv API čita se preko njega).
- [x] **Video:** scenarij v4 s natpisom za svaki od 7 elemenata iz pravila, 327 riječi, sve brojke ponovno pročitane iz API-ja; slike naslov, izvori i kraj; titlovi (`docs/video/`).
- [x] Pristupačnost ponovno provjerena (axe, WCAG 2 A i AA): bez prekršaja na pet glavnih stranica i na prikazu bez WebGL-a.
- [x] `docs/` pospremljen: radni dnevnici u `docs/dnevnik/`.
- [x] **Tim, prvo:** pregledati granu `noc-6-11` i spojiti je u `main`. (spojeno 6.11. navečer, `6dc14d6`, zeleni CI)
- [ ] **Tim:** u `docs/DOKUMENTACIJA.md` upisati naziv tima, članove, mentora i poveznicu na video, pa ponovno ispisati PDF (upute u `pipeline/dokumentacija.py` i `CLAUDE.md`). Tim (Begovi mušketiri) i mentor (doc. dr. sc. Stjepan Begušić, FER) upisani 8.11.; ostaju članovi i poveznica na video.
- [x] ~~**Tim:** poslati poruku iz `docs/PREDAJA.md`, odjeljak 6, na 3 do 5 adresa i jednu rečenicu korisnika staviti u dokumentaciju i video.~~ Odluka 8.11.: izjave nema (još nema korisnika), mjesto u dokumentaciji je obrisano.
- [ ] **Tim:** snimiti glas i video po scenariju v4.
- [x] Preglednici: Firefox 157 i WebKit 27 (Playwrightove verzije, jezgra Safarija) otvaraju naslovnicu, prikaz bez WebGL-a, pregled Povljane, simulator, Kartu reforme i metodologiju bez greške u konzoli i bez vodoravnog pomicanja. Pravi Safari na Macu vrijedi još jednom pogledati.
- [x] **Tim:** opis repozitorija na GitHubu (About: adresa stranice, kratki opis, teme `open-data`, `croatia`, `public-finance`). (provjereno 8.11.: opis, adresa i pet tema su postavljeni)
- [ ] Pročitati i potvrditi dvije rečenice koje govore u ime tima: redak "Claude Code" u README-u (Korišteni AI alati) i `docs/dnevnik/README.md`.
- Nije napravljeno, namjerno: četvrti prikaz karte "Otvoreni podaci" (tko objavljuje na Portalu). Tražio bi novo polje u API-ju i izmjene na naslovnici, dvjema kartama i tablici dan prije zamrzavanja; podatak je već na pregledu jedinice i na stranici "Metodologija i podaci".

# Kasnije, ako ostane vremena

- [ ] P3 + D3: karta promjene stanovništva i karta dohotka, kao jedan paket.

# Odbačeno

- D2 (porez stanovnika naspram poreza koji jedinica knjiži): dvije brojke bi zbunjivale.
