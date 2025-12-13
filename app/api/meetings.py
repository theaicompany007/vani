"""Meetings API routes for Cal.com integration"""
import os
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime
from app.models.meetings import Meeting
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_use_case, get_current_user
from app.integrations.cal_com_client import CalComClient
from uuid import UUID

logger = logging.getLogger(__name__)

meetings_bp = Blueprint('meetings', __name__)


@meetings_bp.route('/api/meetings/schedule', methods=['POST'])
@require_auth
@require_use_case('outreach_management')
def schedule_meeting():
    """Schedule a meeting via Cal.com"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        contact_id = data.get('contact_id')
        meeting_type = data.get('meeting_type', '30min')  # 15min, 30min, 60min
        start_time = data.get('start_time')  # ISO format datetime string
        description = data.get('description', '')
        timezone = data.get('timezone', 'UTC')
        
        if not contact_id or not start_time:
            return jsonify({'error': 'contact_id and start_time are required'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get contact details
        contact_response = supabase.table('contacts').select('*').eq('id', contact_id).limit(1).execute()
        if not contact_response.data:
            return jsonify({'error': 'Contact not found'}), 404
        
        contact = contact_response.data[0]
        if not contact.get('email'):
            return jsonify({'error': 'Contact does not have an email address'}), 400
        
        # Parse start_time
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid start_time format. Use ISO format.'}), 400
        
        # Calculate end_time based on meeting type
        from datetime import timedelta
        duration_minutes = {
            '15min': 15,
            '30min': 30,
            '60min': 60
        }.get(meeting_type, 30)
        
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        # Initialize Cal.com client
        try:
            cal_client = CalComClient()
        except ValueError as e:
            logger.error(f"Cal.com client initialization failed: {e}")
            return jsonify({'error': 'Cal.com not configured. Please set CAL_COM_API_KEY.'}), 503
        
        # Get event type ID from environment or use default
        event_type_id = None
        event_type_map = {
            '15min': os.getenv('CAL_COM_EVENT_TYPE_15MIN'),
            '30min': os.getenv('CAL_COM_EVENT_TYPE_30MIN'),
            '60min': os.getenv('CAL_COM_EVENT_TYPE_60MIN')
        }
        event_type_id = event_type_map.get(meeting_type)
        if event_type_id:
            try:
                event_type_id = int(event_type_id)
            except (ValueError, TypeError):
                event_type_id = None
        
        # Create booking via Cal.com
        booking_result = cal_client.create_booking(
            event_type_id=event_type_id,
            start_time=start_dt,
            end_time=end_dt,
            attendee_email=contact['email'],
            attendee_name=contact.get('name', contact['email']),
            notes=description,
            timezone=timezone
        )
        
        if not booking_result.get('success'):
            return jsonify({
                'error': booking_result.get('error', 'Failed to create booking'),
                'details': booking_result.get('details')
            }), 500
        
        booking_data = booking_result.get('booking', {})
        booking_id = booking_result.get('booking_id') or booking_data.get('id')
        meeting_url = booking_result.get('meeting_url') or booking_data.get('meetingUrl')
        booking_url = booking_result.get('booking_url') or booking_data.get('bookingUrl')
        
        # Find or create target for this contact
        target_id = None
        target_search = supabase.table('targets').select('id').eq('contact_id', contact_id).limit(1).execute()
        if target_search.data and len(target_search.data) > 0:
            target_id = target_search.data[0]['id']
        else:
            # Create target for contact
            target_data = {
                'company_name': contact.get('company') or contact.get('company_name') or 'Unknown',
                'contact_name': contact.get('name'),
                'email': contact.get('email'),
                'phone': contact.get('phone'),
                'linkedin_url': contact.get('linkedin'),
                'contact_id': contact_id,
                'company_id': contact.get('company_id'),
                'status': 'new'
            }
            target_response = supabase.table('targets').insert(target_data).execute()
            if target_response.data:
                target_id = target_response.data[0]['id']
        
        if not target_id:
            return jsonify({'error': 'Failed to create or find target for contact'}), 500
        
        # Save meeting to database
        user = get_current_user()
        meeting_data = {
            'target_id': target_id,
            'cal_event_id': str(booking_id) if booking_id else None,
            'scheduled_at': start_dt.isoformat(),
            'meeting_url': meeting_url,
            'status': 'scheduled',
            'notes': description
        }
        
        response = supabase.table('meetings').insert(meeting_data).execute()
        
        if not response.data:
            return jsonify({'error': 'Failed to save meeting'}), 500
        
        meeting = Meeting.from_dict(response.data[0])
        
        return jsonify({
            'success': True,
            'meeting': meeting.to_dict(),
            'booking_id': booking_id,
            'meeting_url': meeting_url,
            'booking_url': booking_url
        }), 201
        
    except Exception as e:
        logger.error(f"Error scheduling meeting: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@meetings_bp.route('/api/meetings', methods=['GET'])
@require_auth
@require_use_case('outreach_management')
def list_meetings():
    """List scheduled meetings with optional filters"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get query parameters
        contact_id = request.args.get('contact_id')
        company_id = request.args.get('company_id')
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Build query - join with targets to get contact/company info
        query = supabase.table('meetings').select('*, targets(*, contacts(*), companies(*))')
        
        if contact_id:
            # Filter by contact_id through targets
            query = query.eq('targets.contact_id', contact_id)
        if company_id:
            # Filter by company_id through targets
            query = query.eq('targets.company_id', company_id)
        if status:
            query = query.eq('status', status)
        if start_date:
            query = query.gte('scheduled_at', start_date)
        if end_date:
            query = query.lte('scheduled_at', end_date)
        
        query = query.order('scheduled_at', desc=True).limit(limit).offset(offset)
        response = query.execute()
        
        meetings = [Meeting.from_dict(m) for m in response.data]
        
        return jsonify({
            'success': True,
            'meetings': [m.to_dict() for m in meetings],
            'count': len(meetings)
        })
        
    except Exception as e:
        logger.error(f"Error listing meetings: {e}")
        return jsonify({'error': str(e)}), 500


@meetings_bp.route('/api/meetings/<meeting_id>', methods=['GET'])
@require_auth
@require_use_case('outreach_management')
def get_meeting(meeting_id):
    """Get a specific meeting by ID"""
    try:
        # Validate UUID format
        try:
            meeting_uuid = UUID(meeting_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid meeting ID format'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        response = supabase.table('meetings').select('*, targets(*, contacts(*), companies(*))').eq('id', str(meeting_uuid)).limit(1).execute()
        
        if not response.data:
            return jsonify({'error': 'Meeting not found'}), 404
        
        meeting = Meeting.from_dict(response.data[0])
        
        return jsonify({
            'success': True,
            'meeting': meeting.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting meeting {meeting_id}: {e}")
        return jsonify({'error': str(e)}), 500


@meetings_bp.route('/api/meetings/<meeting_id>', methods=['DELETE'])
@require_auth
@require_use_case('outreach_management')
def cancel_meeting(meeting_id):
    """Cancel a scheduled meeting"""
    try:
        # Validate UUID format
        try:
            meeting_uuid = UUID(meeting_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid meeting ID format'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get meeting details first
        meeting_response = supabase.table('meetings').select('*').eq('id', str(meeting_uuid)).limit(1).execute()
        if not meeting_response.data:
            return jsonify({'error': 'Meeting not found'}), 404
        
        meeting = meeting_response.data[0]
        booking_id = meeting.get('booking_id')
        
        # Cancel booking in Cal.com if booking_id exists
        if booking_id:
            try:
                cal_client = CalComClient()
                cancel_result = cal_client.cancel_booking(str(booking_id))
                if not cancel_result.get('success'):
                    logger.warning(f"Failed to cancel Cal.com booking {booking_id}: {cancel_result.get('error')}")
            except Exception as e:
                logger.warning(f"Error cancelling Cal.com booking: {e}")
                # Continue with database update even if Cal.com cancellation fails
        
        # Update meeting status in database
        response = supabase.table('meetings').update({
            'status': 'cancelled',
            'cancelled_at': datetime.utcnow().isoformat()
        }).eq('id', str(meeting_uuid)).execute()
        
        if not response.data:
            return jsonify({'error': 'Failed to update meeting'}), 500
        
        updated_meeting = Meeting.from_dict(response.data[0])
        
        return jsonify({
            'success': True,
            'meeting': updated_meeting.to_dict(),
            'message': 'Meeting cancelled successfully'
        })
        
    except Exception as e:
        logger.error(f"Error cancelling meeting {meeting_id}: {e}")
        return jsonify({'error': str(e)}), 500


@meetings_bp.route('/api/meetings/<meeting_id>', methods=['PATCH', 'PUT'])
@require_auth
@require_use_case('outreach_management')
def update_meeting(meeting_id):
    """Update meeting details (e.g., add notes, change status)"""
    try:
        # Validate UUID format
        try:
            meeting_uuid = UUID(meeting_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid meeting ID format'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Remove id from update data
        update_data = {k: v for k, v in data.items() if k != 'id'}
        
        # Update meeting
        response = supabase.table('meetings').update(update_data).eq('id', str(meeting_uuid)).execute()
        
        if not response.data:
            return jsonify({'error': 'Meeting not found'}), 404
        
        updated_meeting = Meeting.from_dict(response.data[0])
        
        return jsonify({
            'success': True,
            'meeting': updated_meeting.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating meeting {meeting_id}: {e}")
        return jsonify({'error': str(e)}), 500


@meetings_bp.route('/api/meetings/available-slots', methods=['GET'])
@require_auth
@require_use_case('outreach_management')
def get_available_slots():
    """Get available time slots from Cal.com"""
    try:
        meeting_type = request.args.get('meeting_type', '30min')
        date_from = request.args.get('date_from')  # ISO format date
        date_to = request.args.get('date_to')  # ISO format date
        
        # Initialize Cal.com client
        try:
            cal_client = CalComClient()
        except ValueError as e:
            logger.error(f"Cal.com client initialization failed: {e}")
            return jsonify({
                'success': True,
                'slots': [],
                'note': 'Cal.com not configured. Please select time manually.'
            })
        
        # Get event type ID
        event_type_id = None
        event_type_map = {
            '15min': os.getenv('CAL_COM_EVENT_TYPE_15MIN'),
            '30min': os.getenv('CAL_COM_EVENT_TYPE_30MIN'),
            '60min': os.getenv('CAL_COM_EVENT_TYPE_60MIN')
        }
        event_type_id = event_type_map.get(meeting_type)
        if event_type_id:
            try:
                event_type_id = int(event_type_id)
            except (ValueError, TypeError):
                event_type_id = None
        
        # Parse dates
        date_from_dt = None
        date_to_dt = None
        if date_from:
            try:
                date_from_dt = datetime.fromisoformat(date_from)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_dt = datetime.fromisoformat(date_to)
            except ValueError:
                pass
        
        # Get available slots
        slots_result = cal_client.get_available_slots(
            event_type_id=event_type_id,
            date_from=date_from_dt,
            date_to=date_to_dt
        )
        
        return jsonify({
            'success': True,
            'slots': slots_result.get('slots', []),
            'note': slots_result.get('note')
        })
        
    except Exception as e:
        logger.error(f"Error getting available slots: {e}")
        return jsonify({
            'success': True,
            'slots': [],
            'note': 'Unable to fetch available slots. Please select time manually.'
        })

