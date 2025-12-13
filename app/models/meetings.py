"""Meeting models"""
from typing import Optional, Dict, Any
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
    target_id: Optional[str] = None
    cal_event_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    meeting_url: Optional[str] = None
    status: str = "scheduled"
    notes: Optional[str] = None
    meeting_type: Optional[str] = None  # 15min, 30min, 60min
    end_at: Optional[datetime] = None
    booking_id: Optional[str] = None
    booking_url: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Related data (from joins)
    targets: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True

    def to_dict(self) -> dict:
        """Convert to dictionary for Supabase"""
        data = self.dict(exclude_none=True)
        if self.id:
            data['id'] = str(self.id) if isinstance(self.id, str) else self.id
        if self.target_id:
            data['target_id'] = str(self.target_id) if isinstance(self.target_id, str) else self.target_id
        # Convert datetime to ISO strings
        if self.scheduled_at and isinstance(self.scheduled_at, datetime):
            data['scheduled_at'] = self.scheduled_at.isoformat()
        if self.end_at and isinstance(self.end_at, datetime):
            data['end_at'] = self.end_at.isoformat()
        if self.cancelled_at and isinstance(self.cancelled_at, datetime):
            data['cancelled_at'] = self.cancelled_at.isoformat()
        if self.created_at and isinstance(self.created_at, datetime):
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at and isinstance(self.updated_at, datetime):
            data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Meeting':
        """Create from Supabase dictionary"""
        # Handle nested data from joins
        if 'targets' in data and isinstance(data['targets'], dict):
            # Keep targets as-is for frontend
            pass
        
        # Convert string IDs to strings
        if 'id' in data:
            data['id'] = str(data['id'])
        if 'target_id' in data and data['target_id']:
            data['target_id'] = str(data['target_id'])
        
        # Handle datetime strings
        for field in ['scheduled_at', 'end_at', 'cancelled_at', 'created_at', 'updated_at']:
            if field in data and data[field] and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
        
        return cls(**data)


