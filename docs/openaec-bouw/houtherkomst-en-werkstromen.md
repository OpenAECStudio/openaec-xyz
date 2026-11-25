# Herkomst van hout, en werkstromen in alle bedrijven

Stand 25 november 2026. Twee onderwerpen die bij elkaar horen: wat de Europese regels een houthandel vragen vast te
leggen, en de goedkeuringsstromen (werkstromen) die daarbij en in de rest van de bedrijven nodig zijn. Het onderzoek
is van vandaag en komt uit openbare bronnen; **controleer artikelnummers en data in de wetstekst voordat iets hard in
het systeem komt**. Onzekerheden staan onderaan.

## De regels in het kort

De ontbossingsverordening (EUDR, Verordening (EU) 2023/1115) vervangt de houtverordening (EUTR).

- **Voor hout geldt de EUDR vanaf 30 december 2026**, ook voor kleine bedrijven: het uitstel naar 2027 geldt niet voor
  producten die al onder de EUTR vielen. Tot die datum geldt de EUTR. Bron: [NVWA](https://www.nvwa.nl/onderwerpen/plant/eudr-ontbossingsverordening/controle-door-nvwa),
  [Verordening 2025/2650](https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32025R2650).
- De **rol** bepaalt de plicht, en die verschilt per inkoop, niet per bedrijf:

| Situatie | Rol | Wat moet |
|---|---|---|
| Zelf importeren van buiten de EU | Marktdeelnemer | Zorgvuldigheid in drie stappen vóór het in de handel brengen, een zorgvuldigheidsverklaring indienen, het referentienummer doorgeven aan de afnemer, alles vijf jaar bewaren, het stelsel elk jaar evalueren |
| Inkopen bij een leverancier in de EU en doorverkopen | Handelaar of downstream | Geen eigen verklaring. Wel leveranciers en zakelijke afnemers vastleggen, en het referentienummer van de verklaring van de leverancier als die marktdeelnemer is; vijf jaar bewaren; melden bij aanwijzingen dat iets niet klopt |

- **Vast te leggen per partij** (artikel 9): omschrijving met handelsnaam en wetenschappelijke naam van de houtsoort,
  hoeveelheid, land van productie, de geolocatie van de percelen, de kapdatum of -periode, leverancier en afnemer, en
  bewijs dat het hout ontbossingsvrij (peildatum 31 december 2020) en legaal is. De HS-code staat in de verklaring.
- **De drie stappen**: informatie verzamelen, risico beoordelen (veertien criteria, waaronder het risiconiveau van het
  land, de complexiteit van de keten en het risico op vermenging), en risico beperken. Alleen bij "geen of
  verwaarloosbaar risico" mag het hout de markt op. Bij een land met laag risico mogen stap twee en drie vervallen,
  maar de keten en het risico op vermenging moeten nog steeds beoordeeld worden.
- **De verklaring** wordt ingediend in het informatiesysteem van de EU (op TRACES). Je krijgt een **referentienummer**
  en een **verificatienummer** terug. Het referentienummer moet mee naar de afnemer en in de douaneaangifte. Eén
  verklaring mag meer zendingen dekken zolang de keten gelijk blijft; de beoordeling moet minstens elk jaar opnieuw.
- **Certificaten** (FSC, PEFC) vervangen de zorgvuldigheid niet: ze zijn een hulpmiddel bij de risicobeoordeling. Je
  moet nagaan dat het certificaat geldig is en bij het product hoort. Los daarvan moet op een verkoopfactuur met een
  FSC-claim de **certificaatcode van de verkoper** en de **claim per regel** staan (FSC 100%, FSC Mix, ...); bij PEFC
  hetzelfde met de PEFC-claim.
- **Toezicht**: de NVWA, met de Douane aan de grens. De NVWA kijkt of het stelsel de drie stappen bevat, of het aan
  het fysieke product gekoppeld is, of de herkomst binnen het bedrijf te volgen is, en of alles vijf jaar bewaard is.
- **Koppeling**: het informatiesysteem heeft een officiële koppeling (SOAP), ook om een referentienummer met
  verificatienummer te controleren. Er is een acceptatieomgeving om tegen te testen.

## Wat er in het systeem komt

Wat er nu al is: het artikel heeft een keurmerk en een land van herkomst; tropisch hardhout loopt per partij; de
partij heeft land en gebied van herkomst.

Wat erbij komt, als module **Houtherkomst** in de app:

| Onderdeel | Wat | Waarom zo |
|---|---|---|
| **Houtsoort op het artikel** | Wetenschappelijke naam en HS-code (de HS-code is een bestaand veld van ERPNext), en een vinkje "valt onder de houtregels" | De verklaring vraagt ze; het vinkje bepaalt welke artikelen de controle krijgen |
| **Certificaat** | Van een leverancier of van het eigen bedrijf: systeem (FSC of PEFC), code, certificeerder, geldig van en tot | Een verlopen certificaat mag niet ongemerkt op een factuur komen |
| **Zorgvuldigheidsverklaring** | Eén document per keten: leverancier, land van productie met risiconiveau, houtsoort, kapperiode, percelen (geolocatie), de bewijsstukken als bijlage, de risicobeoordeling per criterium, de beperkende maatregelen, de uitkomst, en na indienen het referentienummer en het verificatienummer | Dit ís het stelsel dat de NVWA wil zien, per levering terug te vinden |
| **Partij** | Verwijst naar de verklaring en heeft de kapperiode | De partij verbindt het fysieke hout met de verklaring; de kapdatum bepaalt ook of oud hout nog onder de EUTR valt |
| **Rol per inkoop** | Volgt uit het land van de leverancier: buiten de EU is marktdeelnemer, binnen de EU is handelaar | Niet per bedrijf in te stellen, want een houthandel is allebei |
| **Blokkade bij ontvangst** | Hout van buiten de EU komt het magazijn niet in zonder een verklaring die is ingediend; hout van een leverancier in de EU niet zonder diens referentienummer | Het advies van FSC is letterlijk: geen nummer, niet accepteren |
| **Op de verkoopfactuur** | Het referentienummer van de partij, de claim per regel en de eigen certificaatcode | Wettelijk (nummer) en volgens de norm van FSC en PEFC (claim en code) |
| **Bewaren** | Verklaring, bijlagen en beoordeling zijn vijf jaar niet te verwijderen | Bewaartermijn |
| **Herinneren** | Een maand voor een certificaat verloopt, en elf maanden na een beoordeling | Jaarlijkse herbeoordeling |

De koppeling met het informatiesysteem zelf (indienen en controleren) is een latere stap: eerst vastleggen en
blokkeren, dan tegen de acceptatieomgeving testen. Tot die er is, neemt de gebruiker de nummers over.

### De werkstroom van een verklaring

`Concept` → `Informatie compleet` → `Risico beoordeeld` → `Ingediend` → (na een jaar) `Te herbeoordelen`

- De **inkoper** verzamelt de informatie en zet de verklaring op Informatie compleet.
- De **verantwoordelijke voor de houtregels** (een aangewezen persoon; de NVWA vraagt daarnaar) beoordeelt het risico.
  Bij een uitkomst anders dan verwaarloosbaar gaat de verklaring terug met de maatregelen die nodig zijn, of wordt de
  leverancier afgewezen.
- Na het indienen komen de nummers erbij, en pas dan mag de partij ontvangen worden.

## Werkstromen in alle bedrijven

Een werkstroom is een vaste reeks stappen met per stap wie hem doet. Ze worden vastgelegd als werkstroom van ERPNext
zelf (`Workflow`), niet als losse vinkjes of statusvelden, zodat ze overal hetzelfde werken: in ERPNext, in de
schermen van Y (die een werkstroom al kunnen toepassen bij planning en taken) en straks in de assistent.

Wat we overnemen van hoe AFAS dit doet, omdat het werkt:

1. **Sturen op verantwoordelijkheid, niet op een persoon**: "de leidinggevende van", "de projectleider van het
   project". Een werkstroom overleeft dan een personeelswissel. De lijn van afdelingshoofd tot directeur staat
   daarvoor al op de medewerker.
2. **Een vaste set acties**: akkoord, afkeuren, meer informatie vragen, overdragen. En vervanging bij afwezigheid.
3. **Het akkoord doet de mutatie zelf**: verlof is geboekt zodra het is goedgekeurd, zonder overtypen.
4. **De status blokkeert het vervolg**: een inkoopfactuur gaat niet in het betaalbestand vóór het akkoord. Dezelfde
   regel als "geen ontvangst zonder verklaring".
5. **Signalen op een datum** die een werkstroom starten: een certificaat dat verloopt, een keuring, een contract.
6. **Eén takenlijst** met alles wat op jou wacht, in de app en op de telefoon.

### De stromen, per bedrijf

| Werkstroom | Stappen | Waar |
|---|---|---|
| Inkoopfactuur accorderen | inboeken → akkoord projectleider of budgethouder → (boven een grens) akkoord directeur → vrij voor betaling | alle bedrijven |
| Offerte uitbrengen | opstellen → akkoord directeur boven een grens → verstuurd → opdracht of afgewezen | alle bedrijven |
| Meerwerk | melden door de uitvoerder → prijs door de calculator → akkoord opdrachtgever → opgedragen | aannemer, installateur |
| Onderaannemer contracteren | aanvraag → vergelijken → controle G-rekening en verklaring betalingsgedrag → contract | aannemer |
| Verlof | aanvragen → akkoord leidinggevende → geboekt | alle bedrijven |
| Declaratie en kilometers | indienen → akkoord leidinggevende → uitbetalen | alle bedrijven |
| Indiensttreding | gegevens → contract → account en middelen → eerste werkdag | holding (personeelszaken) |
| Zorgvuldigheidsverklaring hout | zie hierboven | houthandel |
| Keuring materieel | signaal voor de vervaldatum → keuring → goedgekeurd of buiten gebruik | materieelverhuur |
| Storing en werkbon | melding → inplannen → uitvoeren → akkoord klant → factuur | installateur |
| Rapport en advies vrijgeven | opstellen → collegiale toets → vrijgave | adviesbureau, sondeerbedrijf |
| Kwartaalcijfers aan de holding | opstellen door het bedrijf → vragen van de financieel directeur → vastgesteld | alle dochters |

De eerste die gebouwd wordt is **Inkoopfactuur accorderen**, omdat het betaalbestand er al is en de blokkade daar
direct op aansluit; daarna de verklaring voor hout.

Punt dat in Y hersteld moet worden: declaraties en kilometers hebben nu een eigen statusveld dat de indiener zelf op
goedgekeurd kan zetten. Dat wordt een werkstroom met een leidinggevende.

## Onzeker of nog na te gaan

- De overgang van oud hout (gekapt vóór 29 juni 2023): de einddatum en de precieze formulering van artikel 37.
- Of het verificatienummer verplicht mee moet naar de afnemer. Het is wel nodig om een nummer elektronisch te
  controleren; daarom leggen we beide vast en geven we beide door.
- Of er per zending of per keten een verklaring nodig is: overheidsbronnen verschillen. Het ontwerp laat allebei toe
  (één verklaring, veel partijen).
- De lijst met het risiconiveau per land wordt herzien; het niveau is daarom een veld op de verklaring, geen vaste
  tabel in de code.
- Of er voor de koppeling met het informatiesysteem nog verplichte toetsen vooraf gelden.
- De nieuwe versie van de FSC-norm voor de handelsketen (versie 4) is in voorbereiding.
- Bij AFAS zijn een mandagenregister, materieelbeheer en een servicemodule niet als eigen functie bevestigd; die
  nemen we dus niet "van AFAS" over maar ontwerpen we zelf.
