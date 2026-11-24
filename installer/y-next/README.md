# Y-Next lokaal

Y-Next op je eigen pc, zonder de SuperCloud: Frappe, ERPNext en Y-Next in Docker, met één opdracht of één dubbelklik.
Bedoeld om Y-Next te proberen, te demonstreren of er als klein bureau lokaal mee te werken.

| Onderdeel | Versie |
|---|---|
| Y-Next | 0.40.0 (`apps/y_next` in deze repo) |
| ERPNext | 16.51.1 |
| Frappe | 16.52.0 |
| MariaDB | 11.8 |

## Wat je nodig hebt

- **Docker** met Docker Compose 2.17 of nieuwer:
  - Windows 10/11: [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) (met WSL 2);
  - macOS (Intel of Apple Silicon): [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/);
  - Linux (x86-64 of ARM64): [Docker Engine](https://docs.docker.com/engine/install/) met de compose-plugin, of Docker Desktop.
- **Geheugen**: 4 GB vrij voor Docker (een pc met 8 GB of meer). In rust gebruikt het geheel ongeveer 0,6 GB; bij het installeren en onder werk meer.
- **Schijf**: ongeveer 6 GB.
- **Internet** bij de installatie: er wordt ongeveer 2 GB aan images opgehaald. Daarna werkt het zonder internet.

## Installeren

1. Download `y-next-installer-v<versie>.zip` (Windows) of `.tar.gz` (Linux, macOS) van de
   [releases](https://github.com/OpenAECStudio/openaec-xyz/releases) en pak het uit in een map waar het mag blijven
   staan, bijvoorbeeld `Documenten/y-next`.
2. Start Docker (Docker Desktop moet "running" tonen).
3. Start de installer:
   - **Windows**: dubbelklik op `installeer.cmd`.
   - **macOS**: dubbelklik op `installeer.command` (de eerste keer: rechtsklik, Open), of in Terminal `./installeer.sh`.
   - **Linux**: in een terminal `./installeer.sh`.
4. Beantwoord de drie vragen (bedrijfsnaam, je e-mailadres, poort); Enter kiest de standaard.
5. Wacht: de eerste keer duurt het 5 tot 15 minuten, afhankelijk van je verbinding. Aan het eind staan het adres,
   de gebruikersnaam en het wachtwoord op het scherm.
6. Open <http://localhost:8080/y-next> en log in.

Zonder vragen, bijvoorbeeld in een script:

```bash
./installeer.sh --bedrijf "Bouwbedrijf Jansen" --email jan@jansen.nl --naam "Jan Jansen" --poort 8080
./installeer.sh --ja    # alles standaard: Mijn Bedrijf, alleen Administrator, poort 8080
```

Op Windows dezelfde opties: `.\installeer.ps1 -Bedrijf "..." -Email ... -Naam "..." -Poort 8080` of `-Ja`.

## Wat er dan staat

- Een site met ERPNext en Y-Next, Nederlands ingericht: taal Nederlands, euro, tijdzone Amsterdam, het standaard
  rekeningschema en een boekjaar gelijk aan dit kalenderjaar. De installatiewizard van ERPNext is al doorlopen.
- De gebruiker **Administrator**, en als je een e-mailadres opgaf ook een eigen beheerder met alle rollen. Beide met
  hetzelfde, bij de installatie gegenereerde wachtwoord.
- Het bestand `.env` in de installatiemap, met de wachtwoorden en de poort. Het wordt op jouw pc gemaakt en staat
  nergens anders. Bewaar het en deel het niet.
- Y-Next op `/y-next`, ERPNext zelf op `/app`.

Alles luistert alleen op deze pc (`127.0.0.1`). Wil je er vanaf andere apparaten in je eigen netwerk bij, zet dan in
`.env` `LUISTER_OP=0.0.0.0` en draai `docker compose up -d`. Doe dat niet op een open netwerk: er is geen https.

## Dagelijks gebruik

Draai deze opdrachten in de installatiemap.

| Wat | Opdracht |
|---|---|
| Stoppen | `docker compose stop` |
| Weer starten | `docker compose start` (na het herstarten van de pc start het vanzelf met Docker mee) |
| Kijken wat er draait | `docker compose ps` |
| Meldingen lezen | `docker compose logs -f backend` |
| Back-up maken | `docker compose exec backend bench --site y-next.localhost backup --with-files` |
| Back-up naar je pc halen | `docker compose cp backend:/home/frappe/frappe-bench/sites/y-next.localhost/private/backups ./backups` |
| Bijwerken | pak een nieuwere bundel uit over deze map heen (`.env` blijft staan) en draai de installer opnieuw |
| Alles weghalen, **inclusief je gegevens** | `docker compose down -v` |

## Als het niet lukt

- **"Docker draait niet"**: start Docker Desktop en wacht tot het klaar is. Op Linux: `sudo usermod -aG docker $USER`
  en opnieuw inloggen, of draai het script met `sudo`.
- **Poort bezet** (`port is already allocated`): verander `POORT` in `.env` en draai de installer opnieuw.
- **Afgebroken tijdens de eerste installatie**: draai de installer opnieuw; hij begint de site dan opnieuw.
- **Helemaal opnieuw beginnen**: `docker compose down -v`, verwijder `.env` en draai de installer opnieuw.
- **Wachtwoord kwijt**: het staat in `.env`. Heb je het in ERPNext gewijzigd en ben je het kwijt:
  `docker compose exec backend bench --site y-next.localhost set-admin-password <nieuw>`.

## Wat er niet in zit

- Geen HRMS, Wiki of andere apps: Y-Next schakelt verlof, declaraties en de kennisbank pas in als die apps er zijn.
- Geen mailserver. Mail en gedeelde agenda's werken pas als je in ERPNext een e-mailaccount of een Agenda Koppeling
  instelt.
- Geen https en geen automatische back-ups. Dit is een opzet voor de eigen pc, niet voor een server aan het internet.
- Geen SuperCloud-onderdelen (werkplek, Docs, AI).

## Hoe het werkt, en waarom zo

De vorm is een **Docker Compose-bundel met een installatiescript**. Overwogen en afgevallen:

- *Een desktop-installer zoals de OpenAEC Desktop App (`openaec-installer`, Tauri)*: die installeert losse
  desktopprogramma's uit GitHub-releases. Y-Next is een webapp op Frappe met een database, een wachtrij en
  achtergrondwerkers; dat is op Windows en macOS zonder Docker niet te draaien. Een eigen .exe zou dus alsnog Docker
  moeten aansturen, en moet per platform ondertekend worden. De bundel kan later wel als tegel in de Desktop App.
- *Een kant-en-klaar image uit een register*: sneller bij de installatie, maar deze repo is nog privé en een image
  zou dan ook privé zijn. Daarom bouwt de installer het image op de pc zelf. Dat is licht: Y-Next brengt zijn
  gebouwde frontend mee, dus het is alleen het officiële image `frappe/erpnext` plus de map van de app.

De onderdelen:

| Bestand | Wat het doet |
|---|---|
| `installeer.sh`, `installeer.ps1` | controleren Docker, maken `.env` met gegenereerde wachtwoorden, bouwen en starten |
| `installeer.cmd`, `installeer.command` | de dubbelklik voor Windows en macOS |
| `compose.yaml` | de diensten: database, twee keer Valkey, backend, websocket, werker, planner, nginx |
| `Dockerfile` | `frappe/erpnext:v16.51.1` met Y-Next erbij |
| `bench/inrichten.sh`, `bench/inrichten.py` | draaien in de container: site maken, wizard doorlopen, beheerder maken; bij een nieuwere installer migreren |
| `maak-bundel.sh` | maakt de bundel voor een release (installer plus een kopie van `apps/y_next`) |

Vanuit de repo werkt de installer ook direct: `installer/y-next/installeer.sh` pakt dan `apps/y_next`.

## Een release maken

1. Verhoog `VERSIE` en zet de wijziging op `main`.
2. Zet de tag `y-next-installer-v<versie>` en push hem. De workflow `y-next-installer` bouwt de bundel, installeert hem
   op een schone Linux-runner als proef, en maakt de (pre)release met de bundel als bijlage.
