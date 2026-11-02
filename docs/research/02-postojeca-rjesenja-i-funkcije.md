# Postojeća rješenja i prijedlog funkcija (istraživanje, 2.11.2026.)

**Pitanje:** Što već postoji u svijetu i u Hrvatskoj za ocjenu financijskog zdravlja lokalnih jedinica i za simulaciju spajanja? Što od toga možemo naučiti? Koje funkcije treba izgraditi za "Fiskalnu kartu JLS" u 5 do 6 dana?

**Oznake pouzdanosti:**

- **[P]** znači da je izvor provjeren izravno u ovoj sesiji: stranica otvorena u pregledniku, PDF ili DOCX preuzet i pročitan.
- **[S]** znači da je podatak iz sekundarnih izvora (rezultati pretrage, novinski članci) i nije provjeren na izvornoj stranici.
- **[N]** znači da se izvor nije mogao provjeriti, jer ga blokira Cloudflare ili domena ne radi.

Brojevi u uglatim zagradama odnose se na popis izvora na kraju dokumenta.

**Snimke zaslona** su u scratch direktoriju (izvan repozitorija):
`C:\Users\marsi\AppData\Local\Temp\claude\C--Users-marsi-Documents-FER-datathon\99e6195d-8762-4726-9625-6e55a09d7425\scratchpad\research\prior-art\`

- `01-ineko-profil.png`: profil slovačkog grada na INEKO portalu
- `02-gobierto-orgiva.png`: profil španjolske općine na Gobiertu
- `03-ijf-transparentnost-karta.png`: IJF-ova karta transparentnosti 576 JLS
- `04-japan-dashboard-finance.png`: japanski Japan Dashboard, financije općina
- `05-eesti-finantsolukorra-indeks.png`: estonski indeks financijskog stanja (1–5)
- `06-moldova-amalgasim.png`: moldavski simulator spajanja AmalgaSim

---

## Sažetak nalaza

1. **U Hrvatskoj ne postoji javni alat koji svim 576 jedinicama daje ocjenu financijskog zdravlja. Ne postoji ni alat koji simulira fiskalni učinak spajanja.** Najbliži su:
   - **CROračun** (Coin d.o.o., 2016.). Uspoređivao je proračune svih JLS po stanovniku iz podataka Ministarstva financija, ali danas je iza prijave [70][71].
   - **IJF-ove Excel tablice** izvršenja lokalnih proračuna [62][63] i **IJF-ova karta transparentnosti** (0–5, zadnji ciklus 2023.) [61].
   - **Gradske aplikacije "otvoreni proračun"** (Rijeka, Pula, Poreč, Bjelovar, Zagreb) i vendorska rješenja (proracun.hr). Sve prikazuju isplate jedne jedinice. Nijedna ne ocjenjuje i ne uspoređuje [64]–[69].
2. **Najbliži međunarodni analozi:**
   - **Ocjena:** INEKO u Slovačkoj (0–6, svih 2.930 općina, od 2009.) [13]–[15].
   - **Službeni indeks 1–5:** estonski minuomavalitsus.ee, 7 pokazatelja, ministarstvo [31].
   - **Metodologija koju preuzimamo:** austrijski KDZ-Quicktest i offenerhaushalt.at [1]–[3].
   - **UX usporedbe sa sličnim jedinicama:** japanski Japan Dashboard [43].
   - **Simulator spajanja:** moldavski **AmalgaSim**. To je živ, državni alat s kartom, provjerom zakonskih kriterija i izračunom poticaja [55].
3. **Dokazi o uštedama od spajanja su mješoviti.** Danska i Nizozemska nisu ostvarile očekivane uštede administracije [47][49][50]. Simulator zato mora prikazivati **raspon i pretpostavke**, a ne jedan broj. To se slaže s našom validacijom podataka: ekonomija razmjera postoji, ali je koncentrirana ispod oko 5.000 stanovnika (`00-validacija-podataka.md`, odjeljak 7).
4. **Novi argument za relevantnost:** u materijalima 160. sjednice Vlade (16.4.2026.) nalazi se prijedlog zaključka Ministarstva financija o kriteriju "dobrog financijskog upravljanja". Prema njemu jedinica ne smije imati manjak bez EU izvora veći od 10 % prihoda bez EU izvora, inače ne može dobiti pomoći iz državnog proračuna koje se dodjeljuju na temelju poziva [78] [P]. Usvajanje nismo potvrdili. Naš alat bi to mogao izračunati i prikazati za svaku jedinicu.
5. **Kritična UX zamka:** KDZ koristi austrijske školske ocjene (1 = najbolje). U Hrvatskoj je 1 nedovoljan. Ocjena "1" za najzdraviju općinu bit će krivo pročitana. Estonski indeks i INEKO koriste smjer u kojem je veće bolje [31][14]. **Preporuka: prikazivati hrvatsku konvenciju (5 = najbolje) uz riječ ("vrlo stabilno").**

---

## 1. Međunarodni javni alati za financije i fiskalno zdravlje lokalnih jedinica

### 1.1 Austrija: KDZ-Quicktest, offenerhaushalt.at i Bonitätsranking

- **URL i vlasnik:** offenerhaushalt.at. Vodi ga KDZ – Zentrum für Verwaltungsforschung, platforma je nastala uz Bank Austria [3][4]. Stranica je u headless pregledniku vraćala Cloudflare provjeru (403) [N]. Opis je zato iz sekundarnih izvora i iz službenog KDZ priručnika.
- **Metodologija (KDZ-Quicktest, priručnik verzija 2.0 od 7.5.2025.) [1] [P]:**
  - Postoji pet pokazatelja u četiri dimenzije:
    - ÖSQ (javna stopa štednje): snaga prihoda
    - FSQ (slobodni financijski vrh): financijska sposobnost
    - EFQ (stopa samofinanciranja): snaga samofinanciranja
    - VSD (godine otplate duga) i SDQ (stopa servisiranja duga): zaduženost
  - ÖSQ, FSQ i EFQ nose do 25 bodova. VSD i SDQ nose do 12,5 bodova, jer zajedno čine dimenziju duga. Ukupno je 100 bodova.
  - Ukupna ocjena: 81–100 bodova je *Sehr gut*, 61–80 *Gut*, 41–60 *Durchschnitt*, 21–40 *Genügend*, ispod 20 *Unzureichend*.
  - Priručnik daje tumačenje za laike. Primjer: "ÖSQ iznad 25 % je vrlo pozitivan, ispod 5 % jasan znak upozorenja; negativna ÖSQ znači da je sanacija nužna odmah".
  - Uz to postoji i "KDZ-Quicktest NEU" sa 7 pokazatelja iz obračunskog i imovinskog dijela proračuna.
- **Kako se prikazuje:** na offenerhaushalt.at korisnik odabere općinu, otvori "Spezielle Darstellungen" i klikne "Visualisierung" uz KDZ-Quicktest [S].
  - Općine sudjeluju dobrovoljno. Stariji izvori navode 1.159 do 1.327 od 2.095 općina [4] [S].
  - Postoje CSV preuzimanja s oznakom izvora (općina ili Statistik Austria) [S].
- **Bonitätsranking:** KDZ i časopis *Public* svake godine objavljuju Top 250 općina. Izdanje 2022. bilo je jedanaesto [2] [P]. Izdanje 2024. temelji se na prosjeku 2020.–2022. [S].
  - Lokalni mediji ga prenose u pozitivnom tonu ("naša općina među top 250").
- **Pouke:**
  - Metodologija je provjerena 20 godina, a priručnik je javan i izvrstan je predložak za našu stranicu "Metodologija".
  - Objavljuju se samo **najbolji** (Top 250). Lošije se ne prozivaju, a lokalni mediji imaju pozitivnu priču. To je dobar obrazac za politički osjetljivu temu.
  - Ocjena se računa iz **višegodišnjeg prosjeka**, ne iz jedne godine.
- **Nedostaci:** pokrivenost nije potpuna, jer sudjelovanje ovisi o volji općine. Pragovi su normativni i kalibrirani za austrijski računovodstveni okvir VRV 2015. Za Hrvatsku ih treba kalibrirati, kako stoji i u `00-validacija-podataka.md`.

### 1.2 Njemačka: Wegweiser Kommune i Kommunaler Finanzreport (Bertelsmann Stiftung)

- **URL:** wegweiser-kommune.de. Vodi ga Bertelsmann Stiftung, a portal postoji od 2006. [5] [P].
- **Što prikazuje:** demografske, socijalne i financijske pokazatelje za općine iznad 5.000 stanovnika, okruge i savezne zemlje.
  - Svaka općina ima automatski generirano PDF "Finanzbericht" izvješće [7].
  - Kommunaler Finanzreport koristi *Kassenkredite* (kratkoročne kredite za likvidnost) kao središnji pokazatelj krize [8] [S].
- **UX i interoperabilnost [6] [P]:**
  - Sadržaj je pod licencom **CC0**.
  - Postoji **REST API s OpenAPI opisom** (`/openapi` u YAML i JSON formatu).
  - Preuzimanja su dostupna u PDF, Excel, CSV, JSON, SVG i PNG formatu.
  - Postoji **tipologija općina** ("Demografietypen", 9 tipova za oko 3.000 općina). Ona služi za usporedbu sa sličnima.
  - Portal je 2022. dobio German Design Award.
- **Pouke:** naša arhitektura može kopirati ovaj obrazac: otvoreni podaci, OpenAPI specifikacija i izvoz u više formata. Tipologija je njihov odgovor na pitanje "s kim se uspoređujem".
- **Nedostaci:** nema jedne sintetske ocjene i nema simulacije spajanja.

### 1.3 Ujedinjeno Kraljevstvo: CIPFA Financial Resilience Index i Oflog

- **CIPFA FRI** [9][10] (stranica iza Cloudflarea [N], opis iz sekundarnih izvora [S]):
  - Ima 9 pokazatelja za vijeća sa socijalnom skrbi i 8 za ostala, među njima razinu i promjenu rezervi, dug i omjer socijalne skrbi.
  - Svjesno **nema jedinstvenu ocjenu** ni prediktivni model.
  - Prikazuje položaj vijeća prema "nearest neighbours" (15 statistički najsličnijih vijeća) i prema svim vijećima istog tipa.
  - Namijenjen je financijskim direktorima i koristi se u proračunskim izvješćima.
- **Oflog Local Authority Data Explorer:** vladin alat za usporedbu s 15 CIPFA-susjeda. **Ugašen je nakon zatvaranja Ofloga** [11] [S].
  - ONS sada objavljuje "statistical nearest neighbours" za sva lokalna područja (izdanje od ožujka 2026.) [12] [S].
  - LG Inform koristi slične skupine za usporedbu [81].
- **Pouke:**
  - "Slični" su metodološki zasebna stvar. Mi to možemo riješiti jednostavnije: vrsta jedinice × razred veličine × skupina indeksa razvijenosti.
  - Odluka CIPFA-e da ne daje jednu ocjenu je upozorenje: jedna ocjena pojednostavljuje. Zato naša ocjena uvijek mora imati raščlambu na komponente.
  - Sudbina Ofloga pokazuje rizik alata koji ovisi o jednoj instituciji. Otvoreni kod i otvoreni podaci tu pomažu.

### 1.4 Slovačka: INEKO "Hospodárenie obcí" (najbliži analog ocjene)

- **URL:** hospodarenieobci.sk. Vlasnik je INEKO, nevladina organizacija [13] [P].
- **Pokrivenost [14] [P]:** svih 2.930 općina, gradova i gradskih četvrti te 8 VÚC (županija), za razdoblje 2006.–2025.
  - Podaci za 2025. objavljeni su 21.9.2026.
  - Podatke daje Datacentrum Ministarstva financija SR, a INEKO ih je dobio **zahtjevom za pristup informacijama**.
- **Metodologija [14] [P]:**
  - "Finančné zdravie" je broj od 0 (najlošije) do 6 (najbolje).
  - Računa se iz podataka za **4 uzastopne godine**.
  - Ponderirani je prosjek 5 komponenti: ukupni dug 30 %, servis duga 10 %, saldo tekućeg računa 30 %, dospjele obveze 15 % i obveze dospjele više od 60 dana 15 %.
  - Uz to postoji 15 omjera "financijske stabilnosti" i 17 ulaznih pokazatelja.
- **UX profila (snimka `01-ineko-profil.png`) [15] [P]:**
  - Velika ocjena "3,9 z max. 6" s riječju **"Dostatočné"** (dovoljno).
  - Pet vodoravnih traka s ocjenom komponente na skali 0–6 i obojenom legendom ispod.
  - Struktura prihoda i rashoda u obliku krafne, uz trake koje **sivom sjenom pokazuju prosjek gradova** ("priemer miest").
  - Padajući izbornik godine (2010.–2025.) i trend broja stanovnika.
- **Pouke:**
  - Ocjena, riječ i raščlamba na komponente je dobar obrazac.
  - Siva sjena prosjeka usporedivih jedinica ne opterećuje sučelje, a daje kontekst.
  - Odricanje u podnožju je izvrsno i treba ga preuzeti: "Údaje nehodnotia efektívnosť, ale udržateľnosť hospodárenia" (podaci ne ocjenjuju učinkovitost nego održivost poslovanja).
- **Što izbjeći:**
  - Naslovnica prikazuje **3 najbolja i 3 najgora** grada i općine **imenom**.
  - Profil prikazuje **ime i stranku gradonačelnika**.
  - U hrvatskom kontekstu oboje je "prozivanje", pa to ne treba preuzimati.

### 1.5 Portugal: Anuário Financeiro dos Municípios Portugueses

- **Vlasnik:** godišnjak izlazi uz potporu Ordem dos Contabilistas Certificados (OCC) i Tribunal de Contas. Ima 19 ili više izdanja [S].
- **Metoda [16] [S]:**
  - Rang "eficiência financeira" se računa iz 10 pokazatelja. Među njima su likvidnost, obveze po stanovniku, prosječni rok plaćanja, indeks ukupnog duga i izravni porezi po stanovniku.
  - Rang je **odvojen po veličini** (velike, srednje i male općine).
  - Objavljuje se samo top 100.
- **Pojava u medijima:** naslovi poput "oko 80 % općina financijski 'nezdravo'" (RTP) [17].
- **Pouke:** usporedba unutar razreda veličine je ispravna. Nacionalna rang-lista generira negativne naslove.
- **Nedostaci:** to je PDF godišnjak, a ne interaktivan alat.

### 1.6 Španjolska: Gobierto, Civio i podaci Ministarstva financija

- **Gobierto Presupuestos Municipales** (presupuestos.gobierto.es, tvrtka Populate) [18][19] [P]. Snimka je `02-gobierto-orgiva.png`.
  - Pokriva sve španjolske općine iz podataka Ministarstva financija (Hacienda).
  - Ima funkcije "Compara", "Ránkings" i "Mapas". Svi iznosi su i po stanovniku.
- **Zanimljivi UX obrasci na Gobiertu:**
  - Poruke su segmentirane po publici: *para ciudadanos / periodistas / municipios*.
  - Kartica **"¿Cuánto se gasta Órgiva en … Bibliotecas Públicas?"** sadrži rang (#2629/2752) i gumb "Enséñame otra" (pokaži mi drugu). Igra je dobra za angažman.
  - Gumbi pitaju "¿Entiendes de qué va esta partida? ¿Te parece mucho, poco?" (razumiješ li stavku, je li ti to puno ili malo).
  - **Pravo odgovora:** "¿Eres responsable de este municipio? Añade anotaciones" (jesi li odgovoran za ovu općinu, dodaj napomene).
  - Postoji usporedba s prošlom godinom i mjehurićasti dijagram "han subido / han bajado" (porasle i pale stavke).
- **Civio "¿Dónde van mis impuestos?"** (dondevanmisimpuestos.es) [20][21] [P]:
  - Danas prikazuje državni proračun.
  - Kod je otvoren (na temelju Open Data Aragón), a općine i regije su ga koristile za vlastite portale [S].
  - Edukativni obrasci: **"Visita guiada"** (vođena tura), **"Ojo con esto"** (na što paziti), **"¿Qué significa…?"** (rječnik).
- **Hacienda** objavljuje dug ("deuda viva") i prosječni rok plaćanja (PMP) po općini, a općine ga tromjesečno dostavljaju [S].
- **Pouke:**
  - Rječnik i vođena tura su jeftini, a jako pomažu laicima.
  - Kanal za napomene jedinice smanjuje dojam prozivanja.
  - Rang uvijek treba imati nazivnik (#2629/2752).

### 1.7 Češka: Monitor státní pokladny (Ministarstvo financija)

- **URL:** monitor.statnipokladna.gov.cz [22] [P]. Pokriva 6.254 općine, 14 regija i 710 udruženja općina.
- **Funkcije:**
  - Službeni portal ministarstva s mjesečnim financijskim podacima.
  - **"Compare municipalities"** omogućuje usporedbu do 5 općina [23].
  - **Data Catalog** sadrži otvorene podatke, web servis i šifrarnike.
  - **iView** je ugradivi widget koji općina umetne na svoju stranicu jednim retkom HTML-a [24] [P].
- **Pouke:**
  - Widget za ugradnju na mrežne stranice JLS je izravna "integracija s postojećim javnim sustavima". Za nas je to jeftin bod za arhitekturu.
  - Država može biti izdavač ovakvog alata. Naš prototip je argument da to napravi i Ministarstvo financija RH.
- **Nedostaci:** nema sintetske ocjene i nema objašnjenja za laike.

### 1.8 Poljska

- **Ministarstvo financija** od 2008. svake godine objavljuje "Wskaźniki do oceny sytuacji finansowej jednostek samorządu terytorialnego". Zadnje izdanje pokriva 2019.–2024. [25] [S].
  - Pokazatelji su proračunski, po stanovniku i za dug.
  - Prikazuju se po jedinici, uz prosjeke, minimume i maksimume po tipu jedinice.
  - Format su PDF i tablice.
- **Rang-liste:** "Wspólnota" objavljuje rang imućnosti (autori Swianiewicz i Łukomska) [26]. Fundacja Instytut Studiów Wschodnich objavljuje "Ranking Finansowy Samorządu Terytorialnego" (7 pokazatelja, proglašenje na Kraljevskom dvorcu) [27] [S].
- **Pouke:** država daje pokazatelje, a nevladin sektor od njih radi rang i nagrade. Nagrađuje se najbolje, a najgori se ne prozivaju.

### 1.9 Slovenija

- **Nismo našli** javni portal koji uspoređuje fiskalno zdravlje 212 općina.
- Skupnost občin Slovenije 2021. je predstavila aplikaciju za vizualizaciju općinskih podataka (primjerena potrošnja, povprečnina) [28] [S].
- **ERAR** (Komisija za sprječavanje korupcije) prikazuje transakcije javnog sektora, uključujući općine. Ima preko 185 milijuna transakcija [29] [S].
  - Pouka o kvaliteti podataka: GEN-I je zbog krivo prikazanih isplata od države tražio 40.000 € odštete [30] [S].
  - **Za nas:** treba označavati kvalitetu podataka, ne tvrditi više nego što podaci dopuštaju i imati kanal za ispravke.

### 1.10 Estonija: minuomavalitsus.ee (službeni indeks 1–5)

- **URL:** minuomavalitsus.ee. Vodi ga Ministarstvo regionalnih poslova i poljoprivrede [31] [P]. Snimka je `05-eesti-finantsolukorra-indeks.png`.
- **"Omavalitsuste finantsolukorra indeks" (indeks financijskog stanja općina):**
  - Sastoji se od **7 pokazatelja ocijenjenih na skali od 1 do 5** (5 = najbolje, zeleno).
  - **Pragovi su izvedeni iz povijesne razdiobe** pokazatelja općina, uz razine održivosti.
  - Namjena je **prepoznavanje rizika** od financijskih poteškoća.
  - Uz njega postoji i zaseban **indeks učinkovitosti** (7 pokazatelja).
  - Izvor je riigiraha.fin.ee (državna riznica) i Statistički ured.
  - Pogledi: naslovnica s kartom, metodologija, "KOV vaade" (pogled po jedinici), "KOV grupiti vaade" (**pogled po skupinama općina**), sirovi podaci.
  - Zadnje ažuriranje bilo je 19.3.2026.
- **Ostatak portala:**
  - Razine usluga za 15 područja, zadovoljstvo stanovnika (anketa 2024.), karta i tablica za usporedbu.
  - Otvoreni podaci i metodologija skupina općina.
- **Pouke:**
  - **Najbliži službeni analog** našoj ideji: država sama radi ocjenu 1–5.
  - Smjer 5 = najbolje i kalibracija pragova na domaćoj razdiobi su upravo ono što preporučujemo i za Hrvatsku.
- **Nedostaci:** izrađen je u Power BI-ju, koji je vlasnički softver. Za datathon smijemo koristiti samo otvoreni kod.

### 1.11 SAD

- **NY State Comptroller – Fiscal Stress Monitoring System (FSMS)** [34]–[36]. Stranice su iza Cloudflarea [N], a opis je iz sekundarnih izvora [S].
  - Sustav postoji od 2013.
  - Kategorije su *significant / moderate / susceptible / no designation*. Za škole vrijede rasponi bodova 65–100 / 45–64,9 / 25–44,9 / ispod 25 [36].
  - Ulazni pokazatelji su fond-saldo, operativni manjkovi, novac i kratkoročno zaduživanje.
  - Stranica s 10-godišnjom statistikom ima **interaktivnu kartu po okruzima**: klik prikazuje status i ocjene po godinama. Postoji i zasebna kartica za jedinice koje **nisu predale izvješće**.
  - Prema našem saznanju sustav ima i zasebnu "environmental" ocjenu (stanovništvo, siromaštvo, porezna osnovica). **To nismo provjerili u ovoj sesiji.**
  - **Pouke:**
    - Opisne kategorije umjesto školske ocjene ("pod umjerenim pritiskom"), što je manje uvredljivo.
    - Sustav javno prati i one koji ne predaju podatke.
    - Odvojeno se prikazuje što jedinica kontrolira (fiskalna ocjena), a što ne kontrolira (okolinski pritisak). To je ključno za pošten prikaz ovisnosti o pomoćima.
- **Truth in Accounting – Financial State of the Cities** [37][38] [S]:
  - Za 75 najvećih gradova računa "Taxpayer Burden/Surplus" po poreznom obvezniku i daje ocjene od A do F.
  - Jedna brojka u dolarima po obvezniku jako dobro radi u medijima.
  - Pojedini mediji ocjene su uokvirili stranački ("gradovi koje vode demokrati"). To je primjer političke zloupotrebe ocjena.
- **Pew Charitable Trusts** [39][40] [S]:
  - 23 savezne države prate fiskalno zdravlje lokalnih jedinica, a 9 ima sustave ranog upozorenja.
  - Preporučuju kombinaciju statičnih pokazatelja i pokazatelja trenda.
  - Preporučuju i tri vrste usporedbe: sa samim sobom kroz vrijeme, s prosjekom države i s normom iz istraživanja.
- **OpenGov** i slični komercijalni SaaS alati za transparentnost proračuna: nismo ih provjeravali. Oni su za jednu jedinicu i nemaju usporedbe.

### 1.12 OpenSpending i OpenBudgets.eu

- **OpenSpending** (openspending.org) [41] [P] je danas katalog skupova podataka na PortalJS-u (85 skupova, 32 zemlje, uključujući HR), uz slogan "It's our money!". Nije alat za ocjenjivanje.
- **OpenBudgets.eu** (H2020, 2015.–2017.) [42] [S] je bila platforma za proračunske podatke temeljena na linked data pristupu. Ne izgleda da se aktivno razvija.
- **Pouka:** generičke platforme za proračune nisu dugo živjele. Vrijednost nastaje kad se odgovori na **konkretno pitanje** ("je li moja općina financijski zdrava?").

### 1.13 Japan: Japan Dashboard, financije općina (2026.)

- **URL:** digital.go.jp/en/resources/japandashboard/municipal-finance. Izradili su ga Digital Agency i Ministarstvo unutarnjih poslova i komunikacija (MIC) [43][44] [P]. Snimka je `04-japan-dashboard-finance.png`.
  - Verzija za općine izašla je 24.4.2026., a za prefekture 26.5.2026.
- **UX:**
  - Pločice prikazuju 5-godišnji trend za 4 ključna pokazatelja: indeks fiskalne snage, omjer tekućih rashoda, omjer servisa duga i omjer budućeg tereta.
  - **Puna linija prikazuje odabranu jedinicu, a točkasta prosjek "sličnih jedinica" (類似団体).**
  - U podnožju piše u koju skupinu jedinica spada (npr. Sapporo je "grad određen uredbom").
  - Postoje "analitički komentari" uz svaki pokazatelj. Prema opisu ih neke jedinice nemaju, što upućuje da ih pišu same jedinice.
  - Ostalo: karta jednog pokazatelja, ZIP strukturiranih podataka, video upute, obrazac za povratnu informaciju.
- **Pouke:**
  - Mali grafikoni trenda s linijom sličnih jedinica su vrlo čitljivi. Treba ih preuzeti u profil.
  - Prikaz kojoj skupini jedinica pripada je jednostavna i poštena kontekstualizacija.
- **Nedostaci:** sve je u Power BI-ju i nema sintetske ocjene.

### 1.14 Ostalo (kratko)

- **Nizozemska: waarstaatjegemeente.nl (VNG).** Usporedba općina po temama, alat "AMIGO" koji predlaže usporedive općine, dijeljenje putem URL-a i izvoz [80] [S].

---

## 2. Simulatori spajanja i alati reformi

| Država i alat | Što je pokazivalo | Kako | Status |
|---|---|---|---|
| **Moldova – AmalgaSim 2.6.6** (amalgamator.gov.md, Vlada Moldove, potpora Sida i SALAR International) [55][56] | Odabrane jedinice na karti spaja u novu jedinicu. Provjerava zakonske kriterije (Zakon 225/2023: **stanovništvo ≥ 3.000, kontinuirani teritorij**). Bira središte "Auto" bodovanjem (stanovništvo, fiskalni kapacitet, usluge). **Procjenjuje transfere** (pripremni transfer, kapitalni transfer, potpora proračunu kroz 3 godine) prema HG 925/2023. | Karta svih jedinica obojena razredom stanovništva. Desni panel sadrži provjeru kriterija, zbroj stanovništva i površine, odabir središta, transfere i ukupni iznos. Odricanje: "Datele din simulator au caracter orientativ" (podaci su orijentacijski). | **Živ [P]**, snimka `06-moldova-amalgasim.png`. Klik na kartu u headless pregledniku nismo uspjeli izvesti, pa je panel opisan iz teksta stranice. |
| **Norveška – nykommune.no** (ministarstvo, 2014.–2016.) [45][46] | Ključne brojke i projekcije za postojeće i **zamišljene spojene** općine: stanovništvo, potreba za radnom snagom, gospodarstvo, struktura gospodarstva, dnevne migracije. Usporedba do 14 općina, izvoz u Excel. | Alat za općine u reformi (428 → 356 općina 2020.). | **Domena više ne postoji [P]** (DNS ne radi). Alat je bio vezan uz reformu i ugašen je kad je reforma završila. |
| **Estonija – reforma 2017.** [32][33][82] | Kriterij minimalno 5.000 stanovnika. Broj općina pao je s 213 na 79. Oko 160 općina spojilo se dobrovoljno, ostale prisilno. **Poticaj je bio 100 € po stanovniku** (min. 300.000 €, maks. 800.000 € po općini), ukupno 64,5 mil. € za 47 novih općina. | Formula poticaja je javna, pa ju je lako ugraditi u kalkulator. Javnog web-simulatora nije bilo. | Reforma je završena. Novi prijedlog predviđa 30 €/st. (maks. 700.000 €) [S]. |
| **Finska – kuntaliitos** [53][54] | Država nadoknađuje gubitak državnih potpora u godini spajanja i još 3 godine. Postoji jednokratna potpora za spajanje. Postoje zakonski "kriterij krizne općine" (porezna stopa, dug, kumulativni manjak). | Izračun radi ministarstvo za svaki slučaj. | Nismo našli javni kalkulator. |
| **Danska – reforma 2007.** [47][48] | Broj općina pao je s 271 na 98. Prosječna veličina narasla je s manje od 20.000 na oko 55.000 stanovnika. | Ex-post evaluacija: **spojene općine nisu ostvarile očekivanu ekonomiju razmjera u administraciji**, a ex-ante procjene su bile "napuhane radi legitimacije reforme" (Houlberg 2011.). | Važan protuargument za umjerenost u simulatoru. |
| **Nizozemska – herindeling** [49]–[52] | Za svaki prijedlog spajanja radi se "**herindelingsscan**": financijski pregled koji izrađuju pokrajina ili savjetnici. Spojena općina iz gemeentefonds dobiva naknadu za troškove spajanja kroz 5 godina, ali gubi "fiksni iznos" po općini koja nestaje. | Izvješća u PDF-u. **COELO (Allers & Geertsema 2014.): rashodi ne padaju nakon spajanja, ni kod najmanjih općina.** | Formula fiksnog iznosa je primjer kako spajanje mijenja izravnanje. Isto vrijedi za hrvatsko fiskalno izravnanje. |
| **Švicarska – kanton Fribourg** [57] | Oko 30 kontekstualnih pokazatelja (demografija, financije, porezi, gospodarstvo, škole, financijsko izravnanje) za projekte spajanja. | Pomoć pri odluci, nije kalkulator. | [S] |
| **Hrvatska – NPOO i funkcionalno spajanje** [58][59][83][84] | Cilj je bio funkcionalno spajanje najmanje 40 % JLS do 2026. Stvarno spajanje nije provela nijedna jedinica. Zajednički upravni odjel osnovala je 21 jedinica (od toga 2 grada). Preko 100 spajanja ostvareno je preko zajedničkog trgovačkog društva ili ustanove. Planirano je 44,5 mil. € (nakon rebalansa 24,8 mil. €), a isplaćeno 7,1 mil. € (15,9 %). Analiza EIZ-a (Jurlina Alibegović, Novi list 28.1.2026.) [P]: "**neistražena je percepcija stanovnika**", a "građani malo znaju". Svjetska banka (2022.) daje međunarodni pregled i opcije reforme. U sažetku nismo našli simulator [S]. | Nema alata. | **Praznina koju popunjavamo.** |

**Što možemo naučiti za simulator:**

1. **AmalgaSim je gotov UX predložak:**
   - Na karti se biraju susjedne jedinice.
   - Kriteriji su zelene ili sive kvačice (u RH npr. "susjedne", "ista županija", "zbroj stanovnika ≥ X").
   - Panel sadrži zbroj, novo središte i iznos poticaja.
   - Iznos je jasno označen kao orijentacijski.
2. **Nijedan alat ne prikazuje "prije i poslije" financijskog zdravlja.** Svi prikazuju samo zbroj stanovništva, površine i poticaje. **Ponovni izračun ocjene za spojenu jedinicu je naša novost.**
3. **Uštede kao raspon i scenariji, nikad kao jedan broj** (zbog Danske i Nizozemske). Naša validacija daje gornju granicu od oko 41 mil. € godišnje, i to samo za jedinice ispod 2.500 stanovnika.
4. **Poticaje i izravnanje treba modelirati eksplicitno:**
   - Hrvatska pravila iz 2022.: spojena jedinica može dobiti dvostruki iznos fiskalnog izravnanja manje jedinice, a funkcionalno spojene jedinice zadržavaju dotadašnja proračunska sredstva najmanje 2 godine [S].
   - Pravila treba provjeriti u tekstu propisa prije ugradnje.
5. **Alat vezan uz trenutak reforme brzo umre** (nykommune.no). Zato ga treba graditi kao dio trajnog pregleda fiskalnog zdravlja, ne kao jednokratnu kampanju.

---

## 3. Hrvatska: što postoji

### 3.1 Institut za javne financije (IJF)

- **Transparentnost proračuna lokalnih jedinica** [60][61] [P]. Snimka je `03-ijf-transparentnost-karta.png`.
  - Bilo je 9 ciklusa (2015.–2023.) za svih 576 jedinica. Ocjena 0–5 broji objavljene ključne dokumente.
  - Prosjek je narastao s 1,8 na 4,6.
  - **Statična karta** (OpenStreetMap) s 6 boja, podloga je "Arhiva prethodnih istraživanja".
  - Zadnji ciklus je studeni 2022. – travanj 2023. Novijeg nismo našli.
- **Osvrti IJF-a o izvršenju lokalnih proračuna** [62][63] [S].
  - **Excel tablice** s financijskim podacima za 2014.–2022. i transparentnošću za 2015.–2023.
  - Analize poput "najbogatija općina imala je prihode kao 24 najsiromašnije zajedno".
  - IJF navodi da su Excel tablice Ministarstva financija "teške za snalaženje i usporedbu", i to je razlog zašto IJF radi sažetke.
  - IJF upozorava na strukturne razlike (obala i kontinent) i na velik udio državnih i EU pomoći.
- **Projekt "Efikasnost javnih usluga na lokalnim razinama vlasti – definicije, mjerenja i analize (EJU)"** je naveden na naslovnici IJF-a [60] [P]. Detalje nismo našli. **Moguće preklapanje s našom temom, treba pratiti** i u dokumentaciji ga citirati kao srodan rad.
- **Ocjena:** IJF je glavni stručni autoritet. Nema interaktivni alat i ne ocjenjuje financijsko zdravlje. Transparentnost je dobar **dodatni sloj** za povezivanje izvora (COULD).

### 3.2 Ministarstvo financija

- Objavljuje financijske izvještaje JLP(R)S, odnosno PR-RAS, RAS-funkcijski i Bilancu, kao velike Excel datoteke, a dio i na data.gov.hr (npr. "Lokalni proračun 2001.", CKAN pretraga [79] [P]).
- **Nismo našli nikakvu interaktivnu vizualizaciju ili ocjenu** Ministarstva financija za lokalne proračune [S].
- **Prijedlog zaključka Vlade (MF), 160. sjednica, 16.4.2026.** [78] [P]:
  - Uvodi se "kriterij dobrog financijskog upravljanja" za pomoći iz državnog proračuna koje se dodjeljuju na temelju poziva.
  - Prvi uvjet: manjak bez EU izvora ≤ 10 % ukupnih prihoda umanjenih za EU izvore, iz zadnjeg godišnjeg izvještaja.
  - Drugi uvjet: poduzete su sve aktivnosti za naplatu prihoda.
  - Ministarstvo financija podatke daje "na zahtjev".
  - **Usvajanje treba potvrditi.**
  - **Za nas:** državna tijela trebaju upravo ovakav pokazatelj po jedinici, a danas ga dobivaju "na zahtjev". To je jak argument za relevantnost (izazov C) i za integraciju s javnim sustavima.

### 3.3 Gradske aplikacije "otvoreni proračun" i vendorska rješenja

| Alat | Što radi | Status |
|---|---|---|
| **Rijeka – otvoreniproracun.rijeka.hr** [64] | Isplate iz proračuna, ugovori i narudžbenice, plaće dužnosnika (podaci riznice). Softver "GPSWebTransparentnost" v1.4.4. | Živ [P] |
| **Bjelovar** (2019.) [65], **Pula e-Proračun** (prva interaktivna vizualizacija u RH) [66], **Poreč iTransparentnost / Otvoreni grad** [67], **Zagreb Smart City Hub** i hackathon **HACKL** [68], **Omišalj** (isplate) | Transparentnost isplata i proračuna **jedne** jedinice | [S], pojedinačno nismo provjeravali |
| **proracun.hr** (Mobes kvaliteta d.o.o.) [69] | "Aplikacija za postavljanje, praćenje i grafički prikaz proračuna JLS", baza proračuna, isplata i savjetovanja, "Vodič kroz proračun" | Živ [P] |
| **CROračun / PROračun** (Coin d.o.o. Pula, 2016.) [70][71] | CROračun je **uspoređivao proračune svih JLS** iz podataka MF-a na data.gov.hr, apsolutno i po stanovniku. PROračun prikazuje jednu jedinicu i ima modul "Proračun u malom". | **croracun.hr danas preusmjerava na prijavu [P]**, pa nije javno dostupan |
| **Otvoreni proračun Hrvatske zajednice županija** [72] | Usporediva vizualizacija proračuna 20 županija i Grada Zagreba | [S], URL nismo pronašli |
| **otvorenaopcina.hr** | — | **Ne odgovara [P]** (veza nije uspostavljena) |

**Zaključak:** ovi alati odgovaraju na pitanje "na što je moja jedinica potrošila novac" (isplate). **Nijedan ne odgovara na pitanje "je li moja jedinica financijski održiva u odnosu na slične"**. CROračun je bio najbliži, ali bez ocjene i danas nije javan.

### 3.4 Ostali hrvatski izvori i inicijative

- **razvoj.gov.hr – indeks razvijenosti 2024.** [73] [S]:
  - Ima 5 skupina JLS i 4 skupine županija.
  - Podaci su iz razdoblja 2020.–2022. i iz popisa 2021.
  - Objavljeno kao PDF tablice, a interaktivnu kartu nismo pronašli.
  - **Koristi se za skupine sličnih jedinica**, kao drugi izvor koji povezujemo.
- **Državni ured za reviziju (DUR)** [74] [S]:
  - Pojedinačna izvješća o financijskim revizijama JLS u PDF-u.
  - Mišljenja o financijskim izvještajima i o usklađenosti su bezuvjetna ili uvjetna.
  - Skupno izvješće Saboru (ožujak 2026.).
  - Može biti sloj "revizijsko mišljenje" (COULD, jer je izvlačenje iz PDF-a skupo).
- **GONG – LOTUS** (2009. i 2011./12.) [75] [S]: indeks transparentnosti lokalne samouprave s 51 pokazateljem. Stariji je i nije fiskalni.
- **Hackathoni:** HACKL (Zagreb, otvoreni proračun) [68], ODEON open data hackathon (HAMAG-BICRO) [76], Code for Croatia ODD2020 [77] [S]. **Nismo našli** prethodni hackathonski ili datathonski projekt o fiskalnom zdravlju svih JLS ni o simulaciji spajanja. Ni objave pobjednika prethodnih datathona MPUDT-a nismo pronašli.
- **Akademski radovi:** brojni diplomski radovi (EFZG, EFST, EFOS) analiziraju financije pojedinih JLS. EIZ (Jurlina Alibegović) piše o fiskalnoj (ne)samostalnosti [S]. **Nismo našli** objavljen hrvatski model ranog upozorenja ni javnu rang-listu financijskog zdravlja.

### 3.5 Potvrda

> **Prema svemu što smo mogli pronaći, nijedan javno dostupan alat u Hrvatskoj ne daje ocjenu financijskog zdravlja za sve JLS i ne simulira fiskalni učinak spajanja susjednih jedinica.** Ovo ograničenje treba navesti u dokumentaciji. Postoji projekt IJF-a o efikasnosti lokalnih usluga čije rezultate nismo vidjeli. Moguće je i da postoje interni alati MF-a ili MPUDT-a.

---

## 4. Detaljni pregled najpoučnijih alata (sa snimkama)

### 4.1 INEKO profil općine (`01-ineko-profil.png`)

- **Što je dobro:**
  - Ocjena je velik broj u obojenom kvadratu s riječju ("Dostatočné").
  - Uz nju je pet traka komponenti s jednakom skalom 0–6 i obojenom legendom "0 – najhoršie … najlepšie – 6".
  - Odmah ispod je poveznica "Podrobné hodnotenie a informácie →" (progresivno otkrivanje).
  - Strukture prihoda i rashoda imaju sivu sjenu prosjeka gradova iza svake trake.
  - Godina se bira u gornjem desnom kutu.
- **Što preuzeti:**
  - Raspored: ocjena + komponente + "zašto" + struktura s prosjekom sličnih.
  - Rečenicu o održivosti umjesto učinkovitosti.
- **Što ne preuzeti:**
  - Ime i stranku gradonačelnika na profilu.
  - "Top 3 / bottom 3" po imenu na naslovnici.

### 4.2 Japan Dashboard, financije općina (`04-japan-dashboard-finance.png`)

- **Što je dobro:**
  - 8 pločica: 4 apsolutna iznosa (prihod, saldo, rezerve, dug) i 4 omjera s 5-godišnjim trendom.
  - Puna linija prikazuje jedinicu, točkasta prosjek sličnih.
  - Naslov svake pločice ima broj za zadnju godinu velikim slovima.
  - U podnožju piše "skupina sličnih je …".
  - Ikonica (i) uz svaki pokazatelj vodi na definiciju.
- **Što preuzeti:**
  - Točno ovaj obrazac malih grafikona za naših 5 komponenti KDZ-a, uz liniju medijana skupine.
  - Rečenicu "Uspoređujemo s: općine 1.000–2.500 st., III. skupina razvijenosti (N = 84)".

### 4.3 Estonski indeks financijskog stanja (`05-eesti-finantsolukorra-indeks.png`)

- **Što je dobro:**
  - Na naslovnici su samo naslov, tri kratka odlomka (svrha, kako se računa, izvori) i karta s legendom 1–5 (crveno → zeleno).
  - Kartice za metodologiju, pogled po jedinici, pogled po skupinama i sirove podatke.
  - Pragovi su kalibrirani na domaćoj razdiobi.
- **Što preuzeti:**
  - Smjer skale (5 = najbolje).
  - Kratko objašnjenje metodologije na prvoj stranici.
  - Kartice "Po jedinici / Po skupinama / Sirovi podaci".
- **Na što paziti:** paleta je crveno-zelena, što nije prijateljski za daltoniste. Mi trebamo paletu sigurnu za daltoniste (npr. viridis ili plavo-narančastu) uz tekstualne oznake.

### 4.4 Moldavski AmalgaSim (`06-moldova-amalgasim.png`)

- **Što je dobro:**
  - Cijeli ekran je karta jedinica obojenih po razredu stanovništva, a desno je panel s koracima: Validacija → Odabir → Središte → Transferi.
  - Kriteriji iz zakona prikazani su kao kontrolna lista (krug postaje kvačica).
  - Gumb "Auto" za središte radi uz jasno navedeno bodovanje.
  - Iza svakog iznosa stoji zakonska osnova ("Conform HG 925/2023 · Anexa 1").
  - Odricanje odgovornosti je vidljivo u podnožju, a izvori (BNS, MF) su poveznice.
- **Što preuzeti:**
  - Gotovo cijeli UX simulatora.
  - Za hrvatski kontekst dodajemo ocjenu "prije i poslije" i trošak administracije po stanovniku u tri scenarija.

### 4.5 Gobierto (`02-gobierto-orgiva.png`) i IJF karta (`03-ijf-transparentnost-karta.png`)

- **Gobierto:** igra "Kartica stavke + rang + 'pokaži drugu'" i kanal za napomene jedinice.
- **IJF:** dokaz da karta svih 576 JLS u Hrvatskoj već postoji kao statična slika. Mi je činimo interaktivnom, s pretragom i profilom.

---

## 5. Sinteza: prioritetni popis funkcija

**Kratice kriterija:**

- IZV: izvedivost (10)
- UX: dojam UI/UX (10)
- VID: video (10)
- API: otvoreni podaci preko API-ja (5)
- POV: povezivanje izvora (5)
- REL: relevantnost za izazov C (5)
- UTJ: utjecaj (5)
- INO: inovacija i AI (5)
- ARH: arhitektura i interoperabilnost (5)

**Napor:** S je do pola dana, M 1 do 1,5 dan, L 2 ili više dana (za jednu osobu).

### 5.1 MUST (bez ovoga nema predaje)

| # | Funkcija | Korisnička vrijednost | Kriteriji | Napor | Video trenutak |
|---|---|---|---|---|---|
| M1 | **Profil JLS kao "svjedodžba"**: ocjena **5 = najbolje** + riječ, 5 komponenti KDZ-a kao trake s medijanom sličnih (INEKO), 7-godišnji trend malih grafikona s linijom sličnih (Japan), trogodišnje glađenje ocjene, oznaka kvalitete podataka | Građanin u 10 sekundi vidi stanje i razlog | UX, IZV, UTJ | M | ★★★ "Svjedodžba" se otvara |
| M2 | **Karta 576 JLS + pretraga "Pronađi svoju općinu"**, odabir godine, 3 "leće": ocjena, trošak administracije po st., udio tekućih pomoći. Paleta sigurna za daltoniste. **Naslovnica nije rang-lista.** | Ulaz bez predznanja, geografski obrasci (obala i kontinent, Slavonija) | UX, IZV, VID | M | ★★★ Zum s Hrvatske na općinu |
| M3 | **Slične jedinice**: vrsta (općina/grad/županija) × razred veličine × skupina indeksa razvijenosti (+ obala/kontinent). Prikaz "uspoređujemo s N jedinica". Rang **samo unutar skupine** i uvijek s nazivnikom. | Pošten kontekst: mala ruralna općina se ne uspoređuje sa Zagrebom | POV (MF + DZS + razvoj.gov.hr), UTJ, UX | S–M | ★★ "Bolja od 70 % sličnih" |
| M4 | **AI objašnjenje u jednostavnom jeziku**: 2–3 rečenice po jedinici i godini, generirane **unaprijed** open-weights modelom (npr. Qwen, Llama, Mistral, Gemma, licenca navedena u dokumentaciji). Model dobiva **samo izračunate brojke**. Nakon generiranja **automatska provjera da je svaki broj u tekstu iz ulaza**. Oznaka "AI-generirano, brojke provjerene", a prompt je dostupan na stranici metodologije. Ton je neutralan, bez okrivljavanja. | Laik razumije "zašto 3", a ne samo "3" | INO, UX, UTJ | M | ★★★ "Pitaj zašto" i odgovor se pojavi |
| M5 | **Simulator spajanja (MVP prema AmalgaSimu)**: odabir 2–4 susjedne jedinice na karti, provjera susjedstva i iste županije, zbroj stanovnika. **Ocjena prije i poslije** za spojenu jedinicu. Trošak administracije po st. u **3 scenarija** (bez uštede / medijan razreda veličine / P25 razreda). Vidljive pretpostavke i odricanje odgovornosti. Napomena o dokazima iz Danske i Nizozemske. | Prvi put u RH građanin i vijećnik vide što bi spajanje značilo za brojke | REL, INO, UTJ, VID | L | ★★★ Glavni trenutak videa |
| M6 | **Stranica "Metodologija i podaci"**: formule i pragovi (kalibracija na hrvatsku razdiobu), **popis svih skupova s izdavačem i poveznicom** (obvezno prema pravilima), licence, AI alati, ograničenja, rečenica "ocjenjuje održivost, ne kvalitetu upravljanja", značka "podaci povučeni s data.gov.hr CKAN API-ja dana …" | Povjerenje, ispunjava uvjete natječaja | ARH, API, IZV | S | ★ Kratko u videu |
| M7 | **Otvoreni izlaz**: statični JSON i CSV po jedinici i godini + **OpenAPI 3 specifikacija** (kao Wegweiser), licenca CC BY 4.0, DCAT-AP metapodaci spremni za objavu na data.gov.hr | Drugi (novinari, IJF, MF) mogu ponovno koristiti izračune | ARH, API | S–M | ★ "Svatko može preuzeti" |

### 5.2 SHOULD (ako MUST bude gotov do 4. dana)

| # | Funkcija | Korisnička vrijednost | Kriteriji | Napor | Video |
|---|---|---|---|---|---|
| S1 | **Usporedba 2–4 jedinice** jedne uz drugu (Monitor dopušta 5, Gobierto "Compara") | Vijećnik prije sjednice o proračunu | UX, UTJ | M | ★★ |
| S2 | **Indikator "Vladin kriterij dobrog financijskog upravljanja"** (manjak bez EU ≤ 10 % prihoda bez EU) kao kvačica na profilu i filter na karti, uz napomenu da je riječ o prijedlogu zaključka od 16.4.2026. | Izravna veza s politikom: tijela koja dodjeljuju pomoći dobivaju odgovor odmah, a ne "na zahtjev" | REL, ARH, UTJ | S | ★★ "Ovo bi Vlada htjela znati" |
| S3 | **Ugradivi widget i kartica za dijeljenje** (kao češki iView): `<iframe>` sa "svjedodžbom" za mrežne stranice JLS, OG slika za medije | Integracija s postojećim javnim sustavima, viralnost | ARH, UTJ | S–M | ★ |
| S4 | **Rječnik i oblačići** ("Što znači servis duga?") i **vođena tura od 3 koraka** (Civio) | Laici ne odustaju | UX | S | ★ |
| S5 | **Kontekst "što jedinica ne kontrolira"**: indeks razvijenosti, broj stanovnika i trend, udio tekućih pomoći uz napomenu da je dio strukturan (načelo NY FSMS-a "environmental") | Smanjuje dojam prozivanja siromašnih općina | UTJ, POV | S | ★ |
| S6 | **Oznake kvalitete podataka** po jedinici i godini (nedostaje izvještaj, ekstremna vrijednost, "godine otplate nedefinirane"), kanal "prijavi grešku" (pouka ERAR-a) | Vjerodostojnost, manji pravni rizik | IZV, UX | S | — |

### 5.3 COULD (samo ako ostane vremena, ili kao "daljnji razvoj" u videu)

| # | Funkcija | Vrijednost | Kriteriji | Napor |
|---|---|---|---|---|
| C1 | **Kontrafaktualno objašnjenje** ("Da je trošak administracije na medijanu skupine, ocjena bi bila 4 umjesto 3"), klizači "što ako" na profilu | Pokazuje gdje je poluga, a ne samo krivnju | INO, UTJ | M |
| C2 | **Prijedlog partnera za spajanje** (kao "Auto" u AmalgaSimu): susjedi s kojima spojena jedinica prelazi prag veličine ili najviše podiže ocjenu | Alat za planiranje reforme | INO, REL | M |
| C3 | **Dodatni slojevi**: IJF transparentnost (0–5) i DUR mišljenje (bezuvjetno/uvjetno) po jedinici | Više povezanih izvora | POV | M (prikupljanje podataka) |
| C4 | **"Pitaj podatke"**: prirodni jezik pretvara se u filter nad našim skupom (npr. "općine u Lici s ocjenom ispod 3"), uz open-weights LLM i strogo ograničen izlaz | Inovacija | INO | M–L, rizično |
| C5 | **PDF "fiskalna svjedodžba"** po jedinici za vijećnike (kao Wegweiser Finanzbericht) | Lako se nosi na sjednicu | UTJ | M |
| C6 | **Napomena jedinice / pravo odgovora** (Gobierto, Japan) | Ravnoteža, manje političkog otpora | UTJ | M |
| C7 | Engleska verzija | Šira publika | UX | S |

### 5.4 Inovacije koje bi u Hrvatskoj bile nove

1. **Prva javna ocjena financijskog zdravlja svih 576 JLS** s otvorenom metodologijom i kodom. CROračun nije davao ocjenu, a IJF ocjenjuje transparentnost, ne financije.
2. **Prvi simulator spajanja** s ocjenom prije i poslije. AmalgaSim ima samo transfere, nykommune.no samo brojke.
3. **Objašnjenja koja generira LLM, uz automatsku provjeru brojki.** Takav obrazac nismo našli ni u jednom pregledanom alatu. Japan ima komentare, ali ih pišu ljudi.
4. **Strojno provjerljiv "Vladin kriterij od 10 %"** za sve jedinice, umjesto podataka "na zahtjev".
5. **Kalibracija KDZ pragova na hrvatsku razdiobu**, po uzoru na estonski pristup.

### 5.5 UX načela za fiskalne podatke i laike (politički osjetljiva tema)

1. **Smjer ocjene kao u hrvatskoj školi: 5 = najbolje**, uvijek uz riječ (npr. "vrlo stabilno – stabilno – umjereno – pod pritiskom – ozbiljan pritisak"). Interno se može računati kao KDZ (1 = najbolje), ali **korisniku se nikad ne prikazuje "1" za najbolju jedinicu**.
2. **Opisne kategorije umjesto moralnih.** Govorimo o "pritisku" i "otpornosti", ne o "lošem upravljanju". Ocjenjuje se **održivost**, ne učinkovitost ni poštenje (INEKO).
3. **Naslovnica nije rang-lista.** Naslovnica je karta s pretragom. Nema liste "10 najgorih". Ako postoji rang, onda je unutar skupine sličnih i uvijek s nazivnikom (#12/84). Pozitivne priče se mogu isticati: "najveći napredak u skupini" (pouka iz KDZ Top 250).
4. **Bez imena gradonačelnika i stranaka** na profilu (suprotno INEKO-u). Time se smanjuje stranačko uokvirivanje (pouka iz Truth in Accounting).
5. **Uvijek usporedba sa sličnima i sa samim sobom kroz vrijeme** (Pew, Japan, CIPFA).
6. **Glađenje ocjene na 3 godine**, uz godišnje vrijednosti u grafikonu (INEKO 4 godine, KDZ ranking 3 godine). Naša validacija pokazuje da se jednogodišnja ocjena mijenja kod 40–62 % jedinica.
7. **Odvojiti ono što jedinica kontrolira od strukturnog konteksta** (NY FSMS). Ovisnost o pomoćima prikazivati kao kontekst, a ne kao kaznu.
8. **Progresivno otkrivanje:** ocjena i rečenica, zatim 5 komponenti, zatim formule i sirovi podaci, zatim preuzimanje.
9. **Iskrenost o nesigurnosti:**
   - Simulator prikazuje raspon i pretpostavke, uz oznaku "orijentacijski" (AmalgaSim).
   - Ocjena ima oznaku kvalitete podataka.
   - AI tekst je označen kao AI.
10. **Pristupačnost:** paleta sigurna za daltoniste, tekstualne oznake uz boje, kontrast prema WCAG AA i tipkovnička navigacija na karti (alternativa je pretraga).
11. **Rječnik i oblačići** za svaki stručni pojam (Civio "¿Qué significa?").
12. **Kanal za ispravke i napomene jedinica** (Gobierto, ERAR).

### 5.6 Ideje za video do 3 minute

1. **"Svjedodžba za vašu općinu"**: metafora školske svjedodžbe.
   - 0:00–0:20 Problem: 576 jedinica, nitko ne zna je li njegova financijski zdrava, podaci su u Excelu od 100.000 redaka.
   - 0:20–1:30 Demo: Ana iz male općine traži svoju općinu, dobiva ocjenu "4 – stabilno" i 5 "predmeta" (komponente KDZ-a). "Komentar razrednika" je AI objašnjenje. Slijedi usporedba s "razredom" (slične jedinice).
   - 1:30–2:20 Simulator spajanja kao "što ako se spojimo sa susjedima".
   - 2:20–3:00 Arhitektura (API data.gov.hr → izračun → otvoreni API i widget), daljnji razvoj.
   - Metafora odmah radi u Hrvatskoj i nosi UX načelo "5 = najbolje".
2. **"Spoji pa vidi"**: priča o reformi.
   - Hladni početak: "Cilj NPOO-a: 40 % jedinica funkcionalno spojeno. Stvarno spojenih: 0. Isplaćeno 16 % novca."
   - "Zašto? Građani ne znaju što bi spajanje značilo." [59]
   - Demo simulatora na tri susjedne male općine: ocjena prije i poslije, trošak administracije u 3 scenarija, iskreni raspon ("u Danskoj su očekivanja bila prevelika").
   - Završetak: alat za javnu raspravu i prijedlog da ga MPUDT ili MF ugrade na data.gov.hr.
   - Najjače pogađa kriterije REL i UTJ.
3. **"Austrija 20 godina, Slovačka 15, Estonija i Moldova od nedavno – Hrvatska od danas"**: međunarodni okvir u prvih 20 sekundi, kratki isječci snimaka tuđih alata, zatim naš demo. Dobro za dojam inovacije i ozbiljnosti.
4. **Tri persone u 3 minute**: građanka (profil), općinska vijećnica (usporedba i "Vladin kriterij"), novinar ili ministarstvo (karta, API, widget). Pokriva vrijednost za korisnike, ali je teže za montažu.
5. **"Od Excela do objašnjenja"**: put jednog broja od CKAN API-ja preko izračuna i LLM objašnjenja do widgeta na stranici općine. Najbolje pokazuje arhitekturu i API, ali je najmanje emotivno. Bolje kao dio priče 1 nego kao samostalna priča.

**Preporuka:** kombinirati **1 ("Svjedodžba")** kao okvir i **2 ("Spoji pa vidi")** kao vrhunac. Sat u videu: problem 25 s, profil i AI 60 s, simulator 50 s, arhitektura i daljnji razvoj 35 s, završetak 10 s.

---

## Izvori

1. KDZ – Zentrum für Verwaltungsforschung: *KDZ-Quicktest – Leitfaden Version 2.0* (7.5.2025.), objavljeno kod Stadt Salzburg. https://www.stadt-salzburg.at/fileadmin/user_upload/04013/beilage_4_kdz-quicktest_leitfaden.pdf [P]
2. KDZ Newsletter 07/2022, "Bonitätsranking: Die Top 250 Gemeinden 2022". https://www.kdz.eu/en/node/896 [P]
3. offenerhaushalt.at (KDZ). https://www.offenerhaushalt.at [N, Cloudflare 403]
4. Vetter, S.: Masterarbeit o offenerhaushalt.at (FH Vorarlberg). https://opus.fhv.at/files/4640/Masterarbeit_Vetter_Stefanie.pdf [S]
5. Wegweiser Kommune (Bertelsmann Stiftung). https://www.wegweiser-kommune.de/ [P]
6. Wegweiser Kommune – Open Data / REST API / OpenAPI. https://www.wegweiser-kommune.de/open-data [P]
7. Wegweiser Kommune – primjer Finanzbericht (Wetzlar). https://www.wegweiser-kommune.de/data-api/rest/report/export/finanzbericht+wetzlar.pdf [S]
8. Bertelsmann Stiftung – Kommunaler Finanzreport, Kassenkredite. https://www.bertelsmann-stiftung.de/de/unsere-projekte/kommunale-finanzen/kommunaler-finanzreport/kassenkredite [S]
9. CIPFA – Financial Resilience Index. https://www.cipfa.org/services/financial-resilience-index/resilience-index [N, Cloudflare]
10. CIPFA – FRI FAQ. https://cms.cipfa.org/services/financial-resilience-index/frequently-asked-questions [S]
11. GOV.UK – Local authority data explorer (ugašen nakon zatvaranja Ofloga). https://www.gov.uk/government/publications/local-authority-data-explorer [S]
12. ONS – Clustering similar local authorities and statistical nearest neighbours. https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/datasets/clusteringsimilarlocalauthoritiesandstatisticalnearestneighboursintheuk [S]
13. INEKO – Hospodárenie obcí. https://www.hospodarenieobci.sk/ [P]
14. INEKO – Metodika. https://www.hospodarenieobci.sk/metodika [P]
15. INEKO – profil Zlaté Moravce 2025. https://www.hospodarenieobci.sk/profil/samosprava/500968/2025 [P]
16. e-konomista.pt – pokazatelji Anuário Financeiro dos Municípios Portugueses (2017.). https://www.e-konomista.pt/municipios-com-maior-eficiencia-financeira/ [S]
17. RTP – "Cerca de 80% dos municípios com eficiência financeira 'pouco saudável'". https://www.rtp.pt/noticias/economia/cerca-de-80-dos-municipios-com-eficiencia-financeira-pouco-saudavel-segundo-anuario_n1182664 [S]
18. Gobierto Presupuestos Municipales. https://presupuestos.gobierto.es/ [P]
19. Gobierto – Órgiva 2024. https://presupuestos.gobierto.es/municipios/orgiva/2024 [P]
20. Civio – ¿Dónde van mis impuestos? https://dondevanmisimpuestos.es/ [P]
21. Civio – Dossier DVMI (2014.). https://civio.es/uploads/archive/civio/2014/06/Dossier-DVMI-2.pdf [S]
22. Monitor státní pokladny (MF ČR). https://monitor.statnipokladna.gov.cz/ [P]
23. Monitor – usporedba općina. https://monitor.statnipokladna.gov.cz/porovnani [P]
24. Monitor – iView (ugradivi widget). https://monitor.statnipokladna.gov.cz/datovy-katalog/i-view [P]
25. Ministerstwo Finansów RP – Wskaźniki do oceny sytuacji finansowej JST 2019–2024. https://www.gov.pl/attachment/9b849fcf-eb6e-4ea0-937b-fc6021dea4f0 [S]
26. Wspólnota – Ranking: sytuacja finansowa samorządów w 2025 r. https://wspolnota.org.pl/fileadmin/news/RANKINGI/2026/Ranking_-_Sytuacja_finansowa_samorzadow_w_2025_r._1-17.pdf [S]
27. PAP – Prezentacija Rankingu Finansowego Samorządu Terytorialnego za 2025. https://www.pap.pl/mediaroom/prezentacja-rankingu-finansowego-samorzadu-terytorialnego-za-2025-r [S]
28. Skupnost občin Slovenije – predstavitev aplikacije za vizualizacijo občinskih podatkov (2021.). https://arhiv2023.skupnostobcin.si/wp-content/uploads/2021/12/predstavitev-aplikacije-za-vizualizacijo-obcinskih-podatkov-8.12.pdf [S]
29. GOV.SI – Izboljšan vpogled v denarne tokove subjektov javnega sektorja (ERAR, 2025.). https://www.gov.si/novice/2025-03-05-izboljsan-vpogled-v-denarne-tokove-subjektov-javnega-sektorja [S]
30. RTV SLO – GEN-I zahtijeva odštetu zbog krivih podataka na ERAR-u. https://www.rtvslo.si/gospodarstvo/gen-i-zaradi-objave-napacnih-podatkov-na-erarju-od-drzave-zahteva-40-000-evrov-odskodnine/743595 [S]
31. minuomavalitsus.ee – Omavalitsuste finantsolukorra indeks. https://www.minuomavalitsus.ee/omavalitsuste-finantsolukorra-indeks [P]
32. Rahandusministeerium – Administrative-Territorial Reform. https://www.fin.ee/en/administrative-territorial-reform [S]
33. ERR – "Valitsus kinnitas omavalitsuste ühinemistoetused: kokku 65 miljonit eurot". https://www.err.ee/645814/valitsus-kinnitas-omavalitsuste-uhinemistoetused-kokku-65-miljonit-eurot [S]
34. NY OSC – Fiscal Stress Monitoring System, 10-year statistics. https://www.osc.ny.gov/local-government/fiscal-monitoring/fiscal-stress-monitoring-system-10-year-statistics [N, Cloudflare]
35. NY OSC – priopćenje rujan 2025. https://www.osc.ny.gov/press/releases/2025/09/dinapoli-announces-latest-fiscal-stress-scores [S]
36. NY OSC – FSMS školski okruzi 2024. (rasponi bodova). https://www.osc.ny.gov/files/local-government/publications/pdf/2024-fsms-schools.pdf [S]
37. Truth in Accounting – Financial State of the Cities 2024. https://www.truthinaccounting.org/library/doclib/Financial-State-of-the-Cities-2024.pdf [S]
38. Truth in Accounting – Data-Z. https://www.data-z.org/ [P]
39. Pew – State Strategies to Detect Local Fiscal Distress (2017.). https://www.pewtrusts.org/en/research-and-analysis/fact-sheets/2017/08/state-strategies-to-detect-local-fiscal-distress [S]
40. Pew – Early Warning Systems Can Help States Identify Signs of Fiscal Distress (2021.). https://www.pewtrusts.org/research-and-analysis/articles/2021/03/04/early-warning-systems-can-help-states-identify-signs-of-fiscal-distress [S]
41. OpenSpending. https://www.openspending.org/ [P]
42. CORDIS – OpenBudgets.eu (H2020 645833). https://www.cordis.europa.eu/project/id/645833 [S]
43. Digital Agency (Japan) – Local Finance (by City) Dashboard. https://www.digital.go.jp/en/resources/japandashboard/municipal-finance [P]
44. nippon.com / Jiji – "Japan Releases Tool to Visualize Local Govt Finances" (13.6.2026.). https://www.nippon.com/en/news/yjj2026061300159/ [S]
45. Regjeringen.no – "Ny og bedre versjon av Ny kommune". https://www.regjeringen.no/nb/aktuelt/ny-og-bedre-versjon-av-ny-kommune/id2396366/ [S]
46. Regjeringen.no – Reform of local government. https://www.regjeringen.no/en/topics/kommuner-og-regioner/kommunereform/reform-of-local-government/id2548429 [S]
47. Houlberg, K. (2011.): "Administrative economies of scale in local government in Denmark", *Scandinavian Journal of Public Administration*. https://publicera.kb.se/sjpa/article/view/16195 [S]
48. Danske Regioner – The local government reform and evaluation. https://www.regioner.dk/media/3029/the-local-government-reform-and-evaluation-20.pdf [S]
49. Allers, M. & Geertsema, B. (2014.): "The effects of local government amalgamation on public spending and service levels", Univ. of Groningen. https://ideas.repec.org/p/gro/rugsom/14019-eef.html [S]
50. ESB – "Geen grotere doelmatigheid door herindeling gemeenten". https://esb.nu/geen-grotere-doelmatigheid-door-herindeling-gemeenten/ [S]
51. Herindelingsscan Noordoost Fryslân (primjer). https://cuatro.sim-cdn.nl/fryslan/uploads/Herindelingsscan%20Noordoost%20Fryslan.pdf [S]
52. Raad voor het openbaar bestuur – Advies wijziging maatstaf herindeling (2013.). https://www.raadopenbaarbestuur.nl/binaries/raad-openbaar-bestuur/documenten/publicaties/2013/01/24/advies-wijziging-maatstaf-herindeling/Wijziging_maatstaf_gemeentelijke_herindeling_Adviesbvrief_201301.pdf [S]
53. Valtiovarainministeriö – Kuntien yhdistymisen tuki. https://vm.fi/kuntien-yhdistymisen-tuki [S]
54. Kuntaliitto – Kriisikuntakriteeristö (2019.). https://www.kuntaliitto.fi/sites/default/files/media/file/12_Korento_Sari_Kriisikuntakriteeristo_Kuma2019.pdf [S]
55. AmalgaSim 2.6.6 – Moldova (simulator.gov.md → amalgamator.gov.md). https://amalgamator.gov.md/ [P]
56. UNDP Moldova – O viziune comună: o administrare mai eficientă a localităților învecinate. https://www.undp.org/ro/node/517486 [S]
57. Kanton Fribourg – analitičke i metodološke osnove za spajanja općina. https://www.fr.ch/de/staat-und-recht/gemeinden/ein-fusionsprojekt-von-gemeinden-erarbeiten/leitfaden-fuer-die-begleitung-von-gemeindefusionen/analytische-und-methodische-grundlagen-fuer-die-begleitung-rationeller-fusionen [S]
58. World Bank – Municipal Mergers and Associations: International Experience and Reform Options for Croatia (2022./2023.). https://www.worldbank.org/en/country/croatia/publication/croatia-municipal-mergers [S]
59. Novi list (28.1.2026.) – "Papir trpi sve, ne i praksa: Ideja dobrovoljnog spajanja općina i gradova doživjela je fijasko". https://www.novilist.hr/novosti/papir-trpi-sve-ne-i-praksa-ideja-dobrovoljnog-spajanja-opcina-i-gradova-dozivjela-je-fijasko/ [P]
60. Institut za javne financije – naslovnica (transparentnost, projekt EJU). https://www.ijf.hr/ [P]
61. IJF – Transparentnost lokalnih proračuna (studeni 2022. – travanj 2023.). https://www.ijf.hr/hr/transparentnost-2023/ [P]
62. IJF – Osvrti Instituta za javne financije. https://www.ijf.hr/hr/publikacije/povremene/osvrti-instituta-za-javne-financije/ [S]
63. tportal (7.1.2022.) – IJF: najbogatija općina imala je prihode kao 24 najsiromašnije zajedno. https://www.tportal.hr/vijesti/clanak/najbogatija-opcina-u-hrvatskoj-imala-je-prihode-kao-24-najsiromasnije-opcine-zajedno-20220107 [S]
64. Grad Rijeka – Otvoreni proračun (transparentnost). https://otvoreniproracun.rijeka.hr/ [P]
65. tportal (2019.) – Bjelovar otvoreni proračun. https://www.tportal.hr/vijesti/clanak/bjelovarcani-ce-vidjeti-svaku-potrosenu-kuna-i-place-svakog-zaposlenog-u-gradskoj-upravi-foto-20190519 [S]
66. IDS – Pula prvi grad s interaktivnom vizualizacijom e-Proračun. https://arhiva.ids-ddi.com/vijesti/lokalne/5416/miletic-pula-je-prvi-grad-u-hrvatskoj-koji-je-uveo-interaktivnu-vizualizaciju-e-proracun/index.html [S]
67. IDS – Poreč: uvid u isplate iz gradskog proračuna i financijske kartice. https://arhiva.ids-ddi.com/vijesti/lokalne/7371/persuric-svima-omogucen-uvid-u-isplate-iz-gradskog-proracuna-i-financijske-kartice/index.html [S]
68. Dnevnik.hr – Tomašević predstavlja otvoreni proračun Grada Zagreba (Smart City Hub). https://dnevnik.hr/vijesti/hrvatska/tomasevic-predstavlja-otvoreni-proracun-grada-zagreba-putem-platforme-zagreb-smart-city-hub---693598.html [S]
69. Proracun.hr (Mobes kvaliteta d.o.o.). https://proracun.hr/ [P]
70. Lider Media (7.3.2016.) – "CROračun and PROračun – Tools for Visualizing Local Budgets". https://en.lider.media/2016/03/07/croracun-and-proracun-tools-for-visualizing-local-budgets/ [P]
71. CROračun (danas stranica za prijavu). https://www.croracun.hr/ [P]
72. Šibensko-kninska županija – Otvoreni proračun Hrvatske zajednice županija. https://www.sibensko-kninska-zupanija.hr/novosti/novosti-detalj/goran-pauk-građani-moraju-postati-sudionici-u-kreiranju-proracuna [S]
73. MRRFEU – Vrijednosti indeksa razvijenosti i pokazatelja (2024.). https://razvoj.gov.hr/UserDocsImages/O%20ministarstvu/Regionalni%20razvoj/indeks%20razvijenosti/Vrijednosti%20indeksa%20razvijenosti%20i%20pokazatelja%20za%20izra%C4%8Dun%20indeksa%20razvijenosti.pdf [S]
74. Državni ured za reviziju – Izvješće o financijskoj reviziji lokalnih jedinica (Sabor, ožujak 2026.). https://www.sabor.hr/sites/default/files/uploads/sabor/2026-03-31/153602/IZVJ_FINANCIJSKA_REVIZIJA_LOKALNIH_JEDINICA.pdf [S]
75. IDS – GONG LOTUS: Labin i Pula na vrhu ljestvice transparentnosti. https://www.arhiva.ids-ddi.com/vijesti/aktualno/4637/labin-i-pula-na-vrhu-ljestvice-najtransparentnijih-gradova-u-hrvatskoj/index.html [S]
76. Dnevnik.hr – pobjednici ODEON open data hackathona. https://dnevnik.hr/vijesti/tech/proglaseni-pobjednici-open-data-hackathona-odrzanog-u-okviru-projekta-odeon---622073.html [S]
77. Code for Croatia – Program ODD2020. https://odd.codeforcroatia.org/2020/Program_ODD2020.pdf [S]
78. Vlada RH, 160. sjednica (16.4.2026.), točka 11: Prijedlog zaključka o dodjeli pomoći iz državnog proračuna JLP(R)S (predlagatelj Ministarstvo financija). https://vlada.gov.hr/UserDocsImages/2016/Sjednice/2026/Travanj/160_sjednica_VRH/160%20-%2011.docx?vel=87733 [P, usvajanje nepotvrđeno]
79. data.gov.hr – CKAN API, `package_search` (upit "lokalni proračun izvršenje", 2.11.2026.). https://data.gov.hr/ckan/api/3/action/package_search [P]
80. VNG – Waarstaatjegemeente.nl. https://vng.nl/projecten/waarstaatjegemeentenl [S]
81. LG Inform – VfM profiles, using comparison groups. https://help.vfm.lginform.local.gov.uk/vfm-profiles/using-comparison-groups [S]
82. The Baltic Times – "Estonia has completed administrative reform". https://www.baltictimes.com/estonia_has_completed_administrative_reform [S]
83. Informator – Rezultati dobrovoljnog spajanja općina i gradova. https://informator.hr/strucni-clanci/rezultati-dobrovoljnog-spajanja-opcina-i-gradova [S]
84. tportal (8.8.2022.) – Vlada odlučila financijski stimulirati spajanje općina. https://www.tportal.hr/vijesti/clanak/vlada-odlucila-financijski-stimulirati-spajanje-opcina-a-strucnjaci-upozoravaju-to-je-nova-prilika-za-uhljebljivanje-20220808 [S]
