"""Outreach API routes"""
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime
from app.models.outreach import OutreachActivity, Channel, ActivityStatus
from app.models.targets import Target
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_use_case
from app.integrations.resend_client import ResendClient
from app.integrations.twilio_client import TwilioClient
from app.integrations.linkedin_client import LinkedInClient
from app.utils.signature_formatter import SignatureFormatter
import os

logger = logging.getLogger(__name__)

outreach_bp = Blueprint('outreach', __name__)


def should_exclude_weekend() -> bool:
    """Check if weekends should be excluded"""
    exclude = os.getenv('EXCLUDE_WEEKENDS', 'true').lower() == 'true'
    if exclude:
        today = datetime.now().weekday()  # 5=Saturday, 6=Sunday
        return today >= 5
    return False


@outreach_bp.route('/api/outreach/send', methods=['POST'])
@require_auth
@require_use_case('outreach')
def send_outreach():
    """Send single-channel outreach (email or WhatsApp) with optional preview approval"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        target_id = data.get('target_id')
        channel = data.get('channel')
        message = data.get('message')
        subject = data.get('subject')  # For email
        approved = data.get('approved', True)  # Default to True for backward compatibility
        
        # If not approved, return error
        if not approved:
            return jsonify({
                'error': 'Message not approved for sending',
                'requires_approval': True
            }), 400
        
        if not all([target_id, channel, message]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check weekend exclusion
        if should_exclude_weekend():
            return jsonify({
                'error': 'Outreach excluded on weekends',
                'skipped': True
            }), 200
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get target
        target_response = supabase.table('targets').select('*').eq('id', target_id).execute()
        if not target_response.data:
            return jsonify({'error': 'Target not found'}), 404
        
        target_data = target_response.data[0]
        target = Target.from_dict(target_data)
        
        # If target is linked to contact, use contact's email/phone/linkedin
        contact_id = target_data.get('contact_id')
        if contact_id:
            contact_response = supabase.table('contacts').select('*').eq('id', contact_id).limit(1).execute()
            if contact_response.data:
                contact = contact_response.data[0]
                # Override target fields with contact data
                if contact.get('email'):
                    target.email = contact['email']
                if contact.get('phone'):
                    target.phone = contact['phone']
                if contact.get('linkedin'):
                    target.linkedin_url = contact['linkedin']
                if contact.get('name'):
                    target.contact_name = contact['name']
        
        # Get signature profile (default or first available)
        signature = None
        try:
            # Try to get default signature first
            sig_response = supabase.table('signature_profiles').select('*').eq('is_default', True).limit(1).execute()
            if sig_response.data:
                signature = sig_response.data[0]
            else:
                # Fallback to first available signature
                sig_response = supabase.table('signature_profiles').select('*').limit(1).execute()
                if sig_response.data:
                    signature = sig_response.data[0]
        except Exception as e:
            logger.warning(f"Could not fetch signature profile: {e}")
        
        # Format signature for the channel
        signature_text = ''
        if signature:
            signature_text = SignatureFormatter.format_for_channel(signature, channel)
        
        # Append signature to message
        if signature_text:
            if channel == 'email':
                # For email, we'll add signature as HTML
                # Message will be sent as HTML if signature is present
                pass  # Will be handled in send_email call
            else:
                # For WhatsApp and LinkedIn, append as plain text
                message = f"{message}\n\n{signature_text}"
        
        # Create activity record
        activity = OutreachActivity(
            target_id=target_id,
            channel=Channel(channel),
            message_content=message,
            status=ActivityStatus.PENDING
        )
        
        # Send based on channel
        external_id = None
        if channel == 'email':
            if not target.email:
                return jsonify({'error': 'Target has no email address'}), 400
            
            resend_client = ResendClient()
            
            # For email, use HTML if signature is present, otherwise plain text
            if signature_text:
                # Convert message to HTML and append signature
                html_message = _text_to_html(message)
                html_message += signature_text
                result = resend_client.send_email(
                    to=target.email,
                    subject=subject or 'Project VANI - Outreach',
                    html=html_message,
                    text=message  # Plain text fallback
                )
            else:
                result = resend_client.send_email(
                    to=target.email,
                    subject=subject or 'Project VANI - Outreach',
                    text=message
                )
            
            if result['success']:
                external_id = result.get('email_id')
                activity.status = ActivityStatus.SENT
                activity.sent_at = datetime.utcnow()
            else:
                activity.status = ActivityStatus.FAILED
                return jsonify({'error': result.get('error')}), 500
        
        elif channel == 'whatsapp':
            if not target.phone:
                return jsonify({'error': 'Target has no phone number'}), 400
            
            twilio_client = TwilioClient()
            result = twilio_client.send_whatsapp(
                to=target.phone,
                message=message
            )
            
            if result['success']:
                external_id = result.get('message_sid')
                activity.status = ActivityStatus.SENT
                activity.sent_at = datetime.utcnow()
            else:
                activity.status = ActivityStatus.FAILED
                return jsonify({'error': result.get('error')}), 500
        
        elif channel == 'linkedin':
            if not target.linkedin_url:
                return jsonify({'error': 'Target has no LinkedIn URL'}), 400
            
            linkedin_client = LinkedInClient()
            
            # Extract LinkedIn URN from URL or use URL directly
            # For now, we'll use the LinkedIn URL as identifier
            # In production, you'd need to convert URL to URN via LinkedIn API
            linkedin_urn = target.linkedin_url
            
            result = linkedin_client.send_message(
                recipient_urn=linkedin_urn,
                message=message
            )
            
            if result['success']:
                external_id = result.get('message_id')
                activity.status = ActivityStatus.SENT
                activity.sent_at = datetime.utcnow()
            else:
                activity.status = ActivityStatus.FAILED
                # LinkedIn may not be fully configured, return warning instead of error
                return jsonify({
                    'error': result.get('error', 'LinkedIn message failed'),
                    'warning': 'LinkedIn integration may require OAuth setup'
                }), 500
        
        else:
            return jsonify({'error': f'Unsupported channel: {channel}'}), 400
        
        # Save activity
        activity.external_id = external_id
        activity_dict = activity.to_dict()
        activity_dict.pop('id', None)
        
        response = supabase.table('outreach_activities').insert(activity_dict).execute()
        
        if response.data:
            created_activity = OutreachActivity.from_dict(response.data[0])
            
            # Update target status
            supabase.table('targets').update({
                'status': 'contacted',
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', target_id).execute()
            
            return jsonify({
                'success': True,
                'activity': created_activity.to_dict()
            }), 201
        else:
            return jsonify({'error': 'Failed to save activity'}), 500
        
    except Exception as e:
        logger.error(f"Error sending outreach: {e}")
        return jsonify({'error': str(e)}), 500


def _text_to_html(text: str) -> str:
    """Convert plain text to basic HTML"""
    if not text:
        return ''
    
    # Escape HTML
    import html
    text = html.escape(text)
    
    # Convert newlines to <br>
    text = text.replace('\n', '<br>')
    
    # Wrap in paragraph
    return f'<p style="margin:0 0 16px 0;line-height:1.6;color:#333333">{text}</p>'


@outreach_bp.route('/api/activities', methods=['GET'])
@require_auth
@require_use_case('analytics')
def list_activities():
    """List outreach activities with filters"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get query parameters
        target_id = request.args.get('target_id')
        status = request.args.get('status')
        channel = request.args.get('channel')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        query = supabase.table('outreach_activities').select('*')
        
        if target_id:
            query = query.eq('target_id', target_id)
        if status:
            query = query.eq('status', status)
        if channel:
            query = query.eq('channel', channel)
        
        query = query.order('created_at', desc=True).limit(limit).offset(offset)
        response = query.execute()
        
        activities = [OutreachActivity.from_dict(a) for a in response.data]
        
        return jsonify({
            'success': True,
            'activities': [a.to_dict() for a in activities],
            'count': len(activities)
        })
        
    except Exception as e:
        logger.error(f"Error listing activities: {e}")
        return jsonify({'error': str(e)}), 500


