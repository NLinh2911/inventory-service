# Pydantic models for request/response validation, keep separate from database models

from pydantic import BaseModel, Field
from typing import Optional


class UnitOfMeasureCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    abbreviation: str = Field(..., min_length=1, max_length=10)
    description: str = Field(..., min_length=1, max_length=255)


class UnitOfMeasureReadRequest(BaseModel):
    uom_id: int
    name: str
    abbreviation: str
    description: str

    class Config:
        from_attributes = True  # Enables compatibility with SQLAlchemy models


class UnitOfMeasureUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    abbreviation: Optional[str] = Field(None, min_length=1, max_length=10)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
