#!/bin/sh
# Резервная копия БД: deploy/backups/fund_YYYY-MM-DD_HHMM.sql.gz, хранится 14 дней.
# Запуск по cron на сервере (из папки deploy):
#   0 3 * * * cd /opt/hashar/deploy && ./backup.sh >> backups/backup.log 2>&1
# Восстановление:
#   gunzip -c backups/<файл>.sql.gz | docker compose -f docker-compose.prod.yml exec -T db psql -U "$DB_USER" "$DB_NAME"
set -eu

cd "$(dirname "$0")"
. ./.env

mkdir -p backups
FILE="backups/fund_$(date +%Y-%m-%d_%H%M).sql.gz"

docker compose -f docker-compose.prod.yml exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$FILE"
find backups -name 'fund_*.sql.gz' -mtime +14 -delete

echo "$(date -Iseconds) backup ok: $FILE"
