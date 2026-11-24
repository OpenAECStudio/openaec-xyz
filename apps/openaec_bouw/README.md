# OpenAEC Bouw

De OpenAEC-inrichting van ERPNext voor bedrijven in de bouw: van aannemers en installatiebedrijven tot houthandels,
ingenieurs- en architectenbureaus. De inrichting bestaat uit **modules** met stamgegevens (btw, projecttypes, fasen,
uursoorten, groepen, sjablonen). Elke module kan per omgeving aan of uit.

Ontwerp en keuzes: `docs/standaard-bouwinrichting.md`. Routekaart per sector: `docs/openaec-bouw-routekaart.md`.
Versies: `CHANGELOG.md`.

## Wat een gebruiker ziet

- De tegel **Bouwbedrijf** op het startscherm: een werkruimte met tegels en een zijbalk in het Nederlands
  (`openaec_bouw/openaec_bouw/workspace` en `.../sidebar`). In ontwikkelmodus schrijft Frappe wijzigingen aan beide
  terug naar deze bestanden.
- Het rapport **Btw-aangifte** (`.../report/btw_aangifte`).
- Met de module **Rustig menu** aan: een navigatie zonder productie, voorraad, activa en dergelijke.

## Modules

Een module is een bestand in `openaec_bouw/modules/<id>.json`:

```json
{
  "id": "projecten",
  "titel": "Projecten",
  "omschrijving": "Projecttypes, uursoorten en functies",
  "standaard": true,
  "versie": 1,
  "records": [{"doctype": "Project Type", "naam": "Nieuwbouw", "velden": {"project_type": "Nieuwbouw"}}]
}
```

`standaard` bepaalt of de module aan staat bij het installeren van de app. Bijzondere records:

- `"ouder": "@wortel"`: de wortel van een boom (artikel-, klant- of leveranciersgroep), welke naam hij ook heeft.
- `"soort": "btw"`: per bedrijf een btw-rekening en een sjabloon voor verkoop en inkoop.
- `"soort": "projectsjabloon"`: een Project Template met de taken (fasen) als sjabloontaken.
- `"soort": "verberg"`: een moduleprofiel dat de genoemde modules uit de navigatie haalt; gebruikers zonder eigen
  keuze krijgen het, nieuwe gebruikers ook.

`"vereist": ["hrms"]` op de module: de module zet pas iets als die apps op de omgeving staan.

## Regels van de lader (`openaec_bouw.profiel`)

- **Alleen aanvullen.** Een record dat er al staat, blijft zoals het is.
- **Wat de klant weghaalt, blijft weg.** De lader onthoudt in `Bouwprofiel Regel` wat hij zette en zet het niet opnieuw.
- **Uitzetten** haalt weg wat de module zette, voor zover de klant het niet heeft gewijzigd en er niets aan hangt.
- Geen transacties: geen boekingen, geen facturen.

Na elke migratie (uitrol) past de lader de modules die aan staan opnieuw toe; zo komt een nieuwe versie van een module
bij elke omgeving.

## Gebruik

```bash
bench --site <site> install-app openaec_bouw                       # zet de standaardmodules
bench --site <site> execute openaec_bouw.profiel.stand             # welke modules, aan of uit
bench --site <site> execute openaec_bouw.profiel.zet_module --kwargs "{'module': 'ontwerp', 'aan': 1}"
```
