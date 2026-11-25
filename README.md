# OpenAEC XYZ

Eén laag op ERPNext voor de hele bouwsector: van eenmanszaak en installatiebedrijf tot grote aannemer.

Hier komen drie apps samen die tot nu toe los stonden:

| Map | Wat | Kwam uit |
|---|---|---|
| `apps/openaec_bouw` | **X**: de inrichting en de Nederlandse administratie. Rekeningschema met RGS, btw-aangifte, ICP, auditfile, bank en SEPA, G-rekening, UBL, onderhanden werk; modules die per omgeving aan en uit kunnen | **hier** (tot versie 0.5.0 in `OpenAECStudio/openaec-bench`) |
| `apps/y_next` | **Y**: waar medewerkers werken (projecten, uren, agenda) | `OpenAEC-Foundation/y_next`, branch `version-16` |
| `apps/z_next` | **Z**: aannemersmaatwerk (projectadministratie, planning, offertes, termijnstaten, koppeling met Bouw7) | `OpenAEC-Foundation/Z-Next`, branch `main` |

De geschiedenis van X en Y is meegekomen (`git log -- apps/<map>`). Z is als één stand overgenomen en daarbij
algemeen gemaakt: de doctypes heten `Zapp …`, en de koppeling met Bouw7 leest organisatie, filialen en afdelingen uit
de instellingen. Een omgeving die Z-Next al draaide met de oude namen, heeft een eenmalige hernoeming nodig voordat
ze op deze versie kan.

## Stand

**X wordt hier ontwikkeld.** Sinds versie 0.5.0 is deze repo de bron van `apps/openaec_bouw`; de SuperCloud bouwt de
app hieruit. Y en Z staan hier **naast** X en zijn nog niet samengevoegd; de SuperCloud bouwt die twee nog uit hun
oude repo's. De stappen naar één app staan in `docs/routekaart.md` en `docs/voorstel-xyz.md`:

1. Eén ingang: de tegel Bouwbedrijf wordt de tegel XYZ.
2. Eén set stamgegevens.
3. De code samen in één app; doctypes houden hun naam, dus klantdata hoeft niet om.
4. De eigen velden van Z-Next op standaard-doctypes opruimen (`docs/velden-harmonisatie.md`).

## Van een wijziging naar de SuperCloud (X)

1. Wijzig `apps/openaec_bouw` hier, met een nieuwe versie in `apps/openaec_bouw/CHANGELOG.md` en
   `apps/openaec_bouw/openaec_bouw/__init__.py`.
2. Merge naar `main` en zet de tag **`openaec-bouw-v<versie>`** op die commit.
3. In `OpenAECStudio/openaec-bench`: zet die tag in `externe-apps.txt` (de regel `openaec_bouw`), merge, en rol uit met
   een tag `v…` zoals altijd. Het image van de bench neemt de app van precies die tag mee.

De versie ligt dus in de bench vast en niet in deze repo: een nieuwe versie is een commit in de bench, en dat geeft
een nieuw image. Een wijziging hier komt pas bij klanten als de bench naar de nieuwe tag wijst.

**Lokaal ontwikkelen** op de bench: kloon deze repo als `extern/openaec-xyz` in openaec-bench en koppel de app met een
symlink `extern/openaec_bouw -> openaec-xyz/apps/openaec_bouw`; `scripts/init-bench.sh` doet de rest. De tests draaien
met `bench --site <site> run-tests --app openaec_bouw`, op een schone site met ERPNext (en Frappe HR voor de module
loon): op een site waar het demonstratiebedrijf staat, falen twee tests van het profiel.

## Releases

Deze repo geeft veel releases uit, elk met een eigen tag:

- **Y-Next lokaal** (`installer/y-next`, tags `y-next-installer-v*`): Y-Next met ERPNext op de eigen pc, in Docker,
  met één opdracht of één dubbelklik. Zie `installer/y-next/README.md`;
- de Frappe-apps zelf (`y_next`, `z_next`, en straks de ene app XYZ);
- **implementaties**: een inrichting van een ERPNext-omgeving voor een sector (aannemer, installatie, hout en handel,
  bureau). Een implementatie is een lijst modules die aan staan, zie `docs/routekaart.md`.

Versies van de inrichting: `apps/openaec_bouw/CHANGELOG.md`, met tags `openaec-bouw-v*`.

## Documenten

| Stuk | Waarover |
|---|---|
| `docs/voorstel-xyz.md` | XYZ als één app: assistent, post, bellen, intranet, installatietechniek, de lokale vorm |
| `docs/routekaart.md` | De versies van OpenAEC Bouw en de sectoren |
| `docs/standaard-bouwinrichting.md` | Het ontwerp van de inrichting met modules |
| `docs/openaec-bouw-fundament.md` | Wat in ERPNext goed moet staan vóór de eerste boeking |
| `docs/demonstratiebedrijf.md` | De verzonnen bouwgroep Noorderkade voor de demo-omgeving |
| `docs/houtherkomst-en-werkstromen.md` | De Europese houtregels en de werkstromen in alle bedrijven |
| `docs/velden-harmonisatie.md` | De eigen velden van X, Y en Z naast elkaar |
| `docs/y-boekhouding-bevindingen.md` | Wat er in de boekhouding van Y niet klopt |
