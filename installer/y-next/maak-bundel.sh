#!/usr/bin/env bash
# Maakt de bundel voor een release: de installer plus een kopie van apps/y_next, als .zip en .tar.gz in dist/.
set -euo pipefail
cd "$(dirname "$0")"
VERSIE=$(cat VERSIE)
NAAM="y-next-installer-v$VERSIE"
rm -rf dist && mkdir -p "dist/$NAAM"
cp -r compose.yaml Dockerfile .dockerignore VERSIE README.md bench \
  installeer.sh installeer.command installeer.ps1 installeer.cmd "dist/$NAAM/"
# Alleen wat in git staat: geen __pycache__ of lokale resten.
git -C ../.. archive --format=tar --prefix=y_next/ HEAD:apps/y_next | tar -x -C "dist/$NAAM"
chmod +x "dist/$NAAM/installeer.sh" "dist/$NAAM/installeer.command" "dist/$NAAM/bench/inrichten.sh"
(cd dist && tar -czf "$NAAM.tar.gz" "$NAAM" && zip -qr "$NAAM.zip" "$NAAM" && sha256sum "$NAAM.tar.gz" "$NAAM.zip" > SHA256SUMS.txt)
ls -lh dist
