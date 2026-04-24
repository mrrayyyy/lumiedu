#!/usr/bin/env sh
set -eu

if [ "${1:-}" = "" ]; then
  echo "Usage: ./infra/scripts/restore_postgres.sh <backup-file.sql>"
  exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

docker exec -i lumiedu-postgres psql -U "${POSTGRES_USER:-lumiedu}" "${POSTGRES_DB:-lumiedu}" < "$BACKUP_FILE"
echo "Restore completed from $BACKUP_FILE"
