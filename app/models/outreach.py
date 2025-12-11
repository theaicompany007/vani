"""Outreach activity models"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"


class ActivityStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"


class OutreachActivity(BaseModel):
    """Individual outreach activity model"""
    id: Optional[str] = None
    target_id: str
    sequence_id: Optional[str] = None
    channel: Channel
    step_number: int = 1
    message_content: Optional[str] = None
    sent_at: Optional[datetime] = None
    status: ActivityStatus = ActivityStatus.PENDING
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    external_id: Optional[str] = None  # Resend email ID, Twilio SID, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)
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
        if self.sequence_id:
            data['sequence_id'] = self.sequence_id
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'OutreachActivity':
        """Create from Supabase dictionary"""
        if 'id' in data:
            data['id'] = str(data['id'])
        if 'target_id' in data:
            data['target_id'] = str(data['target_id'])
        if 'sequence_id' in data:
            data['sequence_id'] = str(data['sequence_id'])
        return cls(**data)


class SequenceStep(BaseModel):
    """Step in an outreach sequence"""
    step_number: int
    channel: Channel
    delay_hours: int = 24
    template: str
    subject: Optional[str] = None  # For email


class OutreachSequence(BaseModel):
    """Multi-step outreach sequence model"""
    id: Optional[str] = None
    name: str
    channels: List[Channel] = Field(default_factory=list)
    steps: List[Dict[str, Any]] = Field(default_factory=list)  # JSONB in DB
    delay_between_steps: int = 24  # hours
    total_duration: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        use_enum_values = True

    def to_dict(self) -> dict:
        """Convert to dictionary for Supabase"""
        data = self.dict(exclude_none=True)
        if self.id:
            data['id'] = self.id
        # Convert channels to array
        data['channels'] = [c.value if isinstance(c, Channel) else c for c in self.channels]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'OutreachSequence':
        """Create from Supabase dictionary"""
        if 'id' in data:
            data['id'] = str(data['id'])
        # Convert channels from array
        if 'channels' in data and isinstance(data['channels'], list):
            data['channels'] = [Channel(c) if isinstance(c, str) else c for c in data['channels']]
        return cls(**data)


