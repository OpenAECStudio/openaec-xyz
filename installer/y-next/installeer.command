#!/usr/bin/env bash
# macOS: dubbelklik in Finder om Y-Next lokaal te installeren of te starten.
"$(dirname "$0")/installeer.sh" "$@"
echo
read -r -p "Druk op Enter om dit venster te sluiten."
