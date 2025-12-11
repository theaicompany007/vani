"""Resend email integration"""
import os
import logging
from typing import Optional, Dict, Any
import resend

logger = logging.getLogger(__name__)


class ResendClient:
    """Resend email client wrapper"""
    
    def __init__(self):
        api_key = os.getenv('RESEND_API_KEY')
        if not api_key:
            raise ValueError("RESEND_API_KEY not found in environment variables")
        
        # Resend 2.0.0 uses module-level API key setting
        resend.api_key = api_key
        self.from_email = os.getenv('RESEND_FROM_EMAIL', 'noreply@example.com')
        self.from_name = os.getenv('RESEND_FROM_NAME', 'Project VANI')
        self.webhook_base_url = os.getenv('WEBHOOK_BASE_URL', '')
        
    def send_email(
        self,
        to: str,
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Send email via Resend
        
        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML content
            text: Plain text content
            reply_to: Reply-to email address
            tags: List of tags for tracking
            
        Returns:
            Response dict with email ID and status
        """
        try:
            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to],
                "subject": subject,
            }
            
            if html:
                params["html"] = html
            if text:
                params["text"] = text
            if reply_to:
                params["reply_to"] = reply_to
            if tags:
                params["tags"] = tags
            
            # Add webhook URL if configured
            if self.webhook_base_url:
                params["headers"] = {
                    "X-Webhook-URL": f"{self.webhook_base_url}/api/webhooks/resend"
                }
            
            # Resend 2.0.0 API - send() takes SendParams object
            # Create SendParams from dict (or pass dict directly if supported)
            try:
                send_params = resend.Emails.SendParams(**params)
                response = resend.Emails.send(send_params)
            except TypeError:
                # Fallback: try passing dict directly
                response = resend.Emails.send(params)
            
            logger.info(f"Email sent successfully to {to}, ID: {response.get('id')}")
            return {
                'success': True,
                'email_id': response.get('id'),
                'response': response
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_email(self, email_id: str) -> Dict[str, Any]:
        """Get email details by ID"""
        try:
            # Resend 2.0.0 API
            response = resend.Emails.get(email_id=email_id)
            return {
                'success': True,
                'data': response
            }
        except Exception as e:
            logger.error(f"Failed to get email {email_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


