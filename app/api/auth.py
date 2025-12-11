"""Authentication API routes"""
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, current_app, g
import logging
from app.auth import get_supabase_auth_client, get_current_user, require_auth, require_super_user

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return render_template('login.html', error='Email and password are required', next=request.args.get('next'))
        
        supabase = get_supabase_auth_client()
        if not supabase:
            return render_template('login.html', error='Authentication service unavailable', next=request.args.get('next'))
        
        try:
            response = supabase.auth.sign_in_with_password({'email': email, 'password': password})
            
            if response.user and response.session:
                session['access_token'] = response.session.access_token
                session['refresh_token'] = response.session.refresh_token
                session['user_id'] = str(response.user.id)
                session.permanent = True  # Make session permanent
                # Explicitly mark session as modified to ensure it's saved
                if hasattr(session, 'modified'):
                    session.modified = True
                
                # Upsert app_user into public.app_users table
                app_user_data = supabase.table('app_users').select('*').eq('supabase_user_id', response.user.id).limit(1).execute()
                
                is_new_user = False
                if not app_user_data.data:
                    supabase.table('app_users').insert({
                        'supabase_user_id': response.user.id,
                        'email': email,
                        'name': response.user.user_metadata.get('full_name', email.split('@')[0]),
                        'is_super_user': False,
                        'is_industry_admin': False
                    }).execute()
                    logger.info(f"New app_user created for {email}")
                    is_new_user = True
                else:
                    supabase.table('app_users').update({'email': email}).eq('supabase_user_id', response.user.id).execute()
                
                # Auto-grant default permissions for new users (if not super user)
                if is_new_user:
                    try:
                        from app.supabase_client import get_supabase_client
                        db_supabase = get_supabase_client(current_app)
                        if db_supabase:
                            # Get the newly created user's ID
                            new_user_data = supabase.table('app_users').select('id').eq('supabase_user_id', response.user.id).limit(1).execute()
                            if new_user_data.data:
                                user_id = new_user_data.data[0]['id']
                                
                                # Get all use cases
                                use_cases_response = db_supabase.table('use_cases').select('id').execute()
                                
                                if use_cases_response.data:
                                    # Grant all use cases as global permissions (industry_id = NULL)
                                    permissions_to_insert = []
                                    for uc in use_cases_response.data:
                                        permissions_to_insert.append({
                                            'user_id': user_id,
                                            'use_case_id': uc['id'],
                                            'industry_id': None
                                        })
                                    
                                    if permissions_to_insert:
                                        # Insert permissions (ignore duplicates)
                                        granted_count = 0
                                        for perm in permissions_to_insert:
                                            try:
                                                db_supabase.table('user_permissions').insert(perm).execute()
                                                granted_count += 1
                                            except Exception as perm_error:
                                                # Ignore duplicate key errors
                                                error_str = str(perm_error).lower()
                                                if 'duplicate' not in error_str and 'unique' not in error_str and '23505' not in str(perm_error):
                                                    logger.warning(f"Error granting permission: {perm_error}")
                                        
                                        logger.info(f"Auto-granted {granted_count}/{len(permissions_to_insert)} default permissions to {email}")
                    except Exception as perm_error:
                        logger.warning(f"Failed to auto-grant default permissions: {perm_error}")

                logger.info(f"User {email} logged in successfully.")
                next_url = request.args.get('next') or url_for('command_center')
                return redirect(next_url)
            else:
                return render_template('login.html', error='Invalid credentials', next=request.args.get('next'))
        except Exception as e:
            error_str = str(e).lower()
            logger.error(f"Supabase login error for {email}: {e}")
            
            # Check if error is "Email not confirmed"
            if 'email not confirmed' in error_str or 'not confirmed' in error_str:
                # Try to auto-confirm email using admin API REST endpoint
                try:
                    import requests
                    import os
                    supabase_url = current_app.config.get('SUPABASE_URL', '').rstrip('/')
                    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY', '')
                    
                    if supabase_url and supabase_service_key:
                        # Use REST API directly to avoid client library issues
                        auth_url = f"{supabase_url}/auth/v1/admin/users"
                        headers = {
                            'apikey': supabase_service_key,
                            'Authorization': f'Bearer {supabase_service_key}',
                            'Content-Type': 'application/json'
                        }
                        
                        # List users to find the one with this email
                        users_response = requests.get(auth_url, headers=headers, params={'per_page': 1000}, timeout=10)
                        
                        if users_response.status_code == 200:
                            users_data = users_response.json()
                            users = users_data.get('users', [])
                            
                            user_to_confirm = None
                            for user in users:
                                if user.get('email') and user.get('email').lower() == email.lower():
                                    user_to_confirm = user
                                    break
                            
                            if user_to_confirm:
                                user_id = user_to_confirm.get('id')
                                if user_id:
                                    # Update user to confirm email
                                    update_url = f"{supabase_url}/auth/v1/admin/users/{user_id}"
                                    update_response = requests.put(
                                        update_url,
                                        headers=headers,
                                        json={'email_confirm': True},
                                        timeout=10
                                    )
                                    
                                    if update_response.status_code in [200, 204]:
                                        logger.info(f"Auto-confirmed email for {email}")
                                        
                                        # Retry login after confirmation
                                        try:
                                            response = supabase.auth.sign_in_with_password({'email': email, 'password': password})
                                            if response.user and response.session:
                                                session['access_token'] = response.session.access_token
                                                session['refresh_token'] = response.session.refresh_token
                                                session['user_id'] = str(response.user.id)
                                                session.permanent = True
                                                if hasattr(session, 'modified'):
                                                    session.modified = True
                                                
                                                # Upsert app_user
                                                app_user_data = supabase.table('app_users').select('*').eq('supabase_user_id', response.user.id).limit(1).execute()
                                                if not app_user_data.data:
                                                    supabase.table('app_users').insert({
                                                        'supabase_user_id': response.user.id,
                                                        'email': email,
                                                        'name': response.user.user_metadata.get('full_name', email.split('@')[0]),
                                                        'is_super_user': False,
                                                        'is_industry_admin': False
                                                    }).execute()
                                                
                                                logger.info(f"User {email} logged in successfully after auto-confirmation.")
                                                next_url = request.args.get('next') or url_for('command_center')
                                                return redirect(next_url)
                                        except Exception as retry_error:
                                            logger.warning(f"Retry login after confirmation failed: {retry_error}")
                                    else:
                                        logger.warning(f"Failed to confirm email via API. Status: {update_response.status_code}")
                                else:
                                    logger.warning(f"User found but no ID available for {email}")
                            else:
                                logger.warning(f"User {email} not found in Supabase Auth")
                        else:
                            logger.warning(f"Failed to list users. Status: {users_response.status_code}")
                except Exception as confirm_error:
                    logger.warning(f"Failed to auto-confirm email: {confirm_error}")
                
                # If auto-confirmation failed, show helpful error message
                return render_template('login.html', 
                    error='Email not confirmed. The system attempted to auto-confirm your email. If this error persists, please run: python scripts/confirm_user_email.py ' + email,
                    next=request.args.get('next'))
            
            return render_template('login.html', error='Invalid credentials or server error', next=request.args.get('next'))
    
    return render_template('login.html', next=request.args.get('next'))

@auth_bp.route('/auth/callback', methods=['GET'])
def oauth_callback():
    """Handle OAuth callback from Google"""
    try:
        # Get the code and state from query parameters
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            logger.error(f"OAuth error: {error}")
            return render_template('login.html', 
                error=f'OAuth error: {error}',
                next=request.args.get('next'))
        
        if not code:
            logger.error("OAuth callback missing code parameter")
            return render_template('login.html', 
                error='OAuth callback failed: missing authorization code',
                next=request.args.get('next'))
        
        supabase = get_supabase_auth_client()
        if not supabase:
            return render_template('login.html', 
                error='Authentication service unavailable',
                next=request.args.get('next'))
        
        # Exchange code for session
        # Note: Supabase handles this automatically via the redirect URL
        # We need to check the URL hash for tokens
        from flask import request as flask_request
        
        # Check if tokens are in the URL hash (Supabase OAuth pattern)
        # The actual token exchange happens client-side, but we can also handle it server-side
        # For now, redirect to a page that will extract tokens from hash
        
        # Actually, Supabase OAuth redirects with tokens in the URL hash
        # We need to handle this on the client side, then send tokens to server
        # Let's create a simple callback page that extracts tokens and sends them to server
        
        return render_template('oauth_callback.html', code=code)
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return render_template('login.html', 
            error=f'OAuth callback failed: {str(e)}',
            next=request.args.get('next'))

@auth_bp.route('/api/auth/oauth-complete', methods=['POST'])
def oauth_complete():
    """Complete OAuth flow - called from client after extracting tokens"""
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        
        if not access_token:
            return jsonify({'error': 'Access token required'}), 400
        
        supabase = get_supabase_auth_client()
        if not supabase:
            return jsonify({'error': 'Authentication service unavailable'}), 503
        
        # Verify the token and get user info
        try:
            # Use the access token to get user info
            user_response = supabase.auth.get_user(access_token)
            
            if not user_response.user:
                return jsonify({'error': 'Invalid access token'}), 401
            
            user = user_response.user
            
            # Store session
            session['access_token'] = access_token
            session['refresh_token'] = refresh_token
            session['user_id'] = str(user.id)
            session.permanent = True
            if hasattr(session, 'modified'):
                session.modified = True
            
            # Upsert app_user
            app_user_data = supabase.table('app_users').select('*').eq('supabase_user_id', user.id).limit(1).execute()
            
            is_new_user = False
            if not app_user_data.data:
                # New user from OAuth - create app_user record
                user_name = (
                    user.user_metadata.get('full_name') or 
                    user.user_metadata.get('name') or 
                    user.email.split('@')[0]
                )
                
                supabase.table('app_users').insert({
                    'supabase_user_id': user.id,
                    'email': user.email,
                    'name': user_name,
                    'is_super_user': False,
                    'is_industry_admin': False
                }).execute()
                logger.info(f"New app_user created from OAuth for {user.email}")
                is_new_user = True
            else:
                # Update email if changed
                supabase.table('app_users').update({'email': user.email}).eq('supabase_user_id', user.id).execute()
            
            # Auto-grant default permissions for new users
            if is_new_user:
                try:
                    from app.supabase_client import get_supabase_client
                    db_supabase = get_supabase_client(current_app)
                    if db_supabase:
                        new_user_data = supabase.table('app_users').select('id').eq('supabase_user_id', user.id).limit(1).execute()
                        if new_user_data.data:
                            user_id = new_user_data.data[0]['id']
                            
                            use_cases_response = db_supabase.table('use_cases').select('id').execute()
                            
                            if use_cases_response.data:
                                permissions_to_insert = []
                                for uc in use_cases_response.data:
                                    permissions_to_insert.append({
                                        'user_id': user_id,
                                        'use_case_id': uc['id'],
                                        'industry_id': None
                                    })
                                
                                if permissions_to_insert:
                                    granted_count = 0
                                    for perm in permissions_to_insert:
                                        try:
                                            db_supabase.table('user_permissions').insert(perm).execute()
                                            granted_count += 1
                                        except Exception as perm_error:
                                            error_str = str(perm_error).lower()
                                            if 'duplicate' not in error_str and 'unique' not in error_str and '23505' not in str(perm_error):
                                                logger.warning(f"Error granting permission: {perm_error}")
                                    
                                    logger.info(f"Auto-granted {granted_count}/{len(permissions_to_insert)} default permissions to {user.email}")
                except Exception as perm_error:
                    logger.warning(f"Failed to auto-grant default permissions: {perm_error}")
            
            logger.info(f"User {user.email} logged in via OAuth successfully.")
            return jsonify({
                'success': True,
                'redirect_url': url_for('command_center')
            })
            
        except Exception as token_error:
            logger.error(f"Error verifying OAuth token: {token_error}")
            return jsonify({'error': 'Failed to verify access token'}), 401
            
    except Exception as e:
        logger.error(f"OAuth complete error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout handler"""
    supabase = get_supabase_auth_client()
    try:
        if supabase and session.get('access_token'):
            supabase.auth.sign_out(session.get('access_token'))
    except Exception as e:
        logger.error(f"Supabase logout error: {e}")
    finally:
        session.pop('access_token', None)
        session.pop('refresh_token', None)
        session.pop('user_id', None)
        g.pop('user', None)
        g.pop('industry', None)
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/auth/session', methods=['GET'])
@require_auth
def get_session():
    """Get current session info"""
    try:
        # Check if session has access_token
        if 'access_token' not in session:
            logger.warning("get_session: No access_token in session")
            return jsonify({'success': False, 'error': 'No active session'}), 401
        
        user = get_current_user()
        if user:
            # Ensure boolean values are properly converted
            is_super_user = bool(getattr(user, 'is_super_user', False))
            is_industry_admin = bool(getattr(user, 'is_industry_admin', False))
            
            user_dict = user.to_dict() if hasattr(user, 'to_dict') else {
                'id': str(getattr(user, 'id', '')),
                'email': getattr(user, 'email', ''),
                'name': getattr(user, 'name', ''),
                'is_super_user': is_super_user,
                'is_industry_admin': is_industry_admin
            }
            logger.info(f"Session check for user {user_dict.get('email')}: is_super_user={is_super_user}, token_present={bool(session.get('access_token'))}")
            return jsonify({'success': True, 'user': user_dict})
        logger.warning("get_session: No user in context despite require_auth passing")
        return jsonify({'success': False, 'error': 'No active session'}), 401
    except Exception as e:
        logger.error(f"Error in get_session: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/api/auth/register', methods=['POST'])
@require_auth
@require_super_user
def register_user():
    """Register a new user (super user only)"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    is_super_user = data.get('is_super_user', False)
    is_industry_admin = data.get('is_industry_admin', False)
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    
    try:
        # Check if app_user already exists
        existing_app_user = supabase.table('app_users').select('*').eq('email', email).limit(1).execute()
        if existing_app_user.data:
            logger.warning(f"User {email} already exists in app_users table")
            return jsonify({'error': f'User {email} already exists'}), 400
        
        # Use admin API to create user (bypasses email confirmation)
        # Note: This requires SUPABASE_SERVICE_KEY
        from app.supabase_client import get_supabase_client
        admin_supabase = get_supabase_client(current_app)
        
        if not admin_supabase:
            # Fallback to regular sign_up if admin client not available
            user_response = supabase.auth.sign_up({
                'email': email,
                'password': password,
                'email_confirm': True  # Auto-confirm email
            })
        else:
            # Use admin API to create user directly
            try:
                # Create user via admin API
                admin_response = admin_supabase.auth.admin.create_user({
                    'email': email,
                    'password': password,
                    'email_confirm': True
                })
                user_response = admin_response
            except Exception as admin_error:
                logger.warning(f"Admin API failed, using sign_up: {admin_error}")
                user_response = supabase.auth.sign_up({
                    'email': email,
                    'password': password,
                    'email_confirm': True
                })
        
        if user_response and hasattr(user_response, 'user') and user_response.user:
            user_id = user_response.user.id if hasattr(user_response.user, 'id') else user_response.user.get('id')
            
            supabase.table('app_users').insert({
                'supabase_user_id': user_id,
                'email': email,
                'name': email.split('@')[0],
                'is_super_user': bool(is_super_user),
                'is_industry_admin': bool(is_industry_admin)
            }).execute()
            
            logger.info(f"New user {email} registered with is_super_user={is_super_user}, is_industry_admin={is_industry_admin}")
            return jsonify({
                'success': True,
                'message': f'User {email} registered successfully.',
                'user_id': str(user_id)
            })
        else:
            return jsonify({'error': 'Failed to register user - no user returned'}), 400
    except Exception as e:
        logger.error(f"Error registering user {email}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Check if it's a "user already exists" error
        error_str = str(e).lower()
        if 'already registered' in error_str or 'user already exists' in error_str:
            # Try to create app_user for existing auth user
            try:
                # Find user by email in app_users (might exist)
                existing = supabase.table('app_users').select('*').eq('email', email).limit(1).execute()
                if not existing.data:
                    # User exists in Auth but not in app_users - we can't get the ID without admin API
                    return jsonify({
                        'error': f'User {email} already exists in authentication system. Please contact an administrator.',
                        'hint': 'The user may need to be added to app_users table manually'
                    }), 400
                else:
                    return jsonify({'error': f'User {email} already exists'}), 400
            except:
                pass
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/api/auth/users', methods=['GET'])
@require_auth
@require_super_user
def list_users():
    """List all users (super user only)"""
    try:
        # Get current user to verify super user status
        user = get_current_user()
        if not user:
            logger.warning("list_users: No user in context")
            return jsonify({'error': 'Authentication required'}), 401
        
        # Double-check super user status
        is_super = bool(getattr(user, 'is_super_user', False))
        if not is_super:
            logger.warning(f"list_users: User {getattr(user, 'email', 'unknown')} is not a super user")
            return jsonify({'error': 'Super user access required'}), 403
        
        supabase = get_supabase_auth_client()
        if not supabase:
            logger.error("list_users: Supabase auth client not available")
            return jsonify({'error': 'Authentication service unavailable'}), 503
        
        # Use regular Supabase client for database queries
        from app.supabase_client import get_supabase_client
        db_supabase = get_supabase_client(current_app)
        if not db_supabase:
            logger.error("list_users: Supabase database client not available")
            return jsonify({'error': 'Database service unavailable'}), 503
        
        logger.info(f"list_users: Fetching users for super user {getattr(user, 'email', 'unknown')}")
        response = db_supabase.table('app_users').select('*').order('created_at', desc=True).execute()
        
        users = []
        if response.data:
            for u in response.data:
                # Ensure boolean fields are properly converted
                user_dict = dict(u)
                if 'is_super_user' in user_dict:
                    user_dict['is_super_user'] = bool(user_dict['is_super_user'])
                if 'is_industry_admin' in user_dict:
                    user_dict['is_industry_admin'] = bool(user_dict['is_industry_admin'])
                users.append(user_dict)
        
        logger.info(f"list_users: Returning {len(users)} users")
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Error loading users: {str(e)}'}), 500

@auth_bp.route('/api/auth/users/<uuid:user_id>/toggle_industry_admin', methods=['POST'])
@require_auth
@require_super_user
def toggle_industry_admin(user_id):
    """Toggle industry admin status for a user (super user only)"""
    data = request.get_json()
    is_industry_admin = data.get('is_industry_admin')
    industry_id = data.get('industry_id')  # Optional: assign industry when making admin
    
    if is_industry_admin is None:
        return jsonify({'error': 'is_industry_admin field is required'}), 400
    
    try:
        # Use regular Supabase client for database queries
        from app.supabase_client import get_supabase_client
        db_supabase = get_supabase_client(current_app)
        if not db_supabase:
            logger.error("toggle_industry_admin: Supabase database client not available")
            return jsonify({'error': 'Database service unavailable'}), 503

        update_data = {'is_industry_admin': is_industry_admin}
        
        # If making industry admin and industry_id provided, assign it
        if is_industry_admin and industry_id:
            update_data['industry_id'] = industry_id
            # Also set as active_industry_id for convenience
            update_data['active_industry_id'] = industry_id
        
        db_supabase.table('app_users').update(update_data).eq('id', user_id).execute()
        logger.info(f"User {user_id} industry admin status updated to {is_industry_admin}.")
        return jsonify({'success': True, 'message': f'User {user_id} industry admin status updated.'})
    except Exception as e:
        logger.error(f"Error toggling industry admin status for {user_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/api/auth/users/<uuid:user_id>/assign_industry', methods=['POST'])
@require_auth
@require_super_user
def assign_industry(user_id):
    """Assign an industry to a user (super user only)"""
    data = request.get_json()
    industry_id = data.get('industry_id')
    
    if not industry_id:
        return jsonify({'error': 'industry_id is required'}), 400
    
    try:
        from app.supabase_client import get_supabase_client
        db_supabase = get_supabase_client(current_app)
        if not db_supabase:
            return jsonify({'error': 'Database service unavailable'}), 503

        # Verify industry exists
        industry_check = db_supabase.table('industries').select('id, name').eq('id', industry_id).limit(1).execute()
        if not industry_check.data:
            return jsonify({'error': 'Industry not found'}), 404
        
        industry_name = industry_check.data[0]['name']
        
        # Update user's industry assignment
        update_data = {
            'industry_id': industry_id,
            'active_industry_id': industry_id  # Also set as active
        }
        
        db_supabase.table('app_users').update(update_data).eq('id', user_id).execute()
        
        # Get user email for logging
        user_info = db_supabase.table('app_users').select('email').eq('id', user_id).limit(1).execute()
        user_email = user_info.data[0].get('email', 'unknown') if user_info.data else 'unknown'
        
        logger.info(f"User {user_email} ({user_id}) assigned to industry {industry_name} ({industry_id})")
        return jsonify({
            'success': True,
            'message': f'User assigned to industry {industry_name}',
            'industry_id': industry_id,
            'industry_name': industry_name
        })
    except Exception as e:
        logger.error(f"Error assigning industry to user {user_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/api/auth/users/<uuid:user_id>/toggle_super_user', methods=['POST'])
@require_auth
@require_super_user
def toggle_super_user(user_id):
    """Toggle super user status for a user (super user only)"""
    data = request.get_json()
    is_super_user = data.get('is_super_user')
    
    if is_super_user is None:
        return jsonify({'error': 'is_super_user field is required'}), 400
    
    try:
        # Prevent removing super user status from yourself
        current_user = get_current_user()
        if current_user and str(getattr(current_user, 'id', '')) == str(user_id) and not is_super_user:
            return jsonify({'error': 'You cannot remove super user status from yourself'}), 400
        
        # Use regular Supabase client for database queries
        from app.supabase_client import get_supabase_client
        db_supabase = get_supabase_client(current_app)
        if not db_supabase:
            logger.error("toggle_super_user: Supabase database client not available")
            return jsonify({'error': 'Database service unavailable'}), 503

        # Get user info for logging
        user_info = db_supabase.table('app_users').select('email').eq('id', user_id).limit(1).execute()
        user_email = user_info.data[0].get('email', 'unknown') if user_info.data else 'unknown'
        
        db_supabase.table('app_users').update({'is_super_user': bool(is_super_user)}).eq('id', user_id).execute()
        logger.info(f"User {user_email} ({user_id}) super user status updated to {is_super_user}.")
        return jsonify({
            'success': True, 
            'message': f'User {user_email} super user status updated to {is_super_user}.'
        })
    except Exception as e:
        logger.error(f"Error toggling super user status for {user_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500