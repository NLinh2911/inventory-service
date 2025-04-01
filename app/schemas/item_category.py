# Pydantic models for request/response validation, keep separate from database models

from pydantic import BaseModel, Field
from typing import Optional


class ItemCategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=255)


class ItemCategoryReadRequest(BaseModel):
    category_id: int
    name: str
    description: str

    class Config:
        from_attributes = True  # Enables compatibility with SQLAlchemy models


class ItemCategoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
