"""Job status API routes for background import jobs"""
from flask import Blueprint, request, jsonify, current_app, session
import logging
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_use_case
from app.models.import_job import ImportJob
from app.jobs.import_job import cancel_job

logger = logging.getLogger(__name__)

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/api/jobs/<job_id>', methods=['GET'])
@require_auth
@require_use_case('target_management')
def get_job_status(job_id):
    """Get status of an import job"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get app_users.id from current user context (not Supabase Auth user_id)
        from app.auth import get_current_user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get app_users.id (not supabase_user_id)
        user_id = str(getattr(current_user, 'id', None))
        if not user_id:
            # Fallback: look up app_users.id from supabase_user_id in session
            supabase_user_id = session.get('user_id')
            if supabase_user_id:
                try:
                    app_user_response = supabase.table('app_users').select('id').eq('supabase_user_id', supabase_user_id).limit(1).execute()
                    if app_user_response.data and len(app_user_response.data) > 0:
                        user_id = str(app_user_response.data[0]['id'])
                    else:
                        return jsonify({'error': 'User record not found in app_users table'}), 404
                except Exception as e:
                    logger.error(f"Error looking up app_user: {e}")
                    return jsonify({'error': 'Failed to resolve user ID'}), 500
            else:
                return jsonify({'error': 'User not authenticated'}), 401
        
        # Fetch job - try with user_id first, then with supabase_user_id, then without filter
        response = None
        if user_id:
            response = supabase.table('import_jobs').select('*').eq('id', job_id).eq('user_id', user_id).limit(1).execute()
        
        # If not found by user_id, try by supabase_user_id
        if (not response or not response.data or len(response.data) == 0):
            from flask import session
            supabase_user_id = session.get('user_id')
            if supabase_user_id:
                response = supabase.table('import_jobs').select('*').eq('id', job_id).eq('supabase_user_id', supabase_user_id).limit(1).execute()
        
        # If still not found, try without user filter (for debugging)
        if (not response or not response.data or len(response.data) == 0):
            all_jobs_response = supabase.table('import_jobs').select('*').eq('id', job_id).limit(1).execute()
            if all_jobs_response.data and len(all_jobs_response.data) > 0:
                job_user_id = all_jobs_response.data[0].get('user_id')
                job_supabase_user_id = all_jobs_response.data[0].get('supabase_user_id')
                logger.warning(f"Job {job_id} exists but belongs to different user. Requested by user {user_id}, job belongs to user_id={job_user_id}, supabase_user_id={job_supabase_user_id}")
                return jsonify({'error': 'Job not found or access denied'}), 404
            else:
                logger.warning(f"Job {job_id} not found in database. User: {user_id}")
                return jsonify({'error': 'Job not found. It may not have been created or the import_jobs table may not exist.'}), 404
        
        job = ImportJob.from_dict(response.data[0])
        
        return jsonify({
            'success': True,
            'job': job.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/api/jobs', methods=['GET'])
@require_auth
@require_use_case('target_management')
def list_jobs():
    """List all import jobs for current user"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get user ID
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get query parameters
        limit = int(request.args.get('limit', 20))
        status_filter = request.args.get('status')
        
        # Build query - search by user_id or supabase_user_id
        from flask import session
        supabase_user_id = session.get('user_id')
        
        if user_id:
            query = supabase.table('import_jobs').select('*').eq('user_id', user_id)
        elif supabase_user_id:
            query = supabase.table('import_jobs').select('*').eq('supabase_user_id', supabase_user_id)
        else:
            return jsonify({'error': 'User not authenticated'}), 401
        
        if status_filter:
            query = query.eq('status', status_filter)
        
        query = query.order('created_at', desc=True).limit(limit)
        response = query.execute()
        
        jobs = [ImportJob.from_dict(j).to_dict() for j in response.data]
        
        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        })
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/api/jobs/<job_id>/cancel', methods=['POST'])
@require_auth
@require_use_case('target_management')
def cancel_job_endpoint(job_id):
    """Cancel a running import job"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get app_users.id from current user context (not Supabase Auth user_id)
        from app.auth import get_current_user
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get app_users.id (not supabase_user_id)
        user_id = str(getattr(current_user, 'id', None))
        if not user_id:
            # Fallback: look up app_users.id from supabase_user_id in session
            supabase_user_id = session.get('user_id')
            if supabase_user_id:
                try:
                    app_user_response = supabase.table('app_users').select('id').eq('supabase_user_id', supabase_user_id).limit(1).execute()
                    if app_user_response.data and len(app_user_response.data) > 0:
                        user_id = str(app_user_response.data[0]['id'])
                    else:
                        return jsonify({'error': 'User record not found in app_users table'}), 404
                except Exception as e:
                    logger.error(f"Error looking up app_user: {e}")
                    return jsonify({'error': 'Failed to resolve user ID'}), 500
            else:
                return jsonify({'error': 'User not authenticated'}), 401
        
        # Verify job exists and belongs to user - try user_id first, then supabase_user_id
        from flask import session
        supabase_user_id = session.get('user_id')
        
        response = None
        if user_id:
            response = supabase.table('import_jobs').select('*').eq('id', job_id).eq('user_id', user_id).limit(1).execute()
        
        if (not response or not response.data or len(response.data) == 0) and supabase_user_id:
            response = supabase.table('import_jobs').select('*').eq('id', job_id).eq('supabase_user_id', supabase_user_id).limit(1).execute()
        
        if not response or not response.data or len(response.data) == 0:
            return jsonify({'error': 'Job not found'}), 404
        
        job = ImportJob.from_dict(response.data[0])
        
        if job.status not in ['pending', 'processing']:
            return jsonify({'error': f'Cannot cancel job with status: {job.status}'}), 400
        
        # Cancel the job
        if cancel_job(job_id):
            return jsonify({
                'success': True,
                'message': 'Job cancellation requested'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Job may have already completed or failed'
            })
        
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        return jsonify({'error': str(e)}), 500

