"""Target management API routes"""
from flask import Blueprint, request, jsonify, current_app
import logging
import json
import os
from app.models.targets import Target, TargetStatus
from app.models.target_recommendation import TargetRecommendation
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_use_case, get_current_user, get_current_industry
from app.services.target_identification import get_target_identification_service
from app.services.industry_context import get_industry_context
from app.integrations.rag_client import get_rag_client
from app.integrations.gemini_client import get_gemini_client
from app.integrations.redis_client import cache_response, invalidate_cache
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)

targets_bp = Blueprint('targets', __name__)


@targets_bp.route('/api/targets', methods=['GET'])
@require_auth
@require_use_case('target_management')
@cache_response(ttl=300, key_prefix='targets')  # Cache for 5 minutes
def list_targets():
    """List all targets with optional filters and industry-based access control"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get current user for industry-based filtering
        user = get_current_user()
        user_industry_id = None
        is_industry_admin = False
        is_super_user = False
        
        if user:
            is_industry_admin = getattr(user, 'is_industry_admin', False)
            is_super_user = getattr(user, 'is_super_user', False)
            # Get user's active_industry_id (prioritize) or industry_id (fallback)
            # For filtering, we want the currently selected industry (active_industry_id)
            if hasattr(user, 'active_industry_id') and user.active_industry_id:
                user_industry_id = str(user.active_industry_id)
            elif hasattr(user, 'industry_id') and user.industry_id:
                user_industry_id = str(user.industry_id)
        
        # Get query parameters
        status = request.args.get('status')
        company = request.args.get('company')
        industry_param = request.args.get('industry')  # Manual filter (super users only)
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Build query with industry filtering - include industry name via JOIN
        query = supabase.table('targets').select('*, contacts(industry), companies(industry), industries(id, name)')
        
        # For industry filtering, we'll filter after fetching to handle derived industry from contacts/companies
        # But we can optimize by pre-filtering on industry_id if available
        logger.debug(f"list_targets: user_industry_id={user_industry_id}, is_super_user={is_super_user}, is_industry_admin={is_industry_admin}, industry_param={industry_param}")
        
        if status:
            query = query.eq('status', status)
        if company:
            query = query.ilike('company_name', f'%{company}%')
        
        query = query.order('created_at', desc=True).limit(limit * 2).offset(offset)  # Fetch more to filter
        response = query.execute()
        
        # Deduplicate at database level: group by company_name + contact_name + role
        seen_targets = {}  # key: (company_name, contact_name, role) -> target
        targets = []
        logger.debug(f"list_targets: Fetched {len(response.data)} targets from database before filtering")
        
        for t in response.data:
            try:
                # Check industry_id directly from raw response first (before Target model conversion)
                raw_industry_id = t.get('industry_id')
                logger.debug(f"Raw target data: company_name={t.get('company_name')}, industry_id={raw_industry_id}, type={type(raw_industry_id)}")
                
                target = Target.from_dict(t)
                target_dict = target.to_dict()
                
                # Derive industry from target, contact, or company
                target_industry_id = None
                # First check raw data (most reliable)
                if raw_industry_id:
                    target_industry_id = str(raw_industry_id)
                    logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Using raw industry_id={target_industry_id}")
                elif target_dict.get('industry_id'):
                    target_industry_id = str(target_dict['industry_id'])
                    logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Using target_dict industry_id={target_industry_id}")
                elif t.get('contacts') and t['contacts'].get('industry'):
                    # Get industry from contacts table
                    contact_industry = t['contacts']['industry']
                    # Look up industry_id from industry name
                    industry_lookup = supabase.table('industries').select('id').ilike('name', f'%{contact_industry}%').limit(1).execute()
                    if industry_lookup.data:
                        target_industry_id = str(industry_lookup.data[0]['id'])
                        logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Derived industry_id={target_industry_id} from contact industry={contact_industry}")
                elif t.get('companies') and t['companies'].get('industry'):
                    # Get industry from companies table
                    company_industry = t['companies']['industry']
                    industry_lookup = supabase.table('industries').select('id').ilike('name', f'%{company_industry}%').limit(1).execute()
                    if industry_lookup.data:
                        target_industry_id = str(industry_lookup.data[0]['id'])
                        logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Derived industry_id={target_industry_id} from company industry={company_industry}")
                else:
                    logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: No industry_id found (target.industry_id={target_dict.get('industry_id')}, contact={bool(t.get('contacts'))}, company={bool(t.get('companies'))})")
                
                # Apply industry filter
                if is_super_user:
                    # Super users: Show all targets unless industry_param is specified
                    if industry_param:
                        # Super user with manual industry filter: Check if target matches
                        if target_industry_id:
                            # Check if target's industry_id matches the requested industry
                            if str(target_industry_id) != str(industry_param):
                                logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Skipped - industry_id mismatch (target={target_industry_id}, requested={industry_param})")
                                continue
                        else:
                            # If no industry_id on target and super user requested specific industry, skip
                            logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Skipped - no industry_id (super user requested industry={industry_param})")
                            continue
                        logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: PASSED super user filter with industry_param (industry_id={target_industry_id})")
                    else:
                        # Super user without industry filter: Show all targets
                        logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: PASSED super user filter (no industry filter, showing all)")
                elif is_industry_admin and user_industry_id:
                    # Industry admin: Must match their industry
                    if not target_industry_id:
                        logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Skipped - no industry_id (industry admin filter)")
                        continue
                    if target_industry_id != user_industry_id:
                        logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Skipped - industry_id mismatch (target={target_industry_id}, user={user_industry_id})")
                        continue
                    logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: PASSED industry admin filter (industry_id={target_industry_id})")
                elif user_industry_id:
                    # Regular user with active_industry_id: Filter by active industry
                    # Only show targets that have industry_id matching active industry
                    if not target_industry_id or target_industry_id != user_industry_id:
                        logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Skipped - industry_id mismatch (target={target_industry_id}, user={user_industry_id})")
                        continue
                    logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: PASSED regular user filter (industry_id={target_industry_id})")
                
                # Enrich with contact/company data if linked
                if target_dict.get('contact_id'):
                    contact_response = supabase.table('contacts').select('*').eq('id', target_dict['contact_id']).limit(1).execute()
                    if contact_response.data:
                        target_dict['contact'] = contact_response.data[0]
                
                if target_dict.get('company_id'):
                    company_response = supabase.table('companies').select('*').eq('id', target_dict['company_id']).limit(1).execute()
                    if company_response.data:
                        target_dict['company'] = company_response.data[0]
                
                # Add industry information - ALWAYS fetch industry name if industry_id exists
                if target_industry_id:
                    target_dict['industry_id'] = target_industry_id
                    # Always fetch industry name to ensure it's available
                    try:
                        industry_response = supabase.table('industries').select('id, name').eq('id', target_industry_id).limit(1).execute()
                        if industry_response.data and len(industry_response.data) > 0:
                            target_dict['industry'] = industry_response.data[0]['name']
                            logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Added industry name '{target_dict['industry']}' from industry_id={target_industry_id}")
                        else:
                            logger.warning(f"Target {target_dict.get('company_name', 'Unknown')}: industry_id={target_industry_id} found but no industry name in database")
                    except Exception as e:
                        logger.error(f"Error fetching industry name for target {target_dict.get('company_name', 'Unknown')}: {e}")
                
                # Deduplication: Check if we've seen this company+contact+role combination
                company_name = target_dict.get('company_name', '').lower().strip()
                contact_name = target_dict.get('contact_name', '').lower().strip()
                role = target_dict.get('role', '').lower().strip()
                dedup_key = (company_name, contact_name, role)
                
                if dedup_key in seen_targets:
                    # Duplicate found - keep the one with more complete data or newer ID
                    existing = seen_targets[dedup_key]
                    existing_data_score = len(str(existing.get('email', ''))) + len(str(existing.get('phone', ''))) + len(str(existing.get('pain_point', '')))
                    new_data_score = len(str(target_dict.get('email', ''))) + len(str(target_dict.get('phone', ''))) + len(str(target_dict.get('pain_point', '')))
                    
                    if new_data_score > existing_data_score or target_dict.get('id', '') > existing.get('id', ''):
                        # Replace with better/newer target
                        targets.remove(existing)
                        targets.append(target_dict)
                        seen_targets[dedup_key] = target_dict
                        logger.debug(f"Replaced duplicate target: {company_name} - {contact_name} ({role})")
                    else:
                        logger.debug(f"Skipped duplicate target: {company_name} - {contact_name} ({role})")
                else:
                    # New unique target
                    targets.append(target_dict)
                    seen_targets[dedup_key] = target_dict
                
                if len(targets) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"Error processing target {t.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"list_targets: Returning {len(targets)} targets (user_industry_id={user_industry_id}, is_super_user={is_super_user}, is_industry_admin={is_industry_admin})")
        
        # Get total count before filtering (for "All Industries" view)
        total_count = len(response.data) if response.data else 0
        
        return jsonify({
            'success': True,
            'targets': targets,
            'count': len(targets),
            'total_count': total_count  # Total before industry filtering
        })
        
    except Exception as e:
        logger.error(f"Error listing targets: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets', methods=['POST'])
@require_auth
@require_use_case('target_management')
def create_target():
    """Create a new target with industry auto-assignment"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get current user for industry assignment
        user = get_current_user()
        user_industry_id = None
        is_industry_admin = False
        
        if user:
            is_industry_admin = getattr(user, 'is_industry_admin', False)
            if hasattr(user, 'industry_id') and user.industry_id:
                user_industry_id = str(user.industry_id)
            elif hasattr(user, 'active_industry_id') and user.active_industry_id:
                user_industry_id = str(user.active_industry_id)
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Auto-assign industry_id (priority order)
        target_industry_id = None
        
        # 1. User's active_industry_id (if industry admin - mandatory)
        if is_industry_admin and user_industry_id:
            target_industry_id = user_industry_id
            # Validate that provided industry matches user's industry
            if data.get('industry_id') and str(data['industry_id']) != user_industry_id:
                return jsonify({
                    'error': 'Industry admin can only create targets in their assigned industry'
                }), 403
        # 2. Contact's industry (if contact_id provided)
        elif data.get('contact_id'):
            contact_response = supabase.table('contacts').select('industry, companies(industry)').eq('id', data['contact_id']).limit(1).execute()
            if contact_response.data:
                contact_data = contact_response.data[0]
                contact_industry = contact_data.get('industry')
                if not contact_industry and contact_data.get('companies'):
                    contact_industry = contact_data['companies'].get('industry')
                if contact_industry:
                    # Look up industry_id from industry name
                    industry_lookup = supabase.table('industries').select('id').ilike('name', f'%{contact_industry}%').limit(1).execute()
                    if industry_lookup.data:
                        target_industry_id = str(industry_lookup.data[0]['id'])
        # 3. Company's industry (if company_id provided)
        elif data.get('company_id'):
            company_response = supabase.table('companies').select('industry').eq('id', data['company_id']).limit(1).execute()
            if company_response.data and company_response.data[0].get('industry'):
                company_industry = company_response.data[0]['industry']
                industry_lookup = supabase.table('industries').select('id').ilike('name', f'%{company_industry}%').limit(1).execute()
                if industry_lookup.data:
                    target_industry_id = str(industry_lookup.data[0]['id'])
        # 4. Explicit industry_id from request
        elif data.get('industry_id'):
            target_industry_id = str(data['industry_id'])
        
        # Set industry_id in target data
        if target_industry_id:
            data['industry_id'] = target_industry_id
        
        # Validate and create target
        target = Target(**data)
        target_dict = target.to_dict()
        
        # Remove id if present (let Supabase generate it)
        target_dict.pop('id', None)
        
        response = supabase.table('targets').insert(target_dict).execute()
        
        if response.data:
            created_target = Target.from_dict(response.data[0])
            
            # Invalidate cache for targets (all variations)
            invalidate_cache('targets:*')
            logger.debug("Cache invalidated after target creation")
            
            return jsonify({
                'success': True,
                'target': created_target.to_dict()
            }), 201
        else:
            return jsonify({'error': 'Failed to create target'}), 500
        
    except Exception as e:
        logger.error(f"Error creating target: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/<target_id>', methods=['GET'])
@require_auth
@require_use_case('target_management')
def get_target(target_id):
    """Get a specific target by ID"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        response = supabase.table('targets').select('*').eq('id', target_id).execute()
        
        if response.data:
            target = Target.from_dict(response.data[0])
            return jsonify({
                'success': True,
                'target': target.to_dict()
            })
        else:
            return jsonify({'error': 'Target not found'}), 404
        
    except Exception as e:
        logger.error(f"Error getting target: {e}")
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/<target_id>', methods=['PUT', 'PATCH'])
@require_auth
@require_use_case('target_management')
def update_target(target_id):
    """Update a target with industry-based access control"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get current user for industry validation
        user = get_current_user()
        is_industry_admin = getattr(user, 'is_industry_admin', False) if user else False
        user_industry_id = None
        
        if user and is_industry_admin:
            if hasattr(user, 'industry_id') and user.industry_id:
                user_industry_id = str(user.industry_id)
            elif hasattr(user, 'active_industry_id') and user.active_industry_id:
                user_industry_id = str(user.active_industry_id)
        
        # Check industry access if industry admin
        if is_industry_admin and user_industry_id:
            target_response = supabase.table('targets').select('industry_id').eq('id', target_id).limit(1).execute()
            if target_response.data:
                target_industry_id = target_response.data[0].get('industry_id')
                if target_industry_id and str(target_industry_id) != user_industry_id:
                    return jsonify({
                        'error': 'You can only update targets from your assigned industry'
                    }), 403
        
        # Update target
        data['updated_at'] = datetime.utcnow().isoformat()
        response = supabase.table('targets').update(data).eq('id', target_id).execute()
        
        if response.data:
            target = Target.from_dict(response.data[0])
            
            # Invalidate cache for targets (all variations)
            invalidate_cache('targets:*')
            logger.debug("Cache invalidated after target update")
            
            return jsonify({
                'success': True,
                'target': target.to_dict()
            })
        else:
            return jsonify({'error': 'Target not found'}), 404
        
    except Exception as e:
        logger.error(f"Error updating target: {e}")
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/<target_id>/link-contact', methods=['POST'])
@require_auth
@require_use_case('target_management')
def link_target_to_contact(target_id):
    """Link a target to a contact and/or company"""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        company_id = data.get('company_id')
        
        if not contact_id and not company_id:
            return jsonify({'error': 'contact_id or company_id required'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        update_data = {}
        if contact_id:
            update_data['contact_id'] = contact_id
        if company_id:
            update_data['company_id'] = company_id
        
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        response = supabase.table('targets').update(update_data).eq('id', target_id).execute()
        
        if response.data:
            target = Target.from_dict(response.data[0])
            return jsonify({
                'success': True,
                'target': target.to_dict()
            })
        else:
            return jsonify({'error': 'Target not found'}), 404
        
    except Exception as e:
        logger.error(f"Error linking target to contact: {e}")
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/from-contact', methods=['POST'])
@require_auth
@require_use_case('target_management')
def create_target_from_contact():
    """Convert a contact to a target with optional AI enrichment"""
    try:
        data = request.get_json() or {}
        contact_id = data.get('contact_id')
        use_ai = data.get('use_ai', False)  # Optionally use AI to generate pain point, pitch angle, script
        
        if not contact_id:
            return jsonify({'error': 'contact_id is required'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get contact with company info
        contact_response = supabase.table('contacts').select('*, companies(name, industry, domain)').eq('id', contact_id).limit(1).execute()
        
        if not contact_response.data:
            return jsonify({'error': 'Contact not found'}), 404
        
        contact = contact_response.data[0]
        company = contact.get('companies', {})
        
        # Get current user for industry assignment
        user = get_current_user()
        user_industry_id = None
        is_industry_admin = getattr(user, 'is_industry_admin', False) if user else False
        
        if user:
            if hasattr(user, 'industry_id') and user.industry_id:
                user_industry_id = str(user.industry_id)
            elif hasattr(user, 'active_industry_id') and user.active_industry_id:
                user_industry_id = str(user.active_industry_id)
        
        # Determine industry_id
        target_industry_id = None
        if is_industry_admin and user_industry_id:
            target_industry_id = user_industry_id
        elif contact.get('industry'):
            industry_lookup = supabase.table('industries').select('id').ilike('name', f'%{contact["industry"]}%').limit(1).execute()
            if industry_lookup.data:
                target_industry_id = str(industry_lookup.data[0]['id'])
        elif company.get('industry'):
            industry_lookup = supabase.table('industries').select('id').ilike('name', f'%{company["industry"]}%').limit(1).execute()
            if industry_lookup.data:
                target_industry_id = str(industry_lookup.data[0]['id'])
        
        # Build target data from contact
        target_data = {
            'company_name': company.get('name') or contact.get('company') or 'Unknown Company',
            'contact_name': contact.get('name', ''),
            'role': contact.get('role', ''),
            'email': contact.get('email'),
            'phone': contact.get('phone'),
            'linkedin_url': contact.get('linkedin'),
            'contact_id': str(contact_id),
            'company_id': str(contact.get('company_id')) if contact.get('company_id') else None,
            'status': 'new',
            'industry_id': target_industry_id
        }
        
        # Use AI to generate content if requested
        if use_ai:
            try:
                from app.services.target_identification import get_target_identification_service
                from app.services.industry_context import get_industry_context
                
                identification_service = get_target_identification_service()
                industry_context = get_industry_context()
                
                industry_name = contact.get('industry') or (company.get('industry') if company else None) or 'FMCG'
                industry_config = industry_context.get_config(industry_name) if industry_context else {}
                
                # Generate AI content
                ai_prompt = f"Generate a pain point, pitch angle, and LinkedIn script for {target_data['contact_name']} ({target_data['role']}) at {target_data['company_name']} in the {industry_name} industry."
                
                # Use OpenAI to generate content
                from app.integrations.openai_client import OpenAIClient
                openai_client = OpenAIClient()
                
                # Create a simple prompt for content generation
                content_prompt = f"""
                For {target_data['contact_name']} ({target_data['role']}) at {target_data['company_name']} in {industry_name}:
                
                Generate:
                1. A specific pain point they likely face
                2. A compelling pitch angle for VANI
                3. A personalized LinkedIn outreach script
                
                Return as JSON: {{"pain_point": "...", "pitch_angle": "...", "script": "..."}}
                """
                
                try:
                    ai_response = openai_client.client.chat.completions.create(
                        model=openai_client.model,
                        messages=[
                            {"role": "system", "content": f"You are an expert B2B sales strategist for the {industry_name} industry."},
                            {"role": "user", "content": content_prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.7,
                        max_tokens=500
                    )
                    
                    ai_content = json.loads(ai_response.choices[0].message.content)
                    target_data['pain_point'] = ai_content.get('pain_point', '')
                    target_data['pitch_angle'] = ai_content.get('pitch_angle', '')
                    target_data['script'] = ai_content.get('script', '')
                except Exception as ai_error:
                    logger.warning(f"AI content generation failed: {ai_error}. Creating target without AI content.")
            except Exception as e:
                logger.warning(f"AI enrichment failed: {e}. Creating target without AI content.")
        
        # Create target
        target = Target(**target_data)
        target_dict = target.to_dict()
        target_dict.pop('id', None)  # Let Supabase generate ID
        
        response = supabase.table('targets').insert(target_dict).execute()
        
        if response.data:
            created_target = Target.from_dict(response.data[0])
            return jsonify({
                'success': True,
                'target': created_target.to_dict(),
                'message': 'Target created from contact successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to create target'}), 500
        
    except Exception as e:
        logger.error(f"Error creating target from contact: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/import', methods=['POST'])
@require_auth
@require_use_case('sheets_import_export')
def import_targets():
    """Import targets from Google Sheets"""
    try:
        from app.integrations.google_sheets_client import GoogleSheetsClient
        
        # Get sheet name from request (optional)
        data = request.get_json() or {}
        sheet_name = data.get('sheet_name')  # Can be None to use default
        
        try:
            sheets_client = GoogleSheetsClient()
        except ValueError as e:
            # Google Sheets not configured
            return jsonify({
                'success': False,
                'error': 'Google Sheets credentials not found. Please configure GOOGLE_SHEETS_CREDENTIALS_PATH and GOOGLE_SHEETS_SPREADSHEET_ID in .env.local'
            }), 400
        
        try:
            targets_data = sheets_client.import_targets(sheet_name=sheet_name)
        except Exception as e:
            error_msg = str(e)
            if 'index' in error_msg.lower() or 'empty' in error_msg.lower() or 'not found' in error_msg.lower():
                sheet_display = sheet_name or 'Targets'
                return jsonify({
                    'success': False,
                    'error': f'Google Sheets is empty or "{sheet_display}" sheet not found. Please ensure the sheet exists and has data.'
                }), 400
            raise
        
        if not targets_data or len(targets_data) == 0:
            return jsonify({
                'success': False,
                'error': 'No data found in Google Sheets. Please ensure the "Targets" sheet has data rows.'
            }), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        imported_count = 0
        for target_data in targets_data:
            try:
                # Skip empty rows
                if not target_data or not any(target_data.values()):
                    continue
                
                # Clean UUID fields: convert empty strings to None and validate
                uuid_fields = ['industry_id', 'contact_id', 'company_id']
                for field in uuid_fields:
                    if field in target_data:
                        value = target_data[field]
                        # Convert empty string, whitespace-only, or invalid UUID - remove from dict
                        if not value or (isinstance(value, str) and value.strip() == ''):
                            # Remove empty UUID fields completely (don't pass to Target model)
                            target_data.pop(field)
                        elif isinstance(value, str):
                            # Validate UUID format if value is provided
                            try:
                                UUID(value.strip())
                                target_data[field] = value.strip()
                            except (ValueError, AttributeError):
                                # Invalid UUID format, remove it
                                logger.debug(f"Invalid UUID format for {field}: {value}, removing")
                                target_data.pop(field)
                    
                target = Target(**target_data)
                target_dict = target.to_dict()
                target_dict.pop('id', None)
                
                # Final safety check: ensure no empty strings in UUID fields (defensive)
                for field in uuid_fields:
                    if field in target_dict:
                        value = target_dict[field]
                        if isinstance(value, str) and (not value or value.strip() == ''):
                            # Remove empty string fields
                            target_dict.pop(field)
                
                supabase.table('targets').insert(target_dict).execute()
                imported_count += 1
            except Exception as e:
                logger.warning(f"Failed to import target {target_data.get('company_name', 'Unknown')}: {e}")
                continue
        
        # Invalidate cache after import
        if imported_count > 0:
            invalidate_cache('targets:*')
            logger.debug(f"Cache invalidated after importing {imported_count} targets")
        
        return jsonify({
            'success': True,
            'imported': imported_count,
            'total': len(targets_data),
            'sheet_name': sheet_name or 'default'
        })
        
    except Exception as e:
        logger.error(f"Error importing targets: {e}")
        error_msg = str(e)
        if 'credentials' in error_msg.lower() or 'not found' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'Google Sheets not configured. Please add credentials to .env.local'
            }), 400
        return jsonify({'error': error_msg}), 500


@targets_bp.route('/api/targets/sheets/list', methods=['GET'])
@require_auth
@require_use_case('sheets_import_export')
def list_sheets():
    """List all available sheet names in the Google Spreadsheet"""
    try:
        from app.integrations.google_sheets_client import GoogleSheetsClient
        
        try:
            sheets_client = GoogleSheetsClient()
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': 'Google Sheets credentials not found. Please configure GOOGLE_SHEETS_CREDENTIALS_PATH and GOOGLE_SHEETS_SPREADSHEET_ID in .env.local'
            }), 400
        
        try:
            sheet_names = sheets_client.list_sheets()
            return jsonify({
                'success': True,
                'sheets': sheet_names
            })
        except Exception as e:
            logger.error(f"Error listing sheets: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        
    except Exception as e:
        logger.error(f"Error listing sheets: {e}")
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/sheets/url', methods=['GET'])
@require_auth
@require_use_case('sheets_import_export')
def get_sheet_url():
    """Get Google Spreadsheet URL"""
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    if not spreadsheet_id:
        return jsonify({
            'success': False,
            'error': 'Google Sheets not configured. Please configure GOOGLE_SHEETS_SPREADSHEET_ID in .env.local'
        }), 400
    return jsonify({
        'success': True,
        'url': f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}'
    })


@targets_bp.route('/api/targets/<target_id>', methods=['DELETE'])
@require_auth
@require_use_case('target_management')
def delete_target(target_id):
    """Delete a target with industry-based access control"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get current user for industry validation
        user = get_current_user()
        is_industry_admin = getattr(user, 'is_industry_admin', False) if user else False
        user_industry_id = None
        
        if user and is_industry_admin:
            if hasattr(user, 'industry_id') and user.industry_id:
                user_industry_id = str(user.industry_id)
            elif hasattr(user, 'active_industry_id') and user.active_industry_id:
                user_industry_id = str(user.active_industry_id)
        
        # Get target to check industry
        target_response = supabase.table('targets').select('*, contacts(industry), companies(industry)').eq('id', target_id).limit(1).execute()
        
        if not target_response.data:
            return jsonify({'error': 'Target not found'}), 404
        
        target_data = target_response.data[0]
        
        # Check industry access for industry admins
        if is_industry_admin and user_industry_id:
            target_industry_id = target_data.get('industry_id')
            if not target_industry_id:
                # Derive from contact/company
                if target_data.get('contacts') and target_data['contacts'].get('industry'):
                    contact_industry = target_data['contacts']['industry']
                    industry_lookup = supabase.table('industries').select('id').ilike('name', f'%{contact_industry}%').limit(1).execute()
                    if industry_lookup.data:
                        target_industry_id = str(industry_lookup.data[0]['id'])
                elif target_data.get('companies') and target_data['companies'].get('industry'):
                    company_industry = target_data['companies']['industry']
                    industry_lookup = supabase.table('industries').select('id').ilike('name', f'%{company_industry}%').limit(1).execute()
                    if industry_lookup.data:
                        target_industry_id = str(industry_lookup.data[0]['id'])
            
            if target_industry_id and target_industry_id != user_industry_id:
                return jsonify({
                    'error': 'You can only delete targets from your assigned industry'
                }), 403
        
        # Delete target
        delete_response = supabase.table('targets').delete().eq('id', target_id).execute()
        
        # Invalidate cache for targets (all variations)
        invalidate_cache('targets:*')
        logger.debug("Cache invalidated after target deletion")
        
        return jsonify({
            'success': True,
            'message': 'Target deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting target: {e}")
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/ai-identify/report', methods=['POST'])
@require_auth
@require_use_case('ai_target_finder')
def ai_identify_targets_report():
    """Generate detailed B2B sales analysis report from AI recommendations"""
    try:
        data = request.get_json() or {}
        industries = data.get('industries', [])
        industry = data.get('industry')
        limit = int(data.get('limit', 10))
        min_seniority = float(data.get('min_seniority', 0.5))
        preset = data.get('preset', 'custom')
        
        # Normalize industries
        if not industries and industry:
            industries = [industry]
        elif not industries:
            return jsonify({'error': 'At least one industry is required'}), 400
        
        # Get current user
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get contacts (reuse the same logic as ai_identify_targets)
        # For simplicity, we'll call the identify endpoint internally or reuse logic
        # For now, let's create a simplified version that generates report from search_id
        
        search_id = data.get('search_id')
        if not search_id:
            return jsonify({'error': 'search_id is required to generate report'}), 400
        
        # Fetch saved search results
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        search_result = supabase.table('ai_target_search_results').select('*').eq('id', search_id).limit(1).execute()
        if not search_result.data:
            return jsonify({'error': 'Search results not found'}), 404
        
        saved_results = search_result.data[0]
        recommendations = saved_results.get('results', [])
        search_config = saved_results.get('search_config', {})
        primary_industry = search_config.get('industries', [industries[0] if industries else 'general'])[0]
        
        # Generate report
        from app.services.recommendation_report_generator import generate_recommendation_report
        report = generate_recommendation_report(
            recommendations=recommendations,
            industry=primary_industry,
            search_config=search_config
        )
        
        return jsonify({
            'success': True,
            'report': report,
            'search_id': search_id,
            'format': 'markdown'
        })
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/ai-identify', methods=['POST'])
@require_auth
@require_use_case('ai_target_finder')
def ai_identify_targets():
    """AI-powered target identification from contacts with multiple industries support"""
    try:
        data = request.get_json() or {}
        industries = data.get('industries', [])  # Now accepts array
        industry = data.get('industry')  # Backward compatibility
        limit = int(data.get('limit', 10))  # Default to 10
        min_seniority = float(data.get('min_seniority', 0.5))
        preset = data.get('preset', 'custom')  # high_priority, broad_search, c_level_only, custom
        search_config = data.get('search_config', {})
        exclude_processed = data.get('exclude_processed', True)  # Default: exclude processed contacts
        
        # Normalize industries: support both single industry (backward compat) and array
        if not industries and industry:
            industries = [industry]
        elif not industries:
            return jsonify({'error': 'At least one industry is required'}), 400
        
        # Apply preset configurations
        if preset == 'high_priority':
            min_seniority = 0.7
            limit = 10
        elif preset == 'broad_search':
            min_seniority = 0.3
            limit = 10
        elif preset == 'c_level_only':
            min_seniority = 0.9
            limit = 10
        
        # Get current user for industry access control and saving results
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        user_id = str(user.id) if hasattr(user, 'id') else None
        is_industry_admin = getattr(user, 'is_industry_admin', False) if user else False
        is_super_user = getattr(user, 'is_super_user', False) if user else False
        user_industry_id = None
        
        if user:
            if hasattr(user, 'industry_id') and user.industry_id:
                user_industry_id = str(user.industry_id)
            elif hasattr(user, 'active_industry_id') and user.active_industry_id:
                user_industry_id = str(user.active_industry_id)
        
        # Get contacts from database filtered by industries
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Query contacts with company information
        # Also join companies table to get industry from company if contact doesn't have it
        contacts_query = supabase.table('contacts').select('*, companies(name, industry, domain)')
        
        # Filter out processed contacts if exclude_processed is True
        if exclude_processed:
            # Exclude contacts that are already targets
            contacts_query = contacts_query.eq('is_target', False)
            logger.debug(f"Excluding processed contacts (is_target=false)")
        
        logger.debug(f"Initial query: filtering for industries={industries}, exclude_processed={exclude_processed}")
        
        # Filter by industries (OR logic - contact can match any of the selected industries)
        if is_industry_admin and user_industry_id:
            # Get industry name from industry_id
            industry_lookup = supabase.table('industries').select('name').eq('id', user_industry_id).limit(1).execute()
            if industry_lookup.data:
                industry_name = industry_lookup.data[0]['name']
                contacts_query = contacts_query.ilike('industry', f'%{industry_name}%')
        elif industries:
            # For super users or multiple industries: use first industry for initial filter
            # Then filter the rest in Python for better matching
            if len(industries) == 1:
                # Single industry: use direct filter with flexible matching
                industry_name = industries[0].strip()
                # Use ilike for case-insensitive partial matching
                # This should match "retail" when searching for "Retail"
                contacts_query = contacts_query.ilike('industry', f'%{industry_name}%')
                logger.debug(f"Filtering contacts by single industry: {industry_name} (case-insensitive ilike)")
            else:
                # Multiple industries: Don't filter at query level, fetch all and filter in Python
                # This ensures we get contacts matching ANY of the selected industries
                logger.debug(f"Multiple industries selected: {industries}. Will fetch all contacts and filter in Python.")
                # This ensures we get contacts that match ANY of the selected industries
                logger.debug(f"Multiple industries selected: {industries}. Will fetch all contacts and filter in Python.")
                # Don't add industry filter - we'll filter in Python to match any industry
        
        # Increase limit significantly to ensure we get enough contacts, especially for single industry searches
        # For single industry, fetch more to account for potential mismatches in database
        if len(industries) == 1:
            fetch_limit = max(limit * 10, 500)  # At least 500 contacts for single industry search
        else:
            fetch_limit = limit * 5 if (is_super_user or len(industries) > 1) else limit * 3
        contacts_query = contacts_query.limit(fetch_limit)
        logger.debug(f"Set fetch_limit to {fetch_limit} for industries={industries}")
        
        logger.debug(f"Executing contacts query with limit={fetch_limit}, industries={industries}")
        contacts_response = contacts_query.execute()
        
        logger.debug(f"Query executed: fetched {len(contacts_response.data) if contacts_response.data else 0} contacts")
        
        # Check if the fetched contacts actually match the industry (for debugging)
        if contacts_response.data and industries and len(industries) == 1:
            matching_count = 0
            sample_industries = set()
            for c in contacts_response.data[:10]:  # Check first 10
                industry_val = (c.get('industry') or '').strip().lower()
                if c.get('companies') and c['companies'].get('industry'):
                    company_industry = (c['companies'].get('industry') or '').strip().lower()
                    if not industry_val:
                        industry_val = company_industry
                if industry_val:
                    sample_industries.add(industry_val)
                    if industries[0].strip().lower() in industry_val or industry_val in industries[0].strip().lower():
                        matching_count += 1
            logger.debug(f"Sample industries from fetched contacts: {sorted(list(sample_industries))}")
            logger.debug(f"Contacts matching '{industries[0]}' in first 10: {matching_count}/10")
        
        # If no results from initial query, try a fallback: search without industry filter and filter in Python
        # This helps when industry names don't match exactly in the database
        if not contacts_response.data and industries and len(industries) == 1:
            logger.warning(f"No contacts found with industry filter for '{industries[0]}'. Trying broader search without industry filter...")
            # Try fetching without industry filter
            fallback_query = supabase.table('contacts').select('*, companies(name, industry, domain)')
            if exclude_processed:
                fallback_query = fallback_query.eq('is_target', False)
            fallback_query = fallback_query.limit(fetch_limit * 2)  # Get more for filtering
            fallback_response = fallback_query.execute()
            if fallback_response.data:
                logger.warning(f"Fallback query found {len(fallback_response.data)} contacts. Will filter in Python for industry '{industries[0]}'.")
                contacts_response = fallback_response
        
        # If no results and we're filtering by industry, try a broader search for debugging
        if not contacts_response.data and industries:
            logger.warning(f"No contacts found with initial query for industries: {industries}")
            logger.warning("Trying broader search to check if contacts exist...")
            # Try fetching without industry filter to see if contacts exist
            # For multiple industries, fetch more contacts for Python-side filtering
            fetch_limit_broad = max(fetch_limit * 3, 1000) if len(industries) > 1 else fetch_limit * 2
            broad_query = supabase.table('contacts').select('*, companies(name, industry, domain)').limit(fetch_limit_broad)
            if exclude_processed:
                broad_query = broad_query.eq('is_target', False)
            broad_response = broad_query.execute()
            if broad_response.data:
                logger.warning(f"Found {len(broad_response.data)} contacts without industry filter")
                # Check what industries are actually in the database
                industries_found = set()
                for c in broad_response.data[:50]:  # Check first 50
                    industry_val = c.get('industry') or ''
                    if c.get('companies') and c['companies'].get('industry'):
                        industry_val = industry_val or c['companies'].get('industry', '')
                    if industry_val:
                        industries_found.add(industry_val)
                logger.warning(f"Sample industries in database: {sorted(list(industries_found))[:20]}")
                # Check if any match the requested industry with flexible matching
                requested_lower = [ind.lower().strip() for ind in industries]
                matches_found = []
                
                # More flexible matching: check for partial matches, word matches, and normalized variations
                for ind in industries_found:
                    ind_lower = ind.lower().strip()
                    ind_normalized = ind_lower.replace('&', 'and').replace(',', ' ').replace('  ', ' ').strip()
                    
                    for req in requested_lower:
                        req_normalized = req.replace('&', 'and').replace(',', ' ').replace('  ', ' ').strip()
                        
                        # Check multiple matching strategies
                        match_found = (
                            req in ind_lower or  # Exact substring
                            ind_lower in req or  # Reverse substring
                            req_normalized in ind_normalized or  # Normalized substring
                            ind_normalized in req_normalized or  # Reverse normalized
                            any(word in ind_lower for word in req.split() if len(word) > 3) or  # Word matching (words > 3 chars)
                            any(word in req for word in ind_lower.split() if len(word) > 3)  # Reverse word matching
                        )
                        
                        if match_found:
                            matches_found.append(ind)
                            break
                
                if matches_found:
                    logger.warning(f"Found matching industries in database: {matches_found}")
                    # Use the broad query results for Python-side filtering
                    logger.warning(f"Will filter {len(broad_response.data)} contacts in Python for industries: {industries}")
                    contacts_response = broad_response
                else:
                    # Even if no exact matches found, still use broad query for Python-side filtering
                    # Python filtering is more flexible and may find matches
                    logger.warning(f"No exact matches found, but will still filter {len(broad_response.data)} contacts in Python for flexible matching")
                    logger.warning(f"Requested industries {industries} - Python filtering will attempt flexible matching")
                    contacts_response = broad_response
            else:
                logger.warning("No contacts found in database at all (even without filters)")
        
        # Count excluded contacts for user feedback
        excluded_count = 0
        if exclude_processed:
            # Get count of excluded contacts (already targets)
            excluded_query = supabase.table('contacts').select('id', count='exact')
            if is_industry_admin and user_industry_id:
                industry_lookup = supabase.table('industries').select('name').eq('id', user_industry_id).limit(1).execute()
                if industry_lookup.data:
                    industry_name = industry_lookup.data[0]['name']
                    excluded_query = excluded_query.ilike('industry', f'%{industry_name}%')
            elif industries:
                excluded_query = excluded_query.ilike('industry', f'%{industries[0]}%')
            excluded_query = excluded_query.eq('is_target', True)
            excluded_result = excluded_query.execute()
            excluded_count = excluded_result.count if hasattr(excluded_result, 'count') else 0
        
        if not contacts_response.data:
            # Try a diagnostic query to see what's in the database
            logger.warning(f"No contacts found for industries: {industries}")
            logger.warning("Running diagnostic query...")
            
            # Check total contacts
            total_query = supabase.table('contacts').select('id', count='exact')
            if exclude_processed:
                total_query = total_query.eq('is_target', False)
            total_result = total_query.execute()
            total_count = total_result.count if hasattr(total_result, 'count') else len(total_result.data) if total_result.data else 0
            logger.warning(f"Total contacts in database (is_target=false): {total_count}")
            
            # Check sample industries from contacts
            sample_query = supabase.table('contacts').select('industry').limit(100)
            if exclude_processed:
                sample_query = sample_query.eq('is_target', False)
            sample_result = sample_query.execute()
            if sample_result.data:
                industries_found = set()
                for c in sample_result.data:
                    industry_val = c.get('industry') or ''
                    if industry_val:
                        industries_found.add(industry_val)
                logger.warning(f"Sample industries found in contacts: {sorted(list(industries_found))[:20]}")
                
                # Check for Retail specifically
                retail_contacts = [c for c in sample_result.data if c.get('industry') and 'retail' in c.get('industry', '').lower()]
                logger.warning(f"Contacts with 'retail' in industry (sample): {len(retail_contacts)}")
            
            # Check companies table for industry info
            companies_query = supabase.table('companies').select('industry').limit(100)
            companies_result = companies_query.execute()
            if companies_result.data:
                company_industries = set()
                for comp in companies_result.data:
                    industry_val = comp.get('industry') or ''
                    if industry_val:
                        company_industries.add(industry_val)
                logger.warning(f"Sample industries found in companies: {sorted(list(company_industries))[:20]}")
            
            # Save empty result
            if user_id:
                try:
                    search_config_data = {
                        'industries': industries,
                        'min_seniority': min_seniority,
                        'limit': limit,
                        'preset': preset
                    }
                    supabase.table('ai_target_search_results').insert({
                        'user_id': user_id,
                        'search_config': search_config_data,
                        'results': [],
                        'result_count': 0,
                        'status': 'completed'
                    }).execute()
                except Exception as save_error:
                    logger.warning(f"Failed to save search result: {save_error}")
            
            return jsonify({
                'success': True,
                'recommendations': [],
                'count': 0,
                'search_id': None,
                'message': f'No contacts found for industry: {", ".join(industries)}. Check server logs for diagnostic information.'
            })
        
        # Convert to list of dicts and filter by industries
        contacts = []
        logger.debug(f"Fetched {len(contacts_response.data)} contacts from database before industry filtering")
        logger.debug(f"Filtering for industries: {industries}")
        
        # Quick check: if we have contacts but none match, try fallback query
        # This is important because Supabase ilike might not work as expected in all cases
        if contacts_response.data and industries and len(industries) == 1:
            quick_match_count = 0
            sample_industries_found = set()
            for c in contacts_response.data[:20]:  # Check first 20
                contact_industry = (c.get('industry') or '').strip().lower()
                if not contact_industry and c.get('companies') and c['companies'].get('industry'):
                    contact_industry = (c['companies'].get('industry') or '').strip().lower()
                if contact_industry:
                    sample_industries_found.add(contact_industry)
                    # Check if this contact matches the requested industry
                    requested_industry_lower = industries[0].strip().lower()
                    if (requested_industry_lower in contact_industry or 
                        contact_industry in requested_industry_lower or
                        contact_industry == requested_industry_lower):
                        quick_match_count += 1
                        break  # Found at least one match
            
            logger.debug(f"Quick match check: {quick_match_count} matches found in first 20 contacts")
            logger.debug(f"Sample industries in fetched contacts: {sorted(list(sample_industries_found))}")
            
            # If no matches in first 20, try fallback query (fetch all and filter in Python)
            if quick_match_count == 0:
                logger.warning(f"No matching contacts found in first 20 results for '{industries[0]}'. Trying fallback query (no industry filter)...")
                # First, check if retail contacts exist at all
                retail_check_query = supabase.table('contacts').select('id, industry').ilike('industry', '%retail%')
                if exclude_processed:
                    retail_check_query = retail_check_query.eq('is_target', False)
                retail_check_query = retail_check_query.limit(10)
                retail_check_response = retail_check_query.execute()
                if retail_check_response.data:
                    logger.warning(f"Found {len(retail_check_response.data)} contacts with 'retail' in industry field. Initial query may have missed them.")
                    # Use the retail-specific query but with higher limit
                    fallback_query = supabase.table('contacts').select('*, companies(name, industry, domain)')
                    if exclude_processed:
                        fallback_query = fallback_query.eq('is_target', False)
                    # Try lowercase version of industry name
                    fallback_query = fallback_query.ilike('industry', f'%{industries[0].strip().lower()}%')
                    fallback_query = fallback_query.limit(max(fetch_limit * 2, 1000))  # Get more for filtering
                    fallback_response = fallback_query.execute()
                    if fallback_response.data:
                        logger.warning(f"Fallback query (lowercase) found {len(fallback_response.data)} contacts. Will filter in Python for industry '{industries[0]}'.")
                        contacts_response = fallback_response
                else:
                    # No retail contacts found even with direct query - try fetching all and filtering
                    logger.warning(f"No contacts found with 'retail' in industry. Fetching all contacts for Python filtering...")
                    fallback_query = supabase.table('contacts').select('*, companies(name, industry, domain)')
                    if exclude_processed:
                        fallback_query = fallback_query.eq('is_target', False)
                    fallback_query = fallback_query.limit(max(fetch_limit * 3, 1000))  # Get more for filtering
                    fallback_response = fallback_query.execute()
                    if fallback_response.data:
                        logger.warning(f"Fallback query (no filter) found {len(fallback_response.data)} contacts. Will filter in Python for industry '{industries[0]}'.")
                        contacts_response = fallback_response
        
        for c in contacts_response.data:
            # Get industry from contact or company (prioritize contact industry)
            contact_industry = (c.get('industry') or '').strip()
            company_industry = None
            if c.get('companies') and c['companies'].get('industry'):
                company_industry = (c['companies'].get('industry') or '').strip()
            
            # Use company industry if contact industry is missing
            if not contact_industry and company_industry:
                contact_industry = company_industry
                logger.debug(f"Contact {c.get('name', 'Unknown')}: Using company industry '{contact_industry}'")
            
            contact_industry_lower = contact_industry.lower() if contact_industry else ''
            company_industry_lower = company_industry.lower() if company_industry else ''
            
            # Check if contact matches any of the selected industries (case-insensitive, flexible matching)
            matches = False
            matched_industry = None
            for ind in industries:
                ind_clean = ind.strip().lower()
                
                # Normalize industry names for better matching
                # Remove common variations: "&" -> "and", remove commas, remove extra spaces, etc.
                ind_normalized = ind_clean.replace('&', 'and').replace(',', ' ').replace('  ', ' ').strip()
                contact_normalized = contact_industry_lower.replace('&', 'and').replace(',', ' ').replace('  ', ' ').strip()
                company_normalized = company_industry_lower.replace('&', 'and').replace(',', ' ').replace('  ', ' ').strip() if company_industry_lower else ''
                
                # Extract key words from requested industry (words > 3 characters)
                ind_words = [w for w in ind_normalized.split() if len(w) > 3]
                contact_words = contact_industry_lower.split()
                company_words = company_industry_lower.split() if company_industry_lower else []
                
                # Flexible matching: check multiple variations
                match_checks = [
                    ind_clean in contact_industry_lower,
                    contact_industry_lower in ind_clean,
                    contact_industry_lower == ind_clean,
                    ind_normalized in contact_normalized,
                    contact_normalized in ind_normalized,
                    contact_normalized == ind_normalized,
                    # Word-based matching: check if key words from requested industry appear in contact industry
                    any(word in contact_industry_lower for word in ind_words) if ind_words else False,
                    any(word in ind_clean for word in contact_words if len(word) > 3) if contact_words else False,
                ]
                
                # Also check company industry if available
                if company_industry_lower:
                    match_checks.extend([
                        ind_clean in company_industry_lower,
                        company_industry_lower in ind_clean,
                        company_industry_lower == ind_clean,
                        ind_normalized in company_normalized,
                        company_normalized in ind_normalized,
                        company_normalized == ind_normalized,
                        # Word-based matching for company industry
                        any(word in company_industry_lower for word in ind_words) if ind_words else False,
                        any(word in ind_clean for word in company_words if len(word) > 3) if company_words else False,
                    ])
                
                if any(match_checks):
                    matches = True
                    matched_industry = ind
                    logger.debug(f"Contact {c.get('name', 'Unknown')} matches industry '{ind}' (contact industry: '{contact_industry}', company industry: '{company_industry}')")
                    break
            
            if not matches:
                if contact_industry or company_industry:
                    logger.debug(f"Contact {c.get('name', 'Unknown')} does not match (contact: '{contact_industry}', company: '{company_industry}', selected: {industries})")
                continue
            
            contact_dict = {
                'id': str(c.get('id', '')),
                'name': c.get('name', ''),
                'role': c.get('role', ''),
                'email': c.get('email', ''),
                'phone': c.get('phone', ''),
                'linkedin': c.get('linkedin', ''),
                'company': c.get('company', ''),
                'industry': c.get('industry', '')
            }
            if c.get('companies'):
                contact_dict['company_name'] = c['companies'].get('name', contact_dict['company'])
                if not contact_dict['industry']:
                    contact_dict['industry'] = c['companies'].get('industry', '')
            contacts.append(contact_dict)
        
        # Track which contact IDs were analyzed (for updating analysis tracking)
        analyzed_contact_ids = [c.get('id') for c in contacts if c.get('id')]
        
        # Use AI service to identify targets (use first industry for context, but results include all)
        primary_industry = industries[0] if industries else 'general'
        identification_service = get_target_identification_service()
        recommendations = identification_service.identify_targets(
            industry=primary_industry,
            contacts=contacts,
            limit=limit,
            min_seniority=min_seniority
        )
        
        # Update contact analysis tracking (mark as analyzed)
        if analyzed_contact_ids:
            try:
                from datetime import datetime
                now = datetime.utcnow().isoformat()
                # Update last_analyzed_at and increment analysis_count for all analyzed contacts
                for contact_id in analyzed_contact_ids:
                    # Get current analysis_count
                    current_contact = supabase.table('contacts').select('analysis_count').eq('id', contact_id).limit(1).execute()
                    current_count = current_contact.data[0].get('analysis_count', 0) if current_contact.data else 0
                    
                    # Update contact
                    supabase.table('contacts').update({
                        'last_analyzed_at': now,
                        'analysis_count': current_count + 1
                    }).eq('id', contact_id).execute()
            except Exception as track_error:
                logger.warning(f"Failed to update contact analysis tracking: {track_error}")
                # Don't fail the request if tracking fails
        
        # Convert recommendations to dicts for storage and add overall_score
        # Also add contact processing status for frontend display
        recommendations_dicts = []
        for r in recommendations:
            rec_dict = r.to_dict() if hasattr(r, 'to_dict') else r
            # Calculate overall_score if not present
            if 'overall_score' not in rec_dict:
                seniority = rec_dict.get('seniority_score', 0.5)
                confidence = rec_dict.get('confidence_score', 0.5)
                rec_dict['overall_score'] = (seniority * 0.6 + confidence * 0.4)
            
            # Add contact processing status for frontend badges
            contact_id = rec_dict.get('contact_id')
            if contact_id:
                try:
                    contact_status = supabase.table('contacts').select('is_target, last_analyzed_at, analysis_count').eq('id', contact_id).limit(1).execute()
                    if contact_status.data:
                        rec_dict['is_target'] = contact_status.data[0].get('is_target', False)
                        rec_dict['last_analyzed_at'] = contact_status.data[0].get('last_analyzed_at')
                        rec_dict['analysis_count'] = contact_status.data[0].get('analysis_count', 0)
                except Exception as status_error:
                    logger.warning(f"Failed to fetch contact status for {contact_id}: {status_error}")
                    rec_dict['is_target'] = False
                    rec_dict['last_analyzed_at'] = None
            
            recommendations_dicts.append(rec_dict)
        
        # Check if report already exists for this search configuration (to save resources)
        existing_report = None
        existing_search_id = None
        if user_id and data.get('generate_report', False):
            try:
                # Create a hash of search config for comparison
                search_config_hash = {
                    'industries': sorted(industries) if isinstance(industries, list) else [industries],
                    'min_seniority': min_seniority,
                    'limit': limit,
                    'preset': preset,
                    'exclude_processed': exclude_processed
                }
                
                # Check for existing report with same config
                existing_result = supabase.table('ai_target_search_results').select('id, report, report_generated_at').eq('user_id', user_id).eq('status', 'completed').not_.is_('report', 'null').order('report_generated_at', desc=True).limit(10).execute()
                
                if existing_result.data:
                    import json
                    for existing in existing_result.data:
                        existing_config = existing.get('search_config', {})
                        if existing_config:
                            # Compare search configs (normalize industries for comparison)
                            existing_industries = sorted(existing_config.get('industries', []))
                            current_industries = sorted(industries) if isinstance(industries, list) else [industries]
                            
                            if (existing_industries == current_industries and
                                existing_config.get('min_seniority') == min_seniority and
                                existing_config.get('limit') == limit and
                                existing_config.get('preset') == preset):
                                existing_report = existing.get('report')
                                existing_search_id = str(existing['id'])
                                logger.info(f"Found existing report for search config (ID: {existing_search_id})")
                                break
            except Exception as check_error:
                logger.warning(f"Error checking for existing report: {check_error}")
        
        # Generate detailed report if requested and not found in cache
        report = existing_report
        if data.get('generate_report', False) and not report:
            try:
                from app.services.recommendation_report_generator import RecommendationReportGenerator
                # Use primary industry for report generation
                primary_industry = industries[0] if industries else 'General'
                report = RecommendationReportGenerator.generate_report(
                    recommendations=recommendations_dicts,
                    industry=primary_industry,
                    search_config={
                        'industries': industries,
                        'min_seniority': min_seniority,
                        'limit': limit,
                        'preset': preset
                    }
                )
                logger.info("Generated new report")
            except Exception as report_error:
                logger.warning(f"Failed to generate report: {report_error}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Save search results to database (with report if generated)
        search_id = existing_search_id
        if user_id:
            try:
                search_config_data = {
                    'industries': industries,
                    'min_seniority': min_seniority,
                    'limit': limit,
                    'preset': preset,
                    'exclude_processed': exclude_processed
                }
                
                insert_data = {
                    'user_id': user_id,
                    'search_config': search_config_data,
                    'results': recommendations_dicts,
                    'result_count': len(recommendations),
                    'status': 'completed'
                }
                
                # Add report if generated
                if report:
                    from datetime import datetime
                    insert_data['report'] = report
                    insert_data['report_generated_at'] = datetime.utcnow().isoformat()
                
                result = supabase.table('ai_target_search_results').insert(insert_data).execute()
                
                if result.data:
                    search_id = str(result.data[0]['id'])
            except Exception as save_error:
                logger.error(f"Failed to save search result: {save_error}")
                import traceback
                logger.error(traceback.format_exc())
        
        response_data = {
            'success': True,
            'recommendations': recommendations_dicts,
            'count': len(recommendations),
            'search_id': search_id,
            'excluded_count': excluded_count if exclude_processed else 0,
            'exclude_processed': exclude_processed
        }
        
        if report:
            response_data['report'] = report
            response_data['report_cached'] = existing_report is not None  # Indicate if report was from cache
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in AI target identification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/ai-create', methods=['POST'])
@require_auth
@require_use_case('ai_target_finder')
def ai_create_targets():
    """Create targets from AI recommendations with auto-generated content"""
    try:
        data = request.get_json() or {}
        recommendation_ids = data.get('recommendation_ids', [])
        auto_link = data.get('auto_link', True)
        
        if not recommendation_ids:
            return jsonify({'error': 'recommendation_ids is required'}), 400
        
        # Get current user for industry assignment
        user = get_current_user()
        user_industry_id = None
        is_industry_admin = getattr(user, 'is_industry_admin', False) if user else False
        
        if user:
            if hasattr(user, 'industry_id') and user.industry_id:
                user_industry_id = str(user.industry_id)
            elif hasattr(user, 'active_industry_id') and user.active_industry_id:
                user_industry_id = str(user.active_industry_id)
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        identification_service = get_target_identification_service()
        rag_client = get_rag_client()
        gemini_client = get_gemini_client()
        
        created_targets = []
        
        # Get contacts for recommendations - try to find by ID (handle both string and UUID formats)
        contacts_dict = {}
        if recommendation_ids:
            # Try to fetch contacts by IDs directly (more efficient)
            try:
                # Convert all IDs to strings for comparison
                rec_ids_str = [str(rid) for rid in recommendation_ids]
                contacts_query = supabase.table('contacts').select('*').in_('id', rec_ids_str)
                contacts_response = contacts_query.execute()
                if contacts_response.data:
                    # Create dict with both string and original format keys
                    for c in contacts_response.data:
                        contact_id_str = str(c['id'])
                        contacts_dict[contact_id_str] = c
                        # Also store with original ID format if different
                        if contact_id_str != c['id']:
                            contacts_dict[c['id']] = c
            except Exception as e:
                logger.warning(f"Error fetching contacts by IDs: {e}, falling back to full query")
                # Fallback: fetch all contacts
                contacts_query = supabase.table('contacts').select('*')
                contacts_response = contacts_query.execute()
                if contacts_response.data:
                    for c in contacts_response.data:
                        contact_id_str = str(c['id'])
                        contacts_dict[contact_id_str] = c
                        contacts_dict[c['id']] = c
        
        for rec_id in recommendation_ids:
            try:
                # Find contact by ID (try both string and original format)
                rec_id_str = str(rec_id)
                contact = contacts_dict.get(rec_id_str) or contacts_dict.get(rec_id)
                if not contact:
                    logger.warning(f"Contact not found for recommendation ID: {rec_id} (tried as string: {rec_id_str})")
                    continue
                
                # Create recommendation object
                recommendation = TargetRecommendation(
                    contact_id=str(contact['id']),
                    contact_name=contact.get('name', ''),
                    company_name=contact.get('company', ''),
                    role=contact.get('role', ''),
                    email=contact.get('email', ''),
                    phone=contact.get('phone', ''),
                    linkedin_url=contact.get('linkedin', ''),
                    seniority_score=0.7,  # Default, will be updated by AI
                    solution_fit='both',
                    confidence_score=0.7,
                    identified_gaps=[],
                    recommended_pitch_angle='',
                    pain_points=[],
                    reasoning='',
                    industry=contact.get('industry', '')
                )
                
                # Get industry context and knowledge
                industry = recommendation.industry or 'FMCG'
                industry_context = get_industry_context(industry)
                rag_knowledge = rag_client.query(
                    f"{industry} case studies services insights",
                    industry=industry,
                    top_k=5
                )
                gemini_insights = gemini_client.query_notebook_lm(
                    query=f"{industry} customer examples",
                    company_name=recommendation.company_name,
                    industry=industry
                )
                
                # Generate content (pain point, pitch angle, script)
                content = identification_service.generate_target_content(
                    recommendation,
                    industry,
                    industry_context,
                    rag_knowledge.get('results', {}),
                    gemini_insights
                )
                
                # Auto-assign industry_id - prioritize user's current industry
                target_industry_id = None
                if user_industry_id:
                    # Use user's current industry (for both industry admins and regular users)
                    target_industry_id = user_industry_id
                elif contact.get('industry'):
                    # Fallback: try to match contact's industry
                    industry_lookup = supabase.table('industries').select('id').ilike('name', f'%{contact["industry"]}%').limit(1).execute()
                    if industry_lookup.data:
                        target_industry_id = str(industry_lookup.data[0]['id'])
                
                # Create target
                target_data = {
                    'company_name': recommendation.company_name,
                    'contact_name': recommendation.contact_name,
                    'role': recommendation.role,
                    'email': recommendation.email,
                    'phone': recommendation.phone,
                    'linkedin_url': recommendation.linkedin_url,
                    'pain_point': content.get('pain_point', ''),
                    'pitch_angle': content.get('pitch_angle', ''),
                    'script': content.get('script', ''),
                    'status': TargetStatus.NEW.value
                }
                
                if target_industry_id:
                    target_data['industry_id'] = target_industry_id
                
                if auto_link and contact.get('id'):
                    target_data['contact_id'] = str(contact['id'])
                    # Try to find company
                    if contact.get('company_id'):
                        target_data['company_id'] = str(contact['company_id'])
                
                target = Target(**target_data)
                target_dict = target.to_dict()
                target_dict.pop('id', None)  # Remove id for insert
                
                insert_response = supabase.table('targets').insert(target_dict).execute()
                
                if insert_response.data:
                    created_target = Target.from_dict(insert_response.data[0])
                    created_targets.append(created_target.to_dict())
                    
            except Exception as e:
                logger.error(f"Error creating target from recommendation {rec_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        return jsonify({
            'success': True,
            'targets': created_targets,
            'count': len(created_targets),
            'created_count': len(created_targets)  # Frontend expects this field
        })
        
    except Exception as e:
        logger.error(f"Error in AI target creation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/ai-reports', methods=['GET'])
@require_auth
@require_use_case('ai_target_finder')
def list_stored_reports():
    """List all stored reports for the current user"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        user_id = str(user.id) if hasattr(user, 'id') else None
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get limit and offset from query params
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Fetch reports (only those with reports generated)
        result = supabase.table('ai_target_search_results').select(
            'id, search_config, report_generated_at, result_count, created_at'
        ).eq('user_id', user_id).not_.is_('report', 'null').order('report_generated_at', desc=True).limit(limit).offset(offset).execute()
        
        reports = []
        if result.data:
            for r in result.data:
                reports.append({
                    'id': str(r['id']),
                    'search_config': r.get('search_config', {}),
                    'report_generated_at': r.get('report_generated_at'),
                    'result_count': r.get('result_count', 0),
                    'created_at': r.get('created_at')
                })
        
        return jsonify({
            'success': True,
            'reports': reports,
            'count': len(reports)
        })
        
    except Exception as e:
        logger.error(f"Error listing stored reports: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/ai-reports/<report_id>', methods=['GET'])
@require_auth
@require_use_case('ai_target_finder')
def get_stored_report(report_id):
    """Retrieve a specific stored report"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        user_id = str(user.id) if hasattr(user, 'id') else None
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Fetch the report
        result = supabase.table('ai_target_search_results').select(
            'id, search_config, report, report_generated_at, result_count, results, created_at'
        ).eq('id', report_id).eq('user_id', user_id).execute()
        
        if not result.data:
            return jsonify({'error': 'Report not found'}), 404
        
        report_data = result.data[0]
        
        return jsonify({
            'success': True,
            'report': {
                'id': str(report_data['id']),
                'search_config': report_data.get('search_config', {}),
                'report': report_data.get('report'),
                'report_generated_at': report_data.get('report_generated_at'),
                'result_count': report_data.get('result_count', 0),
                'results': report_data.get('results', []),
                'created_at': report_data.get('created_at')
            }
        })
        
    except Exception as e:
        logger.error(f"Error retrieving stored report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/ai-search-history', methods=['GET'])
@require_auth
@require_use_case('ai_target_finder')
def get_ai_search_history():
    """Get AI target search history for current user"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        user_id = str(user.id) if hasattr(user, 'id') else None
        if not user_id:
            return jsonify({'error': 'User ID not found'}), 400
        
        # Check if fetching a specific search by ID
        search_id = request.args.get('search_id')
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        if search_id:
            # Fetch specific search
            try:
                response = supabase.table('ai_target_search_results')\
                    .select('*')\
                    .eq('id', search_id)\
                    .eq('user_id', user_id)\
                    .execute()
            except Exception as table_error:
                error_msg = str(table_error).lower()
                if 'relation' in error_msg and 'does not exist' in error_msg:
                    return jsonify({
                        'error': 'Database table does not exist. Please run migration 016_ai_target_search_results.sql'
                    }), 404
                raise
            
            if not response.data:
                return jsonify({'error': 'Search not found'}), 404
            
            search = response.data[0]
            search_config = search.get('search_config', {})
            search_result = {
                'id': str(search['id']),
                'search_config': search_config,
                'industries': search_config.get('industries', []),
                'preset': search_config.get('preset', 'custom'),
                'min_seniority': search_config.get('min_seniority', 0.5),
                'limit': search_config.get('limit', 10),
                'result_count': search.get('result_count', 0),
                'status': search.get('status', 'completed'),
                'created_at': search.get('created_at'),
                'results': search.get('results', [])
            }
            
            return jsonify({
                'success': True,
                'searches': [search_result]
            })
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        # Fetch search history for user, ordered by most recent first
        try:
            response = supabase.table('ai_target_search_results')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .range(offset, offset + per_page - 1)\
                .execute()
        except Exception as table_error:
            # Table might not exist - check if it's a relation error
            error_msg = str(table_error).lower()
            if 'relation' in error_msg and 'does not exist' in error_msg:
                logger.warning("ai_target_search_results table does not exist. Migration 016 needs to be run.")
                return jsonify({
                    'success': True,
                    'searches': [],
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0,
                    'message': 'No search history. Run a search to create history. (Note: Database migration may be required)'
                })
            raise
        
        # Get total count
        try:
            count_response = supabase.table('ai_target_search_results')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            
            total_count = count_response.count if hasattr(count_response, 'count') else (len(response.data) if response.data else 0)
        except Exception:
            # If count fails, use length of response data
            total_count = len(response.data) if response.data else 0
        
        # Format results
        searches = []
        for search in response.data:
            search_config = search.get('search_config', {})
            searches.append({
                'id': str(search['id']),
                'search_config': search_config,
                'industries': search_config.get('industries', []),
                'preset': search_config.get('preset', 'custom'),
                'min_seniority': search_config.get('min_seniority', 0.5),
                'limit': search_config.get('limit', 10),
                'result_count': search.get('result_count', 0),
                'status': search.get('status', 'completed'),
                'created_at': search.get('created_at'),
                'results': search.get('results', [])  # Include full results for viewing
            })
        
        return jsonify({
            'success': True,
            'searches': searches,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Error fetching AI search history: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@targets_bp.route('/api/targets/export', methods=['GET'])
@require_auth
@require_use_case('sheets_import_export')
def export_targets():
    """Export targets to Google Sheets"""
    try:
        from app.integrations.google_sheets_client import GoogleSheetsClient
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get all targets
        response = supabase.table('targets').select('*').execute()
        targets = [Target.from_dict(t) for t in response.data]
        
        if not targets:
            return jsonify({
                'success': False,
                'error': 'No targets to export. Please add targets first.'
            }), 400
        
        try:
            # Export to Google Sheets
            sheets_client = GoogleSheetsClient()
        except ValueError as e:
            # Google Sheets not configured
            return jsonify({
                'success': False,
                'error': 'Google Sheets credentials not found. Please configure GOOGLE_SHEETS_CREDENTIALS_PATH and GOOGLE_SHEETS_SPREADSHEET_ID in .env.local'
            }), 400
        
        targets_dicts = [t.to_dict() for t in targets]
        success = sheets_client.export_targets(targets_dicts)
        
        if success:
            return jsonify({
                'success': True,
                'exported': len(targets)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to export to Google Sheets. Check logs for details.'
            }), 500
        
    except Exception as e:
        logger.error(f"Error exporting targets: {e}")
        error_msg = str(e)
        if 'credentials' in error_msg.lower() or 'not found' in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'Google Sheets not configured. Please add credentials to .env.local'
            }), 400
        return jsonify({'error': error_msg}), 500

