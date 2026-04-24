#!/usr/bin/env sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-./infra/backups}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

docker exec lumiedu-postgres pg_dump -U "${POSTGRES_USER:-lumiedu}" "${POSTGRES_DB:-lumiedu}" \
  > "${BACKUP_DIR}/lumiedu-${TIMESTAMP}.sql"

echo "Backup created at ${BACKUP_DIR}/lumiedu-${TIMESTAMP}.sql"
