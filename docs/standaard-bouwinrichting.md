# Voorstel: standaardinrichting van een ERP-omgeving voor de bouw

Stand 20 november 2026. Voorstel; de eerste versie van de app staat in openaec-bench PR 88.

## Waarom

Een nieuwe ERP-omgeving in de SuperCloud is kaal ERPNext. Onze klanten zitten allemaal in de bouw, maar niets in de
omgeving weet dat. Gemeten op 19 november op de omgevingen van Van Mierlo, Dorphout en de demo:

- **Apps:** ERPNext, Y-Next en de OpenAEC-apps (Beheer, SSO, Storage, werkplek, BIM). CRM, Raven, HRMS, Helpdesk, Wiki,
  Insights en Gameplan staan in het image, maar een beheerder moet ze per stuk zelf toevoegen
  (`APPSET_KLANTSITE_FRAPPE_EXTRA`).
- **Inrichting:** alleen de wizard van ERPNext (`openaec_beheer.uitvoerder.wizard`): bedrijf, afkorting, Nederland, euro
  en het rekeningschema `Standard`. Dat schema is Engels en algemeen.
- **Btw:** ERPNext levert voor Nederland 21% en 6%. Het lage tarief is sinds 2019 9%; 0% en verlegd ontbreken.
- **Stamgegevens:** de Engelse voorbeelden van ERPNext (activiteiten Planning, Research, Proposal Writing, Execution,
  Communication). Geen projecttypes, fasen, uursoorten of artikelgroepen voor de bouw.
- **Menu's:** die van een productiebedrijf (Manufacturing, Stock, Assets, Quality).
- **Fouten:** een verse omgeving (de demo) heeft geen fouten in het Error Log. Er is alleen geen test die dat bewaakt.

## Het doel: één OpenAEC-implementatie van ERPNext voor de hele bouw

Niet een inrichting per klant, maar één brede **OpenAEC-implementatie op ERPNext** die elk bedrijf in de bouwsector
kan gebruiken: grote en kleine aannemers, installatiebedrijven, houthandels en andere leveranciers,
ingenieursbureaus en architectenbureaus. De basis is breed; per omgeving zet je **modules** aan en uit, zodat een
architectenbureau geen voorraad ziet en een houthandel geen ontwerpfasen.

Een module is een afgebakend stuk inrichting (stamgegevens, sjablonen, werkruimtes, later ook velden en rapporten).
De eerste versie (openaec-bench PR 88) heeft vier modules; de lijst groeit. Voorbeelden van latere modules:

| Module | Voor |
|---|---|
| Basis, Projecten | iedereen |
| Ontwerp en engineering | ingenieurs- en architectenbureaus |
| Uitvoering | aannemers en installateurs |
| Installatietechniek | installatiebedrijven: onderhoudscontracten, serviceorders, keuringen |
| Handel en voorraad | houthandels en bouwmaterialen: voorraad, prijslijsten, levering |
| Materieel | verhuur en eigen materieel |
| Onderaanneming | wet ketenaansprakelijkheid, G-rekening, verlegging |
| Uren en verlof | via HRMS |

Er komt een plek in **Beheer → Inrichting** waar de eigenaar modules aan en uit zet, met per module wat hij doet. Dat
scherm is een latere stap; de lader kan het al (`openaec_bouw.profiel.zet_module`).

Bij het aanmaken van een omgeving kan later een **profiel** gekozen worden (Aannemer, Installateur, Handel, Bureau):
een profiel is niet meer dan een lijst modules die aan staan.

## De vorm: een app, met een modelomgeving ernaast

Twee manieren liggen voor de hand: een modelomgeving die je kopieert, of een app die de inrichting bevat. Het voorstel
is beide te doen, elk voor waar het goed in is.

**De inrichting zit in een app: `openaec_bouw`.** De app bevat de modules als gegevensbestanden (JSON) en een lader
die ze idempotent toepast. Redenen:

- De inrichting staat in git: elke wijziging is te zien, te reviewen en terug te draaien.
- Een nieuwe versie komt met de gewone uitrol bij **alle** omgevingen, ook de bestaande. Een gekopieerde
  modelomgeving kan dat niet: wat al gekopieerd is, loopt daarna uiteen.
- De tests draaien tegen een verse site met het profiel erop.
- Een kopie van een database neemt ook mee wat er niet in hoort (gebruikers, sleutels, testgegevens).

**Daarnaast staat er één modelomgeving: `model.cloud.open-aec.eu`.** Dat is een gewone omgeving van de klant "OpenAEC
(model)", kosteloos, met de app en een paar voorbeeldprojecten. Daar kijk je, daar praten we over, en daar probeer je
een wijziging uit. De modelomgeving is de plek om te beslissen, de app is de bron:

1. Je past in de modelomgeving iets aan (een fase erbij, een uursoort anders).
2. De workflow **Bouwprofiel exporteren** leest de stamgegevens uit de modelomgeving en zet het verschil als pull
   request op de app.
3. Na de merge krijgt elke omgeving het bij de volgende uitrol.

Zo blijft er één waarheid (de app) en hoeft niemand JSON te schrijven om de standaard te wijzigen.

**Regels van de lader**

- Alleen **aanvullen**: wat een klant zelf heeft gewijzigd of verwijderd, blijft zoals de klant het wil. De lader
  onthoudt per record welke versie hij zette (`Bouwprofiel Regel`) en raakt een door de klant gewijzigd record niet aan.
- Een klant kan het profiel uitzetten (Beheer → Inrichting). Een omgeving die geen bouwbedrijf is, krijgt het niet.
- Niets in het profiel is een transactie. Geen boekingen, geen facturen.

## Wat er standaard op komt

### Apps

| App | Voorstel | Opmerking |
|---|---|---|
| CRM | standaard | Zie beslissing 2: ERPNext heeft zelf ook leads en kansen. |
| Raven | standaard | Zie beslissing 3: Y-Next heeft een eigen berichtenfunctie. |
| HRMS | keuze bij aanmaken | Verlof en declaraties; niet elk bureau wil dat hier. |
| Helpdesk, Wiki, Insights, Gameplan | keuze, zoals nu | |

### Bouwprofiel (eerste aanzet, door Maarten te bevestigen)

| Onderdeel | Inhoud |
|---|---|
| Btw | 21%, 9%, 0% en **verlegd** (onderaanneming in de bouw), met sjablonen voor verkoop en inkoop |
| Projecttypes | Nieuwbouw, Verbouw en renovatie, Onderhoud, Infra, Advies en engineering, Intern |
| Fasen ontwerp | SO, VO, DO, TO, UO |
| Fasen uitvoering | Calculatie, Werkvoorbereiding, Uitvoering, Oplevering, Nazorg |
| Uursoorten | Calculatie, Werkvoorbereiding, Tekenwerk en modelleren, Berekeningen, Projectleiding, Uitvoering, Toezicht, Overleg, Reistijd, Meerwerk, Intern |
| Artikelgroepen | Arbeid, Materiaal, Materieel, Onderaanneming, Advies en diensten, Stelposten |
| Eenheden | uur, dag, week, m, m², m³, stuk, kg, ton, post (Nederlands, naast die van ERPNext) |
| Klantgroepen | Particulier, Zakelijk, Overheid, Woningcorporatie, Aannemer, Architect en adviseur |
| Leveranciersgroepen | Onderaannemer, Materiaalleverancier, Verhuur materieel, Adviseur, Zzp |
| Projectsjablonen | Per projecttype een sjabloon met de fasen als taken |
| Betaalvoorwaarden | 14 dagen, 30 dagen, en een termijnstaat (bijvoorbeeld 30/40/25/5) |
| Functies | Projectleider, Werkvoorbereider, Calculator, Uitvoerder, Modelleur, Constructeur, Administratie |

### Menu's

- Manufacturing, Assets, Quality en Stock verborgen (terug te zetten in Beheer).
- Een werkruimte **Bouwbedrijf** vooraan: projecten, offertes, uren, facturen en inkoop.
- De meeste medewerkers werken in Y-Next. Het profiel moet daar zichtbaar zijn: de projecttypes, fasen en uursoorten
  zijn dezelfde records.

### Rekeningschema

Voor een **nieuwe** omgeving het Nederlandse schema dat ERPNext meelevert (`Netherlands - Grootboekschema`) in plaats
van `Standard`. Dat is een algemeen Nederlands schema, niet op de bouw gericht en niet RGS. Een eigen schema op basis
van RGS, met onderhanden werk en onderaanneming, is een latere stap samen met een boekhouder.

Bij een **bestaande** omgeving blijft het schema zoals het is: een schema wisselen kan niet meer als er geboekt is.

## Stappen

1. **Bewaken dat een verse omgeving schoon is.** Een test in de uitrol: omgeving aanmaken, als eigenaar openen
   (Desk, Y-Next, Beheer), en falen als er een regel in het Error Log staat. Dit staat los van het profiel.
2. **App `openaec_bouw` met lader en het profiel hierboven.** In de appset van een ERP-omgeving; CRM en Raven erbij.
   Nieuwe omgevingen krijgen het Nederlandse rekeningschema en de juiste btw.
3. **Modelomgeving** aanmaken en de workflow Bouwprofiel exporteren.
4. **Bestaande omgevingen**: het profiel aanvullend toepassen, per klant na overleg (eerst de demo en de
   modelomgeving, dan de klanten).
5. **Menu's en de werkruimte Bouwbedrijf.**
6. Later: rekeningschema op basis van RGS.

## Beslissingen voor Maarten

1. **De lijsten hierboven**: kloppen de projecttypes, fasen, uursoorten en groepen? Welke modules komen eerst na de
   eerste vier?
2. **CRM**: de losse app Frappe CRM, of de leads en kansen die al in ERPNext zitten? Twee tegelijk geeft twee plekken
   voor dezelfde klant.
3. **Raven**: naast de berichten van Y-Next, of in plaats daarvan? Twee chats in één omgeving is verwarrend.
4. **Modelomgeving**: op staging nu, of pas in prod na de verhuizing?
5. **Bestaande klanten**: het profiel bij iedereen aanvullen, of alleen bij wie erom vraagt?

## Los hiervan: Van Mierlo

De omgeving van Van Mierlo heeft honderden fouten in het Error Log (19 november) over de doctypes `VM Rubriek` en
`VM Toegangsrol`. Die zijn als ingebouwd doctype aangemaakt in plaats van als maatwerk; Frappe zoekt daardoor code die
niet bestaat. Dat is maatwerk in die ene omgeving en geen fout van de standaard. Herstellen vraagt een wijziging in de
omgeving van de klant, dus pas na akkoord.
