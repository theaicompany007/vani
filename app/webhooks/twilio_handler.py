"""Twilio webhook handler"""
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime
from app.supabase_client import get_supabase_client
from app.models.outreach import ActivityStatus
from app.models.webhooks import WebhookEvent, WebhookSource
from app.notifications import send_hit_notification

logger = logging.getLogger(__name__)

twilio_webhook_bp = Blueprint('twilio_webhook', __name__)


@twilio_webhook_bp.route('/api/webhooks/twilio', methods=['POST'])
def handle_twilio_webhook():
    """Handle Twilio status callback webhooks"""
    try:
        # Twilio sends form data
        message_sid = request.form.get('MessageSid')
        message_status = request.form.get('MessageStatus')
        
        logger.info(f"Received Twilio webhook: {message_status} for message {message_sid}")
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Find activity by external_id (message_sid)
        activity = None
        if message_sid:
            response = supabase.table('outreach_activities').select('*').eq('external_id', message_sid).execute()
            if response.data:
                activity = response.data[0]
        
        # Save webhook event
        webhook_data = dict(request.form)
        webhook_event = WebhookEvent(
            source=WebhookSource.TWILIO,
            event_type=message_status,
            payload=webhook_data,
            activity_id=activity['id'] if activity else None
        )
        webhook_dict = webhook_event.to_dict()
        webhook_dict.pop('id', None)
        supabase.table('webhook_events').insert(webhook_dict).execute()
        
        # Update activity status
        if activity:
            status_updates = {}
            is_hit = False
            
            if message_status == 'sent':
                status_updates['status'] = ActivityStatus.SENT.value
            elif message_status == 'delivered':
                status_updates['status'] = ActivityStatus.DELIVERED.value
            elif message_status == 'read':
                status_updates['status'] = ActivityStatus.OPENED.value
                status_updates['opened_at'] = datetime.utcnow().isoformat()
                is_hit = True  # Message read is a HIT
            elif message_status == 'failed':
                status_updates['status'] = ActivityStatus.FAILED.value
            elif message_status == 'undelivered':
                status_updates['status'] = ActivityStatus.BOUNCED.value
            
            if status_updates:
                status_updates['updated_at'] = datetime.utcnow().isoformat()
                supabase.table('outreach_activities').update(status_updates).eq('id', activity['id']).execute()
            
            # Send HIT notification if applicable
            if is_hit:
                # Get target info
                target_response = supabase.table('targets').select('*').eq('id', activity['target_id']).execute()
                if target_response.data:
                    target = target_response.data[0]
                    send_hit_notification(
                        event_type=message_status,
                        target_name=target.get('company_name', 'Unknown'),
                        contact_name=target.get('contact_name', ''),
                        channel='whatsapp',
                        details=f"WhatsApp message {message_status}"
                    )
        
        # Twilio expects TwiML response or 200 OK
        return '', 200
        
    except Exception as e:
        logger.error(f"Error handling Twilio webhook: {e}")
        return jsonify({'error': str(e)}), 500


