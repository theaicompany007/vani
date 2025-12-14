"""Company data models"""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class Company(BaseModel):
    id: Optional[UUID] = None
    name: str = Field(..., min_length=1)
    domain: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda dt: dt.isoformat()
        }

    def to_dict(self):
        return self.model_dump(mode='json', exclude_none=True)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)



















