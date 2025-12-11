"""Import job model for tracking background contact imports"""
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ImportJob:
    """Model for import job status"""
    
    def __init__(
        self,
        id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: str = 'pending',
        total_records: int = 0,
        processed_records: int = 0,
        imported_count: int = 0,
        error_count: int = 0,
        skipped_count: int = 0,
        error_details: Optional[list] = None,
        created_at: Optional[Any] = None,  # Can be datetime or string
        started_at: Optional[Any] = None,  # Can be datetime or string
        completed_at: Optional[Any] = None,  # Can be datetime or string
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
        progress_message: Optional[str] = None,
        industry_id: Optional[str] = None
    ):
        self.id = id
        self.user_id = user_id
        self.status = status
        self.total_records = total_records
        self.processed_records = processed_records
        self.imported_count = imported_count
        self.error_count = error_count
        self.skipped_count = skipped_count
        self.error_details = error_details or []
        self.created_at = created_at
        self.started_at = started_at
        self.completed_at = completed_at
        self.file_name = file_name
        self.file_size = file_size
        self.options = options or {}
        self.progress_message = progress_message
        self.industry_id = industry_id
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImportJob':
        """Create ImportJob from dictionary"""
        return cls(
            id=str(data.get('id', '')),
            user_id=str(data.get('user_id', '')) if data.get('user_id') else None,
            status=data.get('status', 'pending'),
            total_records=data.get('total_records', 0),
            processed_records=data.get('processed_records', 0),
            imported_count=data.get('imported_count', 0),
            error_count=data.get('error_count', 0),
            skipped_count=data.get('skipped_count', 0),
            error_details=data.get('error_details', []),
            created_at=data.get('created_at'),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at'),
            file_name=data.get('file_name'),
            file_size=data.get('file_size'),
            options=data.get('options', {}),
            progress_message=data.get('progress_message'),
            industry_id=str(data.get('industry_id', '')) if data.get('industry_id') else None
        )
    
    def _format_datetime(self, dt):
        """Format datetime to ISO string, handling both datetime objects and strings"""
        if dt is None:
            return None
        if isinstance(dt, str):
            return dt  # Already a string, return as-is
        if isinstance(dt, datetime):
            return dt.isoformat()
        return str(dt)  # Fallback for other types
    
    @classmethod
    def _parse_datetime(cls, value):
        """Parse datetime from string or return datetime object"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                # Try parsing ISO format
                from dateutil import parser
                return parser.parse(value)
            except:
                # If parsing fails, return as string (will be handled in to_dict)
                return value
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ImportJob to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'total_records': self.total_records,
            'processed_records': self.processed_records,
            'imported_count': self.imported_count,
            'error_count': self.error_count,
            'skipped_count': self.skipped_count,
            'error_details': self.error_details,
            'created_at': self._format_datetime(self.created_at),
            'started_at': self._format_datetime(self.started_at),
            'completed_at': self._format_datetime(self.completed_at),
            'file_name': self.file_name,
            'file_size': self.file_size,
            'options': self.options,
            'progress_message': self.progress_message,
            'industry_id': self.industry_id,
            'progress_percent': int((self.processed_records / self.total_records * 100)) if self.total_records > 0 else 0
        }

