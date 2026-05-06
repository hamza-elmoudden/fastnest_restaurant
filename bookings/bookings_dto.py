from typing import Optional, List
from pydantic import BaseModel, field_validator


class CreateBookingDto(BaseModel):
    table_id:  str
    booked_at: str
    guests:    int = 1
    notes:     Optional[str] = None
    plates:    List[dict] = []

    @field_validator("guests")
    @classmethod
    def guests_positive(cls, v):
        if v < 1:
            raise ValueError("At least 1 guest required")
        return v
