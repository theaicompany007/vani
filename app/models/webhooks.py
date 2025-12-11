"""Webhook event models"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class WebhookSource(str, Enum):
    RESEND = "resend"
    TWILIO = "twilio"
    CAL_COM = "cal_com"


class WebhookEvent(BaseModel):
    """Webhook event model"""
    id: Optional[str] = None
    source: WebhookSource
    event_type: str
    payload: Dict[str, Any] = {}
    activity_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        use_enum_values = True

    def to_dict(self) -> dict:
        """Convert to dictionary for Supabase"""
        data = self.dict(exclude_none=True)
        if self.id:
            data['id'] = self.id
        if self.activity_id:
            data['activity_id'] = self.activity_id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'WebhookEvent':
        """Create from Supabase dictionary"""
        if 'id' in data:
            data['id'] = str(data['id'])
        if 'activity_id' in data:
            data['activity_id'] = str(data['activity_id'])
        return cls(**data)


