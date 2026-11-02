# Validacija podataka i metodologije (eksploracija, 2.11.2026.)

Eksploratorni izračun nad podacima Ministarstva financija (PR-RAS, RAS-funkcijski i Bilanca 2019.-2025.) i DZS-ovim Popisom 2021. Svrha je bila provjeriti pretpostavke plana prije konačne metodologije. Ovo nisu rezultati proizvoda.

Skripta: `pipeline/build.py` (skica). Izlaz je u scratchpadu, nije u repozitoriju.

## 1. Povezivanje izvora

- Svih **576 jedinica** povezano je u tri izvora: PR-RAS (list po jedinici), Bilanca (OIB, RKP) i Popis 2021.
- U prvom prolazu nije se povezalo 24 jedinice. Razlozi su bili dvojezični istarski nazivi (`BUJE-BUIE` i `BUJE – BUIE`), kratica `SV.`, oznaka `ZADARSKI`, naziv `VINODOLSKA OPĆINA` te Grad Zagreb, kojeg DZS vodi samo kao županiju. Sve je riješeno pravilom za uparivanje naziva (`match_key`).
- Za trajno rješenje glavni ključ bi trebao biti OIB iz Bilance i službena šifra iz MPUDT-ova popisa JLS, a ne naziv.

## 2. Točnost u odnosu na zbirne podatke Ministarstva financija

- Zbroj prihoda poslovanja (6) i rashoda poslovanja (3) po jedinicama **poklapa se do eura** sa zbirnom tablicom Ministarstva financija za 2019. i 2025.
- Zbroj stanovnika svih općina i gradova je 3.871.833, isto koliko DZS navodi za RH.
- **Zbirni podaci Ministarstva financija za funkcijsku klasifikaciju u 2025. su nepotpuni.** Kontrolni zbroj im je 0,79 mlrd. €, a u 2024. bio je 4,92 mlrd. €. Naš zbroj funkcije 01 po jedinicama (1,20 mlrd. €) je uvjerljiv. Zato se kontrola mora raditi po jedinicama: zbroj funkcija treba biti jednak rashodima 3 + 4.

## 3. Dostupnost i kvaliteta polja

- Prihodi i funkcija 01 postoje za sve jedinice. Funkcija 01 nedostaje u 0 do 2 jedinice godišnje, a broj zaposlenih (Z006) u 0 do 2.
- **Dospjele obveze** (`dio 23 D`, `dio 26 D`) postoje u Bilanci **samo za 2025.** Za 2019.-2024. treba drugi izvor (obrazac Obveze Ministarstva financija) ili se pokazatelj koristi samo za zadnju godinu.
- Obveze za kredite: između 131 i 289 jedinica godišnje nema nikakav dug.

## 4. Kapitalne pomoći moraju izaći iz tekućih prihoda

Prihodi poslovanja (6) uključuju kapitalne pomoći za EU i druge projekte (6312, 6322, 6324, 6332, 6342, 6352, 6362, 6382, 6632). Ako ostanu unutra, operativni saldo je napuhan.

| | Uključene kapitalne pomoći | Isključene (kao KDZ) |
|---|---|---|
| Medijan operativnog salda općina (prosjek 2023.-2025.) | 31,6% | 17,1% |
| Općine s ocjenom 1 / 2 / 3 / 4 / 5 | 296 / 106 / 18 / 7 / 1 | 186 / 127 / 61 / 50 / 4 |
| Gradovi s ocjenom 1 / 2 / 3 / 4 / 5 | 82 / 35 / 8 / 3 / 0 | 40 / 36 / 32 / 20 / 0 |

Primjer, Donji Lapac 2025.: 554 tisuće € kapitalnih pomoći (6332) od 1,26 mil. € ukupnih pomoći.

**Zaključak:** tekući prihodi računaju se kao 6 umanjeno za kapitalne pomoći i donacije. Austrijski pragovi i dalje daju razmjerno blagu razdiobu, pa pragove treba kalibrirati na hrvatske podatke (vidi `01-metode-financijskog-zdravlja.md`).

## 5. Stabilnost ocjene

Uz isključene kapitalne pomoći, ocjena za jednu godinu mijenja se kod **40-62% jedinica** iz godine u godinu. Za jednu godinu ocjena je previše "šumna". Odluke:
- Ocjena se računa iz **trogodišnjih zbrojeva tokova** (npr. 2023.-2025.) i stanja na kraju zadnje godine. Prosjek godišnjih omjera se ne koristi.
- "Godine otplate" su nedefinirane kad je operativni saldo ≤ 0, a postoji dug. Tada se daju izravno 5 bodova i oznaka. Takvo stanje ne smije ulaziti u prosjek kao "beskonačno".

## 6. Županije

Medijan operativnog salda županija je oko 0%, jer županije financiraju decentralizirane funkcije (škole, bolnice). S istim pragovima izgledaju loše. Zato županije čine zasebnu skupinu s vlastitim pragovima ili relativnom ocjenom.

## 7. Ekonomija razmjera (osnova simulatora spajanja)

Trošak administracije po stanovniku (funkcija 01 podijeljena sa stanovnicima Popisa 2021.), općine i gradovi bez Zagreba, prosjek 2023.-2025.:

| Razred veličine | Broj jedinica | Medijan €/stanovniku | P25-P75 | Djelatnici u upravi na 1.000 st. |
|---|---|---|---|---|
| < 1.000 | 55 | 390 | 281-503 | 9,3 |
| 1.000-2.500 | 210 | 229 | 185-314 | 5,8 |
| 2.500-5.000 | 155 | 196 | 144-280 | 4,1 |
| 5.000-10.000 | 73 | 168 | 136-238 | 3,5 |
| 10.000-35.000 | 47 | 160 | 118-230 | 3,4 |
| > 35.000 | 15 | 149 | 123-189 | 2,7 |

- Elasticitet troška administracije po stanovniku prema broju stanovnika: **−0,23** za sve jedinice (R² = 0,15), **−0,41 samo za općine**, −0,24 za gradove. Ekonomija razmjera postoji, ali je **koncentrirana ispod oko 5.000 stanovnika**, a raspršenost je velika.
- Red veličine: 265 jedinica ispod 2.500 stanovnika (402 tisuće stanovnika) troši 114 mil. € godišnje na opće javne usluge. Kad bi trošile kao medijan razreda 2.500-5.000, razlika bi bila oko **41 mil. € godišnje**. To je gornja granica razlike u trošku, a ne procjena ušteda: prijelazni troškovi, različito knjiženje i usluge na terenu tu nisu uračunati.
- **Zaključak:** modul procjene ušteda ima uporište u podacima, ali ga treba prikazati kao raspon i uz kontrolu strukturnih razlika (površina, broj naselja, otoci, turizam).

## 8. Ovisnost o pomoćima

- 166 od 428 općina (39%) i 19 od 128 gradova dobiva više od 50% prihoda poslovanja iz pomoći (prosjek 2023.-2025.). Taj udio uključuje i kapitalne projektne pomoći.
- Strukturnu ovisnost bolje mjeri **udio tekućih pomoći**, uključujući fiskalno izravnanje, u tekućim prihodima. Taj pokazatelj je dodan.

## 9. Crvene zastavice (prosjek 2023.-2025.)

- 29 jedinica ima teret otplate (kamate i glavnica) veći od 20% tekućih prihoda. To nije isto što i zakonsko ograničenje, koje se računa drugačije.
- 33 jedinice imaju dospjele obveze veće od 7% rashoda poslovanja (podatak samo za 2025.).
