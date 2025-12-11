"""Contact data models"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class Contact(BaseModel):
    id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    name: str = Field(..., min_length=1)
    role: Optional[str] = None
    email: Optional[EmailStr] = None
    linkedin: Optional[str] = None
    phone: Optional[str] = None
    lead_source: Optional[str] = None
    company: Optional[str] = None  # Company name as text (for backward compatibility)
    city: Optional[str] = None
    industry: Optional[str] = None
    sheet: Optional[str] = None  # Excel sheet name
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








