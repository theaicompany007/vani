"""Target management API routes"""
from flask import Blueprint, request, jsonify, current_app
import logging
import json
from app.models.targets import Target, TargetStatus
from app.models.target_recommendation import TargetRecommendation
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_use_case, get_current_user, get_current_industry
from app.services.target_identification import get_target_identification_service
from app.services.industry_context import get_industry_context
from app.integrations.rag_client import get_rag_client
from app.integrations.gemini_client import get_gemini_client
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)

targets_bp = Blueprint('targets', __name__)


@targets_bp.route('/api/targets', methods=['GET'])
@require_auth
@require_use_case('target_management')
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
        
        # Build query with industry filtering
        query = supabase.table('targets').select('*, contacts(industry), companies(industry)')
        
        # For industry filtering, we'll filter after fetching to handle derived industry from contacts/companies
        # But we can optimize by pre-filtering on industry_id if available
        logger.debug(f"list_targets: user_industry_id={user_industry_id}, is_super_user={is_super_user}, is_industry_admin={is_industry_admin}, industry_param={industry_param}")
        
        if status:
            query = query.eq('status', status)
        if company:
            query = query.ilike('company_name', f'%{company}%')
        
        query = query.order('created_at', desc=True).limit(limit * 2).offset(offset)  # Fetch more to filter
        response = query.execute()
        
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
                if is_industry_admin and user_industry_id:
                    # Industry admin: Must match their industry
                    if not target_industry_id:
                        logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Skipped - no industry_id (industry admin filter)")
                        continue
                    if target_industry_id != user_industry_id:
                        logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: Skipped - industry_id mismatch (target={target_industry_id}, user={user_industry_id})")
                        continue
                    logger.debug(f"Target {target_dict.get('company_name', 'Unknown')}: PASSED industry admin filter (industry_id={target_industry_id})")
                elif is_super_user and industry_param:
                    # Super user with manual filter: Check if matches
                    if target_industry_id:
                        industry_lookup = supabase.table('industries').select('name').eq('id', target_industry_id).limit(1).execute()
                        if industry_lookup.data:
                            industry_name = industry_lookup.data[0]['name']
                            if industry_param.lower() not in industry_name.lower():
                                continue
                    else:
                        # If no industry_id on target, skip (super user with manual filter wants specific industry)
                        continue
                elif user_industry_id:
                    # User (including super user) with active_industry_id: Filter by active industry
                    # Super users can still filter by active industry for convenience
                    # Only show targets that have industry_id matching active industry
                    if not target_industry_id or target_industry_id != user_industry_id:
                        continue
                
                # Enrich with contact/company data if linked
                if target_dict.get('contact_id'):
                    contact_response = supabase.table('contacts').select('*').eq('id', target_dict['contact_id']).limit(1).execute()
                    if contact_response.data:
                        target_dict['contact'] = contact_response.data[0]
                
                if target_dict.get('company_id'):
                    company_response = supabase.table('companies').select('*').eq('id', target_dict['company_id']).limit(1).execute()
                    if company_response.data:
                        target_dict['company'] = company_response.data[0]
                
                # Add industry information
                if target_industry_id:
                    target_dict['industry_id'] = target_industry_id
                
                targets.append(target_dict)
                
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


@targets_bp.route('/api/targets/<target_id>', methods=['PUT'])
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
        
        try:
            sheets_client = GoogleSheetsClient()
        except ValueError as e:
            # Google Sheets not configured
            return jsonify({
                'success': False,
                'error': 'Google Sheets credentials not found. Please configure GOOGLE_SHEETS_CREDENTIALS_PATH and GOOGLE_SHEETS_SPREADSHEET_ID in .env.local'
            }), 400
        
        try:
            targets_data = sheets_client.import_targets()
        except Exception as e:
            error_msg = str(e)
            if 'index' in error_msg.lower() or 'empty' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'error': 'Google Sheets is empty or "Targets" sheet not found. Please ensure the sheet exists and has data.'
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
                    
                target = Target(**target_data)
                target_dict = target.to_dict()
                target_dict.pop('id', None)
                
                supabase.table('targets').insert(target_dict).execute()
                imported_count += 1
            except Exception as e:
                logger.warning(f"Failed to import target {target_data.get('company_name', 'Unknown')}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'imported': imported_count,
            'total': len(targets_data)
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
        
        return jsonify({
            'success': True,
            'message': 'Target deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting target: {e}")
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
        
        contacts_query = supabase.table('contacts').select('*, companies(name, industry, domain)')
        
        # Filter by industries (OR logic - contact can match any of the selected industries)
        if is_industry_admin and user_industry_id:
            # Get industry name from industry_id
            industry_lookup = supabase.table('industries').select('name').eq('id', user_industry_id).limit(1).execute()
            if industry_lookup.data:
                industry_name = industry_lookup.data[0]['name']
                contacts_query = contacts_query.ilike('industry', f'%{industry_name}%')
        else:
            # Multiple industries: use OR logic
            # Supabase doesn't support OR directly, so we'll filter in Python or use multiple queries
            # For now, use the first industry and filter others in Python
            if industries:
                # Try to match any industry (case-insensitive)
                industry_filter = '|'.join(industries)
                contacts_query = contacts_query.or_(f'industry.ilike.%{industries[0]}%')
                # For multiple industries, we'll filter in Python after fetching
        
        contacts_query = contacts_query.limit(limit * 3)  # Get more to filter
        contacts_response = contacts_query.execute()
        
        if not contacts_response.data:
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
                'search_id': None
            })
        
        # Convert to list of dicts and filter by industries
        contacts = []
        for c in contacts_response.data:
            contact_industry = (c.get('industry') or '').lower()
            # Check if contact matches any of the selected industries
            matches = False
            for ind in industries:
                if ind.lower() in contact_industry or contact_industry in ind.lower():
                    matches = True
                    break
            
            if not matches:
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
        
        # Use AI service to identify targets (use first industry for context, but results include all)
        primary_industry = industries[0] if industries else 'general'
        identification_service = get_target_identification_service()
        recommendations = identification_service.identify_targets(
            industry=primary_industry,
            contacts=contacts,
            limit=limit,
            min_seniority=min_seniority
        )
        
        # Convert recommendations to dicts for storage
        recommendations_dicts = [r.to_dict() for r in recommendations]
        
        # Save search results to database
        search_id = None
        if user_id:
            try:
                search_config_data = {
                    'industries': industries,
                    'min_seniority': min_seniority,
                    'limit': limit,
                    'preset': preset
                }
                result = supabase.table('ai_target_search_results').insert({
                    'user_id': user_id,
                    'search_config': search_config_data,
                    'results': recommendations_dicts,
                    'result_count': len(recommendations),
                    'status': 'completed'
                }).execute()
                
                if result.data:
                    search_id = str(result.data[0]['id'])
            except Exception as save_error:
                logger.error(f"Failed to save search result: {save_error}")
                import traceback
                logger.error(traceback.format_exc())
        
        return jsonify({
            'success': True,
            'recommendations': recommendations_dicts,
            'count': len(recommendations),
            'search_id': search_id
        })
        
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
        
        # Get contacts for recommendations
        contacts_query = supabase.table('contacts').select('*')
        contacts_response = contacts_query.execute()
        contacts_dict = {str(c['id']): c for c in contacts_response.data} if contacts_response.data else {}
        
        for rec_id in recommendation_ids:
            try:
                # Find contact by ID (rec_id should be contact_id)
                contact = contacts_dict.get(rec_id)
                if not contact:
                    logger.warning(f"Contact not found for recommendation ID: {rec_id}")
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
                
                # Auto-assign industry_id
                target_industry_id = None
                if is_industry_admin and user_industry_id:
                    target_industry_id = user_industry_id
                elif contact.get('industry'):
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
            'count': len(created_targets)
        })
        
    except Exception as e:
        logger.error(f"Error in AI target creation: {e}")
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

