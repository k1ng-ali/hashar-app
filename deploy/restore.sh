#!/bin/sh
# Восстановление БД из резервной копии (локальной из backups/ или из R2 — скачается сама).
#   ./restore.sh --list            — копии на сервере и в R2
#   ./restore.sh --check [копия]   — учебное восстановление во временную базу: копия цела и читается.
#                                    Рабочую базу не трогает. Без аргумента — самая свежая копия
#   ./restore.sh <копия>           — ЗАМЕНИТЬ рабочую базу копией (спросит подтверждение;
#                                    перед этим сохранит текущую базу через ./backup.sh)
# <копия> — имя файла (hashar_2026-10-21_0300.sql.gz) или latest.
set -eu

cd "$(dirname "$0")"
. ./backup-lib.sh
load_env

CHECK_DB="hashar_restore_check"

# psql в контейнере db. stdin — только для load (дамп): иначе docker съест ввод подтверждения
psql_in() {
  db="$1"
  shift
  docker compose exec -T -e PGOPTIONS="-c client_min_messages=warning" db \
    psql -U "$DB_USER" -d "$db" -v ON_ERROR_STOP=1 -q "$@" </dev/null
}

list_local() { ls -1 backups 2>/dev/null | grep -E '^hashar_.*\.sql\.gz$' | sort || true; }
list_remote() { offsite_enabled && rclone lsf "r2:$BACKUP_S3_BUCKET/db/" | sort || true; }

# Имя копии → путь к файлу в backups/ (скачивает из R2, если на сервере её нет)
fetch() {
  name="$1"
  if [ "$name" = "latest" ]; then
    name="$( (list_local; list_remote) | sort -u | tail -n 1)"
    [ -n "$name" ] || { echo "Копий нет ни на сервере, ни в R2" >&2; exit 1; }
  fi
  name="$(basename "$name")"
  if [ ! -f "backups/$name" ]; then
    offsite_enabled || { echo "Нет backups/$name, а R2 не настроен (backup.env)" >&2; exit 1; }
    echo "Скачиваю $name из R2..." >&2
    mkdir -p backups
    rclone copyto "r2:$BACKUP_S3_BUCKET/db/$name" "/backups/$name" >&2
  fi
  gzip -t "backups/$name" || { echo "Архив backups/$name повреждён" >&2; exit 1; }
  echo "backups/$name"
}

# Загрузка дампа в пустую базу одной транзакцией: ошибка — и в базе ничего не остаётся
load() {
  gunzip -c "$1" | docker compose exec -T db \
    psql -U "$DB_USER" -d "$2" -v ON_ERROR_STOP=1 -q --single-transaction >/dev/null
}

# Что в базе: пара цифр, чтобы глазами сверить копию. Без конвейера — иначе ошибку psql съест sed
summary() {
  out="$(psql_in "$1" -At -F ': ' -c "
    select 'пользователи', count(*)::text from users
    union all select 'фонды', count(*)::text from funds
    union all select 'взносы', count(*)::text from contributions
    union all select 'расходы', count(*)::text from expenses
    union all select 'последний взнос', coalesce(max(created_at)::text, '—') from contributions")"
  echo "$out" | sed 's/^/  /'
}

recreate_db() {
  psql_in postgres -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '$1' and pid <> pg_backend_pid()" >/dev/null
  psql_in postgres -c "drop database if exists \"$1\""
  psql_in postgres -c "create database \"$1\" owner \"$DB_USER\""
}

case "${1:-}" in
  --list)
    echo "На сервере (backups/):"
    list_local | sed 's/^/  /'
    if offsite_enabled; then
      echo "В R2 ($BACKUP_S3_BUCKET/db/):"
      list_remote | sed 's/^/  /'
    else
      echo "R2 не настроен (backup.env)"
    fi
    ;;

  --check)
    FILE="$(fetch "${2:-latest}")"
    echo "Проверяю $FILE во временной базе $CHECK_DB..."
    recreate_db "$CHECK_DB"
    trap 'psql_in postgres -c "drop database if exists \"$CHECK_DB\"" >/dev/null 2>&1 || true' EXIT
    load "$FILE" "$CHECK_DB"
    summary "$CHECK_DB"
    echo "Копия читается. Временная база удалена, рабочая не тронута."
    ;;

  "" | -h | --help)
    sed -n '2,9p' "$0"
    ;;

  *)
    FILE="$(fetch "$1")"
    echo "Рабочая база $DB_NAME будет ЗАМЕНЕНА копией $FILE. Сейчас в ней:"
    summary "$DB_NAME"
    printf 'Для подтверждения введите имя базы (%s): ' "$DB_NAME"
    read -r ANSWER
    [ "$ANSWER" = "$DB_NAME" ] || { echo "Отменено"; exit 1; }

    # Страховка: текущее состояние тоже сохраняется — восстановление можно откатить
    ./backup.sh
    SAFETY="$(list_local | tail -n 1)"
    docker compose stop backend
    # Пока backend стоит, сайт отвечает 502 — это ожидаемо
    trap 'echo "Восстановление прервано, backend остановлен. Вернуть базу как была: ./restore.sh $SAFETY" >&2' EXIT
    recreate_db "$DB_NAME"
    load "$FILE" "$DB_NAME"
    trap - EXIT
    # Миграции backend применит сам при старте (если копия старше текущей схемы)
    docker compose start backend
    summary "$DB_NAME"
    echo "Готово: база восстановлена из $FILE"
    ;;
esac
