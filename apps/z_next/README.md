# Z-Next

Z-Next van het OpenAEC-ecosysteem: een Frappe-app (`z_next`, module **Z Next**) met
projectadministratie, planning, offertes, termijnstaten, terugkerende taken en de
bronkoppeling met Bouw7 voor ERPNext 16.

Deze app bundelt het maatwerk dat eerder via de UI als losse configuratie (module
"Custom") op de bestaande site was ingericht.

## Inhoud

| Onderdeel | Aantal | Waar |
|---|---|---|
| DocTypes (`Zapp …`, `Z-App …`, `OA Contract`, `Z-Next …`) | 46 | `z_next/z_next/doctype/` |
| Custom Fields (`zapp_*`, `custom_bouw7_*`, offerte- en voortgangsvelden) | 370 | `z_next/fixtures/custom_field.json` |
| Property Setters | 2 | `z_next/fixtures/property_setter.json` |
| Server Scripts | 8 | `z_next/fixtures/server_script.json` |
| Client Scripts | 7 | `z_next/fixtures/client_script.json` |
| Rollen (Zapp Offertes / Productie / Superuser / Werkplaats) | 4 | `z_next/fixtures/role.json` |
| Custom DocPerms van die rollen | 5 | `z_next/fixtures/custom_docperm.json` |
| Workspaces (Z-Next, Zapp Dashboard, Mijn Werkplek, Werkplaats) | 4 | `z_next/fixtures/workspace.json` |
| Number Cards en Dashboard Charts (terugkerende taken) | 4 + 2 | `z_next/fixtures/` |

Niet in deze app:

- De `Y …`-doctypes, die horen bij Y-Next.
- Records van de koppeling (Koppeling, Controle, Log, Overname), terugkerende taken en
  andere data. Dat is data, geen configuratie.
- Siteconfiguratie die niet specifiek Z-Next is: nummerreeksen, HR- en
  Employee Self Service-rechten en webpagina's.
- Velden en instellingen van andere geïnstalleerde apps (hrms, erpnext_netherlands,
  ERPNext Service).

### Server Scripts

| Script | Type | Functie |
|---|---|---|
| Zapp Bouw7 synchronisatie | API `zapp_bouw7_sync` | Synchroniseert relaties, medewerkers, projecten en facturen met de bron |
| Zapp Bouw7 ieder uur | Scheduler (Hourly Long) | Draait de synchronisatie elk uur |
| Zapp Bouw7 beheerstatus beschermen | DocType Event (Koppeling, Before Save) | Beschermt de syncstatus en valideert applicatie-ID en batchgrootte |
| Zapp projectbestanden | API `zapp_project_files` | Projectbestanden (Dropbox-projectmappen) |
| Zapp projectmarges | API `zapp_project_margins` | Backend van de pagina Projectmarges |
| Zapp waterstanden | API `zapp_waterstanden` | Waterstanden uit de open data van Rijkswaterstaat |
| Offertebedrag uit calculatie | DocType Event (File, After Insert) | Neemt het offertebedrag over uit een geüploade calculatie |
| Workspace Redirect Helper | API `workspace_redirect_js` | JavaScript dat workspace-snelkoppelingen doorverwijst naar lijsten |

De scripts zijn als fixtures opgenomen, zodat het gedrag 1-op-1 gelijk blijft aan de bronsite.
Server Scripts moeten op de site zijn ingeschakeld:

```bash
bench --site <site> set-config server_script_enabled 1
```

De API-sleutel van de koppeling staat niet in de repo. Die wordt na installatie
in het Koppeling-record ingevuld (veld `api_key`, opgeslagen als wachtwoord).

"Zapp projectbestanden" gebruikt een Connected App (Dropbox OAuth). De naam van dat
record en de gebruiker zijn nu nog vast in het script gezet. Op een andere site moeten
die worden aangepast of eerst geconfigureerd worden.

## Installatie op een nieuwe site

```bash
bench get-app https://github.com/OpenAEC-Foundation/Z-Next.git
bench --site <site> install-app z_next
bench --site <site> set-config server_script_enabled 1
```

**Let op rechten:** de fixture `custom_docperm.json` bevat de *volledige* set custom
rechten voor **Quotation** (alleen rol Zapp Offertes) en **Purchase Receipt**. In
Frappe vervangen custom rechten de standaardrechten van een doctype. Wil je dat niet
op een nieuwe site, zet die doctypes na installatie terug met
*Role Permissions Manager → Reset to default*.

## Migratiepad voor een bestaande site

Op de bestaande site bestaan alle doctypes al, als `custom=1` in module "Custom".
Ook de custom fields, scripts en de andere fixtures bestaan daar al onder dezelfde
naam. De installatie neemt ze over zonder dataverlies:

1. **Backup**: `bench --site <site> backup --with-files`.
2. **Test eerst op een kopie** van de productiesite (restore van de backup op een
   staging-bench) en voer daar stap 3 en 4 uit.
3. `bench get-app` en `bench --site <site> install-app z_next`.
   - `before_install` (`z_next/install.py`) zet de bestaande doctypes in `tabDocType`
     om naar `custom=0`, module "Z Next". Tabellen en records worden niet aangeraakt.
   - Daarna leest de model-sync de doctype-JSON uit de app in. De JSON-bestanden
     hebben een nieuwere `modified` dan de site, zodat de sync ze altijd verwerkt.
   - De fixtures overschrijven de bestaande records met dezelfde naam. Daardoor
     krijgen Custom Fields, Property Setters, scripts, Number Cards en Charts module
     "Z Next".
4. **Controleer**:
   - het aantal records per doctype is gelijk aan vóór de installatie;
   - `select name, module, custom from tabDocType where module = 'Z Next'`
     geeft 46 rijen met `custom = 0`;
   - de uurlijkse synchronisatie draait (Zapp Bouw7 Log) en de Projectmarges-pagina
     laadt.
5. Pas na een geslaagde test op de kopie: dezelfde stappen op productie.

**Terugdraaien:** `bench --site <site> uninstall-app z_next` verwijdert de doctypes
*inclusief data*. Terugdraaien gaat daarom altijd via de backup uit stap 1, niet via
uninstall.

## Ontwikkelen

Wijzigingen aan doctypes doe je op een development-site (`developer_mode: 1`). Frappe
schrijft de JSON dan terug naar `z_next/z_next/doctype/`. Fixtures exporteer je met:

```bash
bench --site <site> export-fixtures --app z_next
```

`tools/export_site.py` maakt een read-only export van al het maatwerk op een site via
de REST-API (token via `ERPNEXT_API_TOKEN`, URL via `ERPNEXT_URL`).

## Openstaand

- **Betaalschema bij inkoopfacturen**: de synchronisatie geeft aangemaakte en herbouwde
  facturen al `ignore_default_payment_terms_template: 1` en een leeg
  `payment_terms_template` (in deze app aanwezig). Nog niet doorgevoerd: bij een bestaande
  factuur waarvan de vervaldatum in de bron is gewijzigd, zet het oude betaalschema de
  vervaldatum terug. Daardoor faalt de datumcontrole ("ERPNext-datums wijken af van de
  bron") voor een aantal inkoopfacturen. Voorgestelde fix in `invoice_sync`, direct boven
  `result = save_doc(doc, row, values, bool(target))`: als het bestaande
  `payment_schedule` niet uit precies één regel met de bron-vervaldatum bestaat, het
  schema leegmaken en opnieuw laten opbouwen (`payment_schedule: []`,
  `ignore_default_payment_terms_template: 1`, `payment_terms_template: ""`).
- **Server Scripts naar Python**: de scripts ombouwen naar whitelisted methods,
  `scheduler_events` en `doc_events` in deze app. Let op naamconflicten zolang de
  Server Script-API's (`zapp_bouw7_sync` e.d.) nog actief zijn.
- **Projectmarges**: subtab "grootste onderaannemers per jaar" en een overzicht
  "offertes per maand". Onderaannemers zijn in de data lastig te herkennen: alle inkoop
  staat op Cost of Goods Sold en slechts een deel van de leveranciers zit in de groep
  Subcontractor.
- **Mobiele versie** van Z-Next: projectscherm met actietegels (Uren, Materieel, Inkoop,
  Bestanden, Standopname, KVGM), urenoverzicht per medewerker per week met accorderen,
  en tabbar Uren / Planning / Dashboard / Projecten / Meer.
