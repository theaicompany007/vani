"""Industries API routes"""
from flask import Blueprint, request, jsonify, current_app, g
import logging
from app.auth import get_supabase_auth_client, require_super_user, require_auth, get_current_user, get_current_industry
from app.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

industries_bp = Blueprint('industries', __name__)

@industries_bp.route('/api/industries', methods=['GET'])
@require_auth
def list_industries():
    """List industries - filtered by user's assigned industries for all users (including super users)"""
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        # Check if 'all' parameter is requested (for admin purposes only)
        show_all = request.args.get('all', 'false').lower() == 'true'
        is_super_user = getattr(user, 'is_super_user', False)
        
        # Only show all industries if explicitly requested AND user is super user
        if show_all and is_super_user:
            response = supabase.table('industries').select('*').order('name', desc=False).execute()
            return jsonify({'success': True, 'industries': response.data})
        
        # For all users (including super users), show only assigned industries
        supabase_db = get_supabase_client(current_app)
        if not supabase_db:
            return jsonify({'error': 'Database service unavailable'}), 503
        
        # Get user's assigned industries from user_industries table
        assigned_industry_ids = []
        try:
            user_industries_response = supabase_db.table('user_industries').select('industry_id').eq('user_id', user.id).execute()
            if user_industries_response.data:
                assigned_industry_ids = [str(ui['industry_id']) for ui in user_industries_response.data]
        except Exception as e:
            # Fallback to legacy industry_id if user_industries table doesn't exist
            error_str = str(e)
            if 'PGRST205' in error_str or 'user_industries' in error_str.lower():
                if hasattr(user, 'industry_id') and user.industry_id:
                    assigned_industry_ids.append(str(user.industry_id))
            else:
                raise
        
        if not assigned_industry_ids:
            # User has no industries assigned
            return jsonify({'success': True, 'industries': []})
        
        # Get industry details for assigned industries
        response = supabase.table('industries').select('*').in_('id', assigned_industry_ids).order('name', desc=False).execute()
        return jsonify({'success': True, 'industries': response.data})
            
    except Exception as e:
        logger.error(f"Error listing industries: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@industries_bp.route('/api/industries/<uuid:industry_id>', methods=['GET'])
@require_auth
def get_industry(industry_id):
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    try:
        response = supabase.table('industries').select('*').eq('id', industry_id).limit(1).execute()
        if response.data:
            return jsonify({'success': True, 'industry': response.data[0]})
        return jsonify({'success': False, 'error': 'Industry not found'}), 404
    except Exception as e:
        logger.error(f"Error getting industry {industry_id}: {e}")
        return jsonify({'error': str(e)}), 500

@industries_bp.route('/api/industries/create', methods=['POST'])
@require_auth
@require_super_user
def create_industry():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    if not name:
        return jsonify({'error': 'Industry name is required'}), 400
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    try:
        response = supabase.table('industries').insert({'name': name, 'description': description}).execute()
        if response.data:
            return jsonify({'success': True, 'industry': response.data[0]}), 201
        return jsonify({'success': False, 'error': 'Failed to create industry'}), 500
    except Exception as e:
        logger.error(f"Error creating industry {name}: {e}")
        return jsonify({'error': str(e)}), 500

@industries_bp.route('/api/industries/switch', methods=['POST'])
@require_auth
def switch_industry():
    """Switch active industry for current user with access control"""
    data = request.get_json() or {}
    industry_id = data.get('industry_id')
    user = get_current_user()
    
    if not user:
        return jsonify({'error': 'User not authenticated'}), 401
    
    # Use database client for app_users updates
    supabase = get_supabase_client(current_app)
    if not supabase:
        return jsonify({'error': 'Database service unavailable'}), 503
    
    try:
        # Get user's current permissions
        is_industry_admin = getattr(user, 'is_industry_admin', False)
        is_super_user = getattr(user, 'is_super_user', False)
        
        # For industry admins, check user_industries table for assigned industries
        user_assigned_industry_ids = []
        if is_industry_admin:
            # Check both legacy industry_id and user_industries table
            if hasattr(user, 'industry_id') and user.industry_id:
                user_assigned_industry_ids.append(str(user.industry_id))
            
            # Also check user_industries table (if it exists - migration may not have been run)
            try:
                user_industries_response = supabase.table('user_industries').select('industry_id').eq('user_id', user.id).execute()
                if user_industries_response.data:
                    for ui in user_industries_response.data:
                        industry_id_str = str(ui['industry_id'])
                        if industry_id_str not in user_assigned_industry_ids:
                            user_assigned_industry_ids.append(industry_id_str)
            except Exception as e:
                # Table doesn't exist - migration not run yet, use legacy industry_id only
                error_str = str(e)
                if 'PGRST205' not in error_str and 'user_industries' not in error_str.lower():
                    # Re-raise if it's a different error
                    raise
                logger.debug(f"user_industries table not found, using legacy industry_id only")
        
        # Validate industry exists if provided
        if industry_id:
            industry_response = supabase.table('industries').select('*').eq('id', industry_id).limit(1).execute()
            if not industry_response.data:
                return jsonify({'error': 'Industry not found'}), 404
            
            industry_data = industry_response.data[0]
            
            # Industry admin validation: can only switch to their assigned industries
            if is_industry_admin:
                if not user_assigned_industry_ids:
                    return jsonify({
                        'error': 'Industry admin must have at least one assigned industry. Please contact a super user to assign industries.',
                        'help': 'An industry admin needs industries assigned via the User Management interface.'
                    }), 403
                
                if str(industry_id) not in user_assigned_industry_ids:
                    # Get industry names for better error message
                    assigned_industry_names = []
                    for assigned_id in user_assigned_industry_ids:
                        assigned_response = supabase.table('industries').select('name').eq('id', assigned_id).limit(1).execute()
                        if assigned_response.data:
                            assigned_industry_names.append(assigned_response.data[0]['name'])
                    
                    return jsonify({
                        'error': f'Industry admin can only switch to assigned industries: {", ".join(assigned_industry_names)}',
                        'assigned_industry_ids': user_assigned_industry_ids,
                        'assigned_industry_names': assigned_industry_names
                    }), 403
        else:
            # Clearing industry (setting to None) - only super users can do this
            if is_industry_admin:
                return jsonify({
                    'error': 'Industry admin must have an active industry assigned'
                }), 403
            industry_data = None
        
        # Update user's active_industry_id
        user_id = user.id if hasattr(user, 'id') else None
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400
        
        # Prepare update data
        update_data = {
            'active_industry_id': industry_id
        }
        
        # If user doesn't have a default_industry_id yet, set this as default
        if hasattr(user, 'default_industry_id') and not user.default_industry_id:
            update_data['default_industry_id'] = industry_id
        
        update_response = supabase.table('app_users').update(update_data).eq('id', user_id).execute()
        
        if not update_response.data:
            return jsonify({'error': 'Failed to update active industry'}), 500
        
        # Update Flask g context for current request
        if industry_id and industry_data:
            g.industry = type('Industry', (), industry_data)()
        else:
            g.industry = None
        
        # Update user object in g context
        if hasattr(g, 'user'):
            g.user.active_industry_id = industry_id
        
        return jsonify({
            'success': True,
            'message': 'Active industry switched successfully',
            'industry': industry_data if industry_data else None,
            'active_industry_id': industry_id
        })
        
    except Exception as e:
        logger.error(f"Error switching industry: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500