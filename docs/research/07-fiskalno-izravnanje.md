# Fiskalno izravnanje: zakonska formula i provjera prema MF-u (4.11.2026.)

Odluka 17 (PLAN §11) traži da simulator spajanja procijeni promjenu fiskalnog izravnanja po zakonskoj formuli, ali samo ako ta formula na postojećim jedinicama daje iste iznose kao Ministarstvo financija (MF). Provjera je prošla: formula daje MF-ove iznose za svih 576 jedinica, do 1 €. Kod je u `pipeline/izravnanje.py`, a provjera se pokreće s `python -m pipeline.izravnanje --provjera`.

## Zakonska formula

Izvor je Zakon o financiranju jedinica lokalne i područne (regionalne) samouprave, NN 127/17, 138/20, 151/22 i 114/23. Članak 8. u sadašnjem obliku uveden je člankom 3. NN 114/23 i primjenjuje se od 1.1.2024. (https://narodne-novine.nn.hr/clanci/sluzbeni/2023_10_114_1617.html). Pročišćeni tekst je provjeren na zakon.hr 4.11.2026.: novijih izmjena nema, a baza je ažurna do NN 119/26.

| Članak | Što kaže |
|---|---|
| čl. 8. st. 1. | Pravo na izravnanje ima jedinica kojoj je kapacitet ostvarenih poreznih prihoda manji od referentne vrijednosti. |
| čl. 8. st. 2. | Kapacitet općine ili grada je petogodišnji prosjek poreza na dohodak koji bi se na njezinu području ostvario uz najvišu propisanu stopu, uključujući najviši paušalni porez od iznajmljivanja turistima, po stanovniku. |
| čl. 8. st. 3. | Referentna vrijednost za općine je isti prosjek po stanovniku za sve općine, **uvećan za 50 %**. |
| čl. 8. st. 4. | Referentna vrijednost za gradove je prosjek za sve gradove, bez uvećanja. |
| čl. 8. st. 5.-6. | Županije: isto, pomnoženo s udjelom županija u porezu na dohodak (20 %, čl. 5. st. 2. t. 2.). |
| čl. 8. st. 7. | "Najviša propisana stopa" je gornja granica niže stope poreza na dohodak koju jedinica smije propisati. |
| čl. 8. st. 8. | Grad Zagreb se ne uzima u izračun referentnih vrijednosti za gradove i županije. |
| čl. 9. st. 1.-3. | Puni iznos = (referentna vrijednost − kapacitet) × broj stanovnika. |
| čl. 9. st. 4.-5. | Udio jedinice = njezin puni iznos / zbroj svih punih iznosa. |
| čl. 9. st. 7., čl. 16. st. 2. | Ministar odlukom (do 30. rujna za iduću godinu) utvrđuje iznos jedinice: **udio × iznos iz državnog proračuna**. |

U kodu:

- `puni_iznos(kapacitet_pc, referentna_pc, stanovnici)` = max(0, (referentna − kapacitet) × stanovnici). Granicu 0 daje čl. 8. st. 1.: jedinica iznad referentne vrijednosti nema pravo, pa ni negativan iznos.
- MF zaokružuje kapacitet po stanovniku i referentnu vrijednost na cent, i to prije uvećanja od 50 %: 466,56 × 1,5 = 699,84. Kod radi isto.

Jedinica, dakle, ne dobiva puni iznos nego svoj udio u stavci proračuna:

| Godina | Proračun | Zbroj punih iznosa | Isplata kao dio punog iznosa |
|---|---|---|---|
| 2025. | 280.445.617 € | 398.132.805 € | 70,4 % |
| 2026. | 280.445.617 € | 444.596.598 € | 63,1 % |
| 2027. | još nije utvrđen | 514.991.814 € | 54,5 % ako proračun ostane isti |

- Za 2026. iznos stoji u točki II. odluke ("3 × 280.445.617 EUR").
- Za 2025. iznos je potvrđen iz knjiga jedinica. Od 445 jedinica s pravom, njih 270 na kontu 6353 u PR-RAS-u 2025. ima točno udio × 280.445.617 €, s odstupanjem do 1 %. 107 jedinica ima 0 na kontu 6353 (izravnanje knjiže drugdje), a 60 ih ima više. Konto 6353 zato nije pouzdana kontrola za pojedinu jedinicu.

## Izvor MF-a

- **Tablica udjela po JLP(R)S za fiskalno izravnanje u 2027. godini**, Ministarstvo financija.
  - Datoteka: https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava//Tablica%20udjela%20po%20JLP(R)S%20za%20fiskalno%20izravnanje%20u%202027.%20godini.xlsx
  - Popis svih godina (2018.-2027.) i odluke: https://mfin.gov.hr/istaknute-teme/lokalna-samouprava/fiskalno-izravnanje/202
- Preuzeto 4.11.2026. kroz `pipeline.sources.fetch` (ključ `mf_fiskalno_izravnanje`) u `data/raw/izravnanje/fi_2027.xlsx`. Datoteka je stvarni XLSX od 491.583 B, `Last-Modified` 6.10.2026. Redak je u `data/reference/skupovi.csv`.
- List "Izračun udjela za 2027." daje:
  - za svaku jedinicu porez i prirez po godinama 2013.-2025., paušal od turizma, broj smještajnih jedinica, moguću stopu prireza i najvišu nižu stopu poreza;
  - "porez za izračun kapaciteta" po godini, tj. iznos preračunat na najviše stope;
  - P1 (petogodišnji prosjek 2021.-2025.), P2 (kapacitet po stanovniku), P3 (referentnu vrijednost), P4 (puni iznos, u tablici za 2026. nazvan "optimalni iznos") i Z (udio);
  - stanovnike prema Popisu 2021.
- List "Udjeli" sadrži udjele iz odluke.
- Referentne vrijednosti za 2027. su: općine 699,84 €, gradovi 686,33 € i županije 115,32 €. Iste brojke stoje na stranici MF-a.
- Tablica nema OIB, pa se jedinice spajaju sa šifrarnikom preko županije, vrste i naziva bez dijakritika:
  - 546 jedinica spaja se izravno;
  - 14 preko `units.match_key`: dvojezični istarski nazivi, "VINODOLSKA OPĆINA", "NOVIGRAD.";
  - 15 nakon ispravka "BL" u "BO": u tablici za 2027. svaki je "BO" zamijenjen s "BL" (SAMOBLR, ZABLK, BLROVO), pa nijedan naziv u tablici ne sadrži "BO";
  - 1 po sličnosti: "SVETA NEDJELJA" je Grad Sveta Nedelja.
  - Ukupno je spareno 576/576, svaka jedinica jednom.

## Rezultat provjere (tablica za 2027.)

`provjera()` iz godišnjih stupaca računa P1, P2, referentne vrijednosti, P4 i udjele po zakonskoj formuli i uspoređuje ih s MF-om:

| Korak | Članak | Rezultat |
|---|---|---|
| Petogodišnji prosjek P1 | 8. st. 2., 5. | 576/576 jednako (do 1 centa) |
| Kapacitet po stanovniku P2 | 8. st. 2., 5. | 576/576 jednako |
| Referentne vrijednosti | 8. st. 3., 4., 6., 8. | općine 699,84, gradovi 686,33, županije 115,32: sve jednake |
| Puni iznos P4 | 9. st. 1.-3. | **576/576 unutar 5 % (100 %), 576/576 do 1 €**; pravo ima 452 jedinice (358 općina, 80 gradova, 14 županija) |
| Zbroj punih iznosa | 9. st. 4. | 514.991.814,48 €, jednako MF-u |
| Udio | 9. st. 5. | 576/576, najveće odstupanje 2,6·10⁻¹⁷; udio iz odluke jednak je udjelu iz tablice za svih 576 |

**PROŠLO** (prag je 90 % jedinica unutar 5 %). Nijedna jedinica ne odstupa. Zagreb ima kapacitet 1.319,50 € po stanovniku, daleko iznad referentne vrijednosti, pa nema pravo ni u MF-u ni u formuli.

Isti kod na tablici za 2026. (preuzeta samo za provjeru, nije u `data/raw`):

- svih 556 općina i gradova jednako je MF-u, a referentne vrijednosti za općine (608,55) i gradove (589,17) također;
- 13 od 20 županija odstupa više od 5 %. Uzrok je u MF-ovoj tablici: kapacitet županija za 2026. izračunat je kao prosjek 2019.-2023., a ne 2020.-2024. kako piše u zaglavlju i kako je izračunat za općine i gradove. To vrijedi za svih 20 županija;
- ukupno prolazi 563/576 (97,7 %);
- u tablici za 2027. županije su usklađene.

Simulator ne spaja županije, pa ovo ne utječe na procjenu.

## Kako se procjenjuje spojena jedinica

`za_spajanje(clanice, je_grad, *, referentne, preracunaj_stope=True)`:

1. **Vrsta:** grad ako je barem jedna članica grad (pravilo simulatora). Referentna vrijednost je ona za tu vrstu, kako je objavljena.
2. **Kapacitet:** Σ (kapacitet × stanovnici) / Σ stanovnici, tj. zbroj petogodišnjih iznosa kroz zbroj stanovnika. Ako članice imaju istu vrstu i iste stope, formula je linearna: dvije jedinice ispod referentne vrijednosti spojene dobivaju točno zbroj svojih punih iznosa.
3. **Stope (`preracunaj_stope`):** MF svaku godinu računa po stopama koje vrijede za sadašnji status jedinice (čl. 8. st. 2. i 7.):
   - godine do 2023. množe se s 1 + moguća stopa prireza (općina 10 %, grad 12 %, grad iznad 30.000 stanovnika 15 %);
   - godine od 2024. računaju se po najvišoj nižoj stopi poreza (općina 20 %, grad 21 %, sjedište županije ili grad iznad 35.000 stanovnika 22 %).
   - Kad općina uđe u grad, njezini se godišnji iznosi preračunavaju na stope grada. Spojena jedinica zadržava najvišu klasu koju ima neka članica i prelazi u višu klasu kad zbroj stanovnika prijeđe prag.
   - Klase su očitane iz tablice, nisu prepisane iz zakona o porezu na dohodak. Na primjer, Kaštela (37.794 stanovnika) ima 22 %, a Vinkovci (30.842) 21 %.
4. **Izlaz:** `puni_clanice` (zbroj punih iznosa članica), `puni_spojena`, `promjena`, `promjena_udio`, `puni_spojena_bez_preracuna` (bez koraka 3) i `oznake`:
   - `vrsta_grad` / `vrsta_opcina`;
   - `kapacitet_zbroj_clanica`, `kapacitet_preracunat_na_stope_spojene` ili `kapacitet_po_stopama_clanica`;
   - `referentne_nepromijenjene`, `puni_iznos_ne_isplata`;
   - `clanica_iznad_referentne` ili `bez_prava_na_izravnanje`.
5. Ulazi dolaze iz MF tablice (`procjena(df, slugovi)`), ne iz našeg PR-RAS-a. Kapacitet traži porez preračunat na najviše stope i paušal po smještajnoj jedinici, a toga u PR-RAS-u nema.

Iz formule slijedi da spajanje po njoj **nikad ne povećava** puni iznos. Ako su sve članice ispod referentne vrijednosti, zbroj se ne mijenja. Ako je neka iznad, njezin višak smanjuje izravnanje ostalih. Kad općina uđe u grad, referentna vrijednost pada (686,33 umjesto 699,84 €) i rastu stope po kojima se kapacitet mjeri.

### Primjeri (tablica za 2027.)

**Povljana + Pag (Zadarska županija):**

| | Stanovnici | Kapacitet €/st. | Referentna €/st. | Puni iznos |
|---|---|---|---|---|
| Grad Pag | 3.175 | 993,68 | 686,33 | 0 € |
| Općina Povljana | 669 | 950,86 | 699,84 | 0 € |
| Spojeni grad | 3.844 | 991,63 (986,23 bez preračuna stopa) | 686,33 | 0 € |

Promjena je 0 €. Obje jedinice imaju visok porezni kapacitet, ponajviše zbog turizma i paušala, pa nemaju pravo na izravnanje ni prije ni poslije spajanja. Povljana ima stvaran dug i nepovoljno mišljenje DUR-a (`research/05`), a izravnanje joj ipak ne pripada. Izravnanje, naime, mjeri porezni kapacitet, a ne financijsko zdravlje.

**Jelenje + Viškovo (Primorsko-goranska; dvije općine, jedna iznad referentne):**

| | Stanovnici | Kapacitet €/st. | Puni iznos |
|---|---|---|---|
| Općina Jelenje | 5.096 | 583,91 | 590.779 € |
| Općina Viškovo | 16.084 | 735,52 | 0 € |
| Spojena općina | 21.180 | 699,04 | 16.902 € |

Promjena je −573.877 € (−97 %). Viškovo je iznad referentne vrijednosti od 699,84 €, i njegov višak gotovo potpuno pokriva Jelenjin manjak.

**Ivankovo + Vinkovci (Vukovarsko-srijemska; općina ulazi u grad, obje ispod referentne):**

| | Stanovnici | Kapacitet €/st. | Referentna €/st. | Puni iznos |
|---|---|---|---|---|
| Općina Ivankovo | 6.543 | 281,24 | 699,84 | 2.738.900 € |
| Grad Vinkovci | 30.842 | 543,60 | 686,33 | 4.402.079 € |
| Spojeni grad | 37.385 | 512,93 (497,68 bez preračuna) | 686,33 | 6.482.556 € |

Promjena je −658.422 € (−9,2 %). Otprilike 88.000 € pada zato što Ivankovo prelazi na nižu referentnu vrijednost gradova. Ostatak, oko 570.000 €, dolazi od preračuna stopa. Spojeni grad ima više od 35.000 stanovnika, pa mu se kapacitet mjeri po stopi od 22 % (Vinkovci danas 21 %, Ivankovo 20 %), a Ivankovo ulazi s prirezom grada iznad 30.000 stanovnika (15 % umjesto 10 %).

**Barilović + Tounj (Karlovačka; dvije općine ispod referentne):** 749.589 € + 430.159 € = 1.179.748 €, i jednako toliko nakon spajanja. Promjena je 0 €, jer je formula linearna.

### Svih 13.353 skupine simulatora

| Slučaj | Skupina | Promjena punog iznosa |
|---|---|---|
| Barem jedna članica iznad referentne vrijednosti | 4.546 | sve padaju; medijan −100 %, prosjek −1,39 mil. € |
| Općina ulazi u grad, sve ispod referentne | 5.218 | sve padaju; medijan −3,5 % |
| Ista vrsta, različita klasa stopa ili prijelaz praga stanovnika | 30 | sve padaju; medijan −4,8 % |
| Ista vrsta, sve ispod referentne | 2.749 | 0 € |
| Nijedna članica nema pravo | 810 | 0 € |

## Ograničenja

- **Puni iznos, ne isplata.** Jedinica dobiva udio u stavci proračuna (čl. 9. st. 7.). Dok proračun za 2027. ne bude poznat, isplata se može procijeniti samo omjerom iz tablice gore, oko 55-70 % punog iznosa. Spajanje smanjuje zbroj punih iznosa, pa bi uz isti proračun udjeli svih ostalih jedinica malo porasli. To simulator ne prikazuje.
- **Referentne vrijednosti se ne mijenjaju.** Spajanje mijenja prosjeke svih općina i gradova, ali malo. Kad Povljana prijeđe iz općina u gradove, referentna vrijednost za općine pada s 699,84 na 699,39 €, a za gradove raste s 686,33 na 686,42 €. Kod Ivankova je pomak veći: 701,50 i 685,02 €.
- **Klase stopa** za spojenu jedinicu očitane su iz MF tablice. Zakon o porezu na dohodak nismo provjerili u službenom tekstu, a pročišćeni tekst na fiskai.hr navodi drukčije granice, pa se na njega ne oslanjamo. Za spajanje bez promjene vrste i bez prijelaza praga od 30.000 ili 35.000 stanovnika ovo ne igra ulogu.
- **Zakon ne uređuje spojenu jedinicu.** Pretpostavljamo da bi MF njezin kapacitet računao iz zbroja poreza na području svih članica, kao što ga računa za postojeće jedinice. Prijelazne odredbe nekog budućeg zakona o spajanju mogle bi to urediti drukčije.
- **Godina.** Tablica za 2027. koristi porez 2021.-2025. i stanovnike iz Popisa 2021. Procjena vrijedi za tu godinu; za 2028. treba novu tablicu (ista funkcija, druga datoteka u `config.MF_FI_XLSX`).
- Županije i Grad Zagreb nisu u simulatoru (pravilo 2), pa `za_spajanje` za njih javlja grešku.
