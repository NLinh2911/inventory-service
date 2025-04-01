# Pydantic models for request/response validation, keep separate from database models

from pydantic import BaseModel, Field
from typing import Optional


class VendorCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=255)


class VendorReadRequest(BaseModel):
    vendor_id: int
    name: str
    description: str

    class Config:
        from_attributes = True  # Enables compatibility with SQLAlchemy models


class VendorUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
