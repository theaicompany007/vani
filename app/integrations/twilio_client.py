"""Twilio WhatsApp integration"""
import os
import logging
from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

logger = logging.getLogger(__name__)


class TwilioClient:
    """Twilio WhatsApp client wrapper"""
    
    def __init__(self):
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        # Support WhatsApp Sandbox (free account)
        # Priority: TWILIO_SANDBOX_WHATSAPP_NUMBER > TWILIO_WHATSAPP_NUMBER
        whatsapp_number = os.getenv('TWILIO_SANDBOX_WHATSAPP_NUMBER') or os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        if not all([account_sid, auth_token]):
            raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN required in environment variables")
        
        if not whatsapp_number:
            raise ValueError("TWILIO_WHATSAPP_NUMBER or TWILIO_SANDBOX_WHATSAPP_NUMBER required")
        
        self.client = Client(account_sid, auth_token)
        # Ensure whatsapp: prefix
        if not whatsapp_number.startswith('whatsapp:'):
            whatsapp_number = f'whatsapp:{whatsapp_number}'
        self.whatsapp_number = whatsapp_number
        self.webhook_base_url = os.getenv('WEBHOOK_BASE_URL', '')
        
        # Log which number is being used
        if os.getenv('TWILIO_SANDBOX_WHATSAPP_NUMBER'):
            logger.info(f"Using WhatsApp Sandbox number: {self.whatsapp_number}")
        else:
            logger.info(f"Using WhatsApp number: {self.whatsapp_number}")
        
    def send_whatsapp(
        self,
        to: str,
        message: str,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send WhatsApp message via Twilio
        
        Args:
            to: Recipient phone number (format: whatsapp:+1234567890)
            message: Message text
            media_url: Optional media URL
            
        Returns:
            Response dict with message SID and status
        """
        try:
            # Ensure to number has whatsapp: prefix
            if not to.startswith('whatsapp:'):
                to = f'whatsapp:{to}'
            
            params = {
                'from': self.whatsapp_number,
                'to': to,
                'body': message
            }
            
            if media_url:
                params['media_url'] = [media_url]
            
            # Add status callback URL if configured
            if self.webhook_base_url:
                params['status_callback'] = f"{self.webhook_base_url}/api/webhooks/twilio"
            
            message_obj = self.client.messages.create(**params)
            
            logger.info(f"WhatsApp message sent successfully to {to}, SID: {message_obj.sid}")
            return {
                'success': True,
                'message_sid': message_obj.sid,
                'status': message_obj.status,
                'response': {
                    'sid': message_obj.sid,
                    'status': message_obj.status,
                    'date_created': str(message_obj.date_created),
                    'date_sent': str(message_obj.date_sent) if message_obj.date_sent else None,
                }
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error sending WhatsApp to {to}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': e.code if hasattr(e, 'code') else None
            }
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {to}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_message(self, message_sid: str) -> Dict[str, Any]:
        """Get message details by SID"""
        try:
            message = self.client.messages(message_sid).fetch()
            return {
                'success': True,
                'data': {
                    'sid': message.sid,
                    'status': message.status,
                    'body': message.body,
                    'from': message.from_,
                    'to': message.to,
                    'date_created': str(message.date_created),
                    'date_sent': str(message.date_sent) if message.date_sent else None,
                }
            }
        except Exception as e:
            logger.error(f"Failed to get message {message_sid}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


