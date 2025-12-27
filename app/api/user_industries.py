"""User Industries API - Multiple industry assignment"""
from flask import Blueprint, request, jsonify, current_app
import logging
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_super_user, get_current_user

logger = logging.getLogger(__name__)

user_industries_bp = Blueprint('user_industries', __name__)


@user_industries_bp.route('/api/user-industries/<uuid:user_id>', methods=['GET'])
@require_auth
@require_super_user
def get_user_industries(user_id):
    """Get all industries assigned to a user"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Check if user_industries table exists (migration may not have been run)
        try:
            response = supabase.table('user_industries').select('*, industries(id, name)').eq('user_id', user_id).order('is_default', desc=True).order('assigned_at', desc=True).execute()
            
            logger.debug(f"Raw user_industries response for user {user_id}: {response.data}")
            
            industries = []
            if response.data:
                for ui in response.data:
                    industry = ui.get('industries', {})
                    # Ensure is_default is a boolean
                    is_default = ui.get('is_default', False)
                    if isinstance(is_default, str):
                        is_default = is_default.lower() in ('true', '1', 'yes')
                    elif isinstance(is_default, int):
                        is_default = bool(is_default)
                    
                    industries.append({
                        'id': str(ui['industry_id']),
                        'name': industry.get('name', 'Unknown'),
                        'is_default': is_default,
                        'assigned_at': ui.get('assigned_at')
                    })
            
            logger.debug(f"Processed industries for user {user_id}: {industries}")
        except Exception as table_error:
            error_str = str(table_error)
            if 'PGRST205' in error_str or 'user_industries' in error_str.lower():
                # Table doesn't exist - return empty list (migration not run)
                logger.warning(f"user_industries table not found. Migration may not have been run. Error: {error_str}")
                industries = []
            else:
                raise
        
        # Get user's default_industry_id (this column may also not exist)
        default_industry_id = None
        try:
            user_response = supabase.table('app_users').select('default_industry_id, industry_id, active_industry_id').eq('id', user_id).limit(1).execute()
            if user_response.data:
                user_data = user_response.data[0]
                # Try default_industry_id first, fall back to active_industry_id or industry_id
                default_industry_id = user_data.get('default_industry_id') or user_data.get('active_industry_id') or user_data.get('industry_id')
                if default_industry_id:
                    default_industry_id = str(default_industry_id)
        except Exception as e:
            logger.warning(f"Could not fetch default_industry_id (column may not exist): {e}")
        
        return jsonify({
            'success': True,
            'industries': industries,
            'default_industry_id': default_industry_id
        })
    except Exception as e:
        logger.error(f"Error getting user industries: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@user_industries_bp.route('/api/user-industries/<uuid:user_id>', methods=['POST'])
@require_auth
@require_super_user
def assign_user_industry(user_id):
    """Assign an industry to a user"""
    try:
        data = request.get_json() or {}
        industry_id = data.get('industry_id')
        is_default = data.get('is_default', False)
        
        if not industry_id:
            return jsonify({'error': 'industry_id is required'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Verify industry exists
        industry_check = supabase.table('industries').select('id, name').eq('id', industry_id).limit(1).execute()
        if not industry_check.data:
            return jsonify({'error': 'Industry not found'}), 404
        
        industry_name = industry_check.data[0]['name']
        
        # Get current user for logging
        current_user = get_current_user()
        assigned_by = str(current_user.id) if current_user else None
        
        # Insert or update user_industries
        insert_data = {
            'user_id': str(user_id),
            'industry_id': str(industry_id),
            'is_default': is_default,
            'assigned_by': assigned_by
        }
        
        # Use upsert to handle duplicates
        response = supabase.table('user_industries').upsert(
            insert_data,
            on_conflict='user_id,industry_id'
        ).execute()
        
        # Get user email for logging
        user_info = supabase.table('app_users').select('email').eq('id', user_id).limit(1).execute()
        user_email = user_info.data[0].get('email', 'unknown') if user_info.data else 'unknown'
        
        logger.info(f"User {user_email} ({user_id}) assigned to industry {industry_name} ({industry_id}), is_default={is_default}")
        
        return jsonify({
            'success': True,
            'message': f'Industry {industry_name} assigned to user',
            'industry_id': industry_id,
            'industry_name': industry_name,
            'is_default': is_default
        })
    except Exception as e:
        logger.error(f"Error assigning industry to user: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@user_industries_bp.route('/api/user-industries/<uuid:user_id>/<uuid:industry_id>', methods=['DELETE'])
@require_auth
@require_super_user
def remove_user_industry(user_id, industry_id):
    """Remove an industry assignment from a user"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Check if this is the default industry
        check_response = supabase.table('user_industries').select('is_default').eq('user_id', user_id).eq('industry_id', industry_id).limit(1).execute()
        
        if check_response.data and check_response.data[0].get('is_default'):
            # If removing default, set another industry as default or clear default_industry_id
            other_industries = supabase.table('user_industries').select('industry_id').eq('user_id', user_id).neq('industry_id', industry_id).limit(1).execute()
            if other_industries.data:
                # Set first other industry as default
                new_default_id = other_industries.data[0]['industry_id']
                supabase.table('user_industries').update({'is_default': True}).eq('user_id', user_id).eq('industry_id', new_default_id).execute()
                supabase.table('app_users').update({'default_industry_id': new_default_id}).eq('id', user_id).execute()
            else:
                # No other industries, clear default
                supabase.table('app_users').update({'default_industry_id': None}).eq('id', user_id).execute()
        
        # Delete the assignment
        supabase.table('user_industries').delete().eq('user_id', user_id).eq('industry_id', industry_id).execute()
        
        logger.info(f"Removed industry {industry_id} from user {user_id}")
        return jsonify({'success': True, 'message': 'Industry assignment removed'})
    except Exception as e:
        logger.error(f"Error removing user industry: {e}")
        return jsonify({'error': str(e)}), 500


@user_industries_bp.route('/api/user-industries/<uuid:user_id>/set-default', methods=['POST'])
@require_auth
@require_super_user
def set_default_industry(user_id):
    """Set a default industry for a user"""
    try:
        data = request.get_json() or {}
        industry_id = data.get('industry_id')
        
        if not industry_id:
            return jsonify({'error': 'industry_id is required'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Verify user has this industry assigned
        check = supabase.table('user_industries').select('*').eq('user_id', user_id).eq('industry_id', industry_id).limit(1).execute()
        if not check.data:
            return jsonify({'error': 'User does not have this industry assigned'}), 400
        
        # First, unset all other defaults for this user
        supabase.table('user_industries').update({'is_default': False}).eq('user_id', user_id).execute()
        
        # Set this one as default
        result1 = supabase.table('user_industries').update({'is_default': True}).eq('user_id', user_id).eq('industry_id', industry_id).execute()
        
        # Also update app_users.default_industry_id directly
        result2 = supabase.table('app_users').update({'default_industry_id': industry_id}).eq('id', user_id).execute()
        
        # Verify both updates succeeded
        if not result1.data:
            logger.warning(f"user_industries update returned no data for user {user_id}, industry {industry_id}")
        if not result2.data:
            logger.warning(f"app_users update returned no data for user {user_id}, industry {industry_id}")
        
        logger.info(f"Set default industry {industry_id} for user {user_id}")
        return jsonify({'success': True, 'message': 'Default industry set', 'industry_id': industry_id})
    except Exception as e:
        logger.error(f"Error setting default industry: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

