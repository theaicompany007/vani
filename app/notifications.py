"""HIT notification system"""
import os
import logging
from typing import Optional
from app.integrations.resend_client import ResendClient
from app.integrations.twilio_client import TwilioClient

logger = logging.getLogger(__name__)


def send_hit_notification(
    event_type: str,
    target_name: str,
    contact_name: Optional[str] = None,
    channel: str = 'email',
    details: Optional[str] = None
):
    """
    Send HIT notification via Email and WhatsApp
    
    Args:
        event_type: Type of event (opened, clicked, replied, etc.)
        target_name: Company name
        contact_name: Contact person name
        channel: Outreach channel (email, whatsapp)
        details: Additional details
    """
    try:
        notification_email = os.getenv('NOTIFICATION_EMAIL')
        notification_whatsapp = os.getenv('NOTIFICATION_WHATSAPP')
        
        if not notification_email and not notification_whatsapp:
            logger.warning("No notification recipients configured")
            return
        
        # Prepare notification message
        contact_info = f" ({contact_name})" if contact_name else ""
        message = f"🎯 HIT Alert!\n\n"
        message += f"Event: {event_type}\n"
        message += f"Target: {target_name}{contact_info}\n"
        message += f"Channel: {channel}\n"
        if details:
            message += f"Details: {details}\n"
        message += f"\nCheck the command center for more details."
        
        # Send email notification
        if notification_email:
            try:
                resend_client = ResendClient()
                resend_client.send_email(
                    to=notification_email,
                    subject=f"🎯 HIT: {target_name} - {event_type}",
                    text=message
                )
                logger.info(f"HIT notification email sent to {notification_email}")
            except Exception as e:
                logger.error(f"Failed to send HIT email notification: {e}")
        
        # Send WhatsApp notification
        if notification_whatsapp:
            try:
                twilio_client = TwilioClient()
                twilio_client.send_whatsapp(
                    to=notification_whatsapp,
                    message=message
                )
                logger.info(f"HIT notification WhatsApp sent to {notification_whatsapp}")
            except Exception as e:
                logger.error(f"Failed to send HIT WhatsApp notification: {e}")
        
    except Exception as e:
        logger.error(f"Error sending HIT notification: {e}")


