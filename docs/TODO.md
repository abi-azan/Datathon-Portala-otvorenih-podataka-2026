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
- [ ] Snimka naslovnice u README, nakon karte i ikone.
- [ ] **8.11.: ponovno snimiti naslovnicu za README** (do tada će biti još promjena).
- [ ] AI tekstovi: ponovno generiranje 5.11., nakon ostalih promjena.

# Čeka odluku

- [x] Konto 6353: izravnanje se za 2021.-2025. uzima iz odluka MF-a (opcija a, `pipeline/izravnanje_isplate.py`); 18 ocjena raste, Z2 se gasi kod 33 jedinice.
- [x] S1: prikazano na pregledu 124 jedinice s nižom stopom, kratki tekst (`docs/research/11`).
- [x] Stanovništvo 31.12.2025.: iz DZS XLSX-a "Gradovi i općine u statistici" za godine koje PxWeb još nema (opcija A); PxWeb ima prednost čim objavi 2025.
- [x] Trend stanovništva i dohodak u paketu činjenica za AI (kontekst, 253 od 576 jedinica); generiranje kasnije.
- [x] Belišće knjiži izravnanje na 6352: bez posebnog pravila (odluka 5.11.), poznato ograničenje.
- [ ] Prijedlog 6 (silueta jedinice i brojke u praznom prostoru na vrhu pregleda jedinice).
- [ ] Prijedlog 5 (vidljiva provjera AI teksta): samo ako stignemo.
- [ ] Push na `main` i isključivanje tjednog crona prije zamrzavanja (cron pada u ponedjeljak 9.11. u 04:17 UTC).
- [ ] Kriterij od 10 % na pregledu jedinice: ostaje ili samo rečenica u napomenama.
- [ ] Zakonski tekst u simulatoru iza "Kako se računa".

# Kasnije, ako ostane vremena

- [ ] P3 + D3: karta promjene stanovništva i karta dohotka, kao jedan paket.

# Odbačeno

- D2 (porez stanovnika naspram poreza koji jedinica knjiži): dvije brojke bi zbunjivale.
