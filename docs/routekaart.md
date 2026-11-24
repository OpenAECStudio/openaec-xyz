# Routekaart OpenAEC Bouw

Stand 21 november 2026, bij versie 0.2.0 van de app `openaec_bouw`. Het ontwerp van de app staat in
`docs/standaard-bouwinrichting.md`; dit stuk gaat over wat erna komt, voor welke bedrijven, en in welke volgorde.

## Het idee

Eén OpenAEC-implementatie van ERPNext voor de hele bouwsector. Geen inrichting per klant: één app met veel modules,
en per omgeving staat aan wat dat bedrijf nodig heeft. Elke stap is een **versie van de app** (zie
`apps/openaec_bouw/CHANGELOG.md`). Een versie gaat eerst naar de modelomgeving (`model.cloud.open-aec.eu`), daar
kijken en praten we, en daarna komt hij met de gewone uitrol bij elke omgeving die de app heeft.

**XYZ (besluit van 23 november 2026).** Het eindbeeld is één app, **XYZ**: de totale laag op ERPNext voor de hele
bouwsector, van installatiebedrijf tot eenmanszaak. Daarin gaan drie dingen op die nu los staan: de inrichting van
OpenAEC Bouw (deze app), **Y-Next** (waar medewerkers werken: projecten, uren, agenda) en **Z-Next** (het
aannemersmaatwerk: termijnen, calculatie, planning). Een klant ziet straks één product met modules, niet drie apps.
De technische naam `openaec_bouw` blijft tot de samenvoeging; hernoemen is een eigen stap (zie de besluiten onderaan).

## Waar we staan (0.2.0)

| Onderdeel | Stand |
|---|---|
| Startscherm | Tegel **Bouwbedrijf** met werkruimte en Nederlandse zijbalk |
| Rustig menu | Productie, voorraad, activa, kwaliteit, support en dergelijke uit de navigatie |
| Stamgegevens | Projecttypes, fasen, uursoorten, functies, groepen, eenheden, termijnstaat, projectsjablonen |
| Btw | 21%, 9%, 0% en verlegd; rapport Btw-aangifte voor het binnenland |
| Loon | Looncomponenten, verlofsoorten, dienstverbanden en declaratiesoorten (alleen de structuur) |

Wat er nog **niet** is, en wat een Nederlandse administratie wel nodig heeft:

- **Rekeningschema.** Een nieuwe omgeving krijgt nog het Engelse schema `Standard`. Het Nederlandse schema van
  ERPNext is geprobeerd (21 november): de rekeningen komen goed, maar het bedrijf krijgt dan geen standaardrekening
  voor omzet, afronding en afboeking, en dan loopt de eerste factuur vast. Het schema kan dus pas de standaard worden
  als de app ook die standaardrekeningen zet.
- **Btw buitenland** (rubriek 3 en 4, opgaaf ICP), en de aangifte zelf indienen.
- **Loonberekening en loonaangifte.** Zie de keuze bij 0.4.
- **Bank en betalen:** SEPA-betaalbestanden, bankafschriften inlezen, G-rekening.
- **E-factureren:** UBL en Peppol, voor overheid en grote opdrachtgevers.

## De sectoren

Een **profiel** is een lijst modules die aan staan. Bij het aanmaken van een omgeving kies je een profiel; daarna zet
de eigenaar modules aan en uit in Beheer → Inrichting.

| Sector | Wat ze doen in het ERP | Modules bovenop Basis en Projecten |
|---|---|---|
| Kleine aannemer en zzp (tot 10 man) | Offerte, opdracht, factuur, uren; boekhouder doet de rest | Uitvoering |
| Middelgrote aannemer (10 tot 100) | Calculatie naar begroting, termijnstaten, meer- en minderwerk, onderaannemers, uren per project, werkvoorbereiding | Uitvoering, Calculatie, Onderaanneming, Uren en verlof, Materieel |
| Grote aannemer (100+) | Meerdere bv's met consolidatie, projectbewaking (budget, prognose einde werk, onderhanden werk), raamcontracten inkoop, kwaliteit en veiligheid | Als middelgroot, plus Projectbewaking, Concern, Kwaliteit en veiligheid |
| Installatiebedrijf | Projecten én service: onderhoudscontracten, storingen, werkbonnen, installaties per adres, keuringen, busvoorraad, artikelen van de groothandel | Uitvoering, Installatietechniek, Service en onderhoud, Handel en voorraad |
| Handel (hout, bouwmaterialen) | Voorraad, prijslijsten per klantgroep, afhalen en bezorgen, zaagwerk op maat | Handel en voorraad |
| Ingenieurs- en architectenbureau | Fasen, uren, honorarium, capaciteit | Ontwerp en engineering, Uren en verlof |

## De modules die komen

| Module | Inhoud | Voor |
|---|---|---|
| Administratie Nederland | Nederlands rekeningschema met standaardrekeningen, btw buitenland en ICP, SEPA, bankafschriften, UBL en Peppol, jaarafsluiting | iedereen |
| Uren en verlof | Weekstaat per project, goedkeuren, verlof en declaraties (Frappe HR), doorbelasten | iedereen met personeel |
| Loon | Zie 0.4 | iedereen met personeel |
| Calculatie | Begroting met hoofdstukken en staartkosten, van calculatie naar projectbudget en inkoop | aannemers, installateurs |
| Termijnen en meerwerk | Termijnstaat per project, meer- en minderwerk met akkoord van de opdrachtgever, opleverpunten | aannemers, installateurs |
| Onderaanneming | Wet ketenaansprakelijkheid: G-rekening, verklaring betalingsgedrag, mandagenregister; inkoopcontracten | aannemers |
| Projectbewaking | Budget tegen werkelijk, prognose einde werk, onderhanden werk per periode | middelgroot en groot |
| Installatietechniek | Installaties en objecten per adres, keuringen met vervaldatum, artikeldata van de groothandel | installateurs |
| Service en onderhoud | Onderhoudscontracten, storingen, werkbonnen op de telefoon, terugkerende taken | installateurs, onderhoud |
| Handel en voorraad | Zet voorraad weer aan, magazijnen, prijslijsten, afhalen en bezorgen | handel, installateurs |
| Materieel | Eigen materieel en verhuur, keuringen, doorbelasten aan projecten | aannemers |
| Concern | Meerdere bedrijven, onderlinge facturen, consolidatie | groot |
| Kwaliteit en veiligheid | Werkplekinspecties, incidenten, certificaten van mensen | groot |

## De volgorde

| Versie | Wat | Waarom nu |
|---|---|---|
| 0.1 | Lader en de eerste vier modules | klaar |
| 0.2 | Startscherm, rustig menu, btw-aangifte, begin van loon | klaar |
| 0.3 | **Administratie Nederland** en het scherm **Beheer → Inrichting** met profielen | Zonder kloppende boekhouding is de rest niet te verkopen; samen met een boekhouder |
| 0.4 | **Uren en verlof**, en **Loon** | Zie de keuze hieronder |
| 0.5 | **XYZ**: Y-Next en Z-Next erin. Y-Next als de werkschermen (projecten, uren, agenda); Z-Next als modules (termijnen en meerwerk, calculatie, planning, terugkerende taken) | Bestaat al; wordt samen de basis van alle sectoren |
| 0.6 | **Installatietechniek** en **Service en onderhoud** | Eerste sector naast de aannemer |
| 0.7 | **Onderaanneming** en **Projectbewaking** | Middelgrote en grote aannemers |
| 0.8 | **Handel en voorraad**, **Materieel** | Handel |
| 0.9 | **Concern**, **Kwaliteit en veiligheid** | Grote aannemers |
| 1.0 | Alle klanten op de app, profielen per sector vast | |

## Keuze bij 0.4: loon

Twee wegen, met een groot verschil in werk en risico.

- **A. Koppelen met een loonpakket.** Het ERP levert uren, verlof, declaraties en mutaties aan (Nmbrs, Loket, AFAS of
  de salarisadministrateur) en krijgt de loonjournaalpost terug. De loonberekening, de cao en de loonaangifte blijven
  bij een partij die dat elk jaar bijhoudt.
- **B. Zelf verlonen in het ERP.** Loonheffingstabellen, de cao Bouw en Infra, pensioen bij bpfBOUW, de loonaangifte
  naar de Belastingdienst, en elk jaar de nieuwe cijfers. Fouten raken het loon van mensen.

Voorstel: A eerst. De module van 0.2 legt de structuur klaar die voor beide nodig is.

## Y-Next en Z-Next gaan op in XYZ

De samenvoeging gaat in stappen, zodat geen klant iets kwijtraakt:

1. **Eén ingang.** De tegel Bouwbedrijf wordt de tegel XYZ; de schermen van Y-Next en Z-Next hangen eronder.
2. **Eén set stamgegevens.** Wat Y-Next en Z-Next zelf aan types, fasen en uursoorten hebben, wordt dat van de app.
3. **Code samen.** De doctypes en schermen verhuizen als modules naar één app; de oude apps blijven leeg staan tot
   elke omgeving over is. Doctypes houden hun naam, dus er hoeft geen klantdata om.
4. **Velden opruimen.** De 370 eigen velden van Z-Next op standaard-doctypes gaan naar eigen doctypes of vervallen.

- **Y-Next** is waar de meeste medewerkers werken (projecten, uren, agenda). De stamgegevens van OpenAEC Bouw zijn
  nu al dezelfde records: een projecttype of uursoort uit de app is in Y-Next direct te kiezen. De code staat in een
  eigen repo en draait bij elke klant; dat is de grootste verhuizing en vraagt een eigen ontwerp.
- **Z-Next** is nu het maatwerk van één klant in een eigen app: projectadministratie, planning, offertes,
  termijnstaten, terugkerende taken en de koppeling met Bouw7. In 0.5 gaan de algemene delen als modules naar OpenAEC
  Bouw; wat alleen voor die klant geldt, blijft in Z-Next of wordt een klantmodule. Let op: Z-Next zet 370 eigen
  velden; op een omgeving met Z-Next past Frappe HR nu niet meer in de tabel van het bedrijf (lokaal gezien op
  21 november). Dat moet opgelost zijn voordat loon en Z-Next samen op één omgeving staan.

## Wat nog besloten moet worden

1. De volgorde hierboven, en welke sector na de aannemer komt.
2. Loon: weg A of B.
3. Het rustige menu: bij bestaande klanten aanzetten, of alleen bij nieuwe omgevingen.
4. Wie de boekhouder is die het Nederlandse rekeningschema en de btw-aangifte naloopt.
5. XYZ: de definitieve naam (ook voor de klant), en of de app technisch hernoemd wordt of `openaec_bouw` blijft heten.
6. De nog open keuzes uit `docs/standaard-bouwinrichting.md` (CRM, Raven).
