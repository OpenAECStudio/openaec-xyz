# Voorstel: XYZ als één app voor het bouwbedrijf

Stand 25 november 2026. Dit is een voorstel, geen besluit. Het bouwt voort op `docs/routekaart.md` en op wat er nu in
de drie apps zit; de velden staan uitgewerkt in `docs/velden-harmonisatie.md` en de bevindingen over de boekhouding
van Y in `docs/y-boekhouding-bevindingen.md`.

## Het idee in één alinea

XYZ is één app van OpenAEC waarin een bouwbedrijf zijn hele werk doet: projecten, uren, planning, offertes, inkoop,
facturen en boekhouding, met e-mail, berichten en videobellen erbij en een assistent die je project kent. Geen losse
pakketten naast elkaar, en geen drie apps: één ingang, met modules die per bedrijf aan of uit staan. Dezelfde app
draait in de SuperCloud en, voor wie dat wil, op de eigen pc zonder cloud.

## Wat er al is, en waar het vandaan komt

| Onderdeel van XYZ | Bestaat nu als | Stand |
|---|---|---|
| Werkschermen: projecten, taken, uren, agenda, verkoop, inkoop, rapporten | Y (ruim 40 schermen) | Werkt bij klanten; de boekhoudkant heeft herstel nodig |
| Inrichting en Nederlandse administratie: rekeningschema, btw, auditfile, bank, SEPA, G-rekening, UBL | X, versie 0.4.0 | Live op de modelomgeving |
| Uitvoering: calculatie, termijnstaten, planning, bouwdagboek, projectbewaking, onderaanneming | Z (46 doctypes) | Maatwerk van één bedrijf; moet algemeen worden |
| E-mail aan het project gekoppeld | Y (webmail op de post van ERPNext) | Werkt |
| Berichten | Y (meldingen) en Raven in de SuperCloud | Twee plekken |
| Videobellen | Jitsi Meet in elke SuperCloud-omgeving | Live sinds 24 november, alleen als los scherm |
| Assistent | AI-gateway van de SuperCloud; in Y een opdrachtbalk met vaste patronen | De echte assistent zit nog niet in de schermen |
| Bestanden en tekeningen | Docs en de tools van OpenAEC (`.ifcx`) | Los van het project in Y |

## Hoe de app eruitziet

Eén scherm met links de onderdelen en bovenaan het project waarin je werkt. Wat je opent, opent binnen het project.

1. **Vandaag**: wat ligt er voor mij (taken, te keuren facturen, uren van deze week, afspraken, nieuwe post).
2. **Projecten**: het project als middelpunt, met tabbladen voor taken, planning, uren, calculatie, termijnen, inkoop,
   post, bestanden en bewaking.
3. **Verkoop en inkoop**: offertes, opdrachten, facturen, inkoopfacturen, onderaannemers.
4. **Administratie**: bank, btw, grootboek, rapporten, jaarwerk.
5. **Mensen**: medewerkers, uren, verlof, declaraties.
6. **Communicatie**: post, berichten, bellen.
7. **Assistent**: altijd bereikbaar, rechts in beeld.

### Regel voor de schermen

De schermen van Y blijven de schermen. Z levert geen eigen schermen maar modules: elk onderdeel van Z wordt een
tabblad of een scherm in dezelfde app, met dezelfde opmaak. Het bureaublad van ERPNext blijft bereikbaar voor de
beheerder en de boekhouder, maar een gewone medewerker hoeft er niet te komen.

## De assistent: praten met je project

De assistent is geen los chatvenster maar zit in het project. Je vraagt in gewone taal, en hij antwoordt met wat er
in dat project staat.

**Wat hij kan lezen**, steeds met de rechten van wie het vraagt:

- het project zelf: opdrachtgever, aanneemsom, fase, planning, taken;
- geld: offertes, termijnen, facturen, inkoop, wat openstaat, budget tegen werkelijk;
- uren en het bouwdagboek;
- de post die aan het project hangt, en de notulen;
- de bestanden: contract, bestek, tekeningen, opleverpunten.

**Wat hij kan doen**, altijd als voorstel dat een mens bevestigt:

- een inkoopfactuur lezen en een boeking voorstellen (project, kostensoort, btw-code): dit is 0.5 van de routekaart;
- een antwoord op een e-mail opzetten, met de feiten uit het project erin;
- een termijn of meerwerk klaarzetten als concept;
- een overleg plannen en de uitnodiging met de belkamer opstellen;
- een stand van zaken schrijven voor de opdrachtgever.

**Regels:**

- De assistent boekt nooit zelf. Hij maakt een concept; een mens keurt het.
- Hij ziet niet meer dan de gebruiker zelf mag zien.
- Elk antwoord noemt waar het vandaan komt (de factuur, de mail, het document), zodat je het kunt nalopen.
- Hij loopt via de AI-gateway van de SuperCloud; de gegevens blijven in de omgeving van de klant.
- De opdrachtbalk met vaste patronen die nu in Y zit, vervalt: die maakt betalingen en facturen aan met ontbrekende
  velden (zie de bevindingen).

## E-mail, berichten en bellen

- **E-mail** blijft zoals in Y: de postbussen van het bedrijf, in de app, en elke mail kan aan een project, een klant
  of een factuur hangen. Vanuit een mail maak je een offerte, een inkoopfactuur of een taak. De oude webmail die
  rechtstreeks met een mailserver praatte, zit nog als dode code in de schermen en gaat eruit.
- **Berichten**: één plek. Voorstel: Raven voor gesprekken tussen collega's (per project een kanaal), en de meldingen
  van de app zelf (iemand wees je een taak toe) apart in Vandaag.
- **Bellen**: de knop Videobellen komt bij het project, bij een afspraak in de agenda en in een gesprek in berichten.
  Elk project heeft zijn eigen kamer; een uitnodiging voor iemand van buiten is een link die een dag geldt. De
  techniek is er al (Jitsi Meet per server, een kamer opent alleen met een token van de omgeving).

## Voorbereiding voor installatietechniek

Het installatiebedrijf is de eerste sector na de aannemer (0.6 in de routekaart). Het verschil met een aannemer: naast
projecten is er **service**, en het middelpunt is niet het project maar de **installatie op een adres**.

| Begrip | Wat het is | Waar het op bouwt |
|---|---|---|
| Installatie | Een cv-ketel, warmtepomp, wtw, meterkast, koelinstallatie of zonnesysteem op een adres, met merk, type, serienummer en datum van plaatsing | Eén record per object, in hetzelfde doctype dat de andere tools van OpenAEC voor objecten gebruiken; zo is een installatie ook vindbaar vanuit het model |
| Keuring | Een inspectie met een vervaldatum en een rapport: elektra (NEN 1010, NEN 3140), stookinstallaties (Scios), koudemiddelen (F-gassen, met het logboek), legionella | Nieuw, met een herinnering vóór de vervaldatum |
| Onderhoudscontract | Wat is afgesproken per installatie: hoe vaak, welke werkzaamheden, welke prijs | Onderhoudsschema van ERPNext, met terugkerende taken |
| Storing | Een melding van de klant, met urgentie en responstijd | Melding (`Issue`) van ERPNext |
| Werkbon | Wat de monteur ter plaatse deed: tijd, materiaal uit de bus, foto's, handtekening van de klant | Nieuw; op de telefoon, ook zonder bereik. Wordt uren, materiaalverbruik en een factuurregel |
| Busvoorraad | Wat er in elke servicebus ligt | Een magazijn per bus |
| Artikelen van de groothandel | Artikelnummers, prijzen en klassen van de groothandel | Inlezen van artikelbestanden met ETIM-klasse en GTIN; prijslijst per leverancier |

Wat nu al kan, zonder dat er iets vastligt dat we later moeten terugdraaien:

1. Een module **Installatietechniek** in de inrichting met alleen stamgegevens: artikelgroepen (ketels, warmtepompen,
   ventilatie, elektra, sanitair, koeling), uursoorten (montage, service, storing, keuring, voorrijden) en een
   projectsjabloon voor een installatieproject.
2. De soorten installaties en de soorten keuringen als lijsten.
3. Het veld voor de ETIM-klasse en de GTIN op het artikel.

De doctypes voor installatie, keuring en werkbon komen in 0.6, na een gesprek met een installateur. Wat we van Z
leren: geen losse velden op standaard-doctypes, maar eigen doctypes met de velden erin.

## Eén app, twee vormen

| | In de SuperCloud | Op de eigen pc |
|---|---|---|
| Voor wie | Bedrijven met meer mensen, die samen in één administratie werken | Zzp'er of klein bedrijf dat niet in de cloud wil of kan |
| Gegevens | In ERPNext, in de omgeving van de klant | In één bestand op de eigen schijf |
| Schermen | Dezelfde | Dezelfde |
| Installeren | Niets | Eén installer, geen Docker, geen server |
| Meer gebruikers tegelijk | Ja | Nee: één gebruiker per bestand |
| Assistent, bellen | Ja | Alleen met internet, en alleen als je dat aanzet |

De installer die er nu is (`installer/y-next`) zet een complete ERPNext in Docker op de pc. Dat werkt, maar het is
een server op je laptop. De lokale vorm hieronder is iets anders: de app zelf, zonder ERPNext.

### De lokale vorm

Een afsplitsing van Y: dezelfde schermen, maar de laag die nu met ERPNext praat, schrijft naar een bestand.

- **Het bestand** bevat de hele administratie: relaties, projecten, uren, offertes, facturen, het grootboek en de
  instellingen. Voorstel: `.ifcx`, het formaat van de andere documenten van OpenAEC, met een eigen deel voor de
  administratie. Dan kan een project in het bestand naar hetzelfde gebouw wijzen als de tekeningen en het model.
  Een eigen extensie (bijvoorbeeld `.ifcy`) kan ook; dat is een keuze voor de herkenbaarheid, niet voor de techniek.
- **E-mail** staat niet in het bestand maar in een map ernaast, één bestand per bericht. Zo blijft het bestand klein
  en kan een mailprogramma of een back-up er gewoon bij.
- **Bijlagen** (pdf's van facturen, foto's) staan ook in die map.
- **De boekhouding rekent de app zelf**: wat ERPNext nu doet bij het boeken van een factuur (btw uitrekenen,
  journaalpost maken, bijhouden wat openstaat) moet de lokale kern doen. Dat is het grootste stuk werk, en het stuk
  dat het zorgvuldigst getest moet worden: met dezelfde voorbeeldboekhouding als in de cloud, en dezelfde uitkomst.
- **Uitwisselen**: het bestand kan naar de cloud (inlezen in een omgeving) en terug, en de boekhouder krijgt een
  auditfile (XAF) of UBL-facturen, net als in de cloud.
- **De installer** is één programma voor Windows, macOS en Linux, op dezelfde manier gebouwd als de andere tools van
  OpenAEC die zowel in de browser als op de pc draaien.

Wat de lokale vorm in de eerste versie niet heeft: meer gebruikers tegelijk, loon, bankkoppeling anders dan een
afschrift inlezen, en alles wat een server nodig heeft (gedeelde postbussen, agenda's van collega's).

De bron van de schermen staat nu in een eigen repo en hier alleen als gebouwd resultaat. Voor de afsplitsing en voor
elk herstel aan de boekhouding moet die bron hier komen.

## Volgorde

| Stap | Wat | Waarom in deze volgorde |
|---|---|---|
| 1 | **Boekhouding van Y kloppend**: de bevindingen herstellen, getoetst met één voorbeeldboekhouding | Alles wat volgt leunt erop; ook de lokale vorm |
| 2 | **Velden gelijk**: wat botst, het bedrijf leegmaken, Nederlandse administratie en project op één set namen | Voorwaarde om X, Y en Z samen te draaien |
| 3 | **Eén ingang**: de schermen van Y als de app, met de administratie van X erin en bellen bij het project | Eerste versie die een klant als één product ziet |
| 4 | **De assistent in het project**, te beginnen met de inkoopfactuur | Hier zit het verschil met een gewoon pakket |
| 5 | **Z als modules**: termijnen en meerwerk, calculatie, planning, bouwdagboek, projectbewaking | Per module, met overzetten van de gegevens |
| 6 | **De lokale vorm**: kern voor de boekhouding, het bestand, de installer | Kan naast 3 tot 5 lopen zodra stap 1 klaar is |
| 7 | **Installatietechniek en service** | Eerste sector naast de aannemer |

## Wat jij moet beslissen

1. De naam voor de klant (XYZ is een werknaam).
2. Het bestand van de lokale vorm: `.ifcx` met een eigen deel, of een eigen extensie.
3. Berichten: Raven als de ene plek, of de berichten van Y.
4. Of de lokale vorm gratis en los te downloaden is, of bij een abonnement hoort.
5. Met welke installateur we de begrippen van installatietechniek doorlopen voordat de doctypes vastliggen.
