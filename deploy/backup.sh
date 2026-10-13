#!/bin/sh
# Резервная копия БД: deploy/backups/hashar_YYYY-MM-DD_HHMM.sql.gz, хранится 14 дней.
# По cron каждую ночь (ставит setup.sh):
#   0 3 * * * /opt/hashar/deploy/backup.sh >> /opt/hashar/deploy/backups/backup.log 2>&1
# Восстановление (из папки deploy):
#   gunzip -c backups/<файл>.sql.gz | docker compose exec -T db psql -U "$DB_USER" "$DB_NAME"
# Копии лежат на этом же сервере — время от времени уносите их в другое место.
set -eu

cd "$(dirname "$0")"
. ./.env

mkdir -p backups
SQL="backups/hashar_$(date +%Y-%m-%d_%H%M).sql"

# Без pipefail в sh: сначала дамп в файл, чтобы ошибка pg_dump не дала пустой «успешный» архив
if ! docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$SQL"; then
  rm -f "$SQL"
  echo "$(date -Iseconds) backup FAILED" >&2
  exit 1
fi
gzip -f "$SQL"
find backups -name 'hashar_*.sql.gz' -mtime +14 -delete

echo "$(date -Iseconds) backup ok: $SQL.gz"
