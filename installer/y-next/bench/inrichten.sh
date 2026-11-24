#!/bin/bash
# Draait IN de container, bij elke start vóór de rest. Idempotent:
# - eerste keer: site maken met ERPNext en Y-Next, de wizard doorlopen, de beheerder maken;
# - daarna: alleen migreren als de versie van de installer is veranderd.
set -euo pipefail
cd /home/frappe/frappe-bench

SITE=${SITE_NAAM:-y-next.localhost}
VERSIE=${Y_NEXT_INSTALLER_VERSIE:-dev}
MERK="sites/$SITE/.y-next-installer"

ls -1 apps > sites/apps.txt
bench set-config -g db_host db
bench set-config -gp db_port 3306
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-queue:6379
bench set-config -gp socketio_port 9000

if [ ! -f "$MERK" ]; then
  echo "== Site $SITE maken met ERPNext en Y-Next (dit duurt een paar minuten) =="
  # Een map zonder merkteken is een afgebroken eerste poging: opnieuw beginnen.
  FORCEER=()
  [ -d "sites/$SITE" ] && FORCEER=(--force)
  bench new-site "$SITE" "${FORCEER[@]}" \
    --db-root-password "$DB_ROOT_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" \
    --mariadb-user-host-login-scope=% \
    --install-app erpnext \
    --install-app y_next \
    --set-default
  echo "== Bedrijf en beheerder inrichten =="
  (cd sites && ../env/bin/python /opt/y-next/inrichten.py)
  bench --site "$SITE" set-config host_name "http://localhost:${POORT:-8080}"
  bench --site "$SITE" clear-cache
  echo "$VERSIE" > "$MERK"
  echo "== Klaar: site $SITE staat =="
elif [ "$(cat "$MERK")" != "$VERSIE" ]; then
  echo "== Bijwerken van $(cat "$MERK") naar $VERSIE: migreren =="
  bench --site "$SITE" migrate
  bench --site "$SITE" clear-cache
  echo "$VERSIE" > "$MERK"
else
  echo "Site $SITE is al ingericht (installer $VERSIE)."
fi
