# Versies van OpenAEC Bouw

Elke stap van de inrichting is een versie van deze app. Een versie komt eerst op de modelomgeving
(`model.cloud.open-aec.eu`), daarna met de gewone uitrol bij elke omgeving die de app heeft. De routekaart staat in
`docs/openaec-bouw-routekaart.md`.

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
