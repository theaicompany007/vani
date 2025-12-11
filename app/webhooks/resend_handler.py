"""Resend webhook handler"""
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime
from app.supabase_client import get_supabase_client
from app.models.outreach import ActivityStatus
from app.models.webhooks import WebhookEvent, WebhookSource
from app.notifications import send_hit_notification

logger = logging.getLogger(__name__)

resend_webhook_bp = Blueprint('resend_webhook', __name__)


@resend_webhook_bp.route('/api/webhooks/resend', methods=['POST'])
def handle_resend_webhook():
    """Handle Resend webhook events"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        event_type = data.get('type')
        email_data = data.get('data', {})
        email_id = email_data.get('email_id') or email_data.get('id')
        
        logger.info(f"Received Resend webhook: {event_type} for email {email_id}")
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Find activity by external_id (email_id)
        activity = None
        if email_id:
            response = supabase.table('outreach_activities').select('*').eq('external_id', email_id).execute()
            if response.data:
                activity = response.data[0]
        
        # Save webhook event
        webhook_event = WebhookEvent(
            source=WebhookSource.RESEND,
            event_type=event_type,
            payload=data,
            activity_id=activity['id'] if activity else None
        )
        webhook_dict = webhook_event.to_dict()
        webhook_dict.pop('id', None)
        supabase.table('webhook_events').insert(webhook_dict).execute()
        
        # Update activity status based on event type
        if activity:
            status_updates = {}
            is_hit = False
            
            if event_type == 'email.sent':
                status_updates['status'] = ActivityStatus.SENT.value
            elif event_type == 'email.delivered':
                status_updates['status'] = ActivityStatus.DELIVERED.value
            elif event_type == 'email.opened':
                status_updates['status'] = ActivityStatus.OPENED.value
                status_updates['opened_at'] = datetime.utcnow().isoformat()
                is_hit = True  # Email opened is a HIT
            elif event_type == 'email.clicked':
                status_updates['status'] = ActivityStatus.CLICKED.value
                status_updates['clicked_at'] = datetime.utcnow().isoformat()
                is_hit = True  # Link clicked is a HIT
            elif event_type == 'email.bounced':
                status_updates['status'] = ActivityStatus.BOUNCED.value
            elif event_type == 'email.complained':
                status_updates['status'] = ActivityStatus.FAILED.value
            
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
                        event_type=event_type,
                        target_name=target.get('company_name', 'Unknown'),
                        contact_name=target.get('contact_name', ''),
                        channel='email',
                        details=f"Email {event_type.replace('email.', '')}"
                    )
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error handling Resend webhook: {e}")
        return jsonify({'error': str(e)}), 500


