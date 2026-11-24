# OpenAEC XYZ

Eén laag op ERPNext voor de hele bouwsector: van eenmanszaak en installatiebedrijf tot grote aannemer.

Hier komen drie apps samen die tot nu toe los stonden:

| Map | Wat | Kwam uit |
|---|---|---|
| `apps/openaec_bouw` | **X**: de inrichting. Stamgegevens, startscherm Bouwbedrijf, rustig menu, btw-aangifte, begin van loon; modules die per omgeving aan en uit kunnen | `OpenAECStudio/openaec-bench`, map `apps/openaec_bouw` |
| `apps/y_next` | **Y**: waar medewerkers werken (projecten, uren, agenda) | `OpenAEC-Foundation/y_next`, branch `version-16` |
| `apps/z_next` | **Z**: aannemersmaatwerk (projectadministratie, planning, offertes, termijnstaten, koppeling met Bouw7) | `OpenAEC-Foundation/Z-Next`, branch `main` |

De geschiedenis van X en Y is meegekomen (`git log -- apps/<map>`). Z is als één stand overgenomen en daarbij
algemeen gemaakt: de doctypes heten `Zapp …`, en de koppeling met Bouw7 leest organisatie, filialen en afdelingen uit
de instellingen. Een omgeving die Z-Next al draaide met de oude namen, heeft een eenmalige hernoeming nodig voordat
ze op deze versie kan.

## Stand

De drie apps staan hier **naast elkaar**, ongewijzigd. Ze zijn nog niet samengevoegd tot één app, en de SuperCloud
bouwt nog uit de oude plekken. De stappen staan in `docs/routekaart.md`:

1. Eén ingang: de tegel Bouwbedrijf wordt de tegel XYZ.
2. Eén set stamgegevens.
3. De code samen in één app; doctypes houden hun naam, dus klantdata hoeft niet om.
4. De eigen velden van Z-Next op standaard-doctypes opruimen.

Tot de bouw van de SuperCloud naar deze repo wijst, blijven de oude repo's de bron: een wijziging daar moet hier
opnieuw binnengehaald worden (`git subtree pull`).

## Releases

Deze repo geeft veel releases uit, elk met een eigen tag:

- de Frappe-apps zelf (`y_next`, `z_next`, en straks de ene app XYZ);
- **implementaties**: een inrichting van een ERPNext-omgeving voor een sector (aannemer, installatie, hout en handel,
  bureau). Een implementatie is een lijst modules die aan staan, zie `docs/routekaart.md`.

Versies van de inrichting: `apps/openaec_bouw/CHANGELOG.md`.
