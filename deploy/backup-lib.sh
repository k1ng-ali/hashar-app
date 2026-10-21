# Общее для backup.sh и restore.sh: rclone в одноразовом контейнере (на сервер ставить ничего не нужно).
# Подключается через `. ./backup-lib.sh`, затем load_env.

# Значение KEY из env-файла. Файл не выполняется как скрипт: формат docker допускает значения
# с пробелами без кавычек (PAYOMCHI_SENDER_ID=Hashar App), а `. ./.env` принял бы «App» за команду
env_value() {
  [ -f "$2" ] || return 0
  sed -n "s/^$1=//p" "$2" | tail -n 1 | tr -d '\r' \
    | sed -e 's/[[:space:]]*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

# Настройки для backup.sh и restore.sh: база из .env, бакет бэкапов из backup.env
load_env() {
  DB_USER="$(env_value DB_USER .env)"
  DB_NAME="$(env_value DB_NAME .env)"
  if [ -z "$DB_USER" ] || [ -z "$DB_NAME" ]; then
    echo "В .env нет DB_USER или DB_NAME" >&2
    exit 1
  fi
  BACKUP_S3_ENDPOINT_URL="$(env_value BACKUP_S3_ENDPOINT_URL backup.env)"
  BACKUP_S3_ACCESS_KEY_ID="$(env_value BACKUP_S3_ACCESS_KEY_ID backup.env)"
  BACKUP_S3_SECRET_ACCESS_KEY="$(env_value BACKUP_S3_SECRET_ACCESS_KEY backup.env)"
  BACKUP_S3_BUCKET="$(env_value BACKUP_S3_BUCKET backup.env)"
  BACKUP_PING_URL="$(env_value BACKUP_PING_URL backup.env)"
}

RCLONE_IMAGE="rclone/rclone:1.75.1"

offsite_enabled() {
  [ -n "${BACKUP_S3_ENDPOINT_URL:-}" ] && [ -n "${BACKUP_S3_ACCESS_KEY_ID:-}" ] \
    && [ -n "${BACKUP_S3_SECRET_ACCESS_KEY:-}" ] && [ -n "${BACKUP_S3_BUCKET:-}" ]
}

# rclone <команда> ... — папка backups/ видна в контейнере как /backups, удалённое хранилище — как r2:
# (настройки — только из переменных окружения, файл конфига не нужен: --config "")
rclone() {
  # --user: скачанные копии принадлежат пользователю сервера, а не root
  docker run --rm --user "$(id -u):$(id -g)" \
    -v "$(pwd)/backups:/backups" \
    -e RCLONE_CONFIG_R2_TYPE=s3 \
    -e RCLONE_CONFIG_R2_PROVIDER=Cloudflare \
    -e RCLONE_CONFIG_R2_ENDPOINT="$BACKUP_S3_ENDPOINT_URL" \
    -e RCLONE_CONFIG_R2_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY_ID" \
    -e RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_ACCESS_KEY" \
    -e RCLONE_CONFIG_R2_NO_CHECK_BUCKET=true \
    "$RCLONE_IMAGE" --config "" "$@"
}
