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
    
    def create_booking(
        self,
        start_time: datetime,
        attendee_email: str,
        event_type_id: Optional[int] = None,
        end_time: Optional[datetime] = None,
        attendee_name: Optional[str] = None,
        notes: Optional[str] = None,
        timezone: str = 'UTC'
    ) -> Dict[str, Any]:
        """
        Create a booking via Cal.com API
        
        Args:
            event_type_id: Cal.com event type ID
            start_time: Meeting start time
            end_time: Meeting end time (optional, defaults to start_time + duration)
            attendee_email: Attendee email address
            attendee_name: Attendee name
            notes: Additional notes
            timezone: Timezone (default: UTC)
            
        Returns:
            Response dict with booking details
        """
        try:
            # Calculate end_time if not provided (default 30 minutes)
            if not end_time:
                from datetime import timedelta
                end_time = start_time + timedelta(minutes=30)
            
            # Prepare booking payload
            payload = {
                'eventTypeId': event_type_id,
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'responses': {
                    'email': attendee_email,
                    'name': attendee_name or attendee_email,
                    'notes': notes or ''
                },
                'timeZone': timezone,
                'language': 'en'
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            url = f"{self.base_url}/v1/bookings"
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            booking_data = response.json()
            
            return {
                'success': True,
                'booking': booking_data,
                'booking_id': booking_data.get('id'),
                'meeting_url': booking_data.get('meetingUrl') or booking_data.get('meeting_url'),
                'booking_url': booking_data.get('bookingUrl') or booking_data.get('booking_url')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Cal.com API error creating booking: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    return {
                        'success': False,
                        'error': error_detail.get('message', str(e)),
                        'details': error_detail
                    }
                except:
                    return {
                        'success': False,
                        'error': f"HTTP {e.response.status_code}: {e.response.text}"
                    }
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Failed to create booking: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_available_slots(
        self,
        event_type_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get available time slots for booking
        
        Args:
            event_type_id: Cal.com event type ID
            date_from: Start date for availability
            date_to: End date for availability
            
        Returns:
            Response dict with available slots
        """
        try:
            # Use Cal.com availability endpoint
            url = f"{self.base_url}/v1/availability"
            params = {}
            
            if event_type_id:
                params['eventTypeId'] = event_type_id
            if date_from:
                params['dateFrom'] = date_from.isoformat()
            if date_to:
                params['dateTo'] = date_to.isoformat()
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'slots': response.json()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Cal.com API error getting available slots: {e}")
            # If API endpoint doesn't exist, return empty slots (user can manually select time)
            return {
                'success': True,
                'slots': [],
                'note': 'Availability API not available, please select time manually'
            }
        except Exception as e:
            logger.error(f"Failed to get available slots: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_booking(self, booking_id: str) -> Dict[str, Any]:
        """
        Cancel a booking
        
        Args:
            booking_id: Cal.com booking ID
            
        Returns:
            Response dict with cancellation status
        """
        try:
            url = f"{self.base_url}/v1/bookings/{booking_id}"
            response = requests.delete(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'message': 'Booking cancelled successfully'
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Cal.com API error cancelling booking: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    return {
                        'success': False,
                        'error': error_detail.get('message', str(e))
                    }
                except:
                    return {
                        'success': False,
                        'error': f"HTTP {e.response.status_code}: {e.response.text}"
                    }
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Failed to cancel booking: {str(e)}")
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


