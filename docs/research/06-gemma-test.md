# Gemma 4 na Kaggleu: test AI objašnjenja (3.11.2026.)

Cilj je bio provjeriti uvjet iz PLAN §5. Pitanje je prolazi li barem 80% Gemma tekstova provjeru brojki uz pristojan hrvatski. Ako ne prolazi, ide se na veći model ili na Claude.

## Postav

| | |
|---|---|
| Bilježnica | `albertmari/fiskalna-karta-jls-gemma-test` (privatna). Kod je `kaggle/gemma_runner.py`, a iz njega se generira `kaggle/gemma_test.py`. |
| Hardver | Kaggle, 2× Tesla T4 (koristi se jedna), CUDA 13.0 |
| Izvođenje | llama.cpp (commit `2cbca38`), izgrađen iz izvornog koda za sm_75, `llama-server --jinja`, temperatura 0,3, `enable_thinking: false` |
| Model (v2) | Gemma 4 E4B-it, QAT Q4_0 GGUF (`gemma-4-E4B_q4_0-it.gguf`, 5,2 GB), Kaggle Models, Apache-2.0 |
| Uzorak | 20 jedinica. Osam je fiksnih priča: Sveta Marija, Povljana, Senj, Primorski Dolac, Kloštar Podravski, Zagreb, Split i Istarska županija. Ostalih 12 su slučajne, raspoređene po svim ocjenama. |
| Provjera | `pipeline/verify.py`. Svaka brojka mora biti u paketu činjenica, a spomenuta ocjena mora biti stvarna. Ponavlja se najviše 2 puta. |

## v1 (3:07): pad pri izgradnji

CMake nije našao `CUDA::cuda_driver`, jer CUDA 13 na Kaggleu nema stub `libcuda` na putanji. Ispravak u v2: CMake dobiva sve direktorije sa stubovima, a ako to ne pomogne, gradi se s `-DGGML_CUDA_NO_VMM=ON`.

## v2 (3:12-3:43): E4B, prvi prompt

- **Provjeru brojki prošlo je 20/20 tekstova, sva iz prvog pokušaja.** Ukupno je bilo 5-13 brojki po tekstu.
- **Vrijeme:** izgradnja llama.cpp trajala je 1.757 s. Generiranje 20 tekstova trajalo je oko 2 minute, oko 6 s po tekstu.
- **Procjena za svih 576 jedinica:** oko 1 sat generiranja, plus izgradnja ako se binarna datoteka ne koristi ponovno.
- Sirovi izlaz je u `kaggle/results/gemma_test_v2_e4b.json`.

### Ocjena hrvatskog (Claude kao razvojni alat, PLAN §5)

| Vrsta problema | Primjeri | Udio tekstova |
|---|---|---|
| Nesklonjen ili pogrešno sklonjen naziv | "Grada Senj", "Grada Split", "Općine Sveta Marije", "za Općinu Povljana" | otprilike 9/20 |
| Slaganje u broju i padežu | "Najslabija sastavnica … su operativni saldo", "ostvaruje bod 14,7 od 100", "jedna od jake strana", "s medijanjom", "Nemaju upozorenja" | otprilike 10/20 |
| Sadržajno nespretne usporedbe | manjak od 20,6 % "u usporedbi s medijanom 13,3 %" (medijan je višak); Zagreb "jednak medijanu skupine" (skupina od jedne jedinice); dospjele obveze 2,7 % kao "jaka strana" uz medijan 1,0 % | 5/20 |
| Izostavljeno pravilo ili napomena | Povljana ne spominje gornju granicu ocjene zbog dospjelih obveza | 2/20 |

Bez ijedne greške je otprilike 6/20 tekstova. Tekstovi su razumljivi i točni u brojkama, ali "pristojan hrvatski" za objavu traži doradu.

### Uzroci i ispravci (v3)

Uzroci tri vrste problema bili su u paketu činjenica, ne u modelu. Ispravci su u `pipeline/facts.py`:
- Medijan se izriče istim riječima kao vrijednost jedinice, npr. "medijan skupine: višak 13,3 %".
- Grad Zagreb (skupina od jedne jedinice) više nema usporedbe s medijanom.
- Jaka strana mora biti iznad 90 bodova i ne smije biti lošija od medijana.
- Bodovi se pišu s pravom imenicom ("34,2 boda").

Ispravci u promptu (`pipeline/explain.py`):
- Naziv jedinice piše se samo u nominativu, kao subjekt rečenice, pa sklanjanja nema.
- Pravilo o slaganju navodi primjere.
- Zadan je redoslijed dijelova teksta.
- Dodan je jedan primjer teksta za izmišljenu jedinicu.

## v3 (od 3:46): A/B test E4B i 12B s ispravljenim paketom i promptom

U istoj sesiji vrte se oba modela (E4B, pa 12B QAT Q4_0, 7,2 GB) na istih 20 jedinica. Izgrađeni `llama-server` sprema se u izlaz bilježnice (`llama-bin/`), pa iduća pokretanja preskaču izgradnju od oko 30 minuta: dovoljno je bilježnicu priključiti kao izvor jezgre (kernel source).


### Rezultat v3 (završeno oko 4:25, obrađeno u 7:00)

- **Provjeru brojki prošlo je 20/20 tekstova u oba modela, iz prvog pokušaja.**
  - Lokalna provjera s novim, strožim verifikatorom isprva je javila 3 lažne greške kod 12B. Uzrok: iznos nakon riječi "ocjena" ("Ocjenu najviše spuštaju … 1.767.926 €") čitao se kao ocjena 1.
  - To je ispravljeno u `verify.py` i pokriveno regresijskim testom.
- **Vrijeme:** E4B 125 s za 20 tekstova (oko 6 s po tekstu), 12B 267 s (oko 13 s po tekstu). Izgradnja llama.cpp trajala je 1.972 s.
  - Procjena za svih 576 jedinica: E4B oko 1 sat, 12B oko 2,1 sata. Kvota je 30 sati tjedno.
- Sirovi izlaz je u `kaggle/results/gemma_test_v3_e4b_12b.json`.

| | E4B | 12B |
|---|---|---|
| Nazivi (nominativ) | ispravni u 20/20 | ispravni u 20/20 |
| Tekstova bez jezične greške | otprilike 10/20 | otprilike 10/20 |
| Tipične greške | slaganje ("sastavnica je dospjele obveze", "Jedne od jakih strana"); red riječi ("da u Bilanci je"); "koji nedostaje 5,2 %" | jedna sustavna greška: "Ocjenu najviše **spuštaju** operativni saldo" (glagol prepisan iz primjera, a subjekt je u jednini); "se neto dug mogao bi" |
| Sadržajne greške | 1: Zrinski Topolovac ima "jaku stranu: ovisnost o pomoćima", čega nema u činjenicama | 2: Šolta proglašava najslabijom drugu sastavnicu nego činjenice; Istarska navodi najslabiju sastavnicu koja nije označena |
| Potpunost | ponekad izostavi upozorenja ili pravilo | navodi sva upozorenja, pravilo i napomenu, ali često prelazi 110 riječi i ponavlja napomenu o "razdoblju" |

**Ocjena prema pravilu iz PLAN §5** (barem 80% tekstova prolazi provjeru uz pristojan hrvatski):
- provjeru brojki prolazi 100%;
- pristojan hrvatski bez greške ima oko 50% tekstova. **Prag od 80% zasad nije dosegnut.**

Nijedan model nije zabludio u brojkama. Greške su većinom sustavne i dolaze iz prompta (oblik glagola iz primjera, pretjerano opisivanje razdoblja), pa se popravljaju promptom, a ne većim modelom.

### v4 (pokrenut u 7:03, bilježnica `albertmari/fiskalna-karta-jls-gemma-ab`)

Promjene:
- **Prompt:**
  - najslabija sastavnica uvodi se fiksnom frazom "Ocjenu najviše spušta sastavnica „…”" (slaganje ne ovisi o broju);
  - jake strane uvode se frazom "Jake strane jedinice su: …";
  - izričita zabrana proglašavanja konteksta (pomoći, uprava) jakom ili slabom stranom;
  - najviše 100 riječi;
  - upozorenja u najviše dvije rečenice.
- **Činjenice:** uklonjena je stavka "Razdoblje" (prozor se vidi na profilu).
- **Izvođenje:** bilježnica kao kernel source koristi već izgrađeni `llama-server` iz test bilježnice, pa se llama.cpp ne gradi ponovno.

**Preporuka za odluku u srijedu navečer:**
1. Ako v4 doseže barem 80% pristojnih tekstova, uzeti **12B**. Potpuniji je, a 2 sata GPU-a za 576 jedinica je prihvatljivo. E4B je rezerva ako se 12B pokaže sporim.
2. Ako v4 ne dosegne prag, sljedeći je korak iz PLAN §5 Gemma 4 26B-A4B (MoE, 2× T4). Claude u batch načinu dolazi tek nakon toga, uz navođenje kao AI alata.
3. U oba slučaja dodati jeftinu automatsku provjeru sadržaja: tekst smije proglasiti najslabijom samo sastavnicu iz činjenica, a jakom samo navedene jake strane. Fiksne fraze iz prompta čine tu provjeru jednostavnom.

### Rezultat v4 (7:03-7:10)

- Llama.cpp se ponovno koristio iz cachea, pa je cijeli run trajao 364 s.
- Provjeru brojki oba modela prolaze 20/20.
- **12B:** gramatika je sada uglavnom čista. Iz primjera u promptu model je naučio sadržajno krivu rečenicu "zbog prenesenog manjka ocjena je ograničena" (8/20).
- **E4B:** lošiji je ("kućne pomoći", "Bilancije", prazne rečenice o izvoru podataka).
- **Provjera sadržaja** dodana je u `verify.py`. Tekst smije spomenuti ograničenje ocjene samo uz pravilo 2, a najslabiju sastavnicu i jake strane samo kako ih navode činjenice. Na tekstovima iz v4 hvata 13/20 kod 12B i 10/20 kod E4B, upravo one koje sam ručno označio.
- Iz činjenica je izbačen kontekst (pomoći, trošak uprave), zajedno s praznom stavkom "nijedna sastavnica nije izrazito jaka".

### Rezultat v5 (7:13, puna provjera: brojke, ocjena i sadržaj)

| | E4B | 12B |
|---|---|---|
| Prolazi provjeru (uz najviše 2 ponavljanja) | 10/20 | **17/20 (85 %)** |
| Vrijeme za 20 tekstova | 175 s | 283 s |
| Duljina | | 32-109 riječi, prosječno 75 |

12B, ručni pregled:
- 17 tekstova koji su prošli provjeru pisani su ispravnim, iako šablonskim hrvatskim. Gramatičkih grešaka više ne nalazim.
- Tri koja nisu prošla provjeru idu na predložak:
  - Istarska županija i Sveti Križ Začretje imenuju najslabiju sastavnicu kad je u činjenicama nije bilo (sve sastavnice iznad 80 bodova). Rješenje: činjenice sada uvijek navode sastavnicu koja ocjenu najviše spušta, jer je to točno i kod visoke ocjene.
  - Dubravica je izmislila jaku stranu. Provjera je to ispravno odbila.

**Preporuka za odluku u srijedu navečer:** **Gemma 4 12B** (QAT Q4_0, llama.cpp na T4).
- Prema PLAN §5 prag od 80% je dosegnut, i to sa strožom provjerom nego što plan traži (brojke i sadržaj).
- Trošak: za svih 576 jedinica oko 2,3 sata GPU-a, s ponavljanjima.
- Tekstovi koji ne prođu provjeru dobivaju predložak i jasnu oznaku na profilu.
- Prije batcha treba ponoviti test na novih 20 jedinica, s istim pragom, da se izbjegne prilagodba prompta baš ovom uzorku.

Sirovi izlazi: `kaggle/results/gemma_test_v4_e4b_12b.json` i `gemma_test_v5_e4b_12b.json`.

## v6 (3.11. 22:59-23:24): 20 novih jedinica, 12B, 26B-A4B i 31B

Ovo je potvrdni test W5 iz `docs/plan-srijeda-4-11.md`, proširen na veće modele. Pitanje je bilo isplati li se za batch od 576 jedinica uzeti veći model, kad je ostalo 28 h GPU kvote.

**Postav:**
- Bilježnica je `albertmari/fiskalna-karta-jls-gemma-v6` (privatna).
- 20 jedinica nije bilo ni u jednom ranijem testu (`--fresh`, seed 11), po 4 za svaku ocjenu. Među njima su dvojezični istarski nazivi i jedna županija.
- Prompt, činjenice i provjera su isti kao u v5.
- Izvodi se na 2× T4 s llama.cpp `2cbca38` iz predmemorije. Model veći od jedne T4 dijeli se po slojevima na obje kartice.
- Cijela sesija trajala je 1.268 s, odnosno 0,36 h kvote.

| | 12B | 26B-A4B (MoE) | 31B |
|---|---|---|---|
| GGUF | 7,0 GB | 14,4 GB | 17,7 GB |
| VRAM (GPU0 + GPU1) | 3,7 + 4,2 GB | 7,6 + 7,3 GB | 9,5 + 10,0 GB |
| Učitavanje | 66 s | 144 s | 222 s |
| **Prošlo punu provjeru** | **18/20** | **10/20** | **20/20** |
| Iz prvog pokušaja | 17/20 | 9/20 | 20/20 |
| s po tekstu (s ponavljanjima) | 10,2 | 8,9 | 21,9 |
| Generiranje | oko 20 tok/s | oko 38 tok/s | oko 11 tok/s |
| Procjena za 576 jedinica | oko 1,7 h | oko 1,5 h | **oko 3,6 h** |

Nalazi:
- **31B prolazi 20/20 iz prvog pokušaja.**
  - Uvijek navodi godinu i medijan skupine za ukupne bodove, a uz medijan piše i mjernu jedinicu ("uz medijan skupine od 1,7 % tekućih prihoda").
  - Kad u činjenicama nema jakih strana, ne izmišlja ih.
  - Jedina nespretnost je "uz medijan skupine od viška 13,3 %" (Motovun).
- **12B ima 18/20.**
  - Oba pada su izmišljene jake strane (Sveti Petar u Šumi, Benkovac), a provjera ih je ispravno odbila.
  - Sitnice: "Upozorenje:" u jednini ispred više stavki, izostavljena godina i medijan ukupnih bodova, "dok u skupini ostaje 10,8 %" uz jedinicu koja ima manjak.
- **26B-A4B ima 10/20 i nije upotrebljiv s ovim promptom.**
  - Izmišlja jake strane i piše "neplaćane" umjesto "neplaćene".
  - Na povratnu informaciju ponavlja istu grešku u sva tri pokušaja. MoE s oko 4B aktivnih parametara slijedi upute kao mali model.
- **Jezična razlika 12B i 31B je mala**, jer prompt traži fiksne fraze. Oba teksta su ispravna, ali šablonska. Veći model zato donosi točnost i manje predložaka, a ne prirodniji stil.
  - Ako želimo prirodniji tekst, treba olabaviti fiksne fraze. To vjerojatno može samo 31B, a traži još jedan test.

**Preporuka:** batch radi **31B**. Uz 100 % prolaza iz prvog pokušaja gotovo nijedna jedinica ne dobiva predložak. Trošak je oko 3,6 h od 28,2 h preostale kvote, uz novih 30 h u subotu 7.11. 12B ostaje rezerva (oko 1,7 h).

Sirovi izlaz: `kaggle/results/gemma_test_v6_12b_26b_31b.json`.

## v7 (4.11. oko 0:10-0:30): 31B, Q4_0 s Kaggla prema Unsloth UD-Q4_K_XL

**Zašto ovaj test:**
- Istraživanje drugih modela nije našlo nijedan otvoreni model koji stane na 2× T4 i koji bi bio jasno bolji od Gemme 4 31B za hrvatski. Prema EuroEvalu najbliži su Qwen3.6-27B i Qwen3.8-27B, izjednačeni s Gemmom na gramatičnosti.
- Unsloth je izmjerio da Q4_0 s Kaggla (17,65 GB) kod 31B odstupa od nekvantiziranog QAT modela (top-1 87,9 %, KLD 0,093). Njegov `UD-Q4_K_XL` iste veličine odstupa znatno manje (96,7 %, KLD 0,014), prema unsloth.ai/docs/models/gemma-4/qat.
- Zato smo testirali istu Gemmu u boljoj kvantizaciji.

**Postav:**
- Bilježnica je `albertmari/fiskalna-karta-jls-gemma-v7`.
- 20 novih jedinica (`--fresh`), bez preklapanja s v2-v6.
- `UD-Q4_K_XL` (Apache-2.0, `unsloth/gemma-4-31B-it-qat-GGUF`) preuzima se u sesiji s Hugging Facea (`--hf`). Preuzimanje 17,3 GB trajalo je 172 s.
- Sesija je trajala 1.223 s, odnosno 0,34 h kvote.

| | 31B Q4_0 (Kaggle Models) | 31B UD-Q4_K_XL (Unsloth, HF) |
|---|---|---|
| Prošlo punu provjeru | 20/20 | 20/20 |
| Iz prvog pokušaja | 20/20 | 20/20 |
| s po tekstu | 20,7 | 20,3 |
| Učitavanje | 146 s | 76 s (+172 s preuzimanje) |

**Tekstovi su gotovo isti.**
- 15/20 identičnih.
- U ostalih 5 razlikuje se samo interpunkcija (zarez prema točki sa zarezom ili "te") i to je li navedeno "za 2025. godinu".
- S ovim promptom kvantizacija ne mijenja rezultat.
- **31B Q4_0 je ukupno 40/40 na jedinicama koje nije vidio** (v6 i v7).

**Preporuka:** batch radi **31B Q4_0 s Kaggle Models**.
- Službeni je izvor, priključuje se kao model i ne treba ga preuzimati, a kvaliteta je u praksi ista.
- `UD-Q4_K_XL` ima smisla tek ako se prompt olabavi radi prirodnijeg stila, jer tada model ima više slobode, pa preciznost više vrijedi.

Sirovi izlaz: `kaggle/results/gemma_test_v7_31b_q4_0_ud.json`.

## v8: batch 576 (4.11. 1:53-5:23, noćna smjena)

**Postav:**
- Bilježnica `albertmari/fiskalna-karta-jls-gemma-batch`, Gemma 4 31B-it QAT Q4_0 s Kaggle Models (`gemma-4-31B_q4_0-it.gguf`), llama.cpp `2cbca38` iz predmemorije, 2× T4.
- Prompt, činjenice i provjera su isti kao u v6 i v7 (sha256 prompta `1af71adc…`), a paketi svih 576 jedinica su za 2025. (`data/ai/manifest-2025.json`).
- Sesija je trajala 12.527 s (3,48 h kvote; učitavanje modela 184 s), oko 21,7 s po tekstu. Pogrešaka servera nije bilo.
- Sirovi izlaz: `kaggle/results/gemma_batch_2025_31b_q4_0.json`; uvezeno u `data/ai/objasnjenja-2025.json`.

**Rezultat:**

| | |
|---|---|
| Prošlo punu provjeru iz prvog pokušaja | 561/576 |
| **Prošlo nakon najviše 2 ponavljanja (AI tekst na profilu)** | **565/576 (98,1 %)** |
| Predložak s oznakom | 11 |

**Svih 11 padova je lažna uzbuna provjere, ne greška modela.**
- Tekstovi su ispravni, npr. Gradec: "Ocjenu najviše spušta sastavnica „servis duga”: otplata kredita i kamata iznosi 2,2 % zakonske osnovice, uz medijan skupine 3,8 % …".
- `verify.claimed_grades` iza riječi "ocjen…" gleda samo 120 znakova. Kad prozor presiječe "3,8" iza trojke, ostaje samostalno "3" i čita se kao navedena ocjena ("ocjena 3"), a ta nije stvarna.
- Pogođene su Gradec, Breznica, Kostrena, Lovran, Galovac, Bilje, Petrijevci, Pirovac, Fažana, Raša i Orehovica: sve imaju ocjenu 5 i medijan servisa duga od 3,8 %.
- `verify.py` je zamrznut do kraja smjene, pa ispravak (prozor do kraja rečenice, ne 120 znakova) ide kao odluka za korisnika (`docs/noc-4-11.md`).

**Ručni pregled 20 nasumičnih AI tekstova** (seed 2026):
- **Jezik:** svih 20 je gramatički ispravno; nazivi su u nominativu, a slaganje je točno. Stil je šablonski, kako prompt traži, s 48-95 riječi.
- **Sadržaj:** svih 20 se slaže s paketom: najslabija sastavnica, jake strane, upozorenja i napomena o kreditu (Drnje). Nijedan ne izmišlja jaku stranu.
- **Tri ponovljene nespretnosti:**
  1. Medijanu se izgubi riječ predznaka. Primjer: "nakon otplate glavnice kredita nedostaje 12,2 % tekućih prihoda, uz medijan skupine od 16,9 % tekućih prihoda" (Dugopolje, Pušća), a u paketu stoji "medijan skupine: ostaje 16,9 %". Pogađa 2/20.
  2. "uz medijan skupine od viška 20,0 % tekućih prihoda" (Netretić, Bošnjaci, Donji Miholjac), kao u v6 kod Motovuna. Pogađa 3/20.
  3. "Ocjenu najviše spušta sastavnica „operativni saldo”", a ista je sastavnica navedena i kao jaka strana (Netretić sa 100 bodova, Donji Miholjac). To dolazi iz paketa: od v5 paket uvijek imenuje najslabiju sastavnicu, i kad su sve iznad 90 bodova. Pogađa 3/20.
- **Prijedlog** (zahtijeva promjenu činjenica i prompta, pa ponovni batch od oko 3,5 h): kad je najslabija sastavnica iznad 90 bodova, paket i prompt neka kažu "Najniže bodove ima sastavnica …", a medijan neka se uvijek prepiše s riječju predznaka. Odluka je na korisniku.

**Na profilu:** oznaka je "AI tekst · Gemma 4 31B · 11/11 brojki provjereno" (Povljana). Klik na "1.045.908 €" otvara izračun dospjelih obveza s ćelijama Bilance.
