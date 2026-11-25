#!/usr/bin/env bash
# Y-Next lokaal installeren (Linux en macOS). Opnieuw draaien mag: hij start dan wat er al staat
# en werkt bij als de installer nieuwer is.
#
#   ./installeer.sh                     vraagt bedrijfsnaam, beheerder en poort
#   ./installeer.sh --ja                geen vragen, alles standaard
#   ./installeer.sh --bedrijf "Bouwbedrijf Jansen" --email jan@jansen.nl --naam "Jan Jansen" --poort 8080
set -euo pipefail
cd "$(dirname "$0")"

BEDRIJF="" EMAIL="" NAAM="" POORT="" VRAAG=1
while [ $# -gt 0 ]; do
  case "$1" in
    --bedrijf) BEDRIJF=$2; shift 2 ;;
    --email) EMAIL=$2; shift 2 ;;
    --naam) NAAM=$2; shift 2 ;;
    --poort) POORT=$2; shift 2 ;;
    --ja) VRAAG=0; shift ;;
    -h|--help) sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Onbekende optie: $1 (zie --help)" >&2; exit 2 ;;
  esac
done
[ -t 0 ] || VRAAG=0

fout() { echo "FOUT: $*" >&2; exit 1; }

# --- Wat er vooraf moet zijn ---------------------------------------------------------------------
command -v docker >/dev/null 2>&1 \
  || fout "Docker is niet gevonden. Installeer Docker Desktop (Windows, macOS) of Docker Engine (Linux): https://docs.docker.com/get-docker/"
docker compose version >/dev/null 2>&1 \
  || fout "Docker Compose (docker compose) ontbreekt. Werk Docker bij of installeer de compose-plugin."
docker info >/dev/null 2>&1 \
  || fout "Docker draait niet, of je mag het niet gebruiken. Start Docker Desktop; op Linux: voeg jezelf toe aan de groep docker of draai dit script met sudo."
COMPOSE_VERSIE=$(docker compose version --short 2>/dev/null | sed 's/^v//')
case "$COMPOSE_VERSIE" in
  1.*|2.[0-9].*|2.1[0-6].*) fout "Docker Compose $COMPOSE_VERSIE is te oud; 2.17 of nieuwer is nodig. Werk Docker bij." ;;
esac
GEHEUGEN=$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)
if [ "$GEHEUGEN" -gt 0 ] && [ "$GEHEUGEN" -lt 3500000000 ]; then
  echo "LET OP: Docker heeft $((GEHEUGEN / 1048576)) MB geheugen. Y-Next wil minstens 4 GB; zet dat hoger in Docker Desktop (Settings, Resources)."
fi

# --- Instellingen: één keer maken, daarna met rust laten -------------------------------------------
willekeurig() { LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c "$1" || true; }

if [ ! -f .env ]; then
  if [ "$VRAAG" = 1 ]; then
    [ -n "$BEDRIJF" ] || read -r -p "Naam van je bedrijf [Mijn Bedrijf]: " BEDRIJF
    [ -n "$EMAIL" ] || read -r -p "Je e-mailadres, voor een eigen beheerder (leeg = alleen Administrator): " EMAIL
    if [ -n "$EMAIL" ] && [ -z "$NAAM" ]; then read -r -p "Je naam: " NAAM; fi
    [ -n "$POORT" ] || read -r -p "Poort op deze pc [8080]: " POORT
  fi
  BEDRIJF=${BEDRIJF:-Mijn Bedrijf}
  POORT=${POORT:-8080}
  case "$POORT" in ''|*[!0-9]*) fout "De poort moet een getal zijn, niet '$POORT'." ;; esac
  case "$BEDRIJF$NAAM$EMAIL" in *\'*|*\"*|*\$*|*\\*) fout "Gebruik geen aanhalingstekens, \$ of \\ in bedrijfsnaam, naam of e-mailadres." ;; esac

  # In de repo staat de app in apps/y_next; in de bundel in ./y_next.
  BRON=./y_next
  [ -d "$BRON" ] || BRON=../../apps/y_next
  [ -f "$BRON/pyproject.toml" ] || fout "De map met Y-Next ontbreekt (verwacht ./y_next). Pak de bundel opnieuw uit."

  umask 077
  cat > .env <<EOF
# Gemaakt door installeer.sh op $(date +%Y-%m-%d). Bewaar dit bestand; deel het met niemand.
INSTALLER_VERSIE=$(cat VERSIE)
Y_NEXT_BRON=$BRON
SITE_NAAM=y-next.localhost
POORT=$POORT
LUISTER_OP=127.0.0.1
BEDRIJF='$BEDRIJF'
BEHEERDER_EMAIL='$EMAIL'
BEHEERDER_NAAM='$NAAM'
DB_ROOT_PASSWORD=$(willekeurig 32)
ADMIN_PASSWORD=$(willekeurig 20)
EOF
  echo "Instellingen en wachtwoorden staan in $(pwd)/.env"
else
  # Bestaande installatie: alleen de versie van de installer bijwerken.
  sed -i.bak "s/^INSTALLER_VERSIE=.*/INSTALLER_VERSIE=$(cat VERSIE)/" .env && rm -f .env.bak
  echo "Bestaande instellingen in .env blijven staan."
fi

lees() { sed -n "s/^$1=//p" .env | head -n 1 | sed "s/^'\(.*\)'$/\1/"; }
POORT=$(lees POORT)

# --- Bouwen, inrichten, starten ------------------------------------------------------------------
echo "== Image bouwen (de eerste keer wordt ongeveer 2 GB opgehaald) =="
docker compose build inrichten
echo "== Database starten =="
docker compose up -d db redis-cache redis-queue
# In de voorgrond, zodat de voortgang te zien is en een fout hier stopt.
docker compose run --rm inrichten
echo "== Y-Next starten =="
docker compose up -d

printf "Wachten tot Y-Next antwoordt"
for _ in $(seq 1 90); do
  if docker compose exec -T frontend curl -fsS -o /dev/null http://localhost:8080/api/method/ping 2>/dev/null; then
    KLAAR=1; break
  fi
  printf "."; sleep 2
done
echo
[ "${KLAAR:-0}" = 1 ] || fout "Y-Next antwoordt niet binnen drie minuten. Kijk met: docker compose logs backend frontend"

EMAIL=$(lees BEHEERDER_EMAIL)
cat <<EOF

Y-Next draait.

  Y-Next:      http://localhost:$POORT/y-next
  ERPNext:     http://localhost:$POORT/app
  Gebruiker:   Administrator${EMAIL:+  (of $EMAIL)}
  Wachtwoord:  $(lees ADMIN_PASSWORD)

Het wachtwoord staat ook in .env in deze map. Wijzig je het later in ERPNext, dan geldt dat nieuwe.
Stoppen:  docker compose stop      Weer starten:  docker compose start
EOF
