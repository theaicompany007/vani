"""Cal.com webhook handler"""
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime
from app.supabase_client import get_supabase_client
from app.models.meetings import MeetingStatus
from app.models.webhooks import WebhookEvent, WebhookSource
from app.notifications import send_hit_notification
import os
import hmac
import hashlib

logger = logging.getLogger(__name__)

cal_com_webhook_bp = Blueprint('cal_com_webhook', __name__)


def verify_cal_com_signature(payload: bytes, signature: str) -> bool:
    """Verify Cal.com webhook signature"""
    webhook_secret = os.getenv('CAL_COM_WEBHOOK_SECRET') or os.getenv('CAL_COM_WEBHOOK_SECRET_PROD', '')
    if not webhook_secret:
        logger.warning("CAL_COM_WEBHOOK_SECRET not set - skipping signature verification")
        return True  # Allow if secret not configured
    
    try:
        # Cal.com uses HMAC SHA256
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant-time comparison)
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Error verifying Cal.com signature: {e}")
        return False


@cal_com_webhook_bp.route('/api/webhooks/cal-com', methods=['POST'])
def handle_cal_com_webhook():
    """Handle Cal.com webhook events"""
    try:
        # Get raw payload for signature verification
        raw_payload = request.get_data()
        
        # Verify signature if secret is configured
        signature = request.headers.get('X-Cal-Signature-256') or request.headers.get('cal-signature')
        if signature and not verify_cal_com_signature(raw_payload, signature):
            logger.warning("Invalid Cal.com webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse JSON payload
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Cal.com webhook event structure
        # Event types: BOOKING_CREATED, BOOKING_CANCELLED, BOOKING_RESCHEDULED, etc.
        event_type = data.get('triggerEvent') or data.get('type') or data.get('event')
        booking_data = data.get('payload', {}) or data.get('data', {}) or data
        
        # Extract booking ID
        booking_id = booking_data.get('uid') or booking_data.get('id') or booking_data.get('bookingId')
        
        logger.info(f"Received Cal.com webhook: {event_type} for booking {booking_id}")
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Find meeting by cal_event_id (Cal.com booking ID is stored in cal_event_id)
        meeting = None
        if booking_id:
            response = supabase.table('meetings').select('*').eq('cal_event_id', str(booking_id)).execute()
            
            if response.data:
                meeting = response.data[0]
                logger.info(f"Found meeting {meeting.get('id')} for booking {booking_id}")
            else:
                logger.warning(f"No meeting found for cal_event_id: {booking_id}")
                logger.debug(f"Available cal_event_ids in database: {[m.get('cal_event_id') for m in supabase.table('meetings').select('cal_event_id').limit(10).execute().data]}")
        
        # Save webhook event
        webhook_event = WebhookEvent(
            source=WebhookSource.CAL_COM,
            event_type=event_type or 'unknown',
            payload=data,
            activity_id=None  # Meetings are not outreach activities
        )
        webhook_dict = webhook_event.to_dict()
        webhook_dict.pop('id', None)
        supabase.table('webhook_events').insert(webhook_dict).execute()
        
        # Update meeting status based on event type
        if meeting:
            status_updates = {}
            is_hit = False
            
            # Map Cal.com events to meeting statuses
            if event_type in ['BOOKING_CREATED', 'BOOKING_REQUESTED']:
                status_updates['status'] = MeetingStatus.SCHEDULED.value
                # Update booking details if available
                if booking_data.get('startTime'):
                    try:
                        start_time = datetime.fromisoformat(booking_data['startTime'].replace('Z', '+00:00'))
                        status_updates['scheduled_at'] = start_time.isoformat()
                    except (ValueError, AttributeError):
                        pass
                if booking_data.get('endTime'):
                    try:
                        end_time = datetime.fromisoformat(booking_data['endTime'].replace('Z', '+00:00'))
                        status_updates['end_at'] = end_time.isoformat()
                    except (ValueError, AttributeError):
                        pass
                if booking_data.get('location') or booking_data.get('meetingUrl'):
                    status_updates['meeting_url'] = booking_data.get('meetingUrl') or booking_data.get('location', '')
                if booking_data.get('title'):
                    status_updates['notes'] = booking_data.get('title')
                    
            elif event_type == 'BOOKING_CANCELLED':
                status_updates['status'] = MeetingStatus.CANCELLED.value
                status_updates['cancelled_at'] = datetime.utcnow().isoformat()
                
            elif event_type == 'BOOKING_RESCHEDULED':
                status_updates['status'] = MeetingStatus.SCHEDULED.value
                # Update times if provided
                if booking_data.get('startTime'):
                    try:
                        start_time = datetime.fromisoformat(booking_data['startTime'].replace('Z', '+00:00'))
                        status_updates['scheduled_at'] = start_time.isoformat()
                    except (ValueError, AttributeError):
                        pass
                if booking_data.get('endTime'):
                    try:
                        end_time = datetime.fromisoformat(booking_data['endTime'].replace('Z', '+00:00'))
                        status_updates['end_at'] = end_time.isoformat()
                    except (ValueError, AttributeError):
                        pass
                    
            elif event_type == 'MEETING_ENDED':
                status_updates['status'] = MeetingStatus.COMPLETED.value
                is_hit = True  # Meeting completed is a HIT
                
            elif event_type == 'BOOKING_NO_SHOW_UPDATED':
                if booking_data.get('noShow', False):
                    status_updates['status'] = MeetingStatus.NO_SHOW.value
                else:
                    status_updates['status'] = MeetingStatus.COMPLETED.value
                    
            elif event_type == 'BOOKING_PAID':
                # Meeting is confirmed and paid
                status_updates['status'] = MeetingStatus.SCHEDULED.value
                is_hit = True  # Payment received is a HIT
                
            elif event_type == 'BOOKING_REJECTED':
                status_updates['status'] = MeetingStatus.CANCELLED.value
                status_updates['cancelled_at'] = datetime.utcnow().isoformat()
            
            if status_updates:
                status_updates['updated_at'] = datetime.utcnow().isoformat()
                supabase.table('meetings').update(status_updates).eq('id', meeting['id']).execute()
                logger.info(f"Updated meeting {meeting['id']} with status: {status_updates.get('status')}")
            
            # Send HIT notification if applicable
            if is_hit:
                # Get target info
                target_id = meeting.get('target_id')
                if target_id:
                    target_response = supabase.table('targets').select('*').eq('id', target_id).execute()
                    if target_response.data:
                        target = target_response.data[0]
                        send_hit_notification(
                            event_type=event_type,
                            target_name=target.get('company_name', 'Unknown'),
                            contact_name=target.get('contact_name', ''),
                            channel='meeting',
                            details=f"Cal.com {event_type.replace('_', ' ').lower()}"
                        )
        else:
            logger.info(f"Webhook received for booking {booking_id} but no matching meeting found in database")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error handling Cal.com webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

