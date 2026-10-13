#!/bin/sh
# Обновление API на сервере: свежий образ backend из Docker Hub → перезапуск.
#   ./update.sh                          — последняя сборка из ветки release (latest)
#   BACKEND_TAG=sha-1a2b3c4 ./update.sh  — откат на конкретную сборку (теги — в Docker Hub)
# Вернуться на свежую сборку — снова ./update.sh без BACKEND_TAG.
set -eu

cd "$(dirname "$0")"

# Конфиги деплоя (compose, Caddyfile) — из git, если папка — часть клона репозитория
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git pull --ff-only
fi

docker compose pull
# Миграции применяет сам backend при старте
docker compose up -d --remove-orphans
# Caddyfile мог измениться — перечитать без перезапуска (соединения не рвутся)
docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile >/dev/null 2>&1 || true
docker image prune -f >/dev/null

# Ждём, пока backend ответит на /health (миграции могут идти несколько секунд)
i=0
until [ "$(docker compose ps backend --format '{{.Health}}')" = "healthy" ]; do
  i=$((i + 1))
  if [ "$i" -ge 45 ]; then
    echo "backend не стал healthy за 90 с — смотри: docker compose logs --tail 100 backend" >&2
    exit 1
  fi
  sleep 2
done

# Caddy — вход снаружи: если не запустился (например, порт занят), API недоступен,
# хотя backend здоров
if [ "$(docker compose ps -a caddy --format '{{.State}}')" != "running" ]; then
  echo "caddy не запущен — смотри: docker compose logs --tail 30 caddy" >&2
  echo "частая причина — порт API_PORT занят другим проектом: sudo ss -ltnp | grep ':443 '" >&2
  exit 1
fi

echo "$(date -Iseconds) ok: $(docker inspect --format '{{.Config.Image}}' "$(docker compose ps -q backend)")"
