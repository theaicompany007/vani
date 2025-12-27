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
        # Check if 'with_targets' parameter is requested (for pitch/targets tabs)
        with_targets_only = request.args.get('with_targets', 'false').lower() == 'true'
        is_super_user = getattr(user, 'is_super_user', False)
        
        # Check if 'with_contacts_only' parameter is requested (for admin industries management)
        with_contacts_only = request.args.get('with_contacts_only', 'false').lower() == 'true'
        
        # Only show all industries if explicitly requested AND user is super user
        if show_all and is_super_user:
            # If with_contacts_only is requested, filter to only industries with contacts/companies
            if with_contacts_only:
                supabase_db = get_supabase_client(current_app)
                if not supabase_db:
                    return jsonify({'error': 'Database service unavailable'}), 503
                
                # Get all industries first
                all_industries_response = supabase.table('industries').select('*').order('name', desc=False).execute()
                industries_with_counts = []
                
                for industry in all_industries_response.data:
                    industry_name = industry.get('name', '')
                    if not industry_name:
                        continue
                    
                    # Count contacts with this industry (exact case-insensitive match)
                    contacts_count = 0
                    try:
                        # Use exact case-insensitive match by comparing lowercased values
                        # This ensures we only count contacts where industry exactly matches (case-insensitive)
                        contacts_response = supabase_db.table('contacts').select('id', count='exact').ilike('industry', industry_name.strip()).limit(1).execute()
                        if hasattr(contacts_response, 'count') and contacts_response.count is not None:
                            contacts_count = contacts_response.count
                        elif contacts_response.data:
                            # Fallback: count manually if count not available
                            # Use exact match with trimmed industry name
                            contacts_full = supabase_db.table('contacts').select('id').ilike('industry', industry_name.strip()).execute()
                            contacts_count = len(contacts_full.data) if contacts_full.data else 0
                    except Exception as e:
                        logger.debug(f"Error counting contacts for {industry_name}: {e}")
                    
                    # Count companies with this industry (exact case-insensitive match)
                    companies_count = 0
                    try:
                        # Use exact case-insensitive match by comparing lowercased values
                        companies_response = supabase_db.table('companies').select('id', count='exact').ilike('industry', industry_name.strip()).limit(1).execute()
                        if hasattr(companies_response, 'count') and companies_response.count is not None:
                            companies_count = companies_response.count
                        elif companies_response.data:
                            # Fallback: count manually if count not available
                            companies_full = supabase_db.table('companies').select('id').ilike('industry', industry_name.strip()).execute()
                            companies_count = len(companies_full.data) if companies_full.data else 0
                    except Exception as e:
                        logger.debug(f"Error counting companies for {industry_name}: {e}")
                    
                    # Only include if has contacts or companies
                    if contacts_count > 0 or companies_count > 0:
                        industry['contact_count'] = contacts_count
                        industry['company_count'] = companies_count
                        industries_with_counts.append(industry)
                
                return jsonify({'success': True, 'industries': industries_with_counts})
            else:
                # For admin view without filtering, still include counts if requested
                response = supabase.table('industries').select('*').order('name', desc=False).execute()
                industries_with_counts = []
                
                if with_contacts_only:
                    # Filter and add counts
                    supabase_db = get_supabase_client(current_app)
                    if supabase_db:
                        for industry in response.data:
                            industry_name = industry.get('name', '')
                            if not industry_name:
                                continue
                            
                            # Count contacts and companies (exact case-insensitive match)
                            contacts_count = 0
                            companies_count = 0
                            try:
                                industry_name_trimmed = industry_name.strip()
                                contacts_res = supabase_db.table('contacts').select('id', count='exact').ilike('industry', industry_name_trimmed).limit(1).execute()
                                if hasattr(contacts_res, 'count'):
                                    contacts_count = contacts_res.count or 0
                                companies_res = supabase_db.table('companies').select('id', count='exact').ilike('industry', industry_name_trimmed).limit(1).execute()
                                if hasattr(companies_res, 'count'):
                                    companies_count = companies_res.count or 0
                            except Exception as e:
                                logger.debug(f"Error counting for industry '{industry_name}': {e}")
                                pass
                            
                            if contacts_count > 0 or companies_count > 0:
                                industry['contact_count'] = contacts_count
                                industry['company_count'] = companies_count
                                industries_with_counts.append(industry)
                        return jsonify({'success': True, 'industries': industries_with_counts})
                
                # Add counts to all industries for admin view
                supabase_db = get_supabase_client(current_app)
                if supabase_db:
                    for industry in response.data:
                        industry_name = industry.get('name', '')
                        if industry_name:
                            contacts_count = 0
                            companies_count = 0
                            try:
                                contacts_res = supabase_db.table('contacts').select('id', count='exact').ilike('industry', industry_name).limit(1).execute()
                                if hasattr(contacts_res, 'count'):
                                    contacts_count = contacts_res.count or 0
                                companies_res = supabase_db.table('companies').select('id', count='exact').ilike('industry', industry_name).limit(1).execute()
                                if hasattr(companies_res, 'count'):
                                    companies_count = companies_res.count or 0
                            except Exception:
                                pass
                            industry['contact_count'] = contacts_count
                            industry['company_count'] = companies_count
                
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
        
        # If with_targets_only is requested, filter to only industries that have targets
        if with_targets_only:
            try:
                # Get distinct industry_ids from targets table
                targets_response = supabase_db.table('targets').select('industry_id').not_.is_('industry_id', 'null').execute()
                industry_ids_with_targets = set()
                if targets_response.data:
                    for target in targets_response.data:
                        if target.get('industry_id'):
                            industry_ids_with_targets.add(str(target['industry_id']))
                
                # Filter industries to only those with targets
                filtered_industries = [ind for ind in response.data if str(ind.get('id')) in industry_ids_with_targets]
                response.data = filtered_industries
                logger.debug(f"Filtered to {len(filtered_industries)} industries with targets")
            except Exception as e:
                logger.warning(f"Could not filter industries by targets: {e}")
        
        # Check if contact counts are requested
        include_counts = request.args.get('include_counts', 'false').lower() == 'true'
        
        # Get user_industries data to include is_default flag
        industries_with_default = []
        try:
            user_industries_response = supabase_db.table('user_industries').select('industry_id, is_default').eq('user_id', user.id).execute()
            # Create a map of industry_id -> is_default
            default_map = {}
            if user_industries_response.data:
                for ui in user_industries_response.data:
                    default_map[str(ui['industry_id'])] = ui.get('is_default', False)
            
            # Add is_default flag and contact counts to each industry
            for industry in response.data:
                industry_id = str(industry.get('id'))
                industry['is_default'] = default_map.get(industry_id, False)
                
                # Add contact counts if requested
                if include_counts:
                    industry_name = industry.get('name', '')
                    if industry_name:
                        contacts_count = 0
                        try:
                            contacts_res = supabase_db.table('contacts').select('id', count='exact').ilike('industry', industry_name.strip()).limit(1).execute()
                            if hasattr(contacts_res, 'count'):
                                contacts_count = contacts_res.count or 0
                        except Exception:
                            pass
                        industry['contact_count'] = contacts_count
                
                industries_with_default.append(industry)
        except Exception as e:
            # If user_industries table doesn't exist or query fails, just return industries without is_default
            logger.warning(f"Could not fetch is_default flags: {e}")
            industries_with_default = response.data
            
            # Still add contact counts if requested
            if include_counts:
                for industry in industries_with_default:
                    industry_name = industry.get('name', '')
                    if industry_name:
                        contacts_count = 0
                        try:
                            contacts_res = supabase_db.table('contacts').select('id', count='exact').ilike('industry', industry_name.strip()).limit(1).execute()
                            if hasattr(contacts_res, 'count'):
                                contacts_count = contacts_res.count or 0
                        except Exception:
                            pass
                        industry['contact_count'] = contacts_count
        
        return jsonify({'success': True, 'industries': industries_with_default})
            
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

@industries_bp.route('/api/industries/<uuid:industry_id>', methods=['PATCH'])
@require_auth
@require_super_user
def update_industry(industry_id):
    """Update an industry (super user only)"""
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    
    data = request.get_json() or {}
    
    # Only allow updating name and description
    update_data = {}
    if 'name' in data:
        update_data['name'] = data['name']
    if 'description' in data:
        update_data['description'] = data['description']
    
    if not update_data:
        return jsonify({'error': 'No valid fields to update'}), 400
    
    try:
        # Check if industry exists
        industry_response = supabase.table('industries').select('id').eq('id', industry_id).limit(1).execute()
        if not industry_response.data:
            return jsonify({'error': 'Industry not found'}), 404
        
        # If updating name, check for duplicates (case-insensitive)
        if 'name' in update_data and update_data['name']:
            existing = supabase.table('industries').select('id, name').ilike('name', update_data['name']).neq('id', industry_id).limit(1).execute()
            if existing.data:
                return jsonify({'error': f'Industry "{existing.data[0]["name"]}" already exists'}), 400
        
        # Update the industry
        response = supabase.table('industries').update(update_data).eq('id', industry_id).execute()
        
        if response.data:
            return jsonify({'success': True, 'industry': response.data[0]})
        return jsonify({'success': False, 'error': 'Failed to update industry'}), 500
        
    except Exception as e:
        logger.error(f"Error updating industry {industry_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
        # Check if industry with same name already exists (case-insensitive)
        existing = supabase.table('industries').select('id, name').ilike('name', name).limit(1).execute()
        if existing.data:
            return jsonify({'error': f'Industry "{existing.data[0]["name"]}" already exists'}), 400
        
        response = supabase.table('industries').insert({'name': name, 'description': description}).execute()
        if response.data:
            return jsonify({'success': True, 'industry': response.data[0]}), 201
        return jsonify({'success': False, 'error': 'Failed to create industry'}), 500
    except Exception as e:
        logger.error(f"Error creating industry {name}: {e}")
        return jsonify({'error': str(e)}), 500

@industries_bp.route('/api/industries/<uuid:industry_id>', methods=['DELETE'])
@require_auth
@require_super_user
def delete_industry(industry_id):
    """Delete an industry (super user only)"""
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    
    try:
        # Check if industry exists
        industry_response = supabase.table('industries').select('name').eq('id', industry_id).limit(1).execute()
        if not industry_response.data:
            return jsonify({'error': 'Industry not found'}), 404
        
        industry_name = industry_response.data[0].get('name', 'Unknown')
        
        # Check if industry is being used (has targets, contacts, or users assigned)
        supabase_db = get_supabase_client(current_app)
        if supabase_db:
            # Check targets
            targets_check = supabase_db.table('targets').select('id').eq('industry_id', industry_id).limit(1).execute()
            if targets_check.data:
                return jsonify({
                    'error': f'Cannot delete industry "{industry_name}" because it has associated targets. Please reassign or delete targets first.',
                    'has_targets': True
                }), 400
            
            # Check user_industries
            try:
                user_industries_check = supabase_db.table('user_industries').select('id').eq('industry_id', industry_id).limit(1).execute()
                if user_industries_check.data:
                    return jsonify({
                        'error': f'Cannot delete industry "{industry_name}" because it is assigned to users. Please unassign users first.',
                        'has_users': True
                    }), 400
            except Exception:
                # user_industries table might not exist, skip this check
                pass
        
        # Delete the industry
        delete_response = supabase.table('industries').delete().eq('id', industry_id).execute()
        
        return jsonify({
            'success': True,
            'message': f'Industry "{industry_name}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting industry {industry_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
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

@industries_bp.route('/api/industries/sync', methods=['POST'])
@require_auth
@require_super_user
def sync_industries():
    """Sync industries from contacts and companies tables (super user only)"""
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    
    supabase_db = get_supabase_client(current_app)
    if not supabase_db:
        return jsonify({'error': 'Database service unavailable'}), 503
    
    try:
        # Get all unique industries from contacts
        contacts_response = supabase_db.table('contacts').select('industry').not_.is_('industry', 'null').execute()
        contact_industries = set()
        if contacts_response.data:
            for contact in contacts_response.data:
                industry = contact.get('industry')
                if industry and industry.strip():
                    contact_industries.add(industry.strip())
        
        # Get all unique industries from companies
        companies_response = supabase_db.table('companies').select('industry').not_.is_('industry', 'null').execute()
        company_industries = set()
        if companies_response.data:
            for company in companies_response.data:
                industry = company.get('industry')
                if industry and industry.strip():
                    company_industries.add(industry.strip())
        
        # Combine and deduplicate (case-insensitive)
        all_industries = set()
        for ind in contact_industries:
            all_industries.add(ind)
        for ind in company_industries:
            all_industries.add(ind)
        
        logger.info(f"Found {len(all_industries)} unique industries from contacts and companies")
        
        # Get existing industries (case-insensitive comparison)
        existing_response = supabase.table('industries').select('id, name').execute()
        existing_industry_names = set()
        if existing_response.data:
            for ind in existing_response.data:
                existing_industry_names.add(ind['name'].lower().strip())
        
        # Get existing industry codes to avoid conflicts
        existing_codes_response = supabase.table('industries').select('code').execute()
        existing_codes = set()
        if existing_codes_response.data:
            for ind in existing_codes_response.data:
                if ind.get('code'):
                    existing_codes.add(ind['code'].upper())
        
        # Helper function to generate industry code from name
        def generate_industry_code(name):
            """Generate a unique industry code from industry name"""
            # Convert to uppercase, replace spaces and special chars with underscores
            code = name.strip().upper()
            # Replace common separators
            code = code.replace(' ', '_').replace('&', 'AND').replace('-', '_').replace('/', '_')
            # Remove special characters, keep only alphanumeric and underscores
            code = ''.join(c if c.isalnum() or c == '_' else '_' for c in code)
            # Remove multiple consecutive underscores
            while '__' in code:
                code = code.replace('__', '_')
            # Remove leading/trailing underscores
            code = code.strip('_')
            # Ensure it's not empty and has reasonable length
            if not code:
                code = 'INDUSTRY'
            if len(code) > 50:
                code = code[:50]
            return code
        
        # Create missing industries
        created_industries = []
        skipped_count = 0
        
        for industry_name in sorted(all_industries):
            # Check if already exists (case-insensitive)
            if industry_name.lower().strip() in existing_industry_names:
                skipped_count += 1
                continue
            
            try:
                # Generate code from industry name
                base_code = generate_industry_code(industry_name)
                industry_code = base_code
                
                # Ensure code is unique
                counter = 1
                while industry_code.upper() in existing_codes:
                    industry_code = f"{base_code}_{counter}"
                    counter += 1
                    # Prevent infinite loop
                    if counter > 1000:
                        logger.error(f"Could not generate unique code for industry '{industry_name}'")
                        break
                
                # Create new industry with code
                insert_response = supabase.table('industries').insert({
                    'name': industry_name.strip(),
                    'code': industry_code.upper(),
                    'description': f'{industry_name.strip()} industry'
                }).execute()
                
                if insert_response.data:
                    created_industries.append(industry_name.strip())
                    existing_industry_names.add(industry_name.lower().strip())  # Add to set to avoid duplicates
                    existing_codes.add(industry_code.upper())  # Add code to existing codes
                    logger.info(f"Created industry: {industry_name} with code: {industry_code.upper()}")
            except Exception as e:
                logger.warning(f"Failed to create industry '{industry_name}': {e}")
                # Continue with other industries
        
        return jsonify({
            'success': True,
            'created_count': len(created_industries),
            'created_industries': created_industries,
            'skipped_count': skipped_count,
            'total_found': len(all_industries),
            'message': f'Synced {len(created_industries)} new industries from contacts and companies'
        })
        
    except Exception as e:
        logger.error(f"Error syncing industries: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500