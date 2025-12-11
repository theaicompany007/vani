"""Cal.com meeting scheduling integration"""
import os
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CalComClient:
    """Cal.com API client wrapper"""
    
    def __init__(self):
        self.api_key = os.getenv('CAL_COM_API_KEY')
        self.username = os.getenv('CAL_COM_USERNAME')
        self.base_url = os.getenv('CAL_COM_BASE_URL', 'https://api.cal.com')
        # Support both CAL_COM_WEBHOOK_SECRET and CAL_COM_WEBHOOK_SECRET_PROD
        self.webhook_secret = os.getenv('CAL_COM_WEBHOOK_SECRET') or os.getenv('CAL_COM_WEBHOOK_SECRET_PROD', '')
        
        if not self.api_key:
            raise ValueError("CAL_COM_API_KEY not found in environment variables")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_booking_link(
        self,
        event_type_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a booking link for scheduling
        
        Args:
            event_type_id: Cal.com event type ID
            name: Event name
            description: Event description
            
        Returns:
            Response dict with booking link
        """
        try:
            # If username is provided, construct booking URL
            if self.username:
                booking_url = f"https://cal.com/{self.username}"
                if event_type_id:
                    booking_url += f"/{event_type_id}"
                
                return {
                    'success': True,
                    'booking_url': booking_url,
                    'username': self.username
                }
            
            # Otherwise, use API to create booking
            url = f"{self.base_url}/v1/bookings"
            # Cal.com API implementation would go here
            # For now, return basic booking URL
            
            return {
                'success': True,
                'booking_url': f"https://cal.com/{self.username}",
                'username': self.username
            }
            
        except Exception as e:
            logger.error(f"Failed to create booking link: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_bookings(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get scheduled bookings
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            List of bookings
        """
        try:
            url = f"{self.base_url}/v1/bookings"
            params = {}
            
            if start_time:
                params['startTime'] = start_time.isoformat()
            if end_time:
                params['endTime'] = end_time.isoformat()
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return {
                'success': True,
                'bookings': response.json()
            }
            
        except Exception as e:
            logger.error(f"Failed to get bookings: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_booking(self, booking_id: str) -> Dict[str, Any]:
        """Get specific booking by ID"""
        try:
            url = f"{self.base_url}/v1/bookings/{booking_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return {
                'success': True,
                'booking': response.json()
            }
            
        except Exception as e:
            logger.error(f"Failed to get booking {booking_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


