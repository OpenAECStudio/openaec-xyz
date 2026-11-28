# Vastgoed en beheer: van de kaart van Nederland tot de lamp in een ruimte

Stand 28 november 2026. Ontwerp, nog niet gebouwd. Een standaardmodule van XYZ, **Vastgoed en beheer**: alles wat een
bedrijf aan plekken, gebouwen en installaties heeft, in ERPNext vastgelegd en op een kaart te zien. Op de kaart van
Nederland zie je de locaties, je klikt op een locatie en ziet de gebouwen in 3D, je gaat een gebouw in, een verdieping,
een ruimte, en ziet daar de verlichting, de installatie en hoe warm het is.

Het is de beheerkant (FM) van wat de BIM Suite aan de ontwerpkant doet. Hetzelfde geldt voor een bedrijf dat zijn eigen
panden beheert (de eigen vestigingen) als voor een installateur of beheerder die het voor zijn klanten doet.

## De grens tussen ERPNext en IFC

De regel: **ERPNext is de bron van alles wat je over een ding weet; IFC is de bron van waar het staat en hoe het
eruitziet.** Zo veel en zo gedetailleerd mogelijk in ERPNext.

| | In ERPNext | In het IFC-model |
|---|---|---|
| **Wat** | Naam, soort, codering (NL-SfB), merk, type, serienummer, leverancier, installatiedatum, garantie, levensduur, conditie (NEN 2767), onderhoud en keuringen, kosten, eigenaar, contract, documenten, storingen, meetpunten | Alleen wat het model nodig heeft om het ding te tekenen en te vinden |
| **Waar** | De plek in de boom: locatie, perceel, gebouw, bouwlaag, ruimte; adres, kadastraal perceel, BAG-pand, oppervlakten volgens NEN 2580 | Geometrie, plaatsing, de ruimtelijke indeling zoals ontworpen |
| **Hoe ze elkaar vinden** | Het `GlobalId` uit IFC op elk record, plus het model (Docs-bestand en versie) waar het uit komt | Het `GlobalId` zelf; bij uitvoer naar IFC een propertyset `Pset_OpenAEC_Beheer` met wat ERPNext weet |
| **Wie het wijzigt** | De beheerder, de monteur, de boekhouding; de geschiedenis blijft | De ontwerper of modelleur, bij een verbouwing een nieuwe versie |

Gevolgen:

- Een nieuw of verbouwd model **lezen** maakt of werkt records bij op `GlobalId`; wat er in ERPNext over het ding staat
  blijft. Een element dat uit het model verdwijnt wordt niet weggegooid maar "niet meer in het model" (gesloopt,
  vervangen), met de datum.
- Een ding zonder model (een losse brandblusser, een gebouw waar geen IFC van is) bestaat gewoon in ERPNext. Het model is
  een aanvulling, geen voorwaarde.
- **Live meetwaarden** (temperatuur, lamp aan of uit, energie) horen in geen van beide: ze komen uit het gebouwbeheer
  (GBS) of losse sensoren, staan in een tijdreeks naast ERPNext, en ERPNext kent het **meetpunt** met de laatste waarde
  en de grenzen. Zie *Live gegevens*.

## De boom

ERPNext heeft er al de bouwstenen voor: `Location` (een boom, met coördinaten en een kaartvlak) en `Asset` (een ding met
een plek, een categorie, afschrijving en onderhoud). XYZ legt er de Nederlandse indeling en de koppeling met IFC op.

| Niveau | In ERPNext | IFC | Wat XYZ erbij vastlegt |
|---|---|---|---|
| **Portefeuille** of vestiging | `Location` (groep), gekoppeld aan `Branch` en `Company` | – | Bedrijf, vestiging, kostenplaats |
| **Locatie** (terrein, complex) | `Location` met kaartvlak | `IfcSite` | Adres, coördinaten (WGS 84 en RD), eigendom of huur, contract |
| **Perceel** | `Location` | `IfcSite` (deel) | Kadastrale gemeente, sectie, nummer, oppervlakte, grens uit PDOK; bestemming |
| **Gebouw** | `Location` én een `Asset` (het gebouw als bezit, met afschrijving) | `IfcBuilding` | BAG-pand en verblijfsobjecten, bouwjaar, gebruiksfunctie, BVO/GO (NEN 2580), energielabel, monument, het model (Docs-bestand, versie) |
| **Bouwlaag** | `Location` | `IfcBuildingStorey` | Peil, oppervlakte |
| **Ruimte** | `Location` | `IfcSpace` | Ruimtenummer, functie, NEN 2580-oppervlakten, bezetting, schoonmaakklasse, gewenste temperatuur |
| **Element en installatie** | `Asset` (of een onderdeel van een installatie-asset) | `IfcElement`, vooral `IfcDistributionElement` (verlichting, ketel, warmtepomp, luchtbehandeling, sensor) | NL-SfB, merk, type, serienummer, vermogen, garantie, levensduur, conditie, onderhoudsplan, keuringen |
| **Meetpunt** | `Meetpunt` (nieuw) bij een asset of ruimte | `IfcSensor` (als het in het model staat) | Grootheid en eenheid, bron (GBS, sensor, meter), adres in de bron, laatste waarde, grenzen, melding bij overschrijding |

De velden komen als vaste velden op `Location` en `Asset` (zoals de andere velden van XYZ), niet in een eigen doctype
per niveau: zo blijven afschrijving, onderhoud (`Asset Maintenance`), reparaties (`Asset Repair`) en verplaatsingen
(`Asset Movement`) van ERPNext gewoon werken. Een veld `soort` op `Location` zegt welk niveau het is.

## Wat je ziet

Een werkscherm in XYZ, **Vastgoed**, voor wie de module heeft:

1. **De kaart.** De achtergrondkaart van PDOK (BRT), de locaties van het bedrijf als punten of vlakken, gekleurd naar
   wat je wilt zien: open storingen, keuringen die verlopen, energielabel, temperatuur buiten de grenzen. Filters op
   bedrijf, vestiging en soort.
2. **De locatie.** Inzoomen: percelen (kadaster) en de gebouwen in 3D. Eigen gebouwen uit het IFC-model; de omgeving
   uit 3D BAG als grijze blokken, zodat je ziet waar het staat. Ernaast de kaart van de locatie in ERPNext.
3. **Het gebouw.** Klikken op een gebouw opent het model in de viewer. Verdiepingen los te zetten, door de gevel heen.
   Ernaast de gegevens: BAG, oppervlakten, label, contracten, onderhoudsplanning.
4. **De ruimte.** Een verdieping of ruimte kiezen: de ruimten gekleurd naar temperatuur, bezetting of functie. In de
   ruimte de elementen: lampen, radiatoren, sensoren, met hun kaart uit ERPNext.
5. **Het ding.** Klikken op een lamp of de warmtepomp: merk, type, serienummer, laatste keuring, open storingen, het
   onderhoud, de documenten, en de live waarde (aan, uit, temperatuur, vermogen) met een lijn van de laatste dagen.
   Vanuit hier een storing melden of een werkbon maken (module Service en onderhoud).

Het omgekeerde werkt ook: vanuit een asset of storing in ERPNext "Toon in het model" opent de viewer op dat ding.

De viewer is de viewer die de werkplek al heeft (het model uit Docs of Speckle van de omgeving); de kaart en de
3D BAG-omgeving zijn nieuw. De BIM Suite rekent al met RD-coördinaten en vraagt PDOK om percelen en gebouwen
(`bim-gis`); dat gebruiken we ook hier, zodat een model op de goede plek op de kaart staat.

## Live gegevens

| Onderdeel | Hoe |
|---|---|
| **Bron** | Een koppeling per bron: het GBS (BACnet of Modbus, via een kleine gateway op locatie), KNX, of de cloud-API van een fabrikant (warmtepomp, slimme meter). Eerst één bron werkend, de rest volgt |
| **Opslag** | Een tijdreeks per meetpunt, naast ERPNext, op de server van de omgeving. Niet in de database van ERPNext: duizenden waarden per uur per gebouw maken die zwaar |
| **In ERPNext** | Het `Meetpunt`: bij welk ding of welke ruimte, de laatste waarde en het tijdstip, de grenzen. Overschrijding wordt een melding en eventueel een storing |
| **In het scherm** | Kleuren per ruimte, de waarde bij het ding, een lijn van de laatste dagen |
| **Schakelen** | Lezen eerst. Iets aan- of uitzetten vanuit XYZ pas later en alleen met een uitdrukkelijke keuze per meetpunt |

## In de demo

Bij het demonstratiebedrijf (`docs/demonstratiebedrijf.md`) krijgt de groep zijn eigen vastgoed, verzonnen maar op
plekken die op de kaart bestaan:

| Locatie | Van | Wat er staat |
|---|---|---|
| Hoofdkantoor | Holding, Bouw, Advies | Kantoor met twee bouwlagen, kantine, serverruimte |
| Vestiging Zwolle | Installatietechniek | Kantoor met werkplaats en magazijn |
| Vestiging Deventer | Installatietechniek | Kleine vestiging met magazijn |
| Houtwerf | Hout, Materieel | Loods, overkapte opslag, zagerij, werfkantoor; buitenterrein met materieel |

Per gebouw een eenvoudig IFC-model (gemaakt met IfcOpenShell: bouwlagen, ruimten, wanden, ramen, verlichting,
radiatoren, een warmtepomp of ketel, sensoren), de assets en meetpunten in ERPNext, onderhoudsplannen en een paar
storingen, en meetwaarden van een gesimuleerde week (dag en nacht, weekend, één ruimte die te warm wordt).

## Stappen

| Stap | Wat |
|---|---|
| 1 | De boom en de velden op `Location` en `Asset`; IFC lezen naar ERPNext op `GlobalId` (sites, gebouwen, bouwlagen, ruimten, installatie-elementen); het demovastgoed |
| 2 | Het werkscherm Vastgoed: kaart, locatie met 3D BAG, gebouw en ruimte in de viewer, de kaart van een ding |
| 3 | Meetpunten en de tijdreeks, met gesimuleerde waarden in de demo; kleuren per ruimte |
| 4 | Een echte bron (eerst één GBS of één fabrikant), meldingen bij overschrijding |
| 5 | Terugschrijven naar IFC (`Pset_OpenAEC_Beheer`), onderhoud en storingen vanuit het model, NEN 2767-inspecties op de telefoon |

## Open vragen

- Waar de tijdreeks staat: een kleine eigen dienst per server, of een bestaande (TimescaleDB, InfluxDB).
- Welke bron eerst: een GBS bij een klant, of een fabrikant met een open API.
- Of 3D BAG als omgeving genoeg is, of ook de luchtfoto (PDOK) onder de gebouwen.
