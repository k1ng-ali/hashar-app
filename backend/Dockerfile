FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости отдельно (кэш Docker слоёв). В образ — только прод-зависимости
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Не запускаем приложение от root
RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# --proxy-headers: реальный IP клиента из X-Forwarded-For (его ставит Caddy) — нужен лимиту попыток входа
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*", "--workers", "2"]
