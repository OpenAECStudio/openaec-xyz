# Klantenportaal: volg je project, volg je woning

Stand 27 november 2026. Ontwerp, nog niet gebouwd. Een standaardmodule van XYZ, **Klantenportaal**: de klant logt in
op een eigen omgeving, volgt daar zijn project of zijn woning, en communiceert er met het bedrijf. Het bedrijf ziet
aan zijn kant precies wat de klant ziet en wat de klant ervan vindt.

## Twee kanten

| Kant | Wie | Waar |
|---|---|---|
| **Bedrijf** | Wie XYZ gebruikt: aannemer, installateur, bureau, houthandel. Projectleider, uitvoerder, kopersbegeleider | In ERPNext en de Y-app, bij het project |
| **Klant** | Opdrachtgever, koper van een woning, of een zakelijke klant zoals een hovenier met veel projecten | In het portaal, als websitegebruiker, op telefoon en laptop |

Een klant kan drie dingen zijn, en het portaal kent ze alle drie:

- **Koper** van één bouwnummer in een project met meer woningen: ziet alleen zijn eigen woning ("volg je woning").
- **Opdrachtgever** van een heel project: ziet het project.
- **Hoofdgebruiker** bij een zakelijke klant: ziet alle projecten van zijn organisatie en nodigt collega's uit. Dit
  is wat het concept van de Hout Cloud bij Van Dorp Hout al laat zien: de hovenier ziet zijn projecten met tekeningen
  en het 3D-model, en dient er nieuwe in.

## Wat de klant ziet

Elk onderdeel staat per bedrijf aan of uit, en **niets is zichtbaar tot het bedrijf het deelt**.

| Onderdeel | Wat | Waar het vandaan komt |
|---|---|---|
| **Voortgang** | Tijdlijn met fasen en mijlpalen (fundering, ruwbouw, wind- en waterdicht, oplevering), wat klaar is, wat nu loopt, de verwachte opleverdatum | Projectfasen en taken met het vinkje "zichtbaar voor de klant" |
| **Foto's** | Bouwfoto's per datum, met een korte tekst, per project of per bouwnummer | De uitvoerder maakt ze op de bouw (telefoon) en zet ze op "delen" |
| **Tekeningen en documenten** | Altijd de laatste versie, met de vorige eronder; een melding bij een nieuwe versie; 3D-model als dat er is; opmerkingen op een tekening | Docs van de omgeving, met versies; het 3D-model en de opmerkingen zoals bij de datadrop |
| **Berichten** | Eén gesprek per project of bouwnummer, met bijlagen en foto's; beide kanten zien wie wat gelezen heeft; een mail als er iets nieuws is | Berichten aan het project, zoals de communicatie die ERPNext al kent |
| **Keuzes en meer- en minderwerk** | Kopersopties met prijs en sluitingsdatum, kiezen en akkoord geven; meerwerk van het bedrijf accepteren | Optielijst per projecttype; akkoord wordt een offerteregel of meerwerk in de termijnstaat |
| **Facturen en termijnen** | Het termijnschema, wat gefactureerd en betaald is, de pdf | Verkoopfacturen en de termijnstaat |
| **Afspraken** | Kijkdag, keuzegesprek, voorschouw, oplevering | Agenda van het project |
| **Opleverpunten en meldingen** | De klant meldt een punt met foto en plek; ziet de status tot het is opgelost | Melding of klacht, straks in de module Kwaliteit en veiligheid |
| **Wat vind je ervan** | Na een mijlpaal een korte vraag: cijfer en een zin | Reacties per fase |
| **Aanvragen** | Een nieuw project indienen (Hout Cloud: zelf samenstellen in de wizard en indienen) | Wordt een kans (Opportunity) bij het bedrijf |

## Wat het bedrijf ziet

Bij het project in ERPNext en in de Y-app een tabblad **Klant**:

- **Zien als de klant**: het portaal precies zoals deze klant of koper het ziet, zonder in te loggen als die klant.
- Per foto, document, mijlpaal en bericht een schakelaar **gedeeld / niet gedeeld**, met wie het deelde en wanneer.
- Wie wat gelezen heeft, welke vragen openstaan, welke keuzes nog moeten (met de sluitingsdatum), en de reacties en
  cijfers per fase.
- Een nieuwe versie van een tekening klaarzetten: de klant krijgt een melding, en het bedrijf ziet wanneer hij
  geopend is.
- Bij een project met veel woningen: een overzicht per bouwnummer (wie heeft gekozen, open opleverpunten, laatste
  bericht).

## Hoe het gebouwd wordt

Het rust op wat Frappe en ERPNext al hebben, en vult aan:

- **Bekijken met een verborgen link** (de basis): het bedrijf deelt per project of bouwnummer een link met een
  lange willekeurige sleutel (`/portaal/l/<sleutel>`). Wie de link heeft, ziet alleen wat gedeeld is en kan niets
  doen: geen berichten, geen keuzes, geen akkoord. De link heeft een einddatum, kan per stuk ingetrokken worden, en
  elk bezoek komt in het logboek. Geen account nodig.
- **Inloggen met een account** (voor reageren, berichten, keuzes en akkoord): de klant is een websitegebruiker (geen
  bureaubladgebruiker, dus geen licentie- of rechtenvragen in het ERP), gekoppeld aan een contactpersoon van de
  klant. Hij logt in met zijn **Apple-, Microsoft- of Google-account** via de inlog van de SuperCloud (openaec_sso;
  Google en Apple werken daar al voor het forum, Microsoft komt erbij). Geen eigen wachtwoord bij het bedrijf. Wie
  een verborgen link heeft, ziet in het portaal de knop "Inloggen om te reageren"; na het inloggen wordt de link aan
  zijn account gekoppeld (Portaaltoegang), zodat hij daarna zonder link binnenkomt.
- **Wat er al is**: ERPNext heeft een eenvoudig portaal met projecten (`/project`), offertes, facturen en meldingen,
  en per project een lijst gebruikers met "bijlagen zien". Dat is te kaal om te tonen, maar de rechten en de koppeling
  aan de klant nemen we over.
- **Nieuw in de module**:

| Doctype | Waarvoor |
|---|---|
| **Portaaltoegang** | Gebruiker, klant, project of bouwnummer, rol (koper, opdrachtgever, hoofdgebruiker), sinds wanneer |
| **Bouwnummer** | Project, nummer, adres, type, koper(s), status, gekozen opties |
| **Bouwfoto** | Bestand, datum, project, bouwnummer, bijschrift, gedeeld ja/nee |
| **Kopersoptie** en **Koperskeuze** | Optielijst met prijs en sluitingsdatum; de keuze met akkoord, datum en wie |
| **Klantreactie** | Fase, cijfer, tekst |
| Vinkje **zichtbaar voor de klant** | Op taak (mijlpaal), bestand en bericht |

- **De pagina's**: één webapp onder `/portaal` op de omgeving, voor de telefoon eerst, in de huisstijl van het bedrijf
  (logo en kleuren uit de SuperCloud). Elke vraag gaat via de API van de module, die per verzoek nagaat of deze
  gebruiker dit project of bouwnummer mag zien. Nooit een lijst die eerst alles ophaalt en dan filtert.
- **Bestanden** komen uit Docs; de datadrop van het BIM-platform levert het 3D-model en de opmerkingen op tekeningen.
- **Meldingen** per mail, en later als pushbericht.

## Privacy

- Een koper ziet nooit iets van een andere koper, ook niet zijn naam.
- Persoonsgegevens van kopers vallen onder de AVG: bewaartermijn na oplevering per bedrijf in te stellen, en een
  klant kan zijn gegevens inzien.
- Elke deelactie en elke inzage staat in een logboek.

## Volgorde van bouwen

1. Verborgen link, inloggen met Apple, Microsoft of Google, Portaaltoegang, mijn projecten, voortgang, foto's en
   berichten. Het tabblad Klant met "zien als de
   klant".
2. Tekeningen en documenten met versies en meldingen; 3D-model via de datadrop.
3. Facturen, termijnen en afspraken.
4. Bouwnummers met kopersopties, keuzes en meer- en minderwerk.
5. Opleverpunten en reacties per fase.
6. Het concept van de Hout Cloud erop: projecten van een hovenier, het 3D-model, de montagehandleiding, aanvragen
   indienen.

In het demonstratiebedrijf: de aannemer krijgt een project met twaalf woningen en kopers, het adviesbureau een
opdrachtgever die tekeningen volgt.

## Besluiten (27 november 2026)

- Het portaal zit standaard in elke omgeving met XYZ (OpenAEC Bouw), niet als module die aan of uit moet.

- In de basis bekijkt de klant alles met een verborgen link, zonder account.
- Voor reageren en communiceren logt hij in met zijn Apple- of Microsoft-account (en Google), niet met een
  wachtwoord bij het bedrijf.
- De klant communiceert via het portaal, niet via losse mail. Een mail meldt alleen dat er iets nieuws is, met een
  link naar het portaal.

## Open vragen

1. Het portaal op het adres van de omgeving, of per bedrijf een eigen adres (bijvoorbeeld `mijn.<bedrijf>.nl`)?
