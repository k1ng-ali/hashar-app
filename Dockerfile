# ─── Фронтенд: сборка Vite → nginx (статика SPA) ──────────────────────────────
# Сборка из корня репозитория: docker build --build-arg VITE_API_URL=https://api.hashar.app -t hashar-frontend .
# В проде запускается из deploy/docker-compose.prod.yml

# Node 20 больше не поддерживается (EOL 2026-04) — сборка на текущем LTS
FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# VITE_API_URL — адрес API без /api/v1 (в проде https://api.hashar.app).
# Демо-вход и генератор демо-чеков в прод-сборку не попадают
ARG VITE_API_URL=""
ARG VITE_DEV_MODE="false"
ENV VITE_API_URL=$VITE_API_URL \
    VITE_DEV_MODE=$VITE_DEV_MODE
RUN npm run build

FROM nginx:1.27-alpine

ARG VITE_API_URL=""

COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY deploy/nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
# CSP: фронтенду можно ходить только к своему домену и к API
RUN sed -i "s|connect-src 'self'|connect-src 'self' ${VITE_API_URL}|" /etc/nginx/snippets/security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
