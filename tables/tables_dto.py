from typing import Optional
from pydantic import BaseModel


class UpdateTableDto(BaseModel):
    status:   Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None
