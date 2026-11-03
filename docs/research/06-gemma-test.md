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

Rezultat: *dopisuje zakazani zadatak u 7:00.*
