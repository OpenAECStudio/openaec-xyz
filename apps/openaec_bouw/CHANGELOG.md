# Versies van OpenAEC Bouw

Elke stap van de inrichting is een versie van deze app. Een versie komt eerst op de modelomgeving
(`model.cloud.open-aec.eu`), daarna met de gewone uitrol bij elke omgeving die de app heeft. De routekaart staat in
`docs/routekaart.md`.

## 0.5.0 (25 november 2026): fundament voor een groep, en het demonstratiebedrijf

- **Btw-aangifte als document:** nieuw doctype, één per bedrijf per tijdvak. Als concept ververst het de rubrieken
  (desgewenst met conceptfacturen erbij); indienen zet de cijfers vast en kan pas als er in het tijdvak geen concepten
  meer staan. **Journaalpost maken** boekt de btw-rekeningen leeg naar Btw-afdracht.
- **Groep met dochters:** een bedrijf dat onder een moeder met het Nederlandse schema wordt aangemaakt, krijgt van
  ERPNext het schema van de moeder; `neem_schema_over` zet de RGS-codes, de standaardrekeningen en de btw-sjablonen
  erbij.
- **Herstel:** op een omgeving met Frappe HR liep de eerstvolgende opslag vast na "Nederlands rekeningschema zetten",
  omdat een declaratiesoort nog naar een rekening van het oude schema wees.
- **Onderhanden werk als document:** nieuw doctype, één stand per bedrijf per peildatum met een regel per lopend
  project: kosten, gefactureerde termijnen, voortgang, verwacht en genomen resultaat. Het resultaat naar voortgang of
  bij oplevering; een verwacht verlies altijd meteen. **Journaalpost maken** boekt de mutatie naar de balans. Nieuw
  veld **Aanneemsom** op het project en de rekening 8090 Mutatie onderhanden projecten.
- **Hout:** keurmerk op het artikel, en land en gebied van herkomst op de partij.
- **Demonstratiebedrijf** (`openaec_bouw.demo.maak`): een verzonnen bouwgroep met zeven bedrijven en drie jaar
  administratie, alles als concept: voorraad met partijen en grijpvoorraad bij de houthandel, een register van vaste
  activa, onderhanden werk per kwartaal, en vaste gezichten met een lijn van afdelingshoofd tot directeur. Zie
  `docs/demonstratiebedrijf.md`, `docs/openaec-bouw-fundament.md` en `docs/houtherkomst-en-werkstromen.md`.
- De status van een nog niet ingediend document heet in het Nederlands weer Concept (Frappe maakte er Droogte van).

Nog niet: het boeken van het demonstratiebedrijf, de zorgvuldigheidsverklaring voor hout, en de werkstromen.

## 0.4.0 (25 november 2026): Nederlandse administratie, tweede deel

- **Bankafschrift inlezen (CAMT.053):** knop op de lijst met banktransacties. Elke regel wordt een banktransactie op
  de bankrekening met hetzelfde IBAN; een regel die er al staat, komt er niet nog eens bij.
- **Afletteren waar het zeker is:** staat het factuurnummer in de omschrijving en klopt het bedrag met wat openstaat,
  dan wordt de betaling geboekt en gekoppeld. De rest blijft open voor het afstemscherm van ERPNext, waar ook de eigen
  afletterregels gelden. Met **Open regels afletteren** probeer je het later opnieuw.
- **SEPA-betaalbestand (pain.001.001.09):** vink inkoopfacturen aan en kies **Acties → SEPA-betaalbestand**. Het
  kenmerk van elke overboeking is het factuurnummer, zodat het afschrift de betaling daarna vanzelf aflettert. Een
  factuur komt niet ongemerkt twee keer in een bestand.
- **G-rekening:** bij de leverancier het IBAN van de G-rekening en het afgesproken percentage; de inkoopfactuur krijgt
  het G-bedrag en het betaalbestand splitst de betaling. Bij het bedrijf de eigen G-rekening; een verkoopfactuur met
  een G-bedrag wordt in twee delen afgeletterd (bank en G-rekening).
- **UBL (NLCIUS) uit en in:** knop **Nederland → UBL downloaden** op een geboekte verkoopfactuur (ook creditnota's),
  en **UBL-factuur inlezen** op de lijst met inkoopfacturen: dat maakt een concept met het bestand als bijlage.
- Nieuw veld **KvK-nummer** op het bedrijf (staat op de UBL-factuur).

Nog niet: versturen en ontvangen over Peppol; meer dan één btw-tarief op één UBL-factuur; incasso (pain.008). Het
betaalbestand en de UBL zijn niet bij een bank of tegen de officiële validatie van NLCIUS aangeboden.

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
