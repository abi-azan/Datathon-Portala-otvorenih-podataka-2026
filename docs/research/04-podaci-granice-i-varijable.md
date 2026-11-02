# 04 – Podaci: granice JLS, strukturne varijable, provenijencija MF podataka

Istraživanje: 2026-11-02. Sve oznake „provjereno: da" znače da je izvor stvarno dohvaćen (curl, CKAN API ili headless preglednik) toga dana. Skripte i preuzimanja su u radnom (scratch) direktoriju, popis datoteka je u odjeljku 7.

## TL;DR

- **Granice: koristiti DGU „Upravne jedinice INSPIRE"** (data.gov.hr, Otvorena dozvola). Preuzimaju se preko INSPIRE ATOM usluge (ZIP od 209 MB, GML u EPSG:3035). Sadrže **556 JLS + 21 županiju + 6.759 naselja**. Ključ je 5-znamenkasta RPJ šifra (`nationalCode`, npr. `01333` = Grad Zagreb). Lanac je testiran: preuzimanje → GeoJSON WGS84 → mapshaper → `jls.topo.json` od 505 KB. Sve skupa traje oko 50 s.
- **API alternativa s istim ključem:** DZS INSPIRE WFS (`transformiraj.nipp.hr`). Daje 556 poligona i **stanovništvo iz Popisa 2021 po JLS** (ukupno, dob, spol) izravno kao GeoJSON. Ključ je `StatisticalUnit_<šifra>`, isti kao kod DGU-a. Zbroj je 3.871.833, što odgovara službenom broju. Za bodove „open data preko API-ja" stanovništvo treba vući odavde.
- DGU WFS `api.uredjenazemlja.hr/services/inspire/au/wfs` nije upotrebljiv jer nema objavljenih feature typeova (prazan `FeatureTypeList`, prazan `DescribeFeatureType`). Usluga WFS na `geoportal.dgu.hr` je isključena („Service WFS is disabled"). Radi samo WMS.
- GISCO LAU 2024 ima 556 HR jedinica s istom šifrom (`HR_01333`), ali licenca je **nekomercijalna i neprenosiva** (© EuroGeographics). Ne treba ga stavljati u javni repozitorij.
- Spajanje MF → granice: (ID županije + normalizirani naziv + 3 aliasa) daje **556/556**. Iz MF Bilance dobiva se OIB i RKP.
- Strukturne varijable: gotovo sve su dostupne. Turizam, površina i stanovništvo dolaze preko **DZS PxWeb API-ja**. Indeks razvijenosti 2024 je samo u PDF-u, ali se parsira 556/556. Fiskalno izravnanje je MF XLSX po JLS (2018.–2027.). Decentralizirane funkcije su u NN 13/2026.
- MF podaci (PR-RAS ZIP, Bilanca) postoje **samo kao datoteke na mfin.gov.hr**. Nisu na data.gov.hr, nemaju API ni eksplicitnu licencu. URL-ovi su stabilni i imaju ETag i Last-Modified, ali ime ZIP-a ne odgovara sadržaju.

---

## 1. Granice općina, gradova i županija

### 1.1 Pregled izvora

| Izvor | Izdavatelj | URL | Format | API ili datoteka | Licenca | Obuhvat | Provjereno |
|---|---|---|---|---|---|---|---|
| **Upravne jedinice INSPIRE (ATOM)** | Državna geodetska uprava | https://geoportal.dgu.hr/services/atom/INSPIRE_Administrative_Units_(AU).zip (feed: https://geoportal.dgu.hr/services/atom/au/xml) | ZIP 208.831.530 B → `AdministrativeUnit.gml` 601 MB, GML 3.2.1, **EPSG:3035** (redoslijed osi N,E) | Datoteka (INSPIRE usluga preuzimanja), bez ključa | **Otvorena dozvola** (CKAN `open-license`; metapodaci: „…u skladu s otvorenom dozvolom https://data.gov.hr/otvorena-dozvola", „nema ograničenja javnom pristupu") | 1 država, **21 županija** (uklj. Grad Zagreb), **556 JLS**, 6.759 naselja, 13.594 statističkih i 29.263 popisna kruga (ukupno 50.194). Stanje 2026-11-01 | **da** (preuzeto, parsirano) |
| Upravne jedinice – WMS (anonimni) | DGU | https://geoportal.dgu.hr/services/inspire/au/wms?service=WMS&version=1.3.0&request=GetCapabilities | WMS 1.3.0, sloj `AU.AdministrativeUnit` | API (samo slika) | kao gore | podloga za kartu, bez atributa | da (capabilities) |
| Upravne jedinice – WFS | DGU | https://api.uredjenazemlja.hr/services/inspire/au/wfs | WFS 1.1.0/2.0.0 (GeoServer) | — | — | **nema feature typeova**: `FeatureTypeList` je prazan, `DescribeFeatureType` vraća prazan schema, WMS na istom hostu je „disabled". Na `geoportal.dgu.hr/services/inspire/au/wfs` stoji „Service WFS is disabled" | da (neupotrebljivo) |
| **DZS INSPIRE WFS – Kućanstva (AreaStatisticalUnit)** | DZS (custodian), servis DGU/NIPP | `https://transformiraj.nipp.hr/ows/services/org.14.b8096c46-3962-421f-baf8-918a45735eed_wfs` | WFS 2.0, `su-vector:AreaStatisticalUnit`, **application/geo+json**, EPSG:4258/4326/3765 | **API** | Otvorena dozvola (u capabilities `Fees`; CKAN `access_constraints`, iako je CKAN `license_id` prazan) | **556 JLS**, granice iz Popisa 2021. (`HR.DGU.RPJ21`), `id = StatisticalUnit_<5-znam. šifra>`, `areaValue` [m²], ime VELIKIM SLOVIMA | **da** (196 MB, 18 s) |
| GISCO LAU 2024 | Eurostat / GISCO | https://gisco-services.ec.europa.eu/distribution/v2/lau/geojson/LAU_RG_01M_2024_4326.geojson (+ `csv/…`, `gpkg/…`, `topojson/…`) | GeoJSON 149,9 MB (cijela EU), mjerilo 1:1M; HR podskup 1,1 MB, 24.381 točaka | Datoteka (distribution API) | **© EuroGeographics, samo nekomercijalno, neprenosivo**; obavezna napomena „© EuroGeographics for the administrative boundaries" | **556 HR LAU = gradovi/općine**; atributi `GISCO_ID` (`HR_01333`), `LAU_NAME`, `POP_2024`, `POP_DENS_2024`, `AREA_KM2`, `YEAR` | da |
| GISCO NUTS 2024 razina 3 | Eurostat / GISCO | https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson (postoje i 03M/10M/20M/60M te `nuts-2021`) | GeoJSON 27,6 MB (EU) | Datoteka | kao GISCO LAU | **21 HR NUTS3** (HR021…HR028, HR031…HR037, HR050 = Grad Zagreb, HR061…HR065); `COAST_TYPE`, `MOUNT_TYPE`, `URBN_TYPE` | da |
| OpenStreetMap (Overpass) | OSM zajednica | https://overpass-api.de/api/interpreter | JSON/OSM | API | **ODbL** (share-alike za izvedene baze) | admin_level=7: **559** relacija, admin_level=8: 6.765 (uključuje i granične preklope, bez službenih šifri) | da (samo broj; server je bio preopterećen) |
| data.gov.hr, ostalo | Grad Zagreb, PGŽ… | CKAN pretrage „granice", „prostornih jedinica", „upravne jedinice", „geodetska" | — | — | — | Samo lokalni skupovi (Grad Zagreb, PGŽ). Nacionalni skup je samo DGU „Upravne jedinice INSPIRE". Zasebni otvoreni RPJ izvoz nije pronađen; AU INSPIRE je izveden iz RPJ-a | da |

### 1.2 Atributi DGU AU (JLS)

`nationalCode` je 5-znamenkasta RPJ šifra JLS (`00019` Andrijaševci … `01333` Grad Zagreb). Ista šifra je u GISCO-u (`HR_xxxxx`), u DZS INSPIRE-u (`StatisticalUnit_xxxxx`) i, prema shemi, u Sudregu (`sifra_opcine NUMBER(5)`; vidi odjeljak 4). Ostali atributi:

- `inspireId.localId`, npr. `JLS.0052000022`. Isti broj `52000022` je `localId` u DZS WFS-u.
- `name`, npr. „Grad Zagreb", „Umag - Umago". Atribut za tip grad/općina **ne postoji**.
- `upperLevelUnit`, koji pokazuje na županiju čiji je `nationalCode` 01–21 (= „ID Županije" u MF datotekama).
- `beginLifespanVersion`.

Naselja imaju 6-znamenkastu šifru i `upperLevelUnit` → JLS, iz čega se dobiva broj naselja po JLS.

Kontrole:
- Zbroj površina JLS je 56.559,2 km², a zbroj županija je identičan. DZS PxWeb daje 56.561,5 km².
- Površina Grada Zagreba je 641,3 km² (DZS: 641,25).
- Površina je izračunata planarno u EPSG:3035 (equal-area), dakle stvarna je.
- Koordinate su provjerene: Grad Zagreb bbox 15,77–16,24 E / 45,61–45,97 N.

**Imena nisu jedinstvena:** „Otok", „Privlaka" i „Sveta Nedelja" pojavljuju se dvaput, pa se spaja uvijek po (županija, naziv) ili po šifri.

**Dunavska granica:** za Bilje, Draž, Ilok, Kneževi Vinogradi, Bibinje i nekoliko drugih jedinica GISCO daje 8–20 % manju površinu. DGU i DZS računaju katastarske površine (npr. Draž 149,5 km² prema 119,6 km² u GISCO-u). To je još jedan razlog za DGU/DZS.

### 1.3 Preporuka i testirani dohvat

**Preporuka: DGU „Upravne jedinice INSPIRE" kao jedini izvor geometrije i šifrarnika.** Razlozi:

1. To je izvorni javni sektor (RPJ) na data.gov.hr.
2. Licenca je Otvorena dozvola, što dopušta redistribuciju i u javnom repozitoriju uz atribuciju.
3. Sadrži JLS, županije i naselja u jednoj topologiji.
4. Stanje je aktualno (2026-11-01).
5. Ima službenu šifru.

**DZS INSPIRE WFS koristiti za stanovništvo** jer je to pravi OGC API s istim ključem. Opcionalno se može koristiti i kao API izvor geometrije JLS (granice iz 2021.). U dokumentaciji ga treba navesti kao „integraciju s INSPIRE/NIPP infrastrukturom".

Testirana skripta: `scripts/fetch_boundaries.sh`. End-to-end traje oko 50 s.

```bash
curl -sS -f -L -o au.zip "https://geoportal.dgu.hr/services/atom/INSPIRE_Administrative_Units_(AU).zip"
unzip -o -q au.zip                                   # AdministrativeUnit.gml (EPSG:3035, osi N,E)
python -E dgu_au_to_geojson.py AdministrativeUnit.gml out/   # samo lxml; LAEA inverz ugrađen (bez GDAL/pyproj)
npx -y mapshaper@0.6.102 -i out/jls.geojson -simplify 3% keep-shapes -clean \
    -o format=topojson quantization=1e5 web/jls.topo.json -o format=geojson precision=0.00001 web/jls.geojson
npx -y mapshaper@0.6.102 -i out/zupanije.geojson -simplify 3% keep-shapes -clean -o format=geojson precision=0.00001 web/zupanije.geojson
python -E adjacency.py web/jls.topo.json web/jls_neighbours.json
```

Rezultati:

| Datoteka | Veličina | Sadržaj |
|---|---|---|
| `out/jls.geojson` | 34,5 MB | puna rezolucija, 1,58 M točaka |
| `out/zupanije.geojson` | 23,3 MB | |
| `web/jls.topo.json` | **505 KB** | 556 jedinica |
| `web/jls.geojson` | 1,39 MB | |
| `web/zupanije.geojson` | 739 KB | |
| `out/jls.csv` | | code, name, county_code, county, area_km2, n_naselja |
| `out/naselja.csv` | | 6.759 naselja |

Mapshaper (MIT licenca) čuva topologiju, pa susjedne jedinice dijele lukove.

API alternativa za poligone (testirano: 556 značajki, 196 MB, 18 s):

```bash
curl -o asu.json "https://transformiraj.nipp.hr/ows/services/org.14.b8096c46-3962-421f-baf8-918a45735eed_wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=su-vector:AreaStatisticalUnit&COUNT=1000&OUTPUTFORMAT=application/geo%2Bjson&SRSNAME=EPSG:4326"
```

### 1.4 Susjedstvo, otoci i simulator spajanja

Susjedstvo se računa iz zajedničkih lukova TopoJSON-a (`adjacency.py`):

- 1.351 parova susjeda.
- Samo 5 jedinica nema kopnenog susjeda: Lastovo, Mljet, Sali, Vir i Šolta.
- Otočne skupine kao Krk (7 JLS), Brač (8), Hvar (4), Korčula (5), Pag (4), Ugljan i Pašman (5) te Cres i Lošinj (2) međusobno su susjedi, ali nisu povezane s kopnom. Simulator ih zato prirodno ograničava na isti otok.

Oznaka „otok" (`island_flag.py`) obuhvaća sve jedinice izvan komponente Grada Zagreba i Konavala. Konavle su dodane jer je dubrovačko područje odvojeno koridorom Neuma. Rezultat je **44 otočne JLS**.

Treba ručno dodati jedinice koje su mostom ili zajedničkom granicom vezane na kopno ili su poluotok: Murter-Kornati (Murter), Okrug (Čiovo) i Pelješac (Orebić, Trpanj, Janjina, Ston). Vladino izvješće o provedbi Zakona o otocima navodi 51 JLS izravno na otocima, uključujući Pelješac.

### 1.5 Test spajanja s nazivima Ministarstva financija

Postupak:
- Iz MF Bilance (list 2025: `ID Županije`, `RKP`, `OIB`, `KORISNIK`) uzima se 576 redova: 428 općina, 128 gradova i 20 županija.
- Ključ za spajanje je (ID županije, naziv bez prefiksa „GRAD "/„OPĆINA ", s normaliziranim crticama).

Rezultat: 544 jedinice spajaju se točno, 9 po prvom dijelu dvojezičnog imena, a 3 trebaju alias. Ukupno **556/556**. Svih 556 šifri postoji i u GISCO LAU-u i u DZS WFS-u.

| MF naziv | OIB | DGU šifra | DGU naziv (županija) | Način |
|---|---|---|---|---|
| GRAD ZAGREB | 61817894937 | 01333 | Grad Zagreb (Grad Zagreb, šifra županije 21) | točno |
| GRAD SVETA NEDELJA | 24436052952 | 04367 | Sveta Nedelja (Zagrebačka) | točno + županija |
| OPĆINA SVETA NEDELJA | 84615779206 | 04324 | Sveta Nedelja (Istarska) | točno + županija |
| GRAD SVETI IVAN ZELINA | 49654336134 | 04294 | Sveti Ivan Zelina | točno |
| GRAD IVANIĆ-GRAD | 52339045122 | 01589 | Ivanić-Grad | točno |
| OPĆINA MALINSKA - DUBAŠNICA | 36462926568 | 02534 | Malinska-Dubašnica | točno (normalizacija crtice) |
| OPĆINA MURTER - KORNATI | 95623894063 | 06173 | Murter - Kornati | točno |
| GRAD UMAG-UMAGO | 84097228497 | 04685 | Umag - Umago | točno |
| OPĆINA TAR-VABRIGA | 93923679060 | 06319 | Tar-Vabriga - Torre-Abrega | prvi dio imena |
| OPĆINA KAŠTELIR-LABINCI - CASTELLIERE-S.DOMENICA | 92974208191 | 05975 | Kaštelir-Labinci - Castelliere-S. Domenica | prvi dio imena |
| OPĆINA VINODOLSKA | 98133635529 | 04880 | Vinodolska Općina | **alias** |
| OPĆINA NOVIGRAD ZADARSKI | 09817183355 | 05371 | Novigrad (Zadarska) | **alias** |
| OPĆINA SV. FILIP I JAKOV | 57113796391 | 04286 | Sveti Filip i Jakov | **alias** |

Županije: DGU `nationalCode` 01–21 jednak je MF „ID Županije", pa za njih nije potrebno usklađivanje naziva.

---

## 2. Strukturne varijable po JLS

| Varijabla | Najbolji izvor (izdavatelj) | URL | Na data.gov.hr? | Pristup | Godina | Format | Obuhvat | Provjereno |
|---|---|---|---|---|---|---|---|---|
| **Površina km²** | (a) izračun iz DGU AU (equal-area); (b) DZS PxWeb BS_TU19 „Površina, km2" | (b) `https://web.dzs.hr/PXWeb/api/v1/hr/Turizam/Dolasci i noćenja turista u komercijalnim smještajnim objektima/BS_TU19.px` | (a) da; (b) DZS „Turizam" (PC-Axis) | (a) datoteka; (b) **API** (PxWeb POST, json-stat2/csv) | stanje 2026 / 2021 | GeoJSON / JSON | 556 / 556 | da |
| **Broj naselja** | DGU AU, naselja s `upperLevelUnit` | kao 1.1 | da | datoteka | 2026 | GML → `naselja.csv` | 6.759 naselja, svih 556 JLS | da |
| **Stanovništvo 2021** (ukupno, dob 0–14/15–65/65+, spol) | DZS INSPIRE WFS `pd:StatisticalDistribution` | `https://transformiraj.nipp.hr/ows/services/org.14.f834670c-e1ce-4714-ab8d-9d06317a0fb2_wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=pd:StatisticalDistribution&COUNT=10&OUTPUTFORMAT=application/geo%2Bjson` | da („Raspodjela stanovništva … Popisa 2021. INSPIRE") | **API** (WFS; 101 MB, 7 s; `PROPERTYNAME` se ignorira) | 2021 | GeoJSON | 556; ključ = RPJ šifra; zbroj 3.871.833 | da (`fetch_dzs_pop2021_wfs.py`) |
| **Stanovništvo 2011** | DZS „Gradovi u statistici" Tab-1 (Popis 2011 i 2021) | https://podaci.dzs.hr/media/bz5hplcj/gradovi-u-statistici.xlsx | da (`statistika-u-nizu-gradovi-u-statistici`) | datoteka (3,26 MB) | 2011 i 2021 | XLSX | **svih 556 JLS**, ne samo gradovi. Ključ je (županija, naziv) | da |
| (2011, alternativa) | DZS Popis 2011 po gradovima/općinama, 21 XLS po županiji | https://web.dzs.hr/Hrv/censuses/census2011/results/xls/Grad_01_HR.xls … `_21_` | da (`popis-stanovni-tva-2011-po-gradovima-op-inama`; neki resursi `datastore_active`) | datoteka / datastore | 2011 | XLS | po županijama | da (HEAD 200) |
| **Indeks razvijenosti** (vrijednost, rang, skupina I–VIII, 6 pokazatelja i standardizirane vrijednosti) | Ministarstvo regionalnoga razvoja i fondova EU | https://razvoj.gov.hr/UserDocsImages/O%20ministarstvu/Regionalni%20razvoj/indeks%20razvijenosti/Vrijednosti%20indeksa%20razvijenosti%20i%20pokazatelja%20za%20izrac%CC%8Cun%20indeksa%20razvijenosti.pdf | **ne** (CKAN „indeks razvijenosti": 0 rezultata) | datoteka (**samo PDF**, 317 KB, 11 str.) | izračun 2024 (podaci 2020.–2022.) | PDF → parsirano | 21 županija + **556 JLS**, spojeno 556/556 (alias „Sveta Nedjelja" → „Sveta Nedelja") | da (`parse_indeks_razvijenosti.py` → `indeks_razvijenosti_2024.csv`) |
| Razvrstavanje (pravni akt) | Vlada RH, Odluka NN 3/2024 | https://narodne-novine.nn.hr/clanci/sluzbeni/2024_01_3_60.html | ne | HTML | 2024 | HTML | skupine I–VIII (JLS) i I–IV (županije) | da |
| **Potpomognuta područja** | izvedeno: skupine I–IV (indeks < 100) | kao gore | — | — | 2024 | — | **287 JLS** | da (izračunato) |
| **Brdsko-planinska područja** | Vlada RH, Odluka NN 24/2019 | https://narodne-novine.nn.hr/clanci/sluzbeni/2019_03_24_484.html | ne | HTML (popis imena po skupinama) | 2019 (noviji akt nije pronađen) | HTML | oko 85 JLS (nije prebrojano) | da (stranica) |
| **Otočni status** | izvedeno iz DGU topologije (44 JLS) + ručno Pelješac, Murter-Kornati, Okrug. Pravni okvir: Zakon o otocima (NN 116/18, 73/20, 70/21), koji JLS ne navodi popisom | — | — | izračun | — | — | 44 automatski, oko 51 s dopunom | da (izračun) |
| **Primorske JLS** | DZS PxWeb „Turizam u primorskim gradovima i općinama" (BS_T01–T04, popis primorskih JLS i naselja); NUTS3 `COAST_TYPE` samo na razini županije | `…/PXWeb/api/v1/hr/Turizam/Turizam u primorskim gradovima i općinama/BS_T01.px` | (DZS Turizam) | **API** | 2018–2025 | JSON | primorske JLS i njihova naselja | da (metadata) |
| **Turistički dolasci i noćenja, postelje** | DZS PxWeb **BS_TU19** „Intenzitet turizma u gradovima i općinama" (14 pokazatelja: stanovnici 2021, površina, postelje, dolasci, noćenja, po stanovniku i km²…); BS_TU18 mjesečno | kao gore | da (`proizvodnja-orani-nih-usjeva-u-tonama`, naslov „Turizam", PC-Axis; čudan slug) | **API** (PxWeb v1, POST, json-stat2) | **2021–2025** | JSON (85 KB za 2025.) | 582 prostorne jedinice (RH, NUTS2, 21 županija, 556 JLS). Spajanje po (županija iz reda iznad, naziv) | da (`pxweb_tourism.py` → `bs_tu19_latest.csv`) |
| (turizam, alternativa) | DZS „Gradovi u statistici" Tab-6 | kao gore | da | datoteka | 2012–2021 | XLSX | 556 | da |
| (smještajni kapacitet) | MF tablica fiskalnog izravnanja, stupci „20xx smještajnih jedinica" | vidi fiskalno izravnanje | ne | datoteka | 2019–2025 | XLSX | 576 | da |
| **Decentralizirane funkcije** | Vlada RH, Uredba o načinu financiranja decentraliziranih funkcija … za 2026. (**NN 13/2026**) | https://narodne-novine.nn.hr/clanci/sluzbeni/2026_02_13_121.html | ne | HTML (tablice) | 2026 | HTML | Tablica 2: **38 gradova** financira osnovno školstvo (Velika Gorica, Samobor, Vrbovec, Zaprešić, Krapina, Sisak, Kutina, Karlovac, Varaždin, Koprivnica, Križevci, Đurđevac, Bjelovar, Čazma, Garešnica, Grubišno Polje, Rijeka, Crikvenica, Opatija, Gospić, Virovitica, Požega, Slavonski Brod, Zadar, Osijek, Šibenik, Vinkovci, Vukovar, Makarska, Split, Pula, Labin, Pazin, Poreč, Rovinj, Umag, Dubrovnik, Čakovec) + sve županije + Grad Zagreb. Tablica 3: osnivači i suosnivači **JVP** (oko 74 postrojbe, s udjelima u %) = vatrogastvo. Srednje školstvo, domovi za starije i zdravstvo su obveza županija i Grada Zagreba (Tablica 1) | da |
| **Fiskalno izravnanje** (udio, optimalni iznos, kapacitet poreznih prihoda po stanovniku, referentna vrijednost, porez na dohodak po godinama 2013.–2024., stanovnici 2021.) | Ministarstvo financija | 2026: https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava//Tablica%20udjela%20po%20JLP(R)S%20za%20fiskalno%20izravnanje%20u%202026.xlsx (postoje i 2018.–2025. i **2027.**; popis linkova na https://mfin.gov.hr/istaknute-teme/lokalna-samouprava/fiskalno-izravnanje/202) | ne | datoteka | 2018–2027 | XLSX (list „Izračun udjela za 2026.", 73 stupca; list „Udjeli") | 576 jedinica, ključ (ID Županije, Titula, Naziv) kao u MF Bilanci | da |
| (bonus) **Lokalne porezne stope** (porez na dohodak niža/viša 2025/2026, porez na potrošnju, porez na nekretnine, paušalni porez) | Porezna uprava | https://data.gov.hr/ckan/dataset/https-porezna-uprava-gov-hr-hr-odluke-jls-4009 | **da** | datoteke XLSX (datastore postoji, ali ima mojibake i 10.754 redova: koristiti XLSX) | 2025–2026 | XLSX | 556 | da |

Napomene:

- **PxWeb API (DZS)** je drugi pravi API, uz CKAN i WFS. Struktura: GET metapodataka → POST upita `{"query":[{"code":"Godina","selection":{"filter":"item","values":["2025"]}}],"response":{"format":"json-stat2"}}`. U nazivima putanja ostaju razmaci i dijakritici, pa ih treba URL-enkodirati, ili koristiti `requests`. Na Windowsu odgovor treba čitati kao UTF-8. Grad Zagreb se pojavljuje dvaput, kao županija i kao JLS.
- PxWeb tablice „Naselja i stanovništvo RH / Gradovi i Općine" (Tabela3_01…21) pokrivaju samo popise 1857.–2001. i **ne** uključuju 2011. Zato je za 2011. bolji izvor „Gradovi u statistici".
- Indeks razvijenosti iz PDF-a: `pdfplumber` po redovima, regex `^(rang) (naziv županija) (skupina) (indeks) (12 brojeva)$`. Daje 21 + 556 redova, a skupine I–VIII imaju po 67–72 JLS.

---

## 3. Provenijencija podataka Ministarstva financija

| Datoteka | Točan URL | Veličina | Last-Modified / ETag | Napomena |
|---|---|---|---|---|
| **PR-RAS i RAS-funkc 2019.–2025. (EUR)** | https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava/financijski-izvjestaji-jlp-r-s//Lokalci%20FINALI%202019%202024%20EURO.zip | 80.081.539 B | Fri, 24 Jul 2026 14:10:44 GMT / `"4ae3ad37761bdd1:0"` | Stranica: https://mfin.gov.hr/istaknute-teme/lokalna-samouprava/financijski-izvjestaji-jlp-r-s/pr-ras-i-ras-funkc-za-razdoblje-2019-2025-euro/3922. **Ime datoteke kaže „2019 2024", ali naslov linka je „2019 2025".** U ZIP-u su 23 XLSX-a. Uz original je i `14 Osječko_baranjska ispravak.xlsx` od 2026-07-24, koji treba imati prednost. Imena u ZIP-u nisu UTF-8 (CP852). Radi i URL bez dvostrukih kosih crta |
| **Bilanca 2019.–2025. (EUR)** | https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava/financijski-izvjestaji-jlp-r-s//Bilanca_2019_do_2025_R22_EURO.xlsx | 6.725.184 B | Fri, 26 Jun 2026 14:34:14 GMT / `"3294a4dc785dd1:0"` | Listovi 2019–2025. Stupci `ID Županije, RKP, OIB, KORISNIK` + AOP šifre. Razina 22 |
| Bilanca 2002.–2022. (HRK) | https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava/financijski-izvjestaji-jlp-r-s//Bilanca_2002_do_2022_R22_HRK.xlsx | 14.784.158 B | Fri, 29 Mar 2024 | povijest u kunama |
| PR-RAS 2014.–2020. (HRK) | stranica …/pr-ras-i-ras-funkc-za-razdoblje-2014-2020/3173. Datoteke po županiji, npr. https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava/financijski-izvjestaji-jlp-r-s/ostvarenje-proracuna-2010-2020//01%20Zagreba%C4%8Dka%202020.xlsx | — | — | 21 XLSX po godini/županiji. Postoje i stranice 2010.–2014. (/211), 2002.–2010. (/212) i statistički izvještaji 1995.–2001. |
| Fiskalno izravnanje 2018.–2027. | vidi odjeljak 2 | 409–492 KB | — | XLSX + PDF odluke |

- Na stranici `/203` **nema** zasebnih datoteka „Obveze", „P-VRIO" ni samostalnog „RAS-funkcijski". RAS-funkcijski je unutar PR-RAS ZIP-a. Stranica „Zaduživanje JLP(R)S" (`/201`) ima samo obrasce (ZJS, IZJS, FPP), bez podataka po jedinicama.
- **data.gov.hr:** organizacija `ministarstvo-financija` ima 10 skupova. Lokalni su samo „Lokalni proračun 2001.", „Ostvarenje proračuna JLP(R)S 2002.–2010.", „2010.–2014." i „2014.–2015." (izmijenjeno 2026-04-15). Njihovi URL-ovi (`http://www.mfin.hr/...`) **ne rade** (spajanje ne uspijeva). Pretrage „PR-RAS", „bilanca", „financijski izvjestaji" i „proracun JLS" nalaze samo izvještaje pojedinih gradova i općina (npr. Dugo Selo, Grad Zagreb). **Aktualni MF skupovi nisu na portalu i nema API-ja.**
- Isti MF org ima „Registar proračunskih i izvanproračunskih korisnika" (Otvorena dozvola, XLSX na data.gov.hr). Tablica 2 (proračunski korisnici JLP(R)S) daje RKP, naziv, **OIB, matični broj** i adresu, što je korisno kao druga potvrda OIB-a.
- **Licenca MF datoteka:** stranica „Uvjeti korištenja" (https://mfin.gov.hr/uvjeti-koristenja/76) je prazna i nema eksplicitne licence. Osnova za ponovnu uporabu je Zakon o pravu na pristup informacijama (NN 25/13, 85/15, 69/22). U dokumentaciji treba navesti „Izvor: Ministarstvo financija, <URL>, preuzeto <datum>". Ovo nije provjereno kao licenca; to je pravna pretpostavka.
- **Stabilnost za GitHub Actions:** direktoriji su stabilni, ali se imena datoteka mijenjaju po godini (vidi „2019 2024"). Preporučeni postupak:
  1. Dohvatiti HTML podstranice `/3922` i `/203`.
  2. Regexom izvući `href` koji završava na `.zip` ili `Bilanca_*_EURO.xlsx`.
  3. Napraviti uvjetni GET s `If-None-Match`/`If-Modified-Since`, jer IIS vraća ETag.
  4. Ako datoteka postoji u više verzija, preferirati „ispravak".

---

## 4. Master tablica i ključevi

| Izvor | URL | Što sadrži | Provjereno |
|---|---|---|---|
| MPUDT „Popis županija, gradova i općina" | https://data.gov.hr/ckan/dataset/popis-zupanija-gradova-i-opcina. XLS: https://mpu.gov.hr/UserDocsImages/MURH-%20arhiva/Uprava%20za%20politi%C4%8Dki%20sustav/JLRS/100613-Kopija%20opcine_gradovi_RH.xls (preusmjerava na mpudt.gov.hr; zadnje spremanje 2013-06-10). Datastore: `datastore_search?resource_id=55ac291b-63bf-42ac-8d01-7aff77c62223&limit=1000` | **Samo** `Zupanija` (rimski broj + naziv), `Tip jedinice` (Općina/Grad), `Ime jedinice`. 556 redova: 428 općina, 128 gradova uključujući Zagreb. Županije su u zasebnom XLS-u (21 red). **Nema šifre, OIB-a ni matičnog broja** | da (CKAN datastore API; 555/556 se spaja na DGU, a Zagreb ručno) |
| Sudski registar API `/sjedista` | https://sudreg-data.gov.hr/api/javni/sjedista (OpenAPI: https://sudreg-data.gov.hr/api/javni/dokumentacija/open_api, v3.0.4) | `sifra_zupanije NUMBER(3)`, `sifra_opcine NUMBER(5)`, `naziv_opcine`, `sifra_naselja NUMBER(10)`, `naziv_naselja`, `postanski_broj` | **djelomično**. Shema je provjerena; svi endpointi traže OAuth2 client-credentials (`/api/oauth/token`) i bez tokena vraćaju 401. Format (5 znamenki općina, 10 naselje) odgovara RPJ šiframa, ali **vrijednosti nisu potvrđene**. Nakon registracije potrebna je jedna provjera: firma sa sjedištem u Zagrebu mora imati `sifra_opcine = 1333` |

**Strategija ključeva** (testirano, `build_master.py` → `master_jls_draft.csv`, 556 redova):

1. **Primarni ključ `jls_code`** je 5-znamenkasta RPJ šifra iz DGU AU `nationalCode`, kao string s vodećim nulama. Isti je u:
   - DZS INSPIRE WFS (`StatisticalUnit_<code>`),
   - GISCO (`HR_<code>`),
   - vjerojatno Sudreg `sifra_opcine` (kao broj bez nula).
2. **Županija `zup_id`** 01–21 jednak je u DGU AU, MF datotekama (`ID Županije`) i fiskalnom izravnanju. Grad Zagreb ima 21. NUTS3 se veže preko tablice od 21 reda (naziv).
3. **OIB i RKP** dolaze iz MF Bilance spajanjem (zup_id, normalizirani naziv). Tablica aliasa ima samo 3 unosa: `VINODOLSKA→Vinodolska Općina`, `NOVIGRAD ZADARSKI→Novigrad`, `SV. FILIP I JAKOV→Sveti Filip i Jakov`. Dvojezična imena se spajaju po prvom dijelu. OIB se zatim koristi kao stabilan ključ za sve MF godine i za Sudreg ili RKP registar (matični broj).
4. **Tip (grad/općina)** dolazi iz prefiksa MF naziva ili iz MPUDT liste. U master tablici ima 428 općina i 128 gradova.
5. DZS PxWeb i „Gradovi u statistici" nemaju šifre. Spajaju se po (županija, naziv), uz iste aliase. Ako DZS koristi novi naziv, dodaje se alias.

Stupci master tablice: `jls_code, naziv, tip, zup_id, zupanija, oib, rkp, mf_naziv, lau_id, povrsina_km2_dgu, povrsina_km2_gisco, broj_naselja, otok, n_susjeda, indeks_razvijenosti_2024, razvojna_skupina, potpomognuto`.

---

## 5. Blokeri i rizici

1. **DGU WFS je prazan.** Granice se zato dohvaćaju kao INSPIRE ATOM datoteka (209 MB, oko 50 s u CI-ju). Ako žiri strogo traži „API", treba koristiti DZS INSPIRE WFS za poligone (granice 2021.) i za stanovništvo.
2. **MF podaci nemaju API ni licencu i nisu na data.gov.hr.** Ime ZIP-a ne odgovara godinama, a u ZIP-u je duplikat „ispravak". Rješenje je scraping linka + ETag (odjeljak 3). U dokumentaciji treba spomenuti preporuku MF-u da objavi skup na data.gov.hr.
3. **Indeks razvijenosti postoji samo kao PDF.** Parser radi (556/556), ali se može slomiti ako ministarstvo objavi novi PDF.
4. **Sudreg `sifra_opcine` nije potvrđen** jer API traži registraciju.
5. **GISCO licenca** je nekomercijalna i neprenosiva, pa ga ne treba koristiti za objavu. Dunavska granica daje drukčije površine nego DGU/DZS.
6. **CKAN datastore** za porezne stope ima mojibake (`ANDRIJAÅ EVCI`) i višestruke importe, pa treba koristiti XLSX.
7. **Otočni status** je heuristika (44 automatski + 7 ručno). Zakon o otocima ne daje popis JLS.
8. Brdsko-planinska područja su po aktu iz 2019. (NN 24/2019). Noviji akt nije pronađen.
9. Overpass (OSM) je u trenutku testa bio preopterećen (502), ali nije potreban.

---

## 6. Popis skupova podataka (format za predaju)

| Naziv skupa | Izdavatelj | Poveznica | Licenca | Način pristupa |
|---|---|---|---|---|
| Financijski izvještaji JLP(R)S – PR-RAS i RAS-funkcijski 2019.–2025. (EUR) | Ministarstvo financija | https://mfin.gov.hr/istaknute-teme/lokalna-samouprava/financijski-izvjestaji-jlp-r-s/pr-ras-i-ras-funkc-za-razdoblje-2019-2025-euro/3922 | nije navedena; ponovna uporaba prema ZPPI, uz navođenje izvora | preuzimanje datoteke (ZIP/XLSX), automatizirano |
| Bilanca JLP(R)S 2019.–2025. (EUR) | Ministarstvo financija | https://mfin.gov.hr/UserDocsImages//dokumenti/o-ministarstvu/lokalna-samouprava/financijski-izvjestaji-jlp-r-s//Bilanca_2019_do_2025_R22_EURO.xlsx | kao gore | preuzimanje datoteke (XLSX) |
| Fiskalno izravnanje – tablica udjela po JLP(R)S (2026., 2027.) | Ministarstvo financija | https://mfin.gov.hr/istaknute-teme/lokalna-samouprava/fiskalno-izravnanje/202 | kao gore | preuzimanje datoteke (XLSX) |
| Upravne jedinice INSPIRE | Državna geodetska uprava | https://data.gov.hr/ckan/dataset/upravne-jedinice-inspire (ATOM: https://geoportal.dgu.hr/services/atom/au/xml) | Otvorena dozvola | INSPIRE ATOM usluga preuzimanja (GML) + WMS |
| Raspodjela stanovništva prema dobnim skupinama i spolu na razini gradova/općina iz Popisa 2021. INSPIRE | DZS (servis DGU/NIPP) | https://data.gov.hr/ckan/dataset/raspodjela-stanovnitva-prema-dobnim-skupinama-i-spolu-na-razni-gradova-opina-iz-popisa-stanovni | Otvorena dozvola (prema WFS capabilities) | **API – OGC WFS 2.0 (GeoJSON)** |
| Kućanstva – ukupno na razini gradova/općina iz Popisa 2021. INSPIRE (poligoni JLS) | DZS (servis DGU/NIPP) | https://data.gov.hr/ckan/dataset/kuanstva-ukupno-na-razini-gradova-opina-iz-popisa-stanovnitva-2021-inspire | Otvorena dozvola | **API – OGC WFS 2.0 (GeoJSON)** (opcionalno) |
| Turizam – Intenzitet turizma u gradovima i općinama (BS_TU19) | Državni zavod za statistiku | https://data.gov.hr/ckan/dataset/proizvodnja-orani-nih-usjeva-u-tonama (PxWeb: https://web.dzs.hr/PXWeb/Menu.aspx?px_language=hr&px_type=PX&px_db=Turizam) | Otvorena dozvola | **API – DZS PxWeb (JSON-stat)** |
| Statistika u nizu: Gradovi i općine u statistici | Državni zavod za statistiku | https://data.gov.hr/ckan/dataset/statistika-u-nizu-gradovi-u-statistici | Otvorena dozvola | preuzimanje datoteke (XLSX) |
| Statistika u nizu: Popis stanovništva, kućanstava i stanova 2021. – stanovništvo | Državni zavod za statistiku | https://data.gov.hr/ckan/dataset/statistika-u-nizu-popis-stanovnistva-kucanstava-i-stanova-2021 | Otvorena dozvola | preuzimanje datoteke (XLSX); zamjena WFS-om iznad |
| Popis županija, gradova i općina | Ministarstvo pravosuđa, uprave i digitalne transformacije | https://data.gov.hr/ckan/dataset/popis-zupanija-gradova-i-opcina | Otvorena dozvola | **API – CKAN datastore_search** |
| Registar proračunskih i izvanproračunskih korisnika (Tablica 2: JLP(R)S) | Ministarstvo financija | https://data.gov.hr/ckan/dataset/registar-proracunskih-i-izvanproracunskih-korisnika | Otvorena dozvola | preuzimanje preko CKAN API-ja (XLSX) |
| Usporedba poreznih stopa prema odlukama JLS | Porezna uprava | https://data.gov.hr/ckan/dataset/https-porezna-uprava-gov-hr-hr-odluke-jls-4009 | Otvorena dozvola | preuzimanje preko CKAN API-ja (XLSX) |
| Vrijednosti indeksa razvijenosti i pokazatelja 2024. | Ministarstvo regionalnoga razvoja i fondova EU | https://razvoj.gov.hr/o-ministarstvu/djelokrug-1939/regionalni-razvoj/indeks-razvijenosti/vrijednost-indeksa-razvijenosti-i-pokazatelja-za-izracun-indeksa-razvijenosti-2024/5508 | nije navedena; javni podaci tijela javne vlasti, uz navođenje izvora | preuzimanje PDF-a + parsiranje |
| Odluka o razvrstavanju JLP(R)S prema stupnju razvijenosti (NN 3/2024) | Vlada RH / Narodne novine | https://narodne-novine.nn.hr/clanci/sluzbeni/2024_01_3_60.html | službeni tekst (nije predmet autorskog prava) | HTML |
| Uredba o financiranju decentraliziranih funkcija 2026. (NN 13/2026) | Vlada RH / Narodne novine | https://narodne-novine.nn.hr/clanci/sluzbeni/2026_02_13_121.html | službeni tekst | HTML |
| Odluka o brdsko-planinskim područjima (NN 24/2019) | Vlada RH / Narodne novine | https://narodne-novine.nn.hr/clanci/sluzbeni/2019_03_24_484.html | službeni tekst | HTML |
| Sudski registar – sjedišta (ako se koristi) | Ministarstvo pravosuđa, uprave i digitalne transformacije | https://sudreg-data.gov.hr | provjeriti uvjete pri registraciji | **REST API (OAuth2)** |
| Tečajna lista (ako se koristi) | HNB | https://api.hnb.hr/tecajn-eur/v3 | — | REST API |

Prijedlog atribucije za kartu:

> Granice: Državna geodetska uprava, Upravne jedinice INSPIRE (stanje 1.11.2026.), https://data.gov.hr/ckan/dataset/upravne-jedinice-inspire, Otvorena dozvola. Geometrija je preprojicirana u WGS84 i pojednostavljena (mapshaper).

Otvorena dozvola traži izjavu o izvoru, datum zadnje izmjene, URI i oznaku izmjena.

Alati za dokumentaciju (popis korištenog softvera): mapshaper 0.6.102 (MIT), lxml (BSD), pdfplumber (MIT), requests (Apache-2.0), openpyxl (MIT).

---

## 7. Datoteke u radnom direktoriju

Korijen je `C:\Users\marsi\AppData\Local\Temp\claude\C--Users-marsi-Documents-FER-datathon\99e6195d-8762-4726-9625-6e55a09d7425\scratchpad\research\data\`.

Skripte (`scripts\`):

| Datoteka | Namjena |
|---|---|
| `fetch_boundaries.sh` | end-to-end, testirano |
| `dgu_au_to_geojson.py` | GML → GeoJSON, površina, broj naselja, LAEA inverz |
| `adjacency.py` | susjedstvo iz TopoJSON-a |
| `island_flag.py` | oznaka otočnih JLS |
| `join_test.py` | MF → DGU, GISCO, WFS |
| `fetch_dzs_pop2021_wfs.py` | stanovništvo 2021 preko WFS-a |
| `pxweb_probe.py`, `pxweb_tourism.py` | DZS API |
| `parse_indeks_razvijenosti.py` | parsiranje PDF-a indeksa |
| `build_master.py` | master tablica |
| `parse_dgu_au.py` | inventura razina u AU GML-u |

Podaci (`downloads\`):

| Datoteka | Sadržaj |
|---|---|
| `boundaries_test\web\jls.topo.json`, `jls.geojson`, `zupanije.geojson`, `jls_neighbours.json` | granice spremne za web |
| `dgu\out\jls.geojson`, `zupanije.geojson`, `jls.csv`, `naselja.csv` | puna rezolucija |
| `dgu\au_inspire.zip` | izvorni DGU ZIP |
| `crosswalk_oib_dgu.csv` | 556 redova: OIB ↔ šifra |
| `master_jls_draft.csv` | nacrt master tablice |
| `razvoj\indeks_razvijenosti_2024.csv` | indeks razvijenosti |
| `dzs_pxweb\bs_tu19_latest.csv` | turizam 2025. |
| `dzs_wfs\pop2021_wfs.csv` | stanovništvo 2021 |
| `dzs_wfs\asu_all.json` | WFS poligoni |
| `mfin\fi_2025.xlsx`, `fi_2026.xlsx`, `fi_2027.xlsx` | fiskalno izravnanje |
| `gisco\lau2024_HR.geojson` | samo za usporedbu, ne za objavu |
| `mpudt\`, `rkp\`, `sudreg\openapi.json`, `nn_2026_13_121.txt`, `nn_2024_3_60.txt` | ostali izvori |
