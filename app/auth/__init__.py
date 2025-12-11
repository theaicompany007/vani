"""Authentication and authorization module for VANI"""
import os
import logging
from functools import wraps
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

try:
    from flask import current_app, g, request, redirect, url_for, session, jsonify
except ImportError:
    current_app = None
    g = None
    request = None
    redirect = None
    url_for = None
    session = None
    jsonify = None

try:
    from app.models.users import AppUser
except (ImportError, ModuleNotFoundError):
    AppUser = None

try:
    from app.models.industries import Industry
except (ImportError, ModuleNotFoundError):
    Industry = None

def init_auth(app):
    """Initialize authentication system"""
    if not create_client:
        app.supabase_auth = None
        return
    url = app.config.get('SUPABASE_URL', '')
    key = os.getenv('SUPABASE_SERVICE_KEY') or app.config.get('SUPABASE_KEY', '')
    if not url or not key:
        app.supabase_auth = None
        return
    try:
        app.supabase_auth = create_client(url, key)
        logger.info("Supabase Auth client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase Auth: {e}")
        app.supabase_auth = None

def get_supabase_auth_client():
    """Get Supabase Auth client from Flask app context"""
    if not current_app or not hasattr(current_app, 'supabase_auth'):
        return None
    return current_app.supabase_auth

def get_current_user():
    """Get current authenticated user from Flask g context"""
    if not g or 'user' not in g:
        return None
    return g.user

def get_current_industry():
    """Get current active industry from Flask g context"""
    if not g or 'industry' not in g:
        return None
    return g.industry

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is already authenticated in this request (reuse from g context)
        if g and hasattr(g, 'user') and g.user:
            logger.debug(f"require_auth: Reusing authenticated user from g context for {request.path if request else 'unknown'}")
            return f(*args, **kwargs)
        
        if not session:
            logger.warning(f"require_auth: No session object for {request.path if request else 'unknown'}")
            if request and (request.is_json or request.path.startswith('/api/')):
                return jsonify({'error': 'Unauthorized: No session'}), 401
            if redirect and url_for:
                return redirect(url_for('auth.login', next=request.url if request else None))
            return {'error': 'Unauthorized'}, 401
        
        if 'access_token' not in session:
            logger.warning(f"require_auth: No access_token in session for {request.path if request else 'unknown'}")
            if request and (request.is_json or request.path.startswith('/api/')):
                return jsonify({'error': 'Unauthorized: No access token'}), 401
            if redirect and url_for:
                return redirect(url_for('auth.login', next=request.url if request else None))
            return {'error': 'Unauthorized'}, 401
        try:
            supabase = get_supabase_auth_client()
            if not supabase:
                if request and (request.is_json or request.path.startswith('/api/')):
                    return jsonify({'error': 'Service unavailable'}), 503
                return {'error': 'Service unavailable'}, 503
            try:
                access_token = session.get('access_token')
                if not access_token:
                    logger.warning(f"require_auth: No access_token in session for {request.path if request else 'unknown'}")
                    if request and (request.is_json or request.path.startswith('/api/')):
                        return jsonify({'error': 'Unauthorized: No session token'}), 401
                    return {'error': 'Unauthorized'}, 401
                
                # Validate token with Supabase
                logger.debug(f"require_auth: Validating token for {request.path if request else 'unknown'}")
                try:
                    user_response = supabase.auth.get_user(access_token)
                    
                    # Process successful user response
                    if user_response and hasattr(user_response, 'user') and user_response.user:
                        app_user_data = supabase.table('app_users').select('*').eq('supabase_user_id', user_response.user.id).limit(1).execute()
                        if app_user_data.data:
                            user_data = app_user_data.data[0]
                            # Ensure boolean fields are properly converted
                            if 'is_super_user' in user_data:
                                user_data['is_super_user'] = bool(user_data['is_super_user'])
                            if 'is_industry_admin' in user_data:
                                user_data['is_industry_admin'] = bool(user_data['is_industry_admin'])
                            
                            if AppUser:
                                g.user = AppUser.from_dict(user_data)
                            else:
                                g.user = type('AppUser', (), user_data)()
                            
                            # Load active industry (prioritize default_industry_id, then active_industry_id)
                            industry_id_to_load = None
                            if hasattr(g.user, 'default_industry_id') and g.user.default_industry_id:
                                industry_id_to_load = g.user.default_industry_id
                            elif hasattr(g.user, 'active_industry_id') and g.user.active_industry_id:
                                industry_id_to_load = g.user.active_industry_id
                            
                            if industry_id_to_load:
                                industry_data = supabase.table('industries').select('*').eq('id', industry_id_to_load).limit(1).execute()
                                if industry_data.data:
                                    if Industry:
                                        g.industry = Industry.from_dict(industry_data.data[0])
                                    else:
                                        g.industry = type('Industry', (), industry_data.data[0])()
                                else:
                                    g.industry = None
                            else:
                                g.industry = None
                            return f(*args, **kwargs)
                        else:
                            logger.warning(f"App user not found for Supabase user ID: {user_response.user.id}")
                            session.pop('access_token', None)
                            if request and (request.is_json or request.path.startswith('/api/')):
                                return jsonify({'error': 'User not found in app_users table'}), 404
                            return {'error': 'User not found'}, 404
                    else:
                        logger.warning("Invalid user response from Supabase auth")
                        session.pop('access_token', None)
                        if request and (request.is_json or request.path.startswith('/api/')):
                            return jsonify({'error': 'Invalid token'}), 401
                        return {'error': 'Invalid token'}, 401
                except Exception as get_user_error:
                    error_str = str(get_user_error).lower()
                    error_msg = str(get_user_error)
                    logger.warning(f"require_auth: get_user() failed for {request.path if request else 'unknown'}: {error_msg}")
                    
                    # Try to refresh token if we have a refresh_token
                    refresh_token = session.get('refresh_token')
                    if refresh_token and any(keyword in error_str for keyword in ['jwt', 'token', 'expired', 'invalid', 'unauthorized', '401', '403']):
                        logger.info(f"require_auth: Attempting token refresh for {request.path if request else 'unknown'}")
                        try:
                            refresh_response = supabase.auth.refresh_session(refresh_token)
                            if refresh_response and refresh_response.session:
                                # Update session with new tokens
                                session['access_token'] = refresh_response.session.access_token
                                session['refresh_token'] = refresh_response.session.refresh_token
                                session.permanent = True
                                # Explicitly mark session as modified to ensure it's saved
                                if hasattr(session, 'modified'):
                                    session.modified = True
                                logger.info(f"require_auth: Token refreshed successfully, retrying authentication")
                                # Retry getting user with new token
                                user_response = supabase.auth.get_user(refresh_response.session.access_token)
                                if user_response and hasattr(user_response, 'user') and user_response.user:
                                    app_user_data = supabase.table('app_users').select('*').eq('supabase_user_id', user_response.user.id).limit(1).execute()
                                    if app_user_data.data:
                                        user_data = app_user_data.data[0]
                                        if 'is_super_user' in user_data:
                                            user_data['is_super_user'] = bool(user_data['is_super_user'])
                                        if 'is_industry_admin' in user_data:
                                            user_data['is_industry_admin'] = bool(user_data['is_industry_admin'])
                                        
                                        if AppUser:
                                            g.user = AppUser.from_dict(user_data)
                                        else:
                                            g.user = type('AppUser', (), user_data)()
                                        
                                        # Load active industry (prioritize default_industry_id, then active_industry_id)
                                        industry_id_to_load = None
                                        if hasattr(g.user, 'default_industry_id') and g.user.default_industry_id:
                                            industry_id_to_load = g.user.default_industry_id
                                        elif hasattr(g.user, 'active_industry_id') and g.user.active_industry_id:
                                            industry_id_to_load = g.user.active_industry_id
                                        
                                        if industry_id_to_load:
                                            industry_data = supabase.table('industries').select('*').eq('id', industry_id_to_load).limit(1).execute()
                                            if industry_data.data:
                                                if Industry:
                                                    g.industry = Industry.from_dict(industry_data.data[0])
                                                else:
                                                    g.industry = type('Industry', (), industry_data.data[0])()
                                            else:
                                                g.industry = None
                                        else:
                                            g.industry = None
                                        return f(*args, **kwargs)
                        except Exception as refresh_error:
                            logger.warning(f"require_auth: Token refresh failed: {refresh_error}")
                            # Refresh failed, clear session
                            session.pop('access_token', None)
                            session.pop('refresh_token', None)
                            if request and (request.is_json or request.path.startswith('/api/')):
                                return jsonify({'error': 'Session expired. Please login again.'}), 401
                            return {'error': 'Session expired'}, 401
                    
                    # If it's clearly a token issue and refresh didn't work, clear session
                    if any(keyword in error_str for keyword in ['jwt', 'token', 'expired', 'invalid', 'unauthorized', '401', '403']):
                        logger.warning(f"require_auth: Token validation failed - clearing session")
                        session.pop('access_token', None)
                        session.pop('refresh_token', None)
                        if request and (request.is_json or request.path.startswith('/api/')):
                            return jsonify({'error': 'Session expired. Please login again.'}), 401
                        return {'error': 'Session expired'}, 401
                    else:
                        # Might be a temporary network/service error
                        logger.error(f"require_auth: Unexpected auth error (might be temporary): {error_msg}")
                        # Don't clear session for temporary errors
                        if request and (request.is_json or request.path.startswith('/api/')):
                            return jsonify({'error': 'Authentication service temporarily unavailable'}), 503
                        return {'error': 'Authentication error'}, 503
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                if session:
                    session.pop('access_token', None)
                if request and (request.is_json or request.path.startswith('/api/')):
                    return jsonify({'error': 'Authentication error'}), 500
                return {'error': 'Authentication error'}, 500
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            if session:
                session.pop('access_token', None)
            if request and (request.is_json or request.path.startswith('/api/')):
                return jsonify({'error': 'Authentication error'}), 500
            return {'error': 'Authentication error'}, 500
    return decorated_function

def require_use_case(use_case_code: str):
    """Decorator to require specific use case permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                logger.warning(f"require_use_case({use_case_code}): No user in context")
                return jsonify({'error': 'Unauthorized: Authentication required'}), 401
            
            # Check if super user (bypasses all use case checks)
            is_super = False
            if hasattr(user, 'is_super_user'):
                is_super = bool(user.is_super_user)
            elif isinstance(user, dict) and 'is_super_user' in user:
                is_super = bool(user['is_super_user'])
            
            if is_super:
                logger.debug(f"require_use_case({use_case_code}): Super user bypass")
                return f(*args, **kwargs)
            
            supabase = get_supabase_auth_client()
            if not supabase:
                return jsonify({'error': 'Service unavailable'}), 503
            
            user_id = getattr(user, 'id', None)
            if not user_id:
                logger.warning(f"require_use_case({use_case_code}): User has no ID")
                return jsonify({'error': 'Invalid user data'}), 500
            
            use_case_response = supabase.table('use_cases').select('id').eq('code', use_case_code).limit(1).execute()
            if not use_case_response.data:
                logger.error(f"Use case '{use_case_code}' not found")
                return jsonify({'error': f'Use case {use_case_code} not found'}), 500
            
            use_case_id = use_case_response.data[0]['id']
            
            # Check global permission (industry_id is NULL)
            global_permission = supabase.table('user_permissions').select('id').eq('user_id', user_id).eq('use_case_id', use_case_id).is_('industry_id', 'null').limit(1).execute()
            if global_permission.data:
                logger.debug(f"require_use_case({use_case_code}): Global permission granted")
                return f(*args, **kwargs)
            
            # Check industry-specific permission if an industry is active
            if hasattr(g, 'industry') and g.industry:
                industry_id = getattr(g.industry, 'id', None)
                if industry_id:
                    industry_permission = supabase.table('user_permissions').select('id').eq('user_id', user_id).eq('use_case_id', use_case_id).eq('industry_id', industry_id).limit(1).execute()
                    if industry_permission.data:
                        logger.debug(f"require_use_case({use_case_code}): Industry permission granted")
                        return f(*args, **kwargs)
            
            logger.warning(f"require_use_case({use_case_code}): Permission denied for user {getattr(user, 'email', 'unknown')}")
            return jsonify({'error': f'Forbidden: Missing permission for {use_case_code}'}), 403
        return decorated_function
    return decorator

def require_super_user(f):
    """Decorator to require super user access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            logger.warning("require_super_user: No user in context")
            return jsonify({'error': 'Forbidden: Authentication required'}), 401
        
        # Check is_super_user with proper boolean conversion
        is_super = False
        if hasattr(user, 'is_super_user'):
            is_super = bool(user.is_super_user)
        elif isinstance(user, dict) and 'is_super_user' in user:
            is_super = bool(user['is_super_user'])
        
        if not is_super:
            logger.warning(f"require_super_user: User {getattr(user, 'email', 'unknown')} is not a super user (is_super_user={getattr(user, 'is_super_user', None)})")
            return jsonify({'error': 'Forbidden: Super user access required'}), 403
        
        logger.info(f"require_super_user: User {getattr(user, 'email', 'unknown')} granted super user access")
        return f(*args, **kwargs)
    return decorated_function