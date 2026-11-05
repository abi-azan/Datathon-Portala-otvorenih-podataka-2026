# MCP server "Fiskalna karta"

MCP (Model Context Protocol) je otvoreni standard kojim AI asistent poziva vanjske alate.
Naš server daje asistentu šest alata nad statičnim API-jem Fiskalne karte.
Asistent tako odgovara na pitanja o općinama, gradovima i županijama našim brojkama, uz poveznicu na izvor.

Server samo čita. Ne računa nove brojke: vraća polja iz API-ja i poveznice na stranicu i na izvornu datoteku.
Kratko rečeno: DCAT je za portale, MCP je za AI asistente.

## Što server radi

| Alat | Što vraća |
|---|---|
| `pronadi_jedinicu(naziv, zupanija=None)` | Pretraga po nazivu bez dijakritika ("osijek", "dakovo"). Slug, naziv, vrsta, županija, šifra DGU, ocjena i bodovi. |
| `pregled_jedinice(jedinica, godina=None)` | Ocjena 1-5, bodovi, sastavnice I1-I5 s medijanom skupine, rang u skupini, zastavice, kontekst (stanovništvo, dohodak, izravnanje, revizija DUR-a), objašnjenje s oznakom "AI tekst" ili "predložak", poveznice. |
| `usporedi(jedinice, godina=None)` | 2-5 jedinica jedna uz drugu, uz medijane njihovih skupina. |
| `scenarij_spajanja(jedinice)` | Simulator spajanja za 2-4 susjedne jedinice iste županije: prije i poslije, raspon uštede na upravi, izravnanje, poticaj, demografija. Za nevaljanu kombinaciju vraća poruku zašto. |
| `karta_reforme(prag, jedinica=None)` | Karta reforme za prag 2.500, 5.000 ili 10.000 stanovnika: broj jedinica prije i poslije, ušteda, poticaj, izravnanje. Uz jedinicu i njezina spojena skupina. |
| `izvor_brojke(jedinica, pokazatelj)` | Formula pokazatelja i svaki ulaz s kontom, iznosom, datotekom, listom i retkom u izvještajima Ministarstva financija. |

Uz alate postoji resurs `fiskalna://metodologija` (sadržaj `metodologija.json`).

Jedinica se zadaje slugom (`opcina-povljana`), nazivom (`Povljana`), šifrom DGU (`05738`, županije `Z01`-`Z20`) ili OIB-om.
Kad naziv nosi više jedinica (Privlaka, Otok, Sveta Nedelja), alat vraća popis kandidata.
Popis jedinica za spajanje i usporedbu može biti lista ili jedan tekst sa zarezima, npr. `"05738,03166"`.

Pogrešan upit ne ruši server. Alat vraća objekt s poljem `greska`, npr. kad jedinice nisu iz iste županije.

## Pokretanje

```
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m fiskalna_mcp                            # javni API
.venv/Scripts/python -m fiskalna_mcp --api web/public/api/v1    # lokalni API, bez mreže
```

- Transport je stdio: server čita i piše na standardni ulaz i izlaz, pa ga pokreće MCP klijent.
- Zadani API je `https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/api/v1/`.
- `--api` prima URL ili mapu. Mapa `web/public/api/v1` nastaje naredbom `python -m pipeline.publish`.
- `--timeout` je vremensko ograničenje upita prema API-ju u sekundama (zadano 20).
- Svaka datoteka čita se jednom i drži u memoriji dok server radi.
- Poveznice u odgovorima uvijek vode na javnu stranicu i javni API, i kad server čita lokalnu mapu.
- Polje koje stariji API nema (npr. kontekst ili izravnanje) vraća se kao `null`.

Tehnika: službeni MCP Python SDK `mcp==2.3.0` (MIT), klasa `MCPServer` (u SDK-u 1.x zvala se FastMCP).
Paket se zove `fiskalna_mcp`, a ne `mcp`, jer bi `mcp/` zasjenio SDK pri importu.
Kod je u `fiskalna_mcp/`: `api.py` čita API, `tools.py` sadrži logiku alata, `server.py` ih prijavljuje kao MCP alate.

## Spajanje s AI asistentom

### Claude Desktop

U `claude_desktop_config.json` (Settings > Developer > Edit Config) dodajte server.
Putanje su primjer; zamijenite ih putanjom do svoje kopije repozitorija.
`PYTHONPATH` je potreban jer paket nije instaliran, pa ga Python traži u mapi repozitorija.

```json
{
  "mcpServers": {
    "fiskalna-karta": {
      "command": "C:\\Users\\ime\\datathon\\.venv\\Scripts\\python.exe",
      "args": ["-m", "fiskalna_mcp"],
      "env": { "PYTHONPATH": "C:\\Users\\ime\\datathon" }
    }
  }
}
```

Za rad bez mreže dodajte u `args` još `"--api", "C:\\Users\\ime\\datathon\\web\\public\\api\\v1"`.

### Claude Code

U mapi repozitorija:

```
claude mcp add fiskalna-karta -- .venv/Scripts/python -m fiskalna_mcp
```

### MCP Inspector

MCP Inspector je službeni alat za provjeru MCP servera (`@modelcontextprotocol/inspector` 2.13.0, licenca Apache-2.0, a stariji doprinosi MIT; traži Node 22.19 ili noviji).
Web sučelje:

```
npx @modelcontextprotocol/inspector .venv/Scripts/python -m fiskalna_mcp --api web/public/api/v1
```

Isto iz naredbenog retka, bez preglednika:

```
npx @modelcontextprotocol/inspector --cli .venv/Scripts/python -m fiskalna_mcp --api web/public/api/v1 --method tools/list
npx @modelcontextprotocol/inspector --cli .venv/Scripts/python -m fiskalna_mcp --api web/public/api/v1 --method tools/call --tool-name pronadi_jedinicu --tool-arg naziv=povljana
```

Naredbe se pokreću iz mape repozitorija. Inspector pokreće server kao podproces.
Provjera `--method tools/list --strict` ne prijavljuje nijedan problem sa shemama alata.

## Testovi

```
.venv/Scripts/python -m pytest -q tests/test_mcp.py
```

Testovi koriste klijent iz SDK-a u memoriji (`mcp.Client(server)`) nad lokalnim API-jem.
Provjeravaju popis alata, Povljanu (ocjena 2, 39,9 bodova za 2025.), spajanje Paga i Povljane (ocjena 5), nevaljane kombinacije (poruka umjesto greške) i pretragu bez dijakritika.
Preskaču se kad `web/public/api/v1/jedinice.json` ne postoji.

## Primjeri za video

Kadar od oko 10 sekundi: pitanje, poziv alata, odgovor s poveznicom.
Brojke ispod su stvarni izlazi alata nad lokalnim API-jem (build 4.11.2026., godina 2025.).

### 1. "Kako stoji Općina Povljana?"

Poziv: `pregled_jedinice(jedinica="Povljana")`

Izvadak izlaza:

```json
{"godina": 2025, "ocjena": 2, "ocjena_rijec": "nestabilno", "bodovi": 39.9,
 "bodovi_bez_ogranicenja": 68.6, "ogranicenje_do": true,
 "usporedna_skupina": {"naziv": "općine do 2.000", "rang": 179, "od": 202, "medijan_bodova": 80.75},
 "sastavnice": [..., {"oznaka": "I5", "naziv": "Dospjele obveze", "vrijednost": 0.494105, "bodovi": 0.0, "medijan_skupine": 0.019621}],
 "zastavice": [{"oznaka": "Z2", "tekst": "otplata duga i dospjele obveze blizu zakonskog limita (više od 20 % zakonske osnovice)"}],
 "poveznice": {"stranica": "https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/#/jedinica/opcina-povljana"}}
```

Odgovor asistenta: "Povljana za 2025. ima ocjenu 2 (nestabilno) i 39,9 boda, 179. mjesto od 202 općine do 2.000 stanovnika. Bez ograničenja imala bi 68,6 boda, ali dospjele neplaćene obveze iznose 49,4 % rashoda poslovanja (medijan skupine 2,0 %), pa je ocjena ograničena na najviše 2. Izvor: [pregled jedinice](https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/#/jedinica/opcina-povljana)."

### 2. "Što bi bilo da se Povljana spoji s Pagom?"

Poziv: `scenarij_spajanja(jedinice="05738,03166")`

Izvadak izlaza:

```json
{"prije": [{"naziv": "Grad Pag", "ocjena": 5, "bodovi": 96.9, "stanovnici_popis_2021": 3175},
           {"naziv": "Općina Povljana", "ocjena": 2, "bodovi": 39.9, "stanovnici_popis_2021": 669}],
 "poslije": {"vrsta": "grad", "stanovnici_popis_2021": 3844, "ocjena": 5, "ocjena_rijec": "vrlo stabilno",
             "bodovi": 83.6, "rang": 9, "od": 21},
 "usteda_na_upravi": {"raspon_eur_godisnje": [0, 18044.8], "jaz_bez_spajanja_eur": 1400511.1},
 "izravnanje": {"promjena_isplate_eur": 0.0},
 "poveznice": {"simulator": "https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/#/simulator?j=03166,05738"}}
```

Odgovor asistenta: "Spojeni grad imao bi 3.844 stanovnika i ocjenu 5 (83,6 boda), 9. mjesto od 21 grada od 2.000 do 5.000 stanovnika. Realna ušteda na općoj upravi je od 0 do 18.044,8 € godišnje. Isplata fiskalnog izravnanja se ne mijenja. To je scenarij, ne prijedlog. [Simulator](https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/#/simulator?j=03166,05738)."

Nevaljana kombinacija, `scenarij_spajanja(jedinice=["Povljana", "Osijek"])`:

```json
{"greska": "Spajaju se samo jedinice iste županije: Općina Povljana (Zadarska županija), Grad Osijek (Osječko-baranjska županija)."}
```

### 3. "Odakle brojka o dospjelim obvezama Povljane?"

Poziv: `izvor_brojke(jedinica="Povljana", pokazatelj="dospjele obveze")`

Izvadak izlaza:

```json
{"pokazatelj": {"oznaka": "I5", "naziv": "Dospjele obveze", "formula": "DO(t) / 3(t) (rashodi poslovanja)", "vrijednost": 0.494105},
 "velicine": {"DO": {"formula": "23 D + 24 D + 26 D, bez kredita iskazanog kao dospio (pravilo 1)", "godine": {"2025": 1045907.73}}},
 "ulazi": [
   {"konto": "3", "godina": 2025, "iznos": 2116771.35, "redak": 156, "datoteka": "Lokalci FINALI 2019 2024 EURO.zip / 13 Zadarska.xlsx", "list": "OPĆINA POVLJANA"},
   {"konto": "23 D", "godina": 2025, "iznos": 77030.89, "redak": 324, "stupac": "LU", "datoteka": "Bilanca_2019_do_2025_R22_EURO.xlsx", "list": "2025"},
   {"konto": "26 D", "godina": 2025, "iznos": 968876.84, "redak": 324, "stupac": "MA", "datoteka": "Bilanca_2019_do_2025_R22_EURO.xlsx", "list": "2025"}]}
```

Odgovor asistenta: "Dospjele obveze su 1.045.907,73 €: 77.030,89 € obveza za rashode poslovanja (Bilanca, list 2025, redak 324, stupac LU) i 968.876,84 € obveza za kredite i zajmove (stupac MA). Rashodi poslovanja su 2.116.771,35 € (PR-RAS, list OPĆINA POVLJANA, redak 156). Omjer je 49,4 %."

## Ograničenja

- Server vraća samo ono što je u API-ju. Za godine prije 2019. i za podatke kojih nema u API-ju vraća poruku.
- Javni API se osvježava pri svakom deployu. Lokalna mapa može biti novija od javnog API-ja.
- Objašnjenje i izvor brojki postoje samo za zadnju godinu (2025.).
