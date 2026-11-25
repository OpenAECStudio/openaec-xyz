# Het demonstratiebedrijf

Stand 25 november 2026. Eén verzonnen bouwgroep in één ERPNext-omgeving, zo compleet dat je er alles op kunt laten
zien: de administratie, de werkschermen, het intranet, de post en de rapportages. Bedoeld voor de demo-omgeving
`klant0` van de SuperCloud. Alle namen, nummers en bedragen zijn verzonnen.

Het fundament eronder (waarom welke dingen vooraf moeten staan) staat in `docs/openaec-bouw-fundament.md`.

## De groep

| Bedrijf | Soort | Mensen | Projecten | Werkt met | Verhaal |
|---|---|---|---|---|---|
| Noorderkade Holding BV | holding | 6 | – | ERPNext | Belast directie, financiën, personeelszaken en ICT door |
| Noorderkade Bouw BV | aannemer | 34 | 20 | Z-app | Verlies in het eerste jaar door twee werken die uitliepen; G-rekening; onderhanden werk |
| Noorderkade Installatietechniek BV | installateur | 26 | 18 | eigen app op ERPNext | Vestigingen Zwolle en Deventer; service naast projecten |
| Noorderkade Advies BV | adviesbureau | 14 | 18 | Y-app | Verlies in het laatste jaar: twee grote opdrachten vielen weg |
| Noorderkade Sonderingen BV | sondeerbedrijf | 9 | 16 | ERPNext | Verlies in het middelste jaar: de sondeerwagen stond stil |
| Noorderkade Hout BV | houthandel | 12 | 15 | ERPNext | Voorraad en grijpvoorraad; tropisch hardhout van buiten de EU |
| Noorderkade Materieel BV | materieelverhuur | 8 | 15 | ERPNext | Veel vaste activa en afschrijving |

Boven de holding komen nog de **aandeelhouders**: een paar persoonlijke holdings van de directeuren, die een
managementvergoeding factureren en dividend ontvangen.

## Wat er staat

Gemaakt door `openaec_bouw.demo.maak`, alles als **concept** (er wordt niets geboekt tot dat besloten is):

- de groep zoals ERPNext hem bedoelt: holding als groepsbedrijf, dochters met de holding als moeder, overal hetzelfde
  Nederlandse rekeningschema met RGS-codes;
- per bedrijf een bankrekening (en bij de aannemer en de installateur een G-rekening), afdelingen, medewerkers met
  functie, en bij de installateur twee vestigingen met een eigen kostenplaats;
- de bedrijven als interne klant en leverancier van elkaar; de holding belast per maand door, met een factuur aan
  beide kanten;
- een beginbalans per bedrijf;
- projecten met verkoopfacturen (termijnen of maanddeclaraties), meerwerk, en inkoopfacturen met een pdf als bijlage:
  binnenlands, btw verlegd, binnen de EU en buiten de EU;
- maandelijkse lonen en vaste kosten;
- banktransacties van alle betalingen, ook op de G-rekening;
- afboekingen van klanten die niet betalen;
- per bedrijf per kwartaal een **Btw-aangifte** (het nieuwe doctype) met journaalpost en betaling.

Samen ongeveer 5.500 documenten over drie jaar; het maken duurt tien minuten.

## Wat er nog bij komt

In deze volgorde. De eerste drie zijn fundament: ze moeten er zijn vóór er geboekt wordt.

| Nr | Wat | Toelichting |
|---|---|---|
| 1 | **Voorraad bij de houthandel** | Gebouwd: magazijnen, grijpvoorraad, voorraadartikelen met keurmerk, partijen met herkomst, beginvoorraad, inkoop met ontvangst, verkoop met aflevering, zaagwerk |
| 2 | **Vaste activa** | Gebouwd: register per bedrijf met afschrijving. Nog niet: keuringen met vervaldatum |
| 3 | **Onderhanden werk** | Gebouwd: stand per kwartaal met journaalpost. Nog niet: aansluiting op de termijnstaat van de Z-app |
| 3a | **Vaste gezichten en portretten** | Gebouwd: per bedrijf een handvol mensen met naam, functie en karakter, en per medewerker een opdracht voor een beeldgenerator (`demo.portretten`). Nog niet: de foto's zelf en de accounts om in te loggen |
| 4 | **Rollen per soort gebruiker** | Directeur, financieel medewerker, projectleider, uitvoerder, monteur, magazijn: elk met eigen rechten en een eigen startscherm, en een gebruiker hoort bij één bedrijf tenzij hij voor de groep werkt |
| 5 | **Huisstijl** | Een logo en kleuren per bedrijf en voor de groep, in de SuperCloud, op elk document: offerte, factuur, brief, en in de e-mailondertekening van elke medewerker |
| 6 | **Intranet** | Per bedrijf en voor de groep, met verzonnen nieuws, persberichten en mededelingen; toegang volgt het bedrijf van de medewerker |
| 7 | **Aandeelhouders** | Persoonlijke holdings met managementvergoeding en dividend |
| 8 | **Post** | Honderden verzonnen e-mails tussen medewerkers, klanten en leveranciers, gekoppeld aan projecten en facturen en in categorieën; met fouten en misverstanden erin |
| 9 | **Het circus** | Een klant die niet betaalt met aanmaningen en zijn reactie, een geschil dat bij de rechter komt, een factuur die dubbel is gestuurd, een creditnota, een leverancier die te laat levert |
| 10 | **Rapporteren aan de groep** | Elke dochter levert per kwartaal haar cijfers aan bij de holding; de directeur stuurt ze, de financieel directeur van de holding stelt er een vraag over |
| 11 | **Jaarrekeningen** | Per bedrijf en geconsolideerd, per jaar, met de jaarafsluiting |
| 12 | **Grafieken en inzichten** | Per bedrijf en voor de groep: omzet, resultaat, wat openstaat, liquiditeit, onderhanden werk |
| 13 | **Projecten in Docs** | Elk project een map met contract, tekeningen, facturen en notulen |
| 14 | **Uren** | Urenstaten per medewerker per project, als bron voor facturen en projectbewaking |
| 15 | **De apps per bedrijf** | Y bij het adviesbureau, Z bij de aannemer, een eigen app bij de installateur; alle drie op dezelfde ERPNext |
| 16 | **Website, domein en e-mail per bedrijf** | Elk bedrijf een eigen website in de SuperCloud, met de bron op de Git-server van de omgeving, een eigen domeinnaam en e-mailadressen voor de medewerkers. Zolang er geen echte domeinen geregistreerd zijn: een subdomein van de demo-omgeving per bedrijf, en e-mailadressen op dat domein |

## Boeken

Zolang alles concept is, zijn het grootboek, de balans en de rapporten van ERPNext leeg. Het boeken is een eigen stap,
na het fundament: in volgorde van datum, met na elk jaar een afsluiting, en daarna het afletteren van de
banktransacties tegen de facturen. Pas dan zijn de jaarrekeningen, de grafieken en de rapportage aan de groep te maken.

## Draaien

    bench --site <site> execute openaec_bouw.demo.maak
    bench --site <site> execute openaec_bouw.demo.stand

De eerste maakt wat er nog niet is; de tweede geeft per bedrijf en per jaar de omzet, de inkoop, de lonen en het
resultaat uit de concepten. Een startgetal (`zaad`) bepaalt de gegevens; hetzelfde getal geeft hetzelfde bedrijf.
