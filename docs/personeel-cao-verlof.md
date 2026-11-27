# Personeel: contract, rooster, verlof in uren, cao's en feestdagen

Stand 27 november 2026. Ontwerp, nog niet gebouwd. Dit is het deel **Uren en verlof** uit de routekaart (0.8), maar
het hangt nergens van af behalve van Frappe HR en kan dus eerder. De cijfers uit cao's komen uit openbare
samenvattingen; **elke waarde gaat pas het systeem in als ze tegen de cao-tekst is nagelopen** (zie onderaan).

## Wat we willen

- Bij een medewerker kiezen welk contract hij heeft: vast, jaarcontract, nulurencontract, oproepcontract, met hoeveel
  uur en op welke dagen.
- Een verlofsaldo in **uren** dat elke maand opbouwt (bijvoorbeeld 168 of 200 uur per jaar naar rato van het
  contract), met een startsaldo dat ook hoger dan nul kan zijn.
- **Cao's** van de bouwsector met hun afspraken per **looptijd**: tot 31 december geldt de ene periode, vanaf
  1 januari de volgende, en dat is overal zichtbaar zonder dat iemand iets hoeft om te zetten.
- **Feestdagen** per bedrijf een jaar vooruit berekend, en per cao instelbaar welke meetellen.

Alles is per bedrijf en per cao anders, dus alles is een instelling, niets staat vast in de code.

## Wat Frappe HR al doet, en wat niet

| Onderwerp | Frappe HR (v16) | Wat ontbreekt |
|---|---|---|
| Contract | Soort dienstverband (Employment Type) en een einddatum op de medewerker | Uren en dagen per week, min-max, cao, geschiedenis van contracten |
| Rooster | Dienst (Shift Type) → dienstpatroon (Shift Schedule, bijv. ma–vr) → toewijzing per medewerker, roosterweergave | Uren per weekdag voor parttimers; koppeling met verlof in uren |
| Verlof | Verlofsoorten, maandelijkse opbouw (earned leave), startsaldo (Leave Allocation), meenemen en laten vervallen, beleid met ingangs- en einddatum | **Alles in dagen** (hooguit halve dagen). Geen uren, dus parttime en een opname van 3 uur kloppen niet |
| Feestdagen | Feestdagenlijst die zichzelf vult voor land Nederland, elk jaar; toewijzing per medewerker met ingangsdatum (Holiday List Assignment) | Per cao kiezen welke dagen meetellen; lijst per bedrijf een jaar vooruit maken |
| Cao | Bestaat niet | Alles |

OpenAEC Bouw zet nu in de module **loon** (vereist Frappe HR) alleen stamgegevens klaar: contractsoorten, verlofsoorten
(wettelijk, bovenwettelijk, roostervrij, ziekte, bijzonder, onbetaald) en looncomponenten. Dit ontwerp bouwt daarop
voort in een nieuwe module **personeel**, ook met `vereist: hrms`.

## De onderdelen

```
Cao ──< Cao-periode (geldig van/tot, per werknemersgroep)
           ├── verlofrechten (uren per soort, verval)
           ├── feestdagen (telt mee ja/nee)
           ├── collectieve vrije dagen
           └── loonafspraken
            ▲
Medewerker ──< Arbeidscontract (van/tot, soort, uren, werkpatroon, cao + groep)
                    │
                    ▼
               Verlofboeking (uren +/−: startsaldo, opbouw, opname, verval, uitbetaling, correctie)
                    ▲
Verlofaanvraag (Leave Application van Frappe) ── rekent uren uit werkpatroon − feestdagen

Bedrijf + jaar + cao-groep ──> Feestdagenlijst (Holiday List van Frappe), een jaar vooruit
```

### 1. Cao en cao-periode

**Cao** is de afspraak zelf: naam, sector, partijen, bron (link naar de tekst), en de **werknemersgroepen** die hij
kent (bij Bouw & Infra: bouwplaats en uta). Een bedrijf zonder cao krijgt een eigen "cao" met de bedrijfsregeling;
zo werkt alles hetzelfde.

**Cao-periode** is één looptijd voor één werknemersgroep. Een apart document en geen tabel in de cao, zodat elke
periode een eigen lijst, status en geschiedenis heeft.

| Veld | Voorbeeld (Bouw & Infra, uta) |
|---|---|
| Cao, werknemersgroep | Bouw & Infra, uta |
| Geldig van, geldig tot | 1-1-2025, 31-3-2027 |
| Status | Concept, Vastgesteld, Stilzwijgend verlengd, Verlopen |
| Na afloop | Stilzwijgend verlengen met een jaar (ja/nee) |
| Normuren per week | 40 |
| Verlofrechten (tabel) | Wettelijk 160 uur, bovenwettelijk 40 uur, roostervrij 120 uur, per verlofsoort met de vervalregel |
| Opbouw bij oproep en nul-uren | Percentage per gewerkt uur, per verlofsoort |
| Feestdagen (tabel) | Per feestdag: telt als vrije dag ja/nee; Bevrijdingsdag: elk jaar, eens per vijf jaar of nooit |
| Collectieve vrije dagen (tabel) | Datums of "n dagen, door het bedrijf te kiezen" (bouwplaats: 10 van de 20 roostervrije dagen) |
| Loonafspraken (tabel) | Datum, percentage of bedrag, omschrijving (bijv. 1-3-2026 +3%) |
| Bron en nagelopen | Link naar de tekst, wie het naliep en wanneer |

Regels:
- Periodes van dezelfde cao en groep mogen elkaar niet overlappen. Een gat mag wel, maar geeft een waarschuwing.
- **Twee maanden voor het einde** zonder opvolger komt er een melding. Staat "stilzwijgend verlengen" aan, dan maakt
  het systeem op de einddatum een kopie met status *Stilzwijgend verlengd*, zodat er altijd iets geldt.
- Een periode die al gebruikt is (er zijn boekingen op gemaakt), is niet meer te wijzigen; een correctie gaat via een
  nieuwe periode of een correctieboeking.

### 2. Arbeidscontract

Eén document per contract per medewerker; een verlenging is een nieuw contract dat naar het vorige wijst. De
medewerker laat het **huidige contract** en de **cao-periode van vandaag** zien.

| Veld | Toelichting |
|---|---|
| Medewerker, bedrijf | |
| Soort | Onbepaalde tijd, Bepaalde tijd (bijv. jaarcontract), Nulurencontract, Min-maxcontract, Oproepcontract (voorovereenkomst), Stage, BBL |
| Van, tot | Tot is verplicht bij bepaalde tijd |
| Uren per week | Bij min-max: minimum en maximum; bij nul-uren en oproep: leeg |
| Werkpatroon (tabel) | Uren per weekdag, eventueel week A en week B (om de week vrijdag vrij); optioneel een dienst van Frappe voor de tijden |
| Cao, werknemersgroep | De periode volgt uit de datum, die kies je niet |
| Functie, schaal, trede, loon | Voor later en voor de loonkoppeling |
| Proeftijd, opzegtermijn | |
| Vorig contract | Voor de keten |

Uitgerekend: **contractfactor** = uren per week / normuren van de geldende cao-periode (32 / 40 = 0,8).

Controles en meldingen, uit de wet (nalopen voordat het hard wordt):
- Contracten van één medewerker overlappen niet.
- **Ketenregeling**: bij het vierde contract voor bepaalde tijd, of na meer dan drie jaar, een waarschuwing dat dit
  een contract voor onbepaalde tijd wordt (tussenpoos zes maanden; een cao kan afwijken).
- **Aanzegplicht**: een maand voor het einde van een contract van zes maanden of langer een taak voor de leidinggevende.
- **Nul-uren en oproep**: na twaalf maanden een taak om een vast aantal uren aan te bieden.
- De werknemer kan ook in het oude Frappe-veld (Employment Type) blijven staan; dat vullen we uit de soort.

### 3. Rooster

Voor verlof is alleen nodig **hoeveel uur iemand op een dag zou werken**. Dat staat in het werkpatroon van het
contract. Daarmee:
- kost een vrije vrijdag van een parttimer geen verlof;
- kost een feestdag op een werkdag geen verlof, als de cao zegt dat die dag vrij is;
- kun je geschreven uren tegen het patroon leggen (te weinig of overwerk).

Wie ook tijden, ploegen of in- en uitklokken wil, gebruikt het rooster van Frappe HR (dienst en dienstpatroon); het
contract kan daarnaar wijzen, en de toewijzing kan uit het contract worden gemaakt. Dat is optioneel. Nul-uren en
oproep hebben geen patroon: daar tellen alleen de geschreven uren.

### 4. Verlof in uren

De waarheid is een grootboek van **verlofboekingen** in uren, per medewerker en verlofsoort:

| Soort boeking | Wanneer | Bedrag |
|---|---|---|
| Startsaldo | Bij indienst of overgang, met een reden | Wat je invult, ook meer dan nul |
| Opbouw | Elke maand, op de laatste dag (achteraf) | Jaaruren van de cao-periode × contractfactor / 12, naar rato van de dagen in dienst in die maand |
| Opbouw per gewerkt uur | Bij nul-uren en oproep, bij goedgekeurde uren | Gewerkte uren × percentage uit de cao-periode |
| Opname | Bij een goedgekeurde verlofaanvraag | − de uren uit het werkpatroon op die dagen, min feestdagen die vrij zijn |
| Verval | Op de vervaldatum per soort | − wat nog over is van die opbouw |
| Uitbetaling | Bij uitdienst of een keuze (bijv. via het individueel budget) | − uren, met een verwijzing naar de loonmutatie |
| Correctie | Met de hand, met een reden | +/− |

- **Contract of cao wisselt midden in een maand**: de maand wordt in stukken gerekend, elk stuk met zijn eigen
  contractfactor en cao-periode. Zo gaat 1 januari vanzelf goed.
- **Verval** per soort, uit de cao-periode: wettelijk zes maanden na het jaar van opbouw, bovenwettelijk na vijf jaar,
  roostervrij bij Bouw & Infra aan het eind van het jaar. Het oudste saldo gaat er het eerst af.
- **Aanvragen** gaan via de verlofaanvraag van Frappe HR (aanvragen, goedkeuren, in de agenda). Wij voegen het
  veld *uren* toe, rekenen het voor uit het werkpatroon, laten het aanpassen voor een halve of een paar uur, en
  toetsen het saldo in uren. De verlofsoorten krijgen het vinkje *in uren*; voor die soorten maken we geen
  Leave Allocation in dagen meer.
- **Zichtbaar**: per medewerker het saldo per soort met "waarvan vervalt op …", en een rapport
  **Verlofsaldo** per bedrijf (beginsaldo, opbouw, opname, verval, eindsaldo, in uren en in dagen van het contract).

Rekenvoorbeeld: 200 uur per jaar, 32 uur in de week bij een cao met 40 normuren → 200 × 0,8 / 12 = 13,33 uur per
maand. Indienst op 16 maart → maart 13,33 × 16/31 = 6,88 uur.

### 5. Feestdagen per bedrijf

Een **bedrijfskalender** per bedrijf, jaar en cao-groep maakt een feestdagenlijst van Frappe:

1. De datums komen uit de bibliotheek die Frappe al gebruikt (Nederland), dus Goede Vrijdag, Pasen, Hemelvaart en
   Pinksteren rekenen zichzelf uit.
2. De feestdagentabel van de cao-periode die op die datum geldt, bepaalt welke erin komen.
3. Collectieve vrije dagen van de cao en van het bedrijf zelf (bijv. de bouwvak of de dag na Hemelvaart) komen erbij.
4. De lijst wordt via een toewijzing met ingangsdatum aan de medewerkers met die cao gekoppeld.

Elk jaar op **1 oktober** maakt het systeem de kalender van het volgende jaar als concept; het bedrijf kijkt hem na
en stelt hem vast. Een feestdag die op een zaterdag of zondag valt, kost niemand iets en telt dus vanzelf niet.

Voorbeeld 2027 (datums uit de bibliotheek): Nieuwjaarsdag vr 1 jan, Goede Vrijdag 26 mrt, Tweede Paasdag 29 mrt,
Koningsdag di 27 apr, Hemelvaart 6 mei, Tweede Pinksterdag 17 mei, Eerste en Tweede Kerstdag za 25 en zo 26 dec.
Bevrijdingsdag is in 2027 geen lustrumjaar.

### 6. Cao's die erin komen

Als stamgegevens in `data/caos.json`, met bron en status *Concept* tot ze zijn nagelopen.

| Cao | Groepen | Looptijd | Wat al bekend is |
|---|---|---|---|
| Bouw & Infra | bouwplaats, uta | 1-1-2025 t/m 31-3-2027, daarna stilzwijgend per jaar | 25 vakantiedagen (20 wettelijk + 5 bovenwettelijk). Uta: 15 roostervrije dagen (120 uur). Bouwplaats: 20 roostervrije dagen, waarvan 10 collectief. Roostervrij vervalt aan het eind van het jaar |
| Technisch Installatiebedrijf (Metaal & Techniek) | één | 1-2-2026 t/m 31-1-2028 | +3% op 1-3-2026; verlof nog uit de tekst halen |
| Afbouw | één | 1-1-2026 t/m 31-12-2027 | +3,5% en € 30 per maand in 2026 |
| Houthandel | één | 1-7-2025 t/m 30-6-2027 | +2,5% op 1-1-2026, +1,5% op 1-1-2027 |
| Architectenbureaus | één | 1-7-2026 t/m 30-6-2028 | |
| Eigen regeling | per bedrijf | zelf | Voor ingenieurs- en adviesbureaus, sondeerbedrijven en verhuur zolang er geen sector-cao is gevonden |

In het demonstratiebedrijf: de aannemer Bouw & Infra (bouwplaats en uta), de installateur Technisch
Installatiebedrijf, de houthandel Houthandel, de rest een eigen regeling.

## Wat er niet in komt

- **Loonberekening en loonaangifte**: blijft bij het loonpakket (keuze A in de routekaart). Wat dit ontwerp oplevert
  (contract, uren, verlof, uitbetalingen, loonafspraken) is wel precies wat een loonpakket aangeleverd wil krijgen.
- **Ziekteverzuim** (Poortwachter) en opleidingen: later, eigen ontwerp.

## Wat eerst moet

- **Frappe HR naast Z-Next.** Op een site met Z-Next loopt de bedrijfstabel vol ("Row size too large") zodra Frappe HR
  erbij komt: ERPNext, Frappe HR en de 93 velden van Z samen gaan over de grens van MariaDB voor één regel. Dus eerst
  de velden van Z van het bedrijf af naar **Bedrijfsinstellingen** (zie `velden-harmonisatie.md`).
- Frappe HR op elke omgeving installeren, ook op de demosite.

## Volgorde van bouwen

1. Cao en cao-periode, met `data/caos.json` en de melding bij een aflopende periode.
2. Arbeidscontract met werkpatroon en contractfactor; huidig contract en cao op de medewerker.
3. Bedrijfskalender en feestdagenlijsten, een jaar vooruit.
4. Verlofboekingen: startsaldo, maandelijkse opbouw, verval; uren op de verlofaanvraag; het rapport Verlofsaldo.
5. Opbouw per gewerkt uur voor nul-uren en oproep (vraagt goedgekeurde uren).
6. Meldingen uit de wet: keten, aanzeggen, vaste uren aanbieden.

Tests, op een schone site: parttimer met vrije vrijdag, indienst halverwege de maand, contractwijziging halverwege
de maand, wissel van cao-periode op 1 januari, opname over een feestdag die wel en niet meetelt, verval op 1 juli,
stilzwijgende verlenging.

## Besluiten (27 november 2026)

1. **Uren zijn de enige waarheid.** Frappe HR doet het aanvragen en goedkeuren; het saldo staat in de
   verlofboekingen.
2. **Opbouw achteraf**, op de laatste dag van de maand.
3. **Frappe HR zit altijd standaard in onze ERPNext.** Alles bouwt daarop voort. Wat Z (en Y) zelf doen en Frappe HR
   of ERPNext al doet, wordt herontworpen tot één geheel; zie het hoofdstuk Personeel in `velden-harmonisatie.md`.

## Na te lopen in de cao-teksten

Alle getallen hierboven komen uit samenvattingen. Per cao nog uit de tekst halen: vakantie- en roosteruren per
groep, welke feestdagen vrij zijn (Goede Vrijdag, Bevrijdingsdag), vervalregels, opbouw tijdens ziekte en bij
oproep, en wat er via het individueel budget gaat. Ook de wettelijke regels (keten, aanzegplicht, twaalf maanden
oproep) en de vervaltermijnen nalopen in de wettekst.

Bronnen:
- [Bouwend Nederland: verlof rondom vrije tijd](https://www.bouwendnederland.nl/kennis/vakantie-en-verlof/verlof-rondom-vrije-tijd)
- [Samenvatting cao Bouw & Infra 2025–2027](https://www.salaris-informatie.nl/bouwnijverheid/samenvatting-cao-bouw-infra-2025-2027)
- [Cao Bouw & Infra: vakantiedagen en verlof](https://www.salaris-informatie.nl/bouwnijverheid/cao-bouw-infra-vakantiedagen-en-verlof)
- [Techniek Nederland: cao Technisch Installatiebedrijf 2026–2028](https://www.technieknederland.nl/nieuws/cao-technisch-installatiebedrijf-2026-2028-definitief-na-instemming-leden)
- [FNV: nieuwe cao Afbouw](https://www.fnv.nl/nieuwsbericht/sectornieuws/bouwen-en-wonen/2026/01/het-is-nu-officieel-er-is-een-nieuwe-cao-afbouw)
- [Cao Houthandel](https://www.salaris-informatie.nl/cao-sector/houthandel)
- [FNV: cao Architectenbureaus 2026–2028](https://www.fnv.nl/nieuwsbericht/sectornieuws/bouwen-en-wonen/2026/08/cao-architectenbureaus-2026-2028)
