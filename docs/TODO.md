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
- [ ] Opcionalno, sitnica u AI tekstovima: **44 teksta** prepisuju medijan skupine doslovno, pa ispadne nespretno, npr. "uz medijan skupine od nedostaje 1,7 % tekućih prihoda" (Požeško-slavonska županija) ili "uz medijan skupine od viška 13,3 % tekućih prihoda" (Novi Golubovec). Nije netočno. Popravak traži promjenu paketa ili prompta, a time novi batch za svih 576 (oko 4 h na Kaggleu); ne isplati se prije predaje.

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
- [ ] Commit i push na `main`, zeleni CI, provjera stranice uživo (Zagreb, naslovnica, Karta reforme).
- [ ] Nova snimka naslovnice za README nakon pusha (naslovnica se promijenila).
- [ ] Mobitel, ako ostane vremena: u simulatoru s odabranim jedinicama karta je na 4.774. pikselu od 6.014, a na Karti reforme ispod svih brojki.

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

# Kasnije, ako ostane vremena

- [ ] P3 + D3: karta promjene stanovništva i karta dohotka, kao jedan paket.

# Odbačeno

- D2 (porez stanovnika naspram poreza koji jedinica knjiži): dvije brojke bi zbunjivale.
