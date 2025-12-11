"""Meeting models"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Meeting(BaseModel):
    """Cal.com meeting model"""
    id: Optional[str] = None
    target_id: str
    cal_event_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    meeting_url: Optional[str] = None
    status: MeetingStatus = MeetingStatus.SCHEDULED
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True

    def to_dict(self) -> dict:
        """Convert to dictionary for Supabase"""
        data = self.dict(exclude_none=True)
        if self.id:
            data['id'] = self.id
        if self.target_id:
            data['target_id'] = self.target_id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Meeting':
        """Create from Supabase dictionary"""
        if 'id' in data:
            data['id'] = str(data['id'])
        if 'target_id' in data:
            data['target_id'] = str(data['target_id'])
        return cls(**data)


