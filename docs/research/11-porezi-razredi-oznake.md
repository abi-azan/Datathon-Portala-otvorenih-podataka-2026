# 11. Porez na dohodak: neubrani porez, stope spojene jedinice, podjela poreza i oznake DZS-a

Datum: 4.11.2026. Agent D ("porezi-istraživanje"). Samo istraživanje, kod nije mijenjan.

Oznake pouzdanosti:

| Oznaka | Značenje |
|---|---|
| [V] | provjereno u primarnom izvoru (Narodne novine, MF, Porezna uprava, DZS) ili izračunato iz naših podataka |
| [P] | zaključak ili procjena |
| [N] | nije pronađeno |

Skripte i preuzeti dokumenti su u radnoj mapi agenta (`scratchpad/D/scripts`, `scratchpad/D/raw`). Sve brojke ovdje dobivene su iz `data/build/` i iz sirovih MF datoteka u `data/raw/mf/prras/`, bez pisanja u repozitorij.

---

## 1. Sažetak

**Q1. Koliko poreza jedinica s nižom stopom ne naplati.**
Može se pokazati vjerodostojno, ali uz tri korekcije u odnosu na brzi izračun (a):
1. lokalne stope vrijede samo za plaće, mirovine, obrt i drugi dohodak; kapital, najam i paušalisti plaćaju fiksnih 12 % (u ovih 124 jedinica to je 13,9 % poreza);
2. jedinici ostaje samo njezin dio poreza (74 %), a ostatak ide županiji i za decentralizirane funkcije, uz povrate i naknadu Poreznoj upravi;
3. viši razred poreza (iznad 60.000 € godišnje) gotovo ništa ne mijenja (manje od 1 %).
- Za svih 124 jedinica zajedno (stope za 2026., dohodak iz 2025.): **oko 89 mil. € godišnje u proračunima tih jedinica, razumni raspon 74-91 mil. €**. Na svim razinama zajedno to je oko 128 mil. €, od toga oko 23 mil. € županijama.
- (a) 150 mil. € i (b) 104 mil. € reproducirani su točno. Razlika prema našoj procjeni je gotovo u cijelosti porez po fiksnim stopama. Broj (c) 88 mil. € praktički je isti kao naš (89 mil. €). Vjerojatno je dobiven istim pristupom, ali to ne mogu potvrditi bez koda [P].
- **Preporuka:** prikazati na profilu samo tih 124 jedinica, kao kontekst bez utjecaja na ocjenu, zaokruženo i s rasponom. Prijedlog teksta je u §2.6.

**Q2. Najviše stope i razredi spojene jedinice.**
Naše pravilo u `izravnanje.stope_spojene` **odgovara zakonu**, pa kod ne treba mijenjati.
- Najviše niže stope za 2025. i 2026. su: općina 20 %, grad 21 %, veliki grad (više od 35.000 stanovnika) i grad sjedište županije 22 %, Grad Zagreb 23 % (čl. 19.a st. 2. Zakona o porezu na dohodak, NN 152/24) [V].
- Granica razreda je 60.000 € godišnje, odnosno 5.000 € mjesečno (čl. 19. i čl. 24. st. 3.) [V].
- MF-ova tablica izravnanja dosljedno primjenjuje ta pravila na svih 556 općina i gradova [V].
- Treba ispraviti samo dvije rečenice u dokumentaciji koje kažu da pravilo "nije provjereno u zakonu" (§3.4).

**Q3. Podjela poreza na dohodak.**
- Zakonska podjela je: općina ili grad 74 %, županija 20 %, decentralizirane funkcije 6 % (čl. 5. st. 2. Zakona o financiranju JLP(R)S, NN 138/20) [V]. Porezna uprava od svega zadržava naknadu od 1 % (čl. 5. st. 4., NN 114/23) [V].
- Naš omjer (porez u proračunu kroz porez stanovnika) iznosi oko 0,64. To je zakonska podjela umanjena za povrate iz godišnjeg obračuna: povrati su 9 % poreza stanovnika [V]. Prije povrata je omjer 0,725 za općine i 0,752 za gradove, dakle gotovo točno 74 %.
- **Za korisnika omjer nije koristan broj.** Uglavnom je posljedica zakona i knjiženja. Preporučujem ga koristiti samo kao kontrolu kvalitete podataka (11 jedinica je izvan raspona 0,45-0,85) i ne prikazivati ga kao pokazatelj.

**Q4. Oznake DZS-a.**
- "-" znači **nema pojave**, dakle prava nula [V]. Primjer je Vratišinec: nema ni postelja ni turista u komercijalnom smještaju.
- "z" znači **podatak zbog povjerljivosti nije objavljen** [V]. Primjer je Kamanje: 19 postelja je objavljeno, a dolasci i noćenja 2023. i 2025. su skriveni. Godine 2024. bilo je 123 dolaska.
- "0" znači da je podatak manji od 0,5 mjerne jedinice, dakle nije nula [V].
- "." nije oznaka DZS-a. To je tehnički zapis u PX datoteci, gdje broj točaka bira oznaku: ".." je "-", a "...." je "z" [V].
- Naše pravilo u `pxweb.py` je ispravno: "-" je 0, a "z" je prazno.

---

## 2. Q1. Porez koji jedinica s nižom stopom ne naplati (odluka S1)

### 2.1 Tko je ispod maksimuma

Iz `porezna_stope.parquet` [V]:

- **2026.:** 124 jedinice (106 gradova i 18 općina) imaju nižu stopu manju od najviše dopuštene.
- **2025.:** takvih je bilo 125.
- 119 jedinica je ispod maksimuma u obje godine.
- **Rijeka** je 2025. imala najvišu stopu (22 % i 32 %). Za 2026. spustila je stope na 20 % i 25 %. Njezin neubrani porez zato postoji tek od 2026.
- Viša stopa je ispod svog maksimuma (niža stopa + 10 postotnih bodova) kod 109 od 124 jedinice.
- Primjeri:
  - Samobor: 18 % i 27 %, a smije 22 % i 32 %;
  - Karlovac: 19 % i 29 %;
  - Split: 21,5 % i 32 %, pa mu je viša stopa na maksimumu;
  - Baška: 15 % i 25 %, što je zakonski minimum.

### 2.2 Koje vrste dohotka plaćaju lokalnu stopu

Zakon o porezu na dohodak (pročišćeni tekst, NN 115/16 ... 152/24) [V]:

| Vrsta u podacima Porezne uprave | Stopa | Članak | Ovisi o lokalnoj stopi? |
|---|---|---|---|
| zaposlenici (plaće iz JOPPD-a) | niža i viša stopa jedinice | čl. 24. st. 3. (predujam), čl. 19. i 19.a | da |
| umirovljenici | niža i viša stopa jedinice | čl. 24. st. 3. i 5. | da |
| obrt i slobodna zanimanja (poslovne knjige) | godišnji porez po čl. 19. | čl. 19., 46. | da |
| drugi dohodak | predujam po nižoj stopi jedinice | čl. 40. st. 1. (pročišćeni tekst; uveo NN 114/23, čl. 17.) | da |
| kapital (kamate, dividende, kapitalni dobici) | 12 % (iznimno 24 % ili 36 %) | čl. 70. st. 1., 4., 17.-19. | ne |
| imovina (najam i zakup) | 12 % | čl. 62. st. 1. i 6. | ne |
| "povremeni rad - imovina" | najam i zakup te otuđenje nekretnina, fiksne stope | napomena u tablici Porezne uprave | ne |
| paušalisti (samostalna djelatnost) | 12 % | čl. 82. st. 6. | ne |

- **Ispravak uz `research/09` §2.1.** Redak "POVREMENI RAD - IMOVINA" nije paušal od iznajmljivanja turistima. Napomena na dnu lista `2025 EUR` kaže: "U kategoriji povremeni rad - imovina iskazani su iznosi uplaćenog poreza i prireza s osnove dohotka od najma i zakupa te dohotka od otuđenja nekretnina" [V].
- **Udjeli vrsta u porezu.** Nacionalno 2025. vrste koje plaćaju lokalnu stopu nose oko 84,5 % poreza: zaposlenici 74,9 %, obrt 4,8 %, umirovljenici 4,0 % i drugi dohodak 2,7 %. Kapital nosi 7,9 %, povremeni rad - imovina 4,4 %, paušalisti 1,1 % i imovina 0,2 %. U 124 jedinice ispod maksimuma porez po fiksnim stopama čini 13,9 % [V, izračun].

### 2.3 Niži i viši razred

Granice prema zakonu [V]:

| Godina | Godišnja granica | Mjesečna granica (predujam) | Izvor |
|---|---|---|---|
| 2024. | 50.400 € | 4.200 € | NN 114/23, čl. 8. i 11. (čl. 19. i 24. st. 3.) |
| 2025. i 2026. | 60.000 € | 5.000 € | NN 152/24, čl. 3. (čl. 19.) i pročišćeni čl. 24. st. 3. |

Udio poreza iz višeg razreda nije objavljen po jedinicama [N]. Procijenio sam ga iz drugog resursa istog skupa Porezne uprave, `dohodak-po-jls-i-razredima-2023-2024-3.xlsx`. Ta tablica daje broj obveznika ispod i iznad 50.400 € u 2024. [V].
- U 124 jedinice iznad granice je u medijanu 0,6 % obveznika, a najviše 2,3 % (Hvar).
- Na primjer, Samobor ima 19.344 obveznika ispod granice i 324 iznad nje (1,6 %).
- Uz lognormalnu raspodjelu dohotka viši razred nosi 1,4 % poreza po lokalnim stopama. Uz debeli rep (Pareto, α 3 do 1,6) nosi 2,3-7,5 % [P].

Viši razred zato gotovo ne mijenja procjenu. Ukupni iznos za jedinice kreće se između 88,3 i 89,4 mil. €, ovisno o pretpostavci. Razlog je što je razlika do maksimuma kod više stope obično relativno manja nego kod niže. Osijek, na primjer, ima 30 % prema 32 %, što je 6,7 % više, a 20 % prema 22 % je 10 % više. Iznimka je Rijeka 2026. (25 % prema 32 %): kod nje viši razred malo povećava iznos.

### 2.4 Koliko stvarno dođe u proračun jedinice

- Prihod od poreza na dohodak dijeli se po čl. 5. Zakona o financiranju JLP(R)S (vidi Q3). Kad Samobor podigne stopu, 74 % dodatnog poreza ide Samoboru, 20 % Zagrebačkoj županiji, a 6 % za decentralizirane funkcije [V].
- Na to se primjenjuju još dva umanjenja:
  - povrati iz godišnjeg obračuna, na primjer za mlade do 30 godina (čl. 46. st. 2.), koji su razmjerni stopi;
  - naknada Poreznoj upravi od 1 %.
- Sve to zajedno najbolje hvata vlastiti omjer jedinice p_611 / porez stanovnika. Za 124 jedinice je oko 0,69-0,72, a za Rijeku 0,717.
- **Važno za izravnanje [V]:** MF računa kapacitet uz najvišu stopu (`research/07`). Jedinica s nižom stopom zato ne dobiva izravnanje za porez koji sama ne naplaćuje. Neubrani porez nitko ne nadoknađuje.

### 2.5 Metoda i rezultat

Za jedinicu *i* (stope za 2026., porez stanovnika 2025.):

```
T_lok   = porez(zaposlenici + umirovljenici + obrt + drugi_dohodak)
h       = procijenjeni udio osnovice iznad 60.000 € (§2.3); drugi dohodak sav u nižem razredu
T_niži  = dio T_lok po nižoj stopi,  T_viši = dio po višoj stopi
F_bruto = T_niži × (niža_max / niža − 1) + T_viši × (viša_max / viša − 1)    (sve razine)
F_jed   = F_bruto × (p_611 / porez_ukupno)                                   (proračun jedinice)
```

| Varijanta | 124 jedinice, stope 2026. | 125 jedinica, stope 2025. |
|---|---|---|
| (a) cijeli porez × (max/niža − 1) | **149,6 mil. €** | 137,3 mil. € |
| (b) (a) × p_611/porez | **104,2 mil. €** | 95,2 mil. € |
| samo lokalne vrste, bez razreda, sve razine | 128,4 mil. € | 118,2 mil. € |
| lokalne vrste + razredi, sve razine (F_bruto) | 127,5 mil. € | 117,6 mil. € |
| **lokalne vrste + razredi, proračun jedinice (F_jed)** | **88,7 mil. €** | 81,5 mil. € |
| od toga županijama (20 % × 0,99 × (1 − povrati)) | 23,0 mil. € | 21,1 mil. € |

- **Raspon za F_jed: 74-91 mil. €** [P].
  - Gornja granica je najveći iznos među pretpostavkama o višem razredu.
  - Donja granica je najmanji iznos umanjen za 15 %. Tih 15 % je ponašajni učinak: viša stopa malo smanjuje prijavljeni dohodak, a dio ljudi prijavi prebivalište drugdje. Uz uobičajenu elastičnost oporezivog dohotka od 0,2 do 0,4 i povećanje od 2 postotna boda, osnovica padne oko 0,5-1 %. To smanjuje dodatni porez za oko 5-10 %. Seljenje prebivališta (Samobor i Sveta Nedelja uz Zagreb) ne mogu izmjeriti, pa sam dodao rezervu [P].
- **Razlika prema (a):**
  - 150 → 128 mil. €: izbacuju se kapital, najam i paušal, koji ne ovise o lokalnoj stopi;
  - 128 → 89 mil. €: jedinici ostaje oko 70 % poreza, a ostatak ide županiji, za decentralizirane funkcije, na povrate i na naknadu.
  - (b) primjenjuje dobar omjer na pogrešnu osnovicu, zato je 15 mil. € previsok.
- **Razlika prema (c), 88 mil. €.** Gotovo je jednako našem broju, a vrlo blizu su i dvije druge varijante: lokalne vrste × 0,74 × 0,99 × (1 − povrati) daju 85,2 mil. €, a plaće, mirovine i obrt × omjer daju 86,6 mil. €. Najvjerojatnije je ista ideja [P]. Metodu (c) nisam mogao vidjeti, pa ovo ostaje pretpostavka.
- **MF računa drukčije [V].** Za izravnanje MF množi cijeli porez s max/niža (stupci 46 i 50 u tablici za 2027.: `((porez − paušal) + BSJ × MI) / niža stopa × max niža stopa`). To je zakonska definicija kapaciteta, a ne procjena izgubljenog prihoda. Zato je (a) "MF-ov način", ali za priču o neubranom porezu precjenjuje.

**Deset jedinica s najvećim iznosom** (stope 2026., porez stanovnika 2025., mil. €; "po st." je € po stanovniku iz Popisa 2021.):

| Jedinica | Niža / max | Viša / max | Porez stanovnika | (a) | (b) | F_bruto | **F_jed** | raspon | po st. | udio u p_611 |
|---|---|---|---|---|---|---|---|---|---|---|
| Grad Rijeka | 20 / 22 | 25 / 32 | 138,39 | 13,84 | 9,92 | 12,54 | **9,43** | 7,4-9,9 | 87 € | 9,5 % |
| Grad Samobor | 18 / 22 | 27 / 32 | 51,33 | 11,41 | 8,18 | 9,57 | **6,80** | 5,7-6,9 | 182 € | 18,5 % |
| Grad Osijek | 20 / 22 | 30 / 32 | 102,85 | 10,28 | 7,33 | 9,06 | **6,37** | 5,4-6,5 | 66 € | 8,7 % |
| Grad Karlovac | 19 / 22 | 29 / 32 | 48,53 | 7,66 | 5,36 | 6,91 | **4,78** | 4,0-4,9 | 97 € | 14,1 % |
| Grad Velika Gorica | 20 / 22 | 30 / 32 | 74,36 | 7,44 | 5,33 | 6,63 | **4,70** | 4,0-4,8 | 77 € | 8,8 % |
| Grad Zadar | 20 / 22 | 30 / 32 | 72,29 | 7,23 | 5,12 | 6,13 | **4,29** | 3,6-4,4 | 61 € | 8,4 % |
| Grad Bjelovar | 18 / 22 | 25 / 32 | 27,99 | 6,22 | 4,31 | 5,58 | **3,90** | 3,3-3,9 | 107 € | 20,1 % |
| Grad Dubrovnik | 20 / 22 | 30 / 32 | 54,59 | 5,46 | 3,84 | 4,28 | **2,97** | 2,5-3,0 | 71 € | 7,7 % |
| Grad Sveta Nedelja | 18 / 21 | 28 / 31 | 25,60 | 4,27 | 2,93 | 3,70 | **2,49** | 2,1-2,6 | 137 € | 14,2 % |
| Grad Šibenik | 20 / 22 | 30 / 32 | 41,31 | 4,13 | 2,90 | 3,52 | **2,45** | 2,1-2,5 | 57 € | 8,4 % |

- Deset najvećih nosi 54 % ukupnog iznosa.
- 18 općina zajedno ima samo 2,8 mil. €. Najveće su Otok (0,45 mil. €), Punat i Baška.
- Medijan po stanovniku za svih 124 jedinica je 29 €.
- "Udio u p_611" pokazuje koliko bi porez na dohodak u proračunu porastao. Kod Samobora to je 18,5 %.

### 2.6 Preporuka za prikaz

**Prikazati, ali kao kontekst, ne kao slabost.**

- Gdje:
  - samo na profilu tih 124 jedinica, u bloku o prihodima;
  - ne u ocjeni, ne na karti i ne u usporedbi s medijanom skupine.
- Kojim brojem: F_jed, zaokružen na 0,1 mil. € (ili 10.000 € za male jedinice), s rasponom.
- Prijedlog teksta (primjer Samobor):

> **Niža stopa poreza.** Grad Samobor za 2026. naplaćuje porez na dohodak po stopama od 18 % i 27 %. Zakon mu dopušta do 22 % i 32 %. Uz najviše stope gradski proračun imao bi godišnje oko 6,8 milijuna eura više (procjena 5,7 do 6,9 milijuna). Još oko 1,7 milijuna eura dobila bi Zagrebačka županija. Niža stopa je odluka gradskog vijeća: stanovnici zato plaćaju manje poreza. Fiskalno izravnanje to ne nadoknađuje, jer MF kapacitet računa uz najvišu stopu.

- Uz tekst dodati bilješku: "Procjena: porez stanovnika 2025. (Porezna uprava), stope 2026., samo plaće, mirovine, obrt i drugi dohodak; kapital, najam i paušal plaćaju fiksnih 12 %."
- Za AI tekst brojke treba dati kao gotove nizove u paketu činjenica, kako bi ih verifikator prepoznao.
- Ne preporučujem riječi "gubi" ili "propušta". Bolje je "naplaćuje manje" ili "ostavlja građanima".

---

## 3. Q2. Najviše stope i razredi spojene jedinice

### 3.1 Zakon za 2025. i 2026. [V]

Zakon o porezu na dohodak, čl. 19.a st. 2., u tekstu iz NN 152/24 (čl. 4.), na snazi od 1.1.2025. Isti tekst stoji u pročišćenom tekstu na zakon.hr, ažuriranom do NN 119/26.

| Status | Niža stopa | Viša stopa |
|---|---|---|
| općina | 15-20 % | 25-30 % |
| grad | 15-21 % | 25-31 % |
| veliki grad i grad sjedište županije | 15-22 % | 25-32 % |
| Grad Zagreb | 15-23 % | 25-33 % |

- **Granica razreda [V]:** 60.000 € godišnje (čl. 19.), odnosno 5.000 € mjesečne osnovice za predujam (čl. 24. st. 3.).
- **Ako jedinica ne donese odluku [V]:** vrijede 20 % i 30 % (čl. 19.a st. 5.).
- **Veliki grad [V]:** Zakon o lokalnoj i područnoj (regionalnoj) samoupravi, čl. 19.a st. 1. Veliki gradovi su jedinice "koje su ujedno gospodarska, financijska, kulturna, zdravstvena, prometna i znanstvena središta razvitka šireg okruženja i koji imaju više od 35.000 stanovnika".
- **Za usporedbu, 2024. [V]:** NN 114/23, čl. 9., uveo je čl. 19.a s drugim klasama.
  - općina do 22 % i 33 %;
  - grad s manje od 30.000 stanovnika do 22,4 % i 33,6 %;
  - grad s više od 30.000 stanovnika do 23 % i 34,5 %;
  - Zagreb do 23,6 % i 35,4 %;
  - granica 50.400 €.
  - Tablica za 2027. ipak i godinu 2024. računa po maksimumu za 2025. (stupac "MAX NIŽA STOPA POREZA u 2025 godini", formula u stupcu 46), pa 2024. klase u izravnanju ne koristi.
- **Prirez za godine 2021.-2023. [V]:** Zakon o lokalnim porezima, NN 115/16, čl. 21. st. 1. Prirez je bio do 10 % za općinu, do 12 % za grad s manje od 30.000 stanovnika, do 15 % za grad s više od 30.000 stanovnika i do 18 % za Zagreb. Prirez je ukinut od 1.1.2024.

### 3.2 Što MF primjenjuje u tablici za 2027. [V]

- **Niža stopa:**
  - 428 općina ima 20 %;
  - 104 grada imaju 21 %;
  - 23 grada imaju 22 %: 8 sjedišta županija ispod 35.000 stanovnika (Pazin, Gospić, Krapina, Virovitica, Požega, Vukovar, Čakovec, Koprivnica) i 15 gradova iznad 35.000, od kojih tri nisu sjedišta (Samobor, Kaštela, Velika Gorica);
  - Zagreb ima 23 %.
  - Vinkovci (30.842 stanovnika, nisu sjedište) imaju 21 %.
  - To je točno pravilo iz čl. 19.a st. 2.
- **Prirez:**
  - 17 gradova ima 15 %. To je 16 gradova iznad 30.000 stanovnika i Koprivnica (28.580 stanovnika po Popisu 2021.; vjerojatno prema ranijem broju stanovnika [P]);
  - 110 gradova ima 12 %, općine 10 %, a Zagreb 18 %.

### 3.3 Naše pravilo i primjeri

`izravnanje.stope_spojene(clanice, je_grad)`, pozvano iz `za_spajanje` i iz `merge.equalization` (`vrsta == "grad"` ako je barem jedna članica grad):

- Spojena općina dobiva 20 % i prirez 10 %. To je ispravno, jer općina nema razrede po broju stanovnika [V].
- Spojeni grad dobiva najviše među gradovima članicama, a najmanje 21 % i 12 %. Ako zbroj stanovnika prijeđe 30.000, prirez je 15 %. Ako prijeđe 35.000, stopa je 22 %. To odgovara čl. 19.a st. 2. ZPD-a i čl. 21. ZLP-a [V]. Uvjet "više od" znači strogo veće, kao i u kodu.
- Ako je u spoju sjedište županije, spojeni grad ga sadrži, pa nasljeđuje 22 % kroz maksimum članica. Zakon o tome ništa posebno ne kaže, ali sjedište ostaje u spojenom gradu [P].

Rezultati `izravnanje.procjena` (tablica za 2027., puni iznos izravnanja):

| Spoj | Stanovnici | Stope spojene | Članice | Puni iznos prije → poslije | Ocjena |
|---|---|---|---|---|---|
| Jelenje + Viškovo (općine) | 21.180 | 20 %, prirez 10 % | obje 20 % i 10 % | 590.779 € → 16.902 € | ispravno: općina ostaje na 20 % bez obzira na veličinu; stope se ne preračunavaju, pad dolazi samo od Viškova iznad referentne vrijednosti |
| Ivankovo + Vinkovci (prijelaz 35.000) | 37.385 | 22 %, prirez 15 % | 20 %/10 % i 21 %/15 % | 7.140.978 € → 6.482.556 € | ispravno: spojeni grad bio bi veliki grad |
| Dugo Selo + Brckovljani + Rugvica (prijelaz 30.000) | 30.685 | 21 %, prirez 15 % | 21 %/12 %, 20 %/10 %, 20 %/10 % | 3.302.727 € → 1.983.351 € | ispravno: iznad 30.000 je prirez 15 %, a ispod 35.000 stopa 21 % |
| Pazin (sjedište Istarske) + Cerovlje | 9.732 | 22 %, prirez 12 % | 22 %/12 % i 20 %/10 % | 267.715 € → 0 € | ispravno: sjedište zadržava 22 %, a mali grad prirez 12 % |
| Gospić (sjedište Ličko-senjske) + Perušić | 13.475 | 22 %, prirez 12 % | 22 %/12 % i 20 %/10 % | 1.714.238 € → 1.642.840 € | ispravno |

### 3.4 Što promijeniti

U kodu ništa. Pravilo odgovara zakonu i MF-ovoj tablici. Predlažem samo ove izmjene dokumentacije (neka ih napravi onaj tko uređuje te datoteke):

1. `pipeline/izravnanje.py`, docstring `stope_spojene`: rečenicu "The class rules are read from the table, not the tax law" zamijeniti s "The classes follow Zakon o porezu na dohodak čl. 19.a st. 2. (NN 152/24; veliki grad = more than 35,000 inhabitants, ZLP(R)S čl. 19.a) and, for the surtax, Zakon o lokalnim porezima čl. 21. st. 1. (NN 115/16); the MF table applies the same classes (research/11 §3)".
2. `docs/research/07-fiskalno-izravnanje.md`, odjeljak "Ograničenja", stavka "Klase stopa": umjesto "nismo provjerili u službenom tekstu" napisati da je provjereno (ovaj dokument, §3.1-3.2).
3. `docs/research/09-portal-dodatni-izvori.md` §2.1: "povremeni rad - imovina" nije turistički paušal (§2.2 ovdje). Zagreb 0,942 nije 74 % + 20 %, nego 100 % umanjeno za povrate (§4.3).

Moguća rubna pitanja (ne greške):
- Spoj samo općina s više od 10.000 stanovnika po Zakonu o lokalnoj samoupravi mogao bi dobiti status grada. Tada bi bio na 21 % ili 22 %. Simulator ga po svom pravilu drži općinom, i uz to pravilo je 20 % ispravan.
- Status velikog grada zakon veže i uz to da je grad "središte razvitka šireg okruženja". MF ga u praksi daje po broju stanovnika (Kaštela, Samobor), pa je naše pravilo isto [V za MF].

---

## 4. Q3. Podjela poreza na dohodak između razina

### 4.1 Zakon [V]

Zakon o financiranju jedinica lokalne i područne (regionalne) samouprave, NN 127/17, 138/20, 151/22, 114/23:

| Odredba | Sadržaj | Izvor |
|---|---|---|
| čl. 5. st. 1. | Porez na dohodak je zajednički porez općina, gradova i županija. | NN 127/17 |
| čl. 5. st. 2. | Udio općine ili grada 74 %, udio županije 20 %, udio za decentralizirane funkcije 6 %. | NN 138/20, čl. 1., od 1.1.2021. (prije: 60/17/6, uz 17 % za izravnanje) |
| čl. 5. st. 3. | Decentralizirane funkcije: osnovno školstvo 1,9 %, srednje školstvo 1,3 %, socijalna skrb (domovi za starije) 0,8 %, zdravstvo 1,0 %, vatrogastvo (javne vatrogasne postrojbe) 1,0 %. Udio dobiva općina, grad, županija ili Grad Zagreb koji funkciju financira. | NN 151/22, čl. 1. |
| čl. 5. st. 4. | Porezna uprava zadržava naknadu od 1 % ukupno naplaćenih prihoda. | NN 114/23, čl. 1. |
| čl. 6. | Udio za nepreuzetu funkciju dijeli se na ostale preuzete funkcije na tom području. Vatrogasni 1 % ide samo za vatrogasnu mrežu. | NN 114/23, čl. 2. |
| čl. 7. | Podjela vrijedi za uplatu i za povrat poreza, bez obzira na godinu nastanka obveze. | NN 127/17 |
| ZPD čl. 1. st. 2.-3. | Porez pripada prema prebivalištu obveznika. Porez od najma i turističkog iznajmljivanja pripada prema mjestu nekretnine. | Zakon o porezu na dohodak |

- Fiskalno izravnanje od 2021. ide iz državnog proračuna, a ne iz poreza na dohodak (čl. 8.a, NN 138/20).
- Grad Zagreb ima položaj grada i županije, pa dobiva i gradski i županijski udio. Kad financira funkcije, dobiva i udio za njih [P za pravni temelj; podaci to potvrđuju, §4.3].

### 4.2 Kako se omjer raspada (2025.) [V, izračun]

U PR-RAS-u je konto 611 = 6111 do 6116 − 6117 − 6119. Konto 6117 su povrati po godišnjoj prijavi, a 6119 povrat više ostvarenog poreza za decentralizirane funkcije. Porezna uprava za plaće daje porez iz JOPPD-a, dakle porez obustavljen tijekom godine, prije godišnjeg obračuna. Napomena u tablici kaže i da "podaci nisu konačni".

Nacionalno, svih 576 jedinica zajedno (MF, `22.xlsx`, list "SVEUKUPNO OPĆ_GRAD_ŽUPANIJA"):

| | 2024. | 2025. |
|---|---|---|
| Porez stanovnika 556 općina i gradova (Porezna uprava) | 3.593,5 mil. € | 4.168,3 mil. € |
| Konto 611 svih jedinica (neto) | 3.329,2 mil. € (92,6 %) | 3.810,7 mil. € (91,4 %) |
| Konto 6117, povrati | 305,1 mil. € (8,5 %) | 376,1 mil. € (9,0 %) |
| 611 + 6117 + 6119 (prije povrata) | 101,1 % | 100,5 % |

Prije povrata jedinice dakle knjiže gotovo točno porez koji plate njihovi stanovnici. Razlika je mala:
- naknada Poreznoj upravi od 1 %;
- vremenski pomak: porez na prosinačku plaću uplaćuje se u siječnju, a porez stanovnika narastao je 16 % od 2024. do 2025.;
- uplate po godišnjoj prijavi (konto 6115, 87 mil. €).

Po vrsti jedinice (medijani 2025.):

| | Omjer 611 / porez | Prije povrata | Bez dodatnog udjela za funkcije | Povrati / bruto | Zakon |
|---|---|---|---|---|---|
| općine (428) | 0,631 | 0,725 | 0,724 | 9,9 % | 74 % × 0,99 = 73,3 % |
| gradovi (127, bez Zagreba) | 0,670 | 0,752 | 0,747 | 10,6 % | 73,3 % + udio za funkcije |
| županije (20) | 0,218 | 0,246 | 0,207 | 11,9 % | 20 % × 0,99 + udio za funkcije |
| Grad Zagreb | 0,942 | 1,017 | 0,96 | 7,4 % | 100 % × 0,99 |

Grubo: 0,74 × 0,99 × (1 − 0,10) ≈ 0,66, što je vrlo blizu opaženih 0,63 do 0,67.

- **Općine, primjer Bedenica:** 0,633. Plaćeni porez stanovnika je 1.056.516 €. Općina knjiži 668.348 €, a prije povrata 0,745, dakle 74 %.
- **Županije, 22 %:** 20 % plus dodatni udio za funkcije koje županija financira na području gradova koji ih nisu preuzeli. Konto "dio 611" iznosi 3,8 % poreza stanovnika županije, a uz to dolaze povrati. Raspon je mali: od 0,199 (Virovitičko-podravska) do 0,227 (Primorsko-goranska).
- **Zagreb, 94 %:** dobiva sve (74 + 20 + 6 %), a povrati iznose 7,4 % bruto iznosa. Iznos prije povrata (101,7 %) malo je veći od poreza stanovnika. Uzrok su vjerojatno vremenski pomak i porez od najma nekretnina u Zagrebu čiji vlasnici žive drugdje (ZPD čl. 1. st. 3.) [P].
- **Dodatni udio za decentralizirane funkcije:** "dio 611" je u proračunu 51 grada (medijan 2,6 % poreza stanovnika) i 36 općina (medijan 0,9 %, što je otprilike vatrogasni 1 %) [V].

### 4.3 Zašto jedinice odstupaju

- **Povrati po razvijenosti.** Općine I. skupine razvijenosti imaju medijan omjera 0,526, a VIII. skupine 0,691. Prije povrata razlike skoro nema (0,716 i 0,759).
  - Povrati su u I. skupini oko 26 % bruto iznosa. Mogući uzroci su 50 % umanjenja godišnjeg poreza za stanovnike I. skupine i Vukovara (ZPD čl. 46. st. 1.), olakšica za mlade (čl. 46. st. 2.) i olakšica za povratnike (čl. 46. st. 3.). Ta umanjenja se ostvaruju u godišnjem obračunu, kad ih poslodavac nije već primijenio u predujmu (čl. 24. st. 5.) [P].
- **Knjiženje.** 143 općine i 19 gradova imaju 6117 = 0 i sve knjiže na 6111. Primjeri su Čađavica, Kalnik i Drenovci. Povrate tada vjerojatno knjiže neto, pa se "prije povrata" za njih ne može izračunati [P].
- **Jake iznimke 2025.** (omjer izvan 0,45-0,85, 11 jedinica bez Zagreba):
  - nisko: Ervenik 0,40, Čađavica 0,40, Voćin 0,41, Kistanje 0,44, Sopje 0,44, Lokvičići 0,45. Sve su u I. skupini, s velikim povratima ili s neto knjiženjem [P];
  - visoko: Drenovci 1,55 (i 1,5-2,5 svake godine od 2022.), Smokvica 0,96, Otok (Splitsko-dalmatinska) 0,95 i Kalnik 0,87. Za Drenovce ne nalazim zakonski razlog. Vjerojatno se na 611 knjiži nešto što nije porez njihovih stanovnika. Predlažem oznaku kvalitete podataka [P].
- **Udio u razini.** U rasponu 0,55-0,71 je 81 % općina i gradova [V].

### 4.4 Je li omjer koristan korisniku?

Uglavnom nije. Omjer od oko 0,65 nije mjera uspjeha jedinice. To je zakonska podjela (74 %) umanjena za povrate. Povrati ovise o tome tko živi u jedinici (mladi, umirovljenici, I. skupina) i o tome kako jedinica knjiži.

- Preporuke:
  - ne prikazivati omjer kao pokazatelj;
  - zadržati ga kao dijagnostiku u `porezna.omjer_611`, uz oznaku kvalitete kad je izvan 0,45-0,85;
  - korisniku pokazati dva odvojena broja: "porez na dohodak koji plate stanovnici" (Porezna uprava) i "porez na dohodak u proračunu jedinice" (MF, konto 611), uz rečenicu "Jedinici zakonom pripada 74 % poreza na dohodak; 20 % ide županiji, 6 % za škole, bolnice, domove i vatrogasce, a povrati iz godišnjeg obračuna idu na teret svih razina."

---

## 5. Q4. Oznake DZS-a

### 5.1 Službeno značenje [V]

DZS, Statistička izvješća "Turizam u 2023." (br. 1731, Zagreb 2024., str. 6, "Kratice i znakovi"):

- **z**: "podatak zbog povjerljivosti nije objavljen"
- **-**: "nema pojave"
- **0**: "podatak je manji od 0,5 upotrijebljene mjerne jedinice"

Isti popis stoji u izdanju 1639/2019. Ono dodaje i **...**: "ne raspolaže se podatkom". DZS, Statističke informacije 2019. (str. 7, "Znakovi") daju i:
- **0,0** i **0,00**: manje od 0,05 ili 0,005 jedinice;
- **\***: ispravljeni podatak;
- **( )**: manje precizna procjena.

Pravila povjerljivosti ("Turizam u 2023.", metodološka objašnjenja, "Povjerljivost"): podaci kod kojih postoje razlozi za povjerljivost po Zakonu o službenoj statistici (NN 25/20) i Uredbi (EZ) br. 223/2009 "tretiraju se kao povjerljivi i stoga se ne objavljuju". Točan prag, na primjer broj objekata, nije objavljen [N].

### 5.2 Kako to izgleda u PxWebu [V]

- JSON-stat iz PxWeba (`data/raw/pxweb/*.json`, polje `status`) prenosi samo znak ("-" ili "z"), bez legende. U metapodacima tablica nema bilješke o znakovima [N].
- PX datoteka iste tablice (POST s `"format":"px"` na `BS_TU19.px`, 4.11.2026.) sadrži ključne riječi:

```
DATASYMBOL1="N"; DATASYMBOL2="-"; DATASYMBOL4="z"; DATASYMBOL5="A"; DATASYMBOL6="M"; DATASYMBOLSUM="S"; DATASYMBOLNIL="nil";
DATA= 19.00 123.00 455.00 19.00 "...." "...."  ".." ".." ".." ".." ".." ".."
```

- Po specifikaciji formata PX (Statistics Sweden, 2013., §3.3.23-3.3.24) pohranjene točke su mjesto za znak: "." je DATASYMBOL1, ".." je DATASYMBOL2 i tako do "......". DATASYMBOLNIL je pohranjeni "-", "apsolutna nula".
- DZS svoj "-" sprema kao ".." (DATASYMBOL2), a "z" kao "...." (DATASYMBOL4).
- **"." dakle nije znak DZS-a.** To je tehnički zapis za DATASYMBOL1, koji DZS prikazuje kao "N". Značenje tog "N" DZS ne objašnjava [N]. U našim podacima nema ni "." ni "N".
- U `dzs.parquet` nema nijedne numeričke nule. DZS prazne brojke uvijek označava znakom, a ne s 0 [V].

### 5.3 Naši podaci i primjeri [V]

`dzs.parquet` ima 1.410 "-" i 1.284 "z":
- "-": 397 × 3 kod turizma (postelje, dolasci, noćenja), 215 kod građevinskih dozvola i 4 kod rođenih (Civljane 2021. i 2023., Sućuraj 2024., Ribnik 2021.);
- "z": 642 × 2, samo kod dolazaka i noćenja, nikad kod postelja. Ima ih 208 jedinica, a "-" za turizam 111 jedinica.

Primjeri (tablica BS_TU19, "Dolasci i noćenja turista u komercijalnim smještajnim objektima"):

| Jedinica | Godina | Postelje | Dolasci | Noćenja | Značenje |
|---|---|---|---|---|---|
| Općina Vratišinec (Međimurska), HR062005045 | 2021.-2025. | - | - | - | nema komercijalnog smještaja ni turista: prava nula |
| Općina Kamanje (Karlovačka), HR020406238 | 2022. | 19 | 154 | 670 | objavljeno |
| | 2023. | 16 | z | z | turisti postoje, ali je broj skriven |
| | 2024. | 19 | 123 | 455 | objavljeno |
| | 2025. | 19 | z | z | skriveno |

Zaključak: pravilo u `pipeline/pxweb.py` (`NEMA = "-"` kao 0, `TAJNO = "z"` kao NaN) odgovara službenom značenju.
- Kamanje pokazuje zašto "z" ne smije postati 0: 2024. je imalo 123 dolaska.
- Vratišinec pokazuje da je "-" stvarno 0. Tablica pokriva samo komercijalni smještaj, pa "0 turista" znači 0 u registriranom smještaju.
- Za UI predlažem "nema (DZS: nema pojave)" i "podatak nije javan (DZS: povjerljivo)".

---

## 6. Izvori

Zakoni (Narodne novine i pročišćeni tekstovi):
- Zakon o porezu na dohodak, pročišćeni tekst (NN 115/16, 106/18, 121/19, 32/20, 138/20, 151/22, 114/23, 152/24), zakon.hr, preuzeto 4.11.2026.: https://www.zakon.hr/z/85/Zakon-o-porezu-na-dohodak (čl. 1., 19., 19.a, 24., 40., 46., 62., 70., 82.)
- Zakon o izmjenama i dopunama Zakona o porezu na dohodak, NN 152/24 (čl. 3., 4., 14.): https://narodne-novine.nn.hr/clanci/sluzbeni/2024_12_152_2505.html
- Zakon o izmjenama i dopunama Zakona o porezu na dohodak, NN 114/23 (čl. 8., 9., 11., 17.), tekst prema zakon.hr: https://www.zakon.hr/c/nn/58270/nn-114-2023-%284.10.2023.%29%2C-zakon-o-izmjenama-i-dopunama-zakona-o-porezu-na-dohodak (izvor: https://narodne-novine.nn.hr/clanci/sluzbeni/2023_10_114_1609.html)
- Zakon o financiranju JLP(R)S, NN 127/17 (čl. 4., 5., 7.): https://narodne-novine.nn.hr/clanci/sluzbeni/2017_12_127_2874.html
- Izmjene, NN 138/20 (čl. 5. st. 2.: 74/20/6 %; čl. 8.a): https://narodne-novine.nn.hr/clanci/sluzbeni/2020_12_138_2629.html
- Izmjene, NN 151/22 (čl. 5. st. 3.: udjeli funkcija): https://narodne-novine.nn.hr/clanci/sluzbeni/2022_12_151_2334.html
- Izmjene, NN 114/23 (čl. 5. st. 4.: naknada 1 %; čl. 6.; čl. 8.): https://narodne-novine.nn.hr/clanci/sluzbeni/2023_10_114_1617.html
- Pročišćeni tekst Zakona o financiranju JLP(R)S (sekundarni, za usporedbu): https://www.fiskai.hr/propisi/zakon-o-financiranju-jedinica-lokalne-i-podrucne-regionalne-samouprave/
- Zakon o lokalnim porezima, NN 115/16 (čl. 21., prirez): https://narodne-novine.nn.hr/clanci/sluzbeni/2016_12_115_2524.html
- Zakon o lokalnoj i područnoj (regionalnoj) samoupravi, pročišćeni tekst (čl. 19.a, veliki grad): https://www.zakon.hr/z/132/Zakon-o-lokalnoj-i-podru%C4%8Dnoj-(regionalnoj)-samoupravi

Podaci:
- Porezna uprava, "Neto dohodak stanovništva ... 2022.-2025." (napomena o vrstama dohotka na dnu lista): https://data.gov.hr/ckan/dataset/bdbde39b-18b5-47f5-9066-4d73c33b0fcf/resource/f0b05b72-fcab-4597-9e59-e172f90cf506/download/pk_neto-dohodak-stanovnistva-2022_2025-30_9_26-1.xlsx
- Porezna uprava, "Dohodak po JLS i razredima 2023.-2024." (broj obveznika ispod i iznad 47.780,28 € / 50.400 €): https://data.gov.hr/ckan/dataset/bdbde39b-18b5-47f5-9066-4d73c33b0fcf/resource/2f609d6a-0375-43a0-a66a-574c1b0d459d/download/dohodak-po-jls-i-razredima-2023-2024-3.xlsx
- Porezna uprava, usporedba stopa 2025./2026.: https://data.gov.hr/ckan/dataset/3c19c044-4cc4-42f1-ac97-29286a2bf305/resource/a33cb1d7-969f-498f-9e9d-0d6eddd9cd87/download/stope_poreza_na_dohodak_usporedba-2025-i-2026.xlsx
- MF, PR-RAS po jedinicama 2019.-2025. (`data/raw/mf/prras/01-22.xlsx`; konta 611, 6111-6119, "dio 611")
- MF, Tablica udjela za fiskalno izravnanje u 2027. (`data/raw/izravnanje/fi_2027.xlsx`; stupci 8-9, 46-55): https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava//Tablica%20udjela%20po%20JLP(R)S%20za%20fiskalno%20izravnanje%20u%202027.%20godini.xlsx

DZS i format PX:
- DZS, Statistička izvješća 1731, "Turizam u 2023." (str. 6 i metodološka objašnjenja): https://podaci.dzs.hr/2024/hr/79000
- DZS, Statistička izvješća 1639/2019., "Turizam u 2018.": https://web.dzs.hr/Hrv_Eng/publication/2019/SI-1639.pdf
- DZS, Statističke informacije 2019. (znakovi): https://podaci.dzs.hr/media/davje01x/statinfo2019.pdf
- DZS PxWeb, BS_TU19 (POST, `format: px`, 4.11.2026.): https://web.dzs.hr/PXWeb/api/v1/hr/Turizam/Dolasci%20i%20no%C4%87enja%20turista%20u%20komercijalnim%20smje%C5%A1tajnim%20objektima/BS_TU19.px
- Statistics Sweden, PX-file format specification 2013 (§3.3.23-3.3.24): https://scb.se/globalassets/vara-tjanster/px-programmen/PX-file_format_specification_2013.pdf
