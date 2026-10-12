#!/bin/sh
# Обновление API на сервере: свежий образ backend из Docker Hub → перезапуск.
# Запуск из любой папки:  ./update.sh
# Откат на конкретную сборку:  BACKEND_TAG=sha-1a2b3c4 ./update.sh
# (теги — в Docker Hub или в логе GitHub Actions; вернуться на свежую — просто ./update.sh)
set -eu

cd "$(dirname "$0")"
COMPOSE="docker compose -f docker-compose.prod.yml"

# Конфиги деплоя (compose, Caddyfile) — из git, если папка — часть клона репозитория
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git pull --ff-only
fi

$COMPOSE pull
# Миграции применяет сам backend при старте
$COMPOSE up -d --remove-orphans
docker image prune -f >/dev/null

# Ждём, пока backend ответит на /health (миграции могут идти несколько секунд)
i=0
until [ "$($COMPOSE ps backend --format '{{.Health}}')" = "healthy" ]; do
  i=$((i + 1))
  if [ "$i" -ge 30 ]; then
    echo "backend не стал healthy за 60 с — смотри: $COMPOSE logs --tail 100 backend" >&2
    exit 1
  fi
  sleep 2
done

echo "$(date -Iseconds) ok: $(docker inspect --format '{{.Config.Image}}' "$($COMPOSE ps -q backend)")"
