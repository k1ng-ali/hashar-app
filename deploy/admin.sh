#!/bin/sh
# Администратор платформы (подтверждает тарифы, страница /platform).
# Пользователь сначала регистрируется в приложении, потом:
#   ./admin.sh +992 90 123 45 67      — выдать права (телефон в любом формате или email)
#   ./admin.sh --revoke name@mail.com — забрать права
#   ./admin.sh --list                 — кто сейчас админ
# После выдачи прав пользователю нужно выйти и войти заново.
set -eu

cd "$(dirname "$0")"
. ./.env

psql() { docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 "$@"; }

case "${1:-}" in
  --list)
    psql -c "select id, full_name, phone, email from users where is_platform_admin order by id"
    exit 0
    ;;
  --revoke)
    VALUE=false
    shift
    ;;
  "" | -h | --help)
    sed -n '2,8p' "$0"
    exit 0
    ;;
  *)
    VALUE=true
    ;;
esac

LOGIN="$*"
[ -n "$LOGIN" ] || { echo "Укажите телефон или email" >&2; exit 1; }

# Так же, как backend при входе: email — в нижнем регистре, телефон — «+» и только цифры
case "$LOGIN" in
  *@*) LOGIN="$(printf '%s' "$LOGIN" | tr '[:upper:]' '[:lower:]')" ;;
  *) LOGIN="+$(printf '%s' "$LOGIN" | tr -cd '0-9')" ;;
esac

# Логин передаём переменной psql (:'login' — экранированная строка), не склеиваем SQL
RESULT="$(psql -qtA -v login="$LOGIN" <<SQL
update users set is_platform_admin = $VALUE
where phone = :'login' or email = :'login'
returning id || ' · ' || full_name;
SQL
)"

if [ -z "$RESULT" ]; then
  echo "Пользователь $LOGIN не найден — сначала зарегистрируйтесь в приложении" >&2
  exit 1
fi
echo "$RESULT: is_platform_admin = $VALUE"
