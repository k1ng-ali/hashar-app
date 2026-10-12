from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.formatting import format_phone


class EmergencyContactIn(BaseModel):
    title: str = Field(min_length=2, max_length=100)  # «Медпункт», «Пожарная»
    phone: str = Field(min_length=5, max_length=30)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        return value.strip()

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return format_phone(value)


class EmergencyContactOut(BaseModel):
    id: int
    title: str
    phone: str

    model_config = ConfigDict(from_attributes=True)
