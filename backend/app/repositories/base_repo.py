from sqlalchemy.ext.asyncio import AsyncSession


def like_pattern(text: str) -> str:
    """Подстрока для ILIKE: экранируем % и _, чтобы они искались как обычные символы."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
