Y-Next op je eigen pc, zonder de SuperCloud: Frappe 16.52.0, ERPNext 16.51.1 en Y-Next 0.40.0 in Docker.

## Installeren

1. Zorg voor **Docker** (Windows en macOS: Docker Desktop; Linux: Docker Engine met de compose-plugin), 4 GB geheugen
   voor Docker en ongeveer 6 GB schijfruimte.
2. Download hieronder `y-next-installer-v0.1.0.zip` (Windows) of `.tar.gz` (Linux, macOS) en pak het uit.
3. Start de installer in de uitgepakte map:
   - Windows: dubbelklik op `installeer.cmd`
   - macOS: dubbelklik op `installeer.command` (eerste keer: rechtsklik, Open)
   - Linux: `./installeer.sh`
4. Geef je bedrijfsnaam, e-mailadres en de poort op (Enter = standaard) en wacht 5 tot 15 minuten.
5. Open <http://localhost:8080/y-next> en log in met de gegevens die de installer toont.

De wachtwoorden worden op je eigen pc gegenereerd en staan in `.env` in de installatiemap. Alles over stoppen,
back-ups, bijwerken en weghalen staat in `README.md` in de bundel.

## Getest

- **Linux (x86-64)**: van begin tot eind getest, lokaal en bij elke release op een schone GitHub-runner
  (installeren uit de bundel, inloggen, Y-Next openen, de installer een tweede keer draaien).
- **Windows en macOS**: **niet getest.** De diensten zijn dezelfde Docker-containers; alleen de startscripts
  (`installeer.ps1`, `installeer.cmd`, `installeer.command`) verschillen, en die zijn alleen op syntaxis gecontroleerd.
  Meld het als het daar misgaat.

Dit is een voorlopige uitgave (pre-release) voor de eigen pc: geen https, geen automatische back-ups, geen HRMS of
SuperCloud-onderdelen.
