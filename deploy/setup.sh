#!/bin/sh
# Первый запуск API на чистом сервере (Ubuntu/Debian). Можно запускать повторно —
# готовое (Docker, .env, cron) не трогает, а с места остановки продолжает.
#   ./setup.sh
#   BACKEND_IMAGE=login/hashar-backend ./setup.sh   — без вопроса про образ
#
# Что делает: ставит Docker → создаёт .env со случайными SECRET_KEY и паролем БД →
# проверяет Origin-сертификат Cloudflare → скачивает образ и запускает (./update.sh) →
# ставит ночной бэкап в cron.
set -eu

cd "$(dirname "$0")"
DEPLOY_DIR="$(pwd)"

say() { printf '\n\033[1m── %s\033[0m\n' "$1"; }
fail() { printf '\n\033[31m%s\033[0m\n' "$1" >&2; exit 1; }

# sudo — только если запущено не от root
SUDO=""
[ "$(id -u)" -eq 0 ] || SUDO="sudo"

# ─── 1. Docker ─────────────────────────────────────────────────────────────────
say "Docker"
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  echo "уже есть: $(docker --version)"
else
  echo "ставлю официальным скриптом https://get.docker.com"
  curl -fsSL https://get.docker.com | $SUDO sh
  $SUDO systemctl enable --now docker
fi

# Пользователь не root и не в группе docker — работаем через sudo
DOCKER_OK=1
docker info >/dev/null 2>&1 || DOCKER_OK=0
if [ "$DOCKER_OK" -eq 0 ]; then
  if [ -n "$SUDO" ]; then
    $SUDO usermod -aG docker "$(id -un)"
    fail "Добавил $(id -un) в группу docker. Перезайдите по ssh и запустите ./setup.sh ещё раз."
  fi
  fail "Docker не отвечает: systemctl status docker"
fi

# ─── 2. .env ──────────────────────────────────────────────────────────────────
say ".env"
random_hex() { openssl rand -hex "$1" 2>/dev/null || od -An -N"$1" -tx1 /dev/urandom | tr -d ' \n'; }
set_env() { sed -i "s|^$1=.*|$1=$2|" .env; }

if [ ! -f .env ]; then
  cp .env.example .env
  set_env SECRET_KEY "$(random_hex 32)"
  set_env DB_PASSWORD "$(random_hex 24)"
  echo "создан .env: SECRET_KEY и DB_PASSWORD сгенерированы"
else
  echo "уже есть — не трогаю"
fi
chmod 600 .env

# Образ backend: из переменной окружения или спросим
CURRENT_IMAGE="$(sed -n 's/^BACKEND_IMAGE=//p' .env)"
if [ -n "${BACKEND_IMAGE:-}" ]; then
  set_env BACKEND_IMAGE "$BACKEND_IMAGE"
elif [ -z "$CURRENT_IMAGE" ]; then
  printf 'Образ backend в Docker Hub (логин/hashar-backend): '
  read -r ANSWER
  [ -n "$ANSWER" ] || fail "Без образа запускать нечего."
  set_env BACKEND_IMAGE "$ANSWER"
fi
echo "BACKEND_IMAGE=$(sed -n 's/^BACKEND_IMAGE=//p' .env)"

# ─── 3. Сертификат Cloudflare ─────────────────────────────────────────────────
say "Сертификат Cloudflare Origin CA"
mkdir -p certs backups
if [ ! -s certs/origin.pem ] || [ ! -s certs/origin.key ]; then
  fail "Нет certs/origin.pem или certs/origin.key.
Cloudflare → SSL/TLS → Origin Server → Create Certificate (hashar.app, *.hashar.app, 15 лет),
сохраните сертификат и ключ в $DEPLOY_DIR/certs/ и запустите ./setup.sh ещё раз."
fi
chmod 600 certs/origin.key
openssl x509 -in certs/origin.pem -noout -subject -enddate 2>/dev/null || echo "файлы на месте"

# ─── 4. Образ и запуск ────────────────────────────────────────────────────────
say "Образ backend"
chmod +x update.sh backup.sh admin.sh
if ! docker compose pull backend; then
  echo "Не скачался — возможно, репозиторий в Docker Hub приватный. Вход:"
  docker login
  docker compose pull backend
fi

say "Запуск"
# Порт Caddy должен быть свободен (или уже занят нашим же caddy при повторном запуске)
API_PORT="$(sed -n 's/^API_PORT=//p' .env)"
API_PORT="${API_PORT:-443}"
if [ "$(docker compose ps -a caddy --format '{{.State}}' 2>/dev/null)" != "running" ] \
  && ss -Hltn "sport = :$API_PORT" 2>/dev/null | grep -q .; then
  fail "Порт $API_PORT уже занят:
$($SUDO ss -Hltnp "sport = :$API_PORT" 2>/dev/null | head -3)
Поставьте в .env API_PORT=8443 и в Cloudflare → Rules → Origin Rules создайте правило:
Hostname equals $(sed -n 's/^API_DOMAIN=//p' .env) → Destination Port: 8443. Затем ./setup.sh ещё раз."
fi
./update.sh

# ─── 5. Бэкап по cron ─────────────────────────────────────────────────────────
say "Ночной бэкап БД (03:00)"
if ! command -v crontab >/dev/null 2>&1; then
  # На минимальных образах Debian/Ubuntu cron не установлен
  $SUDO apt-get update -qq && $SUDO apt-get install -y -qq cron
  $SUDO systemctl enable --now cron
fi
CRON_LINE="0 3 * * * $DEPLOY_DIR/backup.sh >> $DEPLOY_DIR/backups/backup.log 2>&1"
if crontab -l 2>/dev/null | grep -Fq "$DEPLOY_DIR/backup.sh"; then
  echo "уже в cron"
else
  (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
  echo "добавлено: $CRON_LINE"
fi

API_DOMAIN="$(sed -n 's/^API_DOMAIN=//p' .env)"
say "Готово"
cat <<EOF
Проверка:   https://$API_DOMAIN/health  →  {"db":1}
Обновление: ./update.sh   (после того как GitHub Actions собрал образ)
Админ:      зарегистрируйтесь в приложении, затем ./admin.sh +992XXXXXXXXX
Логи:       docker compose logs -f backend
EOF
