"""
Ограничение частоты попыток (вход, регистрация) — скользящее окно в памяти процесса.

Защищает от перебора паролей и от нагрузки bcrypt'ом. Счётчики живут в воркере:
при N воркерах uvicorn реальный лимит до N раз выше — для перебора этого достаточно.
Если понадобится общий лимит на несколько серверов — перенести в Redis.
"""

import time
from collections import deque

# Чистим устаревшие ключи, когда их накопилось столько
PRUNE_THRESHOLD = 10_000


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = {}

    def is_blocked(self, key: str) -> bool:
        return len(self._actual(key)) >= self.limit

    def hit(self, key: str) -> None:
        if len(self._hits) > PRUNE_THRESHOLD:
            self._prune()
        self._actual(key).append(time.monotonic())

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)

    def _actual(self, key: str) -> deque[float]:
        hits = self._hits.setdefault(key, deque())
        border = time.monotonic() - self.window
        while hits and hits[0] < border:
            hits.popleft()
        return hits

    def _prune(self) -> None:
        for key in list(self._hits):
            if not self._actual(key):
                del self._hits[key]
