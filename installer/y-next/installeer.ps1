# Y-Next lokaal installeren (Windows, met Docker Desktop). Opnieuw draaien mag: hij start dan wat er al staat
# en werkt bij als de installer nieuwer is. Dubbelklik op installeer.cmd, of:
#
#   .\installeer.ps1                    vraagt bedrijfsnaam, beheerder en poort
#   .\installeer.ps1 -Ja                geen vragen, alles standaard
#   .\installeer.ps1 -Bedrijf "Bouwbedrijf Jansen" -Email jan@jansen.nl -Naam "Jan Jansen" -Poort 8080
param(
  [string]$Bedrijf = "",
  [string]$Email = "",
  [string]$Naam = "",
  [string]$Poort = "",
  [switch]$Ja
)
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Fout($tekst) { Write-Host "FOUT: $tekst" -ForegroundColor Red; exit 1 }
# Docker schrijft voortgang naar stderr; alleen de exitcode telt.
function Docker-Stil { $ErrorActionPreference = "Continue"; & docker @args *> $null; return $LASTEXITCODE -eq 0 }
function Docker-Moet { $ErrorActionPreference = "Continue"; & docker @args; if ($LASTEXITCODE -ne 0) { Fout "docker $($args -join ' ') is mislukt." } }

# --- Wat er vooraf moet zijn ---------------------------------------------------------------------
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Fout "Docker is niet gevonden. Installeer Docker Desktop: https://docs.docker.com/desktop/setup/install/windows-install/"
}
if (-not (Docker-Stil compose version)) { Fout "Docker Compose ontbreekt. Werk Docker Desktop bij." }
if (-not (Docker-Stil info)) { Fout "Docker draait niet. Start Docker Desktop en wacht tot het klaar is." }
$composeVersie = (& docker compose version --short) -replace '^v', ''
if ([version]($composeVersie -replace '[^0-9.].*$', '') -lt [version]"2.17") {
  Fout "Docker Compose $composeVersie is te oud; 2.17 of nieuwer is nodig. Werk Docker Desktop bij."
}
$geheugen = [int64](& docker info --format '{{.MemTotal}}')
if ($geheugen -gt 0 -and $geheugen -lt 3500000000) {
  Write-Host "LET OP: Docker heeft $([int]($geheugen / 1MB)) MB geheugen. Y-Next wil minstens 4 GB; zet dat hoger in Docker Desktop (Settings, Resources)."
}

# --- Instellingen: één keer maken, daarna met rust laten -------------------------------------------
function Willekeurig([int]$lengte) {
  $tekens = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
  $bytes = New-Object byte[] $lengte
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  $rng.GetBytes($bytes)
  -join ($bytes | ForEach-Object { $tekens[$_ % $tekens.Length] })
}
# Zonder BOM en met LF: Docker Compose leest .env anders verkeerd.
function Schrijf-Env([string[]]$regels) {
  [IO.File]::WriteAllText((Join-Path $PSScriptRoot ".env"), (($regels -join "`n") + "`n"), (New-Object Text.UTF8Encoding($false)))
}
$versie = (Get-Content -LiteralPath VERSIE -TotalCount 1).Trim()

if (-not (Test-Path -LiteralPath .env)) {
  if (-not $Ja) {
    if (-not $Bedrijf) { $Bedrijf = Read-Host "Naam van je bedrijf [Mijn Bedrijf]" }
    if (-not $Email) { $Email = Read-Host "Je e-mailadres, voor een eigen beheerder (leeg = alleen Administrator)" }
    if ($Email -and -not $Naam) { $Naam = Read-Host "Je naam" }
    if (-not $Poort) { $Poort = Read-Host "Poort op deze pc [8080]" }
  }
  if (-not $Bedrijf) { $Bedrijf = "Mijn Bedrijf" }
  if (-not $Poort) { $Poort = "8080" }
  if ($Poort -notmatch '^[0-9]+$') { Fout "De poort moet een getal zijn, niet '$Poort'." }
  if ("$Bedrijf$Naam$Email" -match "['`"\$\\]") { Fout "Gebruik geen aanhalingstekens, `$ of \ in bedrijfsnaam, naam of e-mailadres." }

  # In de repo staat de app in apps/y_next; in de bundel in ./y_next.
  $bron = "./y_next"
  if (-not (Test-Path -LiteralPath $bron)) { $bron = "../../apps/y_next" }
  if (-not (Test-Path -LiteralPath (Join-Path $bron "pyproject.toml"))) {
    Fout "De map met Y-Next ontbreekt (verwacht .\y_next). Pak de bundel opnieuw uit."
  }

  Schrijf-Env @(
    "# Gemaakt door installeer.ps1 op $(Get-Date -Format yyyy-MM-dd). Bewaar dit bestand; deel het met niemand.",
    "INSTALLER_VERSIE=$versie",
    "Y_NEXT_BRON=$bron",
    "SITE_NAAM=y-next.localhost",
    "POORT=$Poort",
    "LUISTER_OP=127.0.0.1",
    "BEDRIJF='$Bedrijf'",
    "BEHEERDER_EMAIL='$Email'",
    "BEHEERDER_NAAM='$Naam'",
    "DB_ROOT_PASSWORD=$(Willekeurig 32)",
    "ADMIN_PASSWORD=$(Willekeurig 20)"
  )
  Write-Host "Instellingen en wachtwoorden staan in $(Join-Path $PSScriptRoot '.env')"
} else {
  # Bestaande installatie: alleen de versie van de installer bijwerken.
  Schrijf-Env @((Get-Content -LiteralPath .env) -replace '^INSTALLER_VERSIE=.*', "INSTALLER_VERSIE=$versie")
  Write-Host "Bestaande instellingen in .env blijven staan."
}

function Lees([string]$sleutel) {
  $regel = Get-Content -LiteralPath .env | Where-Object { $_ -match "^$sleutel=" } | Select-Object -First 1
  if (-not $regel) { return "" }
  ($regel -replace "^$sleutel=", "") -replace "^'(.*)'$", '$1'
}
$Poort = Lees "POORT"

# --- Bouwen, inrichten, starten ------------------------------------------------------------------
Write-Host "== Image bouwen (de eerste keer wordt ongeveer 2 GB opgehaald) =="
Docker-Moet compose build inrichten
Write-Host "== Database starten =="
Docker-Moet compose up -d db redis-cache redis-queue
# In de voorgrond, zodat de voortgang te zien is en een fout hier stopt.
Docker-Moet compose run --rm inrichten
Write-Host "== Y-Next starten =="
Docker-Moet compose up -d

Write-Host -NoNewline "Wachten tot Y-Next antwoordt"
$klaar = $false
foreach ($i in 1..90) {
  if (Docker-Stil compose exec -T frontend curl -fsS -o /dev/null http://localhost:8080/api/method/ping) { $klaar = $true; break }
  Write-Host -NoNewline "."
  Start-Sleep -Seconds 2
}
Write-Host ""
if (-not $klaar) { Fout "Y-Next antwoordt niet binnen drie minuten. Kijk met: docker compose logs backend frontend" }

$beheerder = Lees "BEHEERDER_EMAIL"
$wie = "Administrator"
if ($beheerder) { $wie = "Administrator  (of $beheerder)" }
Write-Host @"

Y-Next draait.

  Y-Next:      http://localhost:$Poort/y-next
  ERPNext:     http://localhost:$Poort/app
  Gebruiker:   $wie
  Wachtwoord:  $(Lees "ADMIN_PASSWORD")

Het wachtwoord staat ook in .env in deze map. Wijzig je het later in ERPNext, dan geldt dat nieuwe.
Stoppen:  docker compose stop      Weer starten:  docker compose start
"@
