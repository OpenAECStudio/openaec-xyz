# Versies van OpenAEC Bouw

Elke stap van de inrichting is een versie van deze app. Een versie komt eerst op de modelomgeving
(`model.cloud.open-aec.eu`), daarna met de gewone uitrol bij elke omgeving die de app heeft. De routekaart staat in
`docs/openaec-bouw-routekaart.md`.

## 0.3.0 (24 november 2026): Nederlandse administratie, eerste deel

- **Eigen rekeningschema:** `Nederland - OpenAEC Bouw (RGS)`, een compact Nederlands schema voor een bouwbedrijf
  (onderhanden projecten, G-rekening, onderaanneming, btw-rekeningen), met de standaardrekeningen van het bedrijf erbij.
  Een nieuwe Nederlandse omgeving krijgt het vanzelf; op een bestaand bedrijf zonder boekingen zet je het met de knop
  **Nederland → Nederlands rekeningschema zetten** op het bedrijf. Een bedrijf waar al op geboekt is, houdt zijn schema.
- **RGS-code per rekening** (veld op de grootboekrekening). Rapporten en de auditfile lezen die code, niet de naam.
  Bestaande rekeningen krijgen een voorstel op rekeningtype; wat al ingevuld is, blijft staan.
- **Btw-code per btw-sjabloon**, die de rubriek van de aangifte bepaalt. Nieuw: btw binnen en buiten de EU.
- **Btw-aangifte** nu ook met rubriek 3a, 3b, 4a en 4b, en een rapport **Opgaaf ICP** per btw-nummer.
- **Auditfile (XAF 3.2)** van een boekjaar: knop **Nederland → Auditfile (XAF)** op het bedrijf.
- Herstel: na een mislukte poging onthield de cache dat een module aan stond terwijl de database dat niet wist.

Nog niet: de RGS-codes en het schema zijn niet door een boekhouder nagelopen, en de auditfile is niet tegen het
officiële XSD gevalideerd of in een accountantspakket ingelezen.

## 0.2.3 (24 november 2026)

- **Herstel:** het moduleprofiel van het rustige menu wordt rechtstreeks aangemaakt. Via Frappe bleef na een mislukte
  poging een slot op het profiel staan, waar elke volgende migratie op vastliep.

## 0.2.2 (24 november 2026)

- **Herstel:** het rustige menu liep op de modelomgeving nog steeds vast, nu op het DocShare van de gebruiker. De
  lader schrijft het moduleprofiel nu rechtstreeks bij de gebruiker en slaat de gebruiker zelf niet meer op.

## 0.2.1 (23 november 2026)

- **Herstel:** het rustige menu liep op de modelomgeving vast als een gebruiker tijdens de uitrol door een andere
  aanvraag was gewijzigd; daardoor werd het hele profiel van 0.2.0 niet toegepast. De lader leest de gebruiker nu met
  een slot.
- Routekaart: Y-Next en Z-Next gaan samen op in XYZ.

## 0.2.0 (november 2026)

- **Startscherm Bouwbedrijf:** een eigen tegel op het startscherm, met een werkruimte (tegels voor projecten, offertes,
  opdrachten, facturen, uren, taken, klanten en leveranciers) en een zijbalk in het Nederlands.
- **Module Rustig menu:** haalt productie, voorraad, activa, kwaliteit, support, website en de bouwstenen voor
  ontwikkelaars uit de navigatie. Per gebruiker terug te zetten; de gegevens en rechten blijven.
- **Rapport Btw-aangifte:** de rubrieken 1a, 1b, 1c, 1e, 2a en 5a tot en met 5c over een tijdvak. Buitenland (rubriek 3
  en 4) nog niet.
- **Btw 21%** erbij; met het Nederlandse rekeningschema boeken de btw-sjablonen op de rekeningen van dat schema
  (af te dragen en te vorderen, hoog, laag, overig en verlegd).
- **Module Personeel en loon (begin):** Nederlandse looncomponenten, verlofsoorten, dienstverbanden en
  declaratiesoorten voor Frappe HR. Nog geen loonberekening of loonaangifte.
- **Lader:** een module kan apps vereisen (`vereist`) en wacht dan tot die er zijn; een nieuwe standaardmodule gaat
  ook op bestaande omgevingen aan, maar een module die de klant uitzette blijft uit.

## 0.1.0 (november 2026)

- De lader en de modules Basis, Projecten, Ontwerp en engineering, en Uitvoering.
