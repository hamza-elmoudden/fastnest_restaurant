from typing import Optional
from pydantic import BaseModel, field_validator


class CreatePlateDto(BaseModel):
    name:        str
    description: Optional[str] = None
    price:       float
    category:    str = "main"
    image_url:   Optional[str] = None

    @field_validator("price")
    @classmethod
    def price_positive(cls, v):
        if v < 0:
            raise ValueError("Price must be >= 0")
        return v

    @field_validator("category")
    @classmethod
    def valid_cat(cls, v):
        if v not in {"starter", "main", "dessert", "drink"}:
            raise ValueError("Invalid category")
        return v
