# Velden van X, Y en Z naast elkaar

Stand 25 november 2026. Dit stuk legt vast welke eigen velden en doctypes de drie apps gebruiken, waar ze hetzelfde
bedoelen of elkaar in de weg zitten, en wat er per geval mee gebeurt. Het is de uitwerking van stap 2 en 4 uit
`docs/routekaart.md` ("één set stamgegevens" en "velden opruimen").

Bron: de code in deze repo (`apps/openaec_bouw`, `apps/y_next`, `apps/z_next`). Er is nog niets gewijzigd; dit is het
plan.

## De cijfers

| App | Eigen doctypes | Eigen velden op standaard-doctypes | Hoe gezet |
|---|---|---|---|
| X (`openaec_bouw`) | 1 (`Bouwprofiel Regel`) | 10 | `boekhouding.py`, bij elke migratie |
| Y (`y_next`) | 7 | ruim 25 | `setup/custom_fields.json`, bij elke migratie |
| Z (`z_next`) | 46, waarvan 9 kindtabellen | 357 (plus 13 op eigen doctypes) | fixture `custom_field.json` |

Z per doctype: Company 93, Project 54, Customer 43, Supplier 42, Quotation 30, Employee 26, Sales Invoice 14,
Purchase Invoice 11, Item 8, Purchase Order 7, Purchase Invoice Item 6, File 5, Project Type 4, Department 4, UOM 3,
Quotation Item 2, Timesheet Detail 2, en één op Purchase Order Item, Item Group en User.

Het gedrag van Z zit niet in Python maar in Server Scripts en Client Scripts (fixtures). Wie een veld hernoemt, moet
die scripts in dezelfde stap meenemen; vooral de synchronisatie met Bouw7 schrijft naar veel van deze velden.

## Wat nu al botst

Deze vier moeten eerst, want ze geven verlies van rechten of strijd bij elke migratie zodra de apps samen op één
omgeving staan.

| Wat | Waarom het botst | Besluit |
|---|---|---|
| `Project.custom_address` | Y en Z beschrijven hetzelfde veld met een ander label en een andere plek; wie het laatst migreert, wint | Eén definitie, in de gezamenlijke app. De losse adresvelden van Z op het project vervallen ten gunste van het adresrecord |
| Rechten op Offerte en Ontvangst in Z | Z zet eigen rechten op `Quotation` en `Purchase Receipt`; eigen rechten vervangen de standaardrechten, dus gebruikers van X en Y verliezen toegang | Uit de fixtures van Z; hoort bij de klantmodule |
| `Timesheet Detail.custom_is_billed` (Y) | Dubbelt het standaardveld `is_billed` | Y gaat het standaardveld gebruiken |
| 93 velden op `Company` (Z) | De tabel van het bedrijf zit vol: Frappe HR past er niet meer bij | Naar een eigen doctype met instellingen per bedrijf (zie hieronder) |

Daarnaast: Y zet `Company.disabled` zonder voorvoegsel. Dat kan botsen met een toekomstig standaardveld en krijgt
een eigen naam.

## Zelfde betekenis, andere naam

De linkerkolom is de naam die overblijft. "Standaard" betekent: het veld of doctype van ERPNext zelf.

### Nederlandse administratie (X is leidend)

X bouwt het betaalbestand, de UBL-factuur, het afletteren en de auditfile op deze namen. Twee bronnen naast elkaar
geven foute betaalbestanden, dus hier wijkt Z.

| Blijft | Vervangt in Z | Opmerking |
|---|---|---|
| `kvk_nummer` op Company, Customer en Supplier | `zapp_kvk` | X heeft het nu alleen op Company; komt er op klant en leverancier bij |
| `g_rekening` (Company, link naar bankrekening) | `zapp_g_rekening_tekst`, `zapp_n_rekening_tekst` | De teksten gaan naar de factuurtekst |
| `g_rekening_iban`, `g_percentage` (Supplier) | `zapp_g_rekening_pct` | Type wordt overal Percent; Z had Float |
| `g_bedrag` (Purchase Invoice, Sales Invoice) | geen | Bestaat alleen in X |
| Bankrekening van de relatie (standaard `Bank Account`) | `zapp_iban` op Company, Customer en Supplier | |
| `tax_id` (standaard) | geen | Z schrijft hier al naar |
| Btw-sjabloon met `btw_code` | `zapp_btw_verlegd`, `zapp_btw_tarieven` (btw per filiaal) | Verlegd is een sjabloon, geen vinkje |
| Rekeningen per relatie (standaard `Party Account`) | `zapp_admin_links`, `zapp_debiteurnummer` | Eén debiteurnummer blijft als veld |
| Betaalvoorwaarde (standaard `payment_terms`) | `zapp_vervaltijd`, `zapp_factuur_vervaltijd` | |
| Aanmaning (standaard `Dunning`) | `zapp_herinnering_1`, `zapp_herinnering_2`, `zapp_factuur_herinnering_*` | |

Open: of een percentage voor de G-rekening ook bij de klant hoort (Z heeft het daar, X niet).

### Project (Y is leidend)

Y is het werkscherm voor projecten.

| Blijft | Vervangt | Opmerking |
|---|---|---|
| `custom_project_manager` (link naar medewerker) | `zapp_projectleider` (link naar gebruiker) | Omzetten via de gebruiker van de medewerker. `zapp_uitvoerder` en `zapp_werkvoorbereider` blijven, onder één naamgeving |
| `custom_customer_reference` | `zapp_referentie` | Op de factuur is `po_no` de standaard |
| `custom_address` | `zapp_straatnaam`, `zapp_huisnummer`, `zapp_postcode`, `zapp_plaats`, `zapp_land`, `zapp_werkadres` | |
| `project_type` (standaard, met de projecttypes van X) | `zapp_categorie` | De velden van Z op het projecttype (code, percentage algemene kosten, minimale marge) gaan mee naar de stamgegevens van X |
| `percent_complete` (standaard) | `zapp_voortgang`, `custom_physical_progress` | `custom_financial_progress` blijft, voor projectbewaking |
| `expected_start_date`, `expected_end_date` (standaard) | geen | `zapp_opleverdatum` blijft: dat is de datum van oplevering, niet de planning |
| Vestiging (standaard `Branch`) | `zapp_filiaal` op Project, Employee, Quotation en Department | Was een keuzelijst zonder opties |
| Projectfase als stamgegeven van XYZ | `zapp_projectstatus`, `zapp_onderhoudsstatus` | Naast de standaardstatus (open, afgerond, geannuleerd) |
| Omschrijving van de offerte: `custom_description` | `custom_description_quotation`; `custom_title` wordt standaard `title` | |

`zapp_aanneemsom`, `zapp_meerwerk`, `zapp_stelpost`, `zapp_urenbegroting` en de bedragen voor algemene kosten en winst
en risico blijven tot de module Projectbewaking bestaat; daarna horen ze daar.

### Uren en tarieven

| Blijft | Vervangt | Opmerking |
|---|---|---|
| Uursoort (standaard `Activity Type`, met de uursoorten van X) | doctype `Zapp Uurtarief` | |
| Tarief per medewerker en uursoort (standaard `Activity Cost`) | de acht tariefvelden op Employee | |
| Prijsafspraak per klant (standaard prijslijst of prijsregel) | `zapp_uurtype_*`, `zapp_uurtarief`, `zapp_afgesproken_uurtarief` op Customer en Supplier | |
| Urenstaat (standaard `Timesheet`) | `Zapp Contacturenlog`, `Zapp Regie Gefactureerd` | Een externe is een medewerker met het kenmerk extern |
| Kilometers: `Y Km Registratie` | `Zapp Kilometerstand` | Samenvoegen |
| Werkweek en kantooruren | zeven velden op Employee en zeven op Company | Blijft, maar als tabel in de instellingen per bedrijf |

### Personeel (Frappe HR is leidend)

Besluit 27 november 2026: Frappe HR zit altijd standaard in de ERPNext van XYZ. Wat Z of Y zelf doen en Frappe HR,
ERPNext of de module personeel (`docs/personeel-cao-verlof.md`) al doet, vervalt.

| Blijft | Vervangt | Opmerking |
|---|---|---|
| Werkpatroon op het **Arbeidscontract** (uren per weekdag, week A en B) | `zapp_ww_ma` … `zapp_ww_zo` op Employee | Het patroon hoort bij een contract met een datum, niet los op de medewerker |
| Standaardwerkpatroon in **Bedrijfsinstellingen** | `zapp_kantooruren_*` op Company | Voorstel bij een nieuw contract |
| Dienst (standaard `Shift Type`) met begin- en eindtijd | `zapp_planning_starttijd`, `zapp_planning_eindtijd` op Company | Eén standaarddienst per bedrijf |
| Werkpatroon van het contract, via de API van de module personeel | `Shift Plan` en `Shift Plan Assignment` in Y | Bestaan niet in Frappe HR 16 (dat heet daar Shift Schedule); Y valt nu terug op 5 × de dienst. Y vraagt het patroon voortaan op |
| Verlofsaldo in uren, via de API van de module personeel | Y leest `Leave Allocation` in dagen | Y toont uren en "vervalt op" |
| Vestiging (standaard `Branch`) | `zapp_filiaal` op Employee en Department | Al genoemd bij Project |
| Contractsoort; extern = soort Inhuur, met de leverancier | `zapp_extern`, `zapp_bedrijfsnaam` | Een ingehuurde kracht is een medewerker met soort Inhuur en een link naar de leverancier |
| Adres van de medewerker (standaard `current_address` en het adresrecord) | `zapp_adres`, `zapp_postcode`, `zapp_plaats` | |
| `bsn` in de module personeel, alleen zichtbaar voor HR (rechtenniveau) | `zapp_bsn` | Privacy: niet in lijsten, niet in de export naar Bouw7 |
| Kostprijs per uur uit het contract (loon × opslag), tarief in `Activity Cost` | `zapp_kostprijs_uurtarief`, `custom_gross_hourly_rate`, `zapp_loonkosten_percentage`, de tariefvelden | De opslag voor loonkosten staat in Bedrijfsinstellingen |
| Rollen (standaard) | `zapp_type_gebruiker` | |
| Afwezigheid door **onwerkbaar weer**: verlofsoort "Onwerkbaar weer" (niet van het saldo) en de dag in het bouwdagboek | `Zapp Onwerkbare Dag` als los register | De uitvoerder legt de dag vast in het dagboek; het systeem maakt de afwezigheid voor de ploeg op dat project |
| Planitem blijft, maar **leest beschikbaarheid** uit werkpatroon, verlof en feestdagen | | Wie verlof heeft of op een feestdag vrij is, kleurt rood in de planning |
| Urenstaat (standaard `Timesheet`) | `Zapp Contacturenlog` | Een extern persoon wordt een medewerker met soort Inhuur |
| Mandagenregister uit de urenstaten, per week en project | `Zapp Dagboekweek` met aantallen per dag | Telt nu losse getallen; wordt een overzicht van wie er echt was |

Gevolg: het formulier Medewerker houdt alleen de standaardvelden van ERPNext en Frappe HR, plus het huidige contract,
de cao en `bsn`.

### Offerte, inkoop en onderaanneming

| Blijft | Vervangt | Opmerking |
|---|---|---|
| Eén calculatie | `Zapp Offerteberekening` en `Zapp Calculatie` | Twee bronnen voor hetzelfde: samen tot de module Calculatie |
| Eén termijnstaat | `Zapp Termijnstaat` en het sjabloon "Termijnstaat 30-40-25-5" van X | De percentages komen uit het betaalsjabloon; een termijn wordt een verkoopfactuur |
| Kans en opvolging (standaard `Opportunity` en taak) | `custom_acquisitie_status`, `custom_scoringskans`, `custom_vervolgactie_op`, `Zapp Offerte Status`, `Zapp Offerte Herinnering` | |
| Standaardteksten (standaard `Terms and Conditions`) | `Zapp Offerte Sjabloon`, `Zapp Inkoop Sjabloon` | |
| Goedkeuring als werkstroom (standaard `Workflow`) | `zapp_inkoop_status`, `zapp_huidige_flatteur`, `zapp_order_status`, `zapp_geaccordeerd`, `zapp_betaald` | |
| Contract met de onderaannemer | `OA Contract` én de gekopieerde contractvelden op de inkooporder | Eén van de twee kiezen; sluit aan op de module Onderaanneming en het G-bedrag van X |
| Mandagenregister | `Zapp Dagboekweek` | Is het in feite al; krijgt die naam |

### Wat een eigen begrip van XYZ blijft

Deze hebben geen goede standaard en blijven, met één naamgeving en met hun velden in het doctype zelf in plaats van
als los veld:

- **Bewakingscode** (met hoofdstuk en object): de kostencode van de projectbewaking.
- **Planitem** met medewerkers, contacten en materieel: de planning.
- **Projectboekingen** van materiaal, materieel en afval. Voorstel: één doctype met een soort, of de voorraadmutatie
  van ERPNext als voorraad aan staat.
- **Bouwdagboek** en onwerkbare dagen.
- **Toeslagen** per kostensoort (zeven stuks), op één plek en overal als percentage.
- **Klacht**: later in de module Kwaliteit en veiligheid.

## De instellingen per bedrijf

De 93 velden van Z op het bedrijf gaan naar één nieuw doctype, **Bedrijfsinstellingen** (één per bedrijf, in
`openaec_bouw`), met
tabbladen voor facturen, inkoop, offertes, projecten, planning en pdf's, en kindtabellen voor de werkweek en de
toeslagen. Het bedrijf zelf houdt alleen wat een bedrijf ís: `kvk_nummer`, `g_rekening` en de standaardvelden.

Dit is de stap die Frappe HR en Z samen op één omgeving mogelijk maakt, en dus een voorwaarde voor loon.

## Wat naar een klantmodule gaat

Niet algemeen, dus niet in de basis van XYZ:

- de koppeling met Bouw7 (vier doctypes, alle `custom_bouw7_*`-velden, de synchronisatie);
- de map per project in Dropbox en de opmerkingen per pagina van een bestand;
- de vinkjes en velden van de overgang uit een ander boekhoudpakket (`zapp_exact`, `zapp_basecone`, dagboeken);
- correcties voor een eigen rapportage, waterstanden, en de velden die maar één bedrijf gebruikt.

Een klantmodule is een module zoals elke andere: hij staat aan op de omgeving die hem nodig heeft.

## Volgorde

1. **Wat nu botst** (de vier hierboven). Klein, en nodig voordat de apps samen ergens draaien.
2. **Het bedrijf leegmaken** naar XYZ Bedrijfsinstellingen.
3. **Nederlandse administratie** op de namen van X.
4. **Project** op de namen van Y en de standaard, met de synchronisatie met Bouw7 in dezelfde stap.
5. **Stamgegevens samen**: uursoorten, tarieven, projecttypes, projectfasen, bewakingscodes.
6. **Per module kiezen**: termijnen, onderaanneming, calculatie, offerte, uren, kilometers, inkoopgoedkeuring.
7. **Klantmodule afsplitsen.**
8. **Opruimen**: velden in het doctype zelf, Server Scripts naar Python, werkruimtes naast het rustige menu leggen,
   één voorvoegsel.

Elke stap is een migratie met een patch die de gegevens overzet en het oude veld pas daarna verwijdert. Een omgeving
die Z al draait, verliest dus niets; ze heeft wel één keer de hernoeming nodig die in `README.md` staat.

## Wat nog niet is nagegaan

- Dit is gelezen uit de code, niet getest op een omgeving met gegevens.
- De schermen van Z (`/zapp` en verwanten) staan niet in deze repo; welke velden díe gebruiken, is hier niet te zien.
- Welke van de 357 velden in de praktijk gevuld zijn. Dat bepaalt wat zonder overzetten kan vervallen.
