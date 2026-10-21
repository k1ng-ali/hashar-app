#!/bin/sh
# Резервная копия БД: deploy/backups/hashar_YYYY-MM-DD_HHMM.sql.gz, хранится 14 дней.
# Если заполнен backup.env — копия ещё и уходит в Cloudflare R2 (бакет для бэкапов, префикс db/),
# там её удаляет правило жизненного цикла бакета (см. README → «Бэкапы»).
# По cron каждую ночь (ставит setup.sh):
#   0 3 * * * /opt/hashar/deploy/backup.sh >> /opt/hashar/deploy/backups/backup.log 2>&1
# Восстановление и проверка копий — ./restore.sh
set -eu

cd "$(dirname "$0")"
# Ключи бакета бэкапов — в отдельном файле backup.env: .env целиком уходит в контейнер backend,
# а ключ, которым можно стереть бэкапы, приложению не нужен
. ./backup-lib.sh
load_env

# Пинг мониторинга (healthchecks.io и т. п.): тишина или /fail — повод проверить сервер
ping_monitor() {
  [ -n "${BACKUP_PING_URL:-}" ] || return 0
  curl -fsS -m 10 --retry 3 "$BACKUP_PING_URL$1" >/dev/null || true
}
fail() {
  echo "$(date -Iseconds) backup FAILED: $1" >&2
  ping_monitor /fail
  exit 1
}

mkdir -p backups
NAME="hashar_$(date +%Y-%m-%d_%H%M).sql"
SQL="backups/$NAME"

# Без pipefail в sh: сначала дамп в файл, чтобы ошибка pg_dump не дала пустой «успешный» архив
if ! docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$SQL"; then
  rm -f "$SQL"
  fail "pg_dump"
fi
gzip -f "$SQL"
gzip -t "$SQL.gz" || fail "архив повреждён: $SQL.gz"
find backups -name 'hashar_*.sql.gz' -mtime +14 -delete

if offsite_enabled; then
  # copyto сверяет контрольную сумму после загрузки; ошибка — бэкап считается неудачным
  rclone copyto "/backups/$NAME.gz" "r2:$BACKUP_S3_BUCKET/db/$NAME.gz" || fail "загрузка в R2"
  echo "$(date -Iseconds) backup ok: $SQL.gz (+ R2 $BACKUP_S3_BUCKET/db/$NAME.gz)"
else
  echo "$(date -Iseconds) backup ok: $SQL.gz (только на сервере: backup.env не заполнен)"
fi
ping_monitor ""
