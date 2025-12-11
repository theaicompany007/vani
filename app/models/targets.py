"""Target data models"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

# Use str for email to avoid email-validator dependency issues
# Email validation can be done at API level if needed


class TargetStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    MEETING_SCHEDULED = "meeting_scheduled"
    CONVERTED = "converted"
    NOT_INTERESTED = "not_interested"


class Target(BaseModel):
    """Target contact model"""
    id: Optional[str] = None
    company_name: str
    contact_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    pain_point: Optional[str] = None
    pitch_angle: Optional[str] = None
    script: Optional[str] = None
    status: TargetStatus = TargetStatus.NEW
    industry_id: Optional[str] = None  # Industry assignment
    contact_id: Optional[str] = None  # Link to contact
    company_id: Optional[str] = None  # Link to company
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True

    def to_dict(self) -> dict:
        """Convert to dictionary for Supabase"""
        data = self.dict(exclude_none=True)
        if self.id:
            data['id'] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Target':
        """Create from Supabase dictionary"""
        # Create a copy to avoid modifying the original
        target_data = dict(data)
        
        # Convert UUID fields to strings
        if 'id' in target_data and target_data['id']:
            target_data['id'] = str(target_data['id'])
        if 'industry_id' in target_data and target_data['industry_id']:
            target_data['industry_id'] = str(target_data['industry_id'])
        if 'contact_id' in target_data and target_data['contact_id']:
            target_data['contact_id'] = str(target_data['contact_id'])
        if 'company_id' in target_data and target_data['company_id']:
            target_data['company_id'] = str(target_data['company_id'])
        
        # Filter out fields that aren't in the model (like nested contacts/companies)
        model_fields = cls.__fields__.keys()
        filtered_data = {k: v for k, v in target_data.items() if k in model_fields}
        
        return cls(**filtered_data)


