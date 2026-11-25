# De boekhouding van Y: bevindingen

Stand 25 november 2026, bij Y 0.40.0. **Dit is gelezen uit de code, nog niet getoetst met gegevens.** De volgende
stap is één voorbeeldboekhouding invoeren en elk punt hieronder bevestigen of schrappen; de uitkomst komt in dit stuk.

Y laat het rekenen aan ERPNext: totalen, btw en grootboek komen van de server, en bijna alles wordt als concept
aangemaakt. De problemen zitten op de plekken waar Y het zelf doet: de rapporten, de btw-aangifte en een paar
knoppen die meer doen dan ze zeggen.

De schermen staan in deze repo alleen als gebouwd resultaat (`apps/y_next/y_next/public/app`). Herstel kan pas als de
bron erbij staat.

## Ernstig: kan tot een foute aangifte of dubbele factuur leiden

| Nr | Waar | Wat | Gevolg |
|---|---|---|---|
| 1 | Btw-aangifte | Rekent in de browser. Als de btw-regels van een factuur niet te lezen zijn, telt het scherm alles als 21% | Een aangifte die niet klopt zonder dat iemand het ziet |
| 2 | Btw-aangifte | Rubrieken onvolledig: verlegd, binnen en buiten de EU ontbreken; een afwijkend tarief komt bij 0%; voorbelasting telt alleen inkoopfacturen | Idem |
| 3 | Uren naar factuur | De uren worden als gefactureerd gemerkt terwijl de factuur nog concept is, en een fout daarbij wordt genegeerd; het scherm zelf kijkt naar een ander veld | Dezelfde uren kunnen in een tweede factuur komen |
| 4 | Factuur mailen | Een conceptfactuur wordt bij het versturen eerst definitief geboekt, zonder dat de knop dat zegt | Een factuur die niet meer te wijzigen is |
| 5 | Creditnota | Wordt aangemaakt zonder verwijzing naar de oorspronkelijke factuur en met positieve aantallen | Fout bij boeken, of een creditnota die als factuur telt |
| 6 | Opdrachtbalk | Maakt een betaling aan zonder rekeningen en zonder koppeling aan een factuur | Een betaling die niets aflettert |
| 7 | Declaraties en kilometers | Een medewerker kan zijn eigen declaratie op goedgekeurd zetten; het bedrag wordt niet gecontroleerd | Geen scheiding tussen indienen en goedkeuren |

## Onjuist of onvolledig: geeft verkeerde cijfers in een overzicht

| Nr | Waar | Wat |
|---|---|---|
| 8 | Jaarrekening | De balans klopt alleen als eerdere jaren zijn afgesloten; het resultaat van eerdere jaren komt anders niet in het eigen vermogen |
| 9 | Grootboek en jaarrekening | Halen alle boekingen op en tellen in de browser, tot ongeveer 50.000 regels; daarboven stopt het zonder melding |
| 10 | Winstgevendheid | Telt balansrekeningen als kosten en herkent salaris aan de naam van de rekening |
| 11 | Betaaltermijn | Het veld voor de betaaldatum wordt nergens gevuld; de analyse meet dus de vervaldatum |
| 12 | Declaraties en kilometers | Komen niet in de boekhouding: geen inkoopfactuur, declaratie of journaalpost |
| 13 | Offerte | De klant wordt op naam gekoppeld in plaats van op nummer; de nummerreeks staat vast in de code |

## Vast in de code: werkt alleen bij toeval

- De jaren 2022 tot en met 2026 in de btw-aangifte en de jaarrekening: in 2027 is er niets te kiezen.
- Valuta euro bij uren naar factuur.
- Het kilometertarief van 0,23 op drie plekken.
- Het patroon van het factuurnummer dat de nummercontrole verwacht.
- Uren naar factuur vraagt een artikel dat precies zo heet als de uursoort.

## Wat er niet is

- **Geen tests voor de boekhouding.** Er zijn tests voor de installatie, de post en de agenda, maar geen enkele voor
  facturen, btw, uren naar factuur of de rapporten.
- De lokale installer zet het Engelse rekeningschema, niet het Nederlandse van X.

## Voorstel

1. De **btw-aangifte en de opgaaf ICP van X** gebruiken in plaats van de eigen berekening: die rekenen op de server,
   op de btw-code van het sjabloon, en hebben tests.
2. De **rapporten op de server** laten rekenen (de rapporten van ERPNext), en in de schermen alleen tonen.
3. **Uren naar factuur** via de functie van ERPNext, die het merk "gefactureerd" zelf zet bij het boeken.
4. **Boeken is een eigen knop.** Mailen boekt niet stilzwijgend.
5. **Goedkeuren** van declaraties op de server, door iemand anders dan de indiener, met een boeking als gevolg.
6. De opdrachtbalk eruit; de assistent ervoor in de plaats, die alleen concepten maakt.
7. Eén **voorbeeldboekhouding** als test die bij elke versie draait: dezelfde invoer, dezelfde cijfers, in de cloud
   en in de lokale vorm.
