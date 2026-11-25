# Het fundament onder de administratie

Stand 25 november 2026. Dit stuk hoort bij het demonstratiebedrijf (`apps/openaec_bouw/openaec_bouw/demo.py`) en bij
elke echte inrichting: wat moet er in ERPNext goed staan **voordat** de eerste factuur wordt geboekt, omdat het
daarna niet of alleen met veel werk te veranderen is.

De regel: we bouwen op wat ERPNext zelf heeft en zetten er alleen iets naast waar ERPNext niets heeft. Geen velden of
tabellen rechtstreeks in de database zetten om een controle te omzeilen.

## Wat later niet meer te veranderen is

| Onderwerp | Waarom het vooraf moet | Hoe het hoort | Stand |
|---|---|---|---|
| **Groep en dochters** | Een bedrijf onder een ander hangen nadat er geboekt is, geeft rekeningschema's die niet meer gelijk lopen; de geconsolideerde rapporten kloppen dan niet | De holding als groepsbedrijf, elke werkmaatschappij aangemaakt mét de holding als moeder. ERPNext kopieert dan het schema van de moeder, en een nieuwe rekening bij de moeder komt vanzelf bij de dochters | Gebouwd: `boekhouding.neem_schema_over` zet daarna de RGS-codes, standaardrekeningen en btw-sjablonen |
| **Rekeningschema** | Kan niet meer vervangen worden zodra er geboekt is | Het Nederlandse schema van OpenAEC Bouw, met RGS-code per rekening | Gebouwd (0.3) |
| **Artikel met of zonder voorraad** | Een artikel kan na de eerste mutatie niet meer van dienst naar voorraadartikel | Per bedrijf vooraf kiezen: handel houdt voorraad, een adviesbureau niet | Gebouwd voor de houthandel, zie hieronder |
| **Waardering van de voorraad** | De methode (gemiddelde prijs of fifo) ligt vast na de eerste mutatie | Gemiddelde inkoopprijs voor hout; doorlopende voorraadboeking aan, met de voorraadrekeningen van het schema | Gebouwd |
| **Vaste activa** | Een actief dat als kosten is geboekt, komt niet meer op de balans; en de beginbalans moet met het register kloppen | Elk actief in het register, met wat er vóór het eerste boekjaar al is afgeschreven; de beginbalans neemt aanschafwaarde en afschrijving daaruit over | Gebouwd: register per bedrijf, lineair per kwartaal |
| **Beginbalans** | Zonder beginbalans staat de bank na de eerste betaling negatief en klopt geen enkele balans | Een openingspost per bedrijf op de eerste dag van het eerste boekjaar | Gebouwd in de generator (concept) |
| **Boekjaren en afsluiting** | Zonder jaarafsluiting komt het resultaat van een oud jaar niet in het eigen vermogen | Een boekjaar per kalenderjaar; na elk jaar een afsluiting die het resultaat naar Onverdeeld resultaat boekt | Boekjaren gebouwd; afsluiting hoort bij het boeken, nog te doen |
| **Onderlinge relaties** | Een onderlinge factuur moet aan beide kanten staan, anders loopt de consolidatie scheef | Elk bedrijf van de groep als interne klant en interne leverancier van de andere; een verkoopfactuur maakt de inkoopfactuur bij de ander | Relaties gebouwd; onderlinge facturen nog niet |
| **Kostenplaats en vestiging** | Achteraf een vestiging aan oude boekingen hangen kan niet | Een kostenplaats per vestiging; de vestiging van de medewerker als vestiging (`Branch`) | Kostenplaatsen gebouwd; de facturen krijgen er nog geen mee |
| **Nummerreeksen** | Een factuurnummer mag niet veranderen en moet per bedrijf doorlopen | Een eigen reeks per bedrijf en per jaar voor verkoopfacturen | Nog te doen: nu de standaardreeks van ERPNext voor alle bedrijven samen |
| **Btw-nummer en fiscale eenheid** | Bepaalt of de groep één aangifte doet of elk bedrijf zijn eigen | Per bedrijf een eigen aangifte, tot anders besloten | Gebouwd: een aangifte per bedrijf |

## Btw-aangifte als document

Tot nu toe was de btw-aangifte een rapport: het rekende, maar legde niets vast. Vanaf deze versie is er het doctype
**Btw-aangifte**: één per bedrijf per tijdvak.

- Als concept ververst het de rubrieken bij elke opslag, en kan het ook conceptfacturen meetellen voor een
  voorlopige stand.
- **Indienen** zet de cijfers vast. Dat kan pas als er in het tijdvak geen conceptfacturen meer staan.
- Twee aangiftes van hetzelfde bedrijf mogen elkaar niet overlappen.
- **Journaalpost maken** boekt de btw-rekeningen van het tijdvak leeg naar Btw-afdracht; de betaling aan de
  Belastingdienst lettert daar tegen af.
- De datum van indienen en het betalingskenmerk staan erbij.

Nog niet: suppletie, rubriek 1d en 3c, en het indienen zelf (dat gaat via Digipoort met een eigen certificaat).

## Voorraad voor de houthandel

De houthandel rekent met voorraad (`demo_voorraad.py`). Wat er staat, in de volgorde waarin het nodig is:

1. **Magazijnen**: hoofdmagazijn, zagerij en een **grijpvoorraad**. Uit de grijpvoorraad (schroeven, lijm, bouten)
   wordt zonder bon gepakt; het verbruik blijkt uit de telling per kwartaal, niet uit een mutatie per stuk.
2. **Artikelen** als voorraadartikel, met houtsoort, afmeting, eenheid (strekkende meter, m³ of plaat), het land van
   herkomst en het keurmerk (FSC of PEFC; nieuw veld op het artikel).
3. **Herkomst**: tropisch hardhout loopt per partij (`Batch`), met het land en het gebied van herkomst op de partij
   (twee nieuwe velden). De Europese regels voor hout vragen dat een levering naar de kap te herleiden is: de
   verkoopfactuur noemt de partij.
4. **Beginvoorraad** als voorraadtelling op de eerste dag, tegen het eigen vermogen.
5. **Inkoop met ontvangst** en **verkoop met aflevering**, gewaardeerd tegen de gemiddelde inkoopprijs. De marge van
   de houthandel komt uit de voorraad, niet uit een vast percentage.
6. **Zaagwerk**: van eiken kwartiers naar geschaafde planken, als omzetting van het ene artikel in het andere, met
   zaagverlies.

De generator houdt de voorraad per maand bij: eerst inkoop, dan verkoop, en nooit meer verkopen dan er ligt. Zo kan
alles later in volgorde van datum geboekt worden zonder dat de voorraad negatief wordt.

Nog niet: omrekenen tussen strekkende meter en m³ op één artikel, voorraad op meer vestigingen, en een minimumvoorraad
met bestelvoorstel.

## Onderhanden werk bij de aannemer

Een aannemer factureert in termijnen en maakt kosten in een ander tempo. Aan het eind van een periode staat een
project dus óf voor (meer gefactureerd dan gemaakt) óf achter. Zonder onderhanden werk schommelt het resultaat per
maand met de termijnen mee en zegt het niets.

- **Positie per project per periode**: gemaakte kosten, gefactureerde termijnen, voortgang, verwacht resultaat.
- **Boeking**: de kosten en termijnen van lopende projecten gaan naar de balans (rekening 3100 Onderhanden projecten
  en 3110 Gefactureerde termijnen), en het resultaat wordt genomen naar voortgang of bij oplevering. Welke van de
  twee is een keuze per bedrijf, in overleg met de accountant.
- **Verlies**: een verwacht verlies op een project wordt meteen genomen, als voorziening.

De Z-app heeft hier onderdelen van (termijnstaat, bewakingscodes, fysieke en financiële voortgang, aanneemsom,
meerwerk).

Gebouwd is het doctype **Onderhanden Werk**: één stand per bedrijf per peildatum, met een regel per lopend project.
De aanneemsom staat in een nieuw veld op het project; de begrote kosten zijn het standaardveld van ERPNext. De
journaalpost boekt het verschil met de vorige stand: een positief saldo naar Onderhanden projecten (3100), een
negatief naar Gefactureerde termijnen (3110), tegen de nieuwe rekening Mutatie onderhanden projecten (8090).
Vastleggen kan pas als er op die projecten geen conceptfacturen meer staan.

Nog niet: de uren van eigen mensen als kosten (dat komt met de urenstaten), een eigen invoer voor de voortgang (nu
kosten gedeeld door begroting), en de aansluiting op de termijnstaat en de bewakingscodes van de Z-app.

## Wat de generator nu doet en niet doet

Doet: de groep volgens ERPNext, schema met RGS, banken en G-rekeningen, vestigingen, kostenplaatsen, afdelingen,
medewerkers met vaste gezichten per bedrijf, interne relaties en de doorbelasting van de holding, het register van
vaste activa, de beginbalans, projecten met aanneemsom, verkoop- en inkoopfacturen met pdf, voorraad bij de
houthandel, onderhanden werk per kwartaal bij de aannemer en de installateur, lonen, vaste kosten, banktransacties,
afboekingen en een Btw-aangifte per kwartaal. Alles als concept.

Doet nog niet: uren en urenstaten, nummerreeksen per bedrijf, kostenplaats op de facturen, keuringen van materieel,
de aankoop van een nieuw actief in de loop van een jaar, en het boeken zelf met de jaarafsluitingen.
