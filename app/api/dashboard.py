"""Dashboard API routes"""
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime, timedelta
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_use_case

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@require_auth
@require_use_case('analytics')
def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get time range (default: last 30 days)
        days = int(request.args.get('days', 30))
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Total targets
        targets_response = supabase.table('targets').select('id', count='exact').execute()
        total_targets = targets_response.count if hasattr(targets_response, 'count') else len(targets_response.data)
        
        # Targets by status
        targets_by_status = {}
        for status in ['new', 'contacted', 'responded', 'meeting_scheduled', 'converted']:
            response = supabase.table('targets').select('id', count='exact').eq('status', status).execute()
            count = response.count if hasattr(response, 'count') else len(response.data)
            targets_by_status[status] = count
        
        # Total activities
        try:
            activities_response = supabase.table('outreach_activities').select('id', count='exact').execute()
            total_activities = activities_response.count if hasattr(activities_response, 'count') else len(activities_response.data) if activities_response.data else 0
        except Exception as e:
            logger.warning(f"Error getting total activities: {e}")
            total_activities = 0
        
        # Activities by status
        activities_by_status = {'sent': 0, 'delivered': 0, 'opened': 0, 'clicked': 0, 'replied': 0}
        for status in ['sent', 'delivered', 'opened', 'clicked', 'replied']:
            try:
                response = supabase.table('outreach_activities').select('id', count='exact').eq('status', status).gte('created_at', start_date).execute()
                count = response.count if hasattr(response, 'count') else len(response.data) if response.data else 0
                activities_by_status[status] = count
            except Exception as e:
                logger.warning(f"Error getting activities by status {status}: {e}")
                activities_by_status[status] = 0
        
        # Activities by channel
        activities_by_channel = {'email': 0, 'whatsapp': 0, 'linkedin': 0}
        for channel in ['email', 'whatsapp', 'linkedin']:
            try:
                response = supabase.table('outreach_activities').select('id', count='exact').eq('channel', channel).gte('created_at', start_date).execute()
                count = response.count if hasattr(response, 'count') else len(response.data) if response.data else 0
                activities_by_channel[channel] = count
            except Exception as e:
                logger.warning(f"Error getting activities by channel {channel}: {e}")
                activities_by_channel[channel] = 0
        
        # Recent activities (last 10)
        try:
            recent_activities_response = supabase.table('outreach_activities').select('*').order('created_at', desc=True).limit(10).execute()
            recent_activities = recent_activities_response.data if recent_activities_response.data else []
        except Exception as e:
            logger.warning(f"Error getting recent activities: {e}")
            recent_activities = []
        
        # Scheduled meetings
        try:
            meetings_response = supabase.table('meetings').select('id', count='exact').eq('status', 'scheduled').gte('scheduled_at', datetime.utcnow().isoformat()).execute()
            upcoming_meetings = meetings_response.count if hasattr(meetings_response, 'count') else len(meetings_response.data) if meetings_response.data else 0
        except Exception as e:
            logger.warning(f"Error getting scheduled meetings: {e}")
            upcoming_meetings = 0
        
        return jsonify({
            'success': True,
            'stats': {
                'targets': {
                    'total': total_targets,
                    'by_status': targets_by_status
                },
                'activities': {
                    'total': total_activities,
                    'by_status': activities_by_status,
                    'by_channel': activities_by_channel
                },
                'meetings': {
                    'upcoming': upcoming_meetings
                },
                'recent_activities': recent_activities[:10]
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/meetings', methods=['GET'])
@require_auth
@require_use_case('meetings')
def list_meetings():
    """List all meetings"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get query parameters
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        query = supabase.table('meetings').select('*')
        
        if status:
            query = query.eq('status', status)
        
        # Use scheduled_at if it exists, otherwise use start_time
        try:
            query = query.order('scheduled_at', desc=True).limit(limit).offset(offset)
            response = query.execute()
        except Exception as order_error:
            # Fallback to start_time if scheduled_at doesn't exist
            logger.warning(f"Error ordering by scheduled_at: {order_error}, trying start_time")
            query = supabase.table('meetings').select('*')
            if status:
                query = query.eq('status', status)
            query = query.order('start_time', desc=True).limit(limit).offset(offset)
            response = query.execute()
        
        meetings = response.data if response.data else []
        
        return jsonify({
            'success': True,
            'meetings': meetings,
            'count': len(meetings)
        })
        
    except Exception as e:
        logger.error(f"Error listing meetings: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Error listing meetings: {str(e)}'}), 500


