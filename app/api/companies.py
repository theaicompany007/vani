"""Companies API routes"""
from flask import Blueprint, request, jsonify, current_app
import logging
from app.models.companies import Company
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_use_case, get_current_industry
from uuid import UUID

logger = logging.getLogger(__name__)

companies_bp = Blueprint('companies', __name__)


@companies_bp.route('/api/companies', methods=['GET'])
@require_auth
@require_use_case('company_management')
def list_companies():
    """List all companies with optional filters and industry-based access control"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            logger.error("Supabase client not available")
            return jsonify({'error': 'Supabase not configured', 'success': False}), 503
        
        # Get current user for industry-based filtering
        from app.auth import get_current_user
        user = get_current_user()
        user_industry_id = None
        is_industry_admin = False
        is_super_user = False
        
        if user:
            is_industry_admin = getattr(user, 'is_industry_admin', False)
            is_super_user = getattr(user, 'is_super_user', False)
            if hasattr(user, 'industry_id') and user.industry_id:
                user_industry_id = str(user.industry_id)
            elif hasattr(user, 'active_industry_id') and user.active_industry_id:
                user_industry_id = str(user.active_industry_id)
        
        # Get query parameters
        industry = request.args.get('industry')  # Manual filter (super users only)
        search = request.args.get('search')
        limit = int(request.args.get('limit', 500))
        offset = int(request.args.get('offset', 0))
        
        logger.debug(f"Listing companies: industry={industry}, search={search}, limit={limit}, offset={offset}")
        
        # Industry-based filtering - only apply if user is NOT a super user
        # Super users should see all companies regardless of industry
        if is_industry_admin and user_industry_id and not is_super_user:
            # Industry admin: Only see companies from their assigned industry
            # Get industry name from industry_id
            industry_lookup = supabase.table('industries').select('name').eq('id', user_industry_id).limit(1).execute()
            if industry_lookup.data:
                industry = industry_lookup.data[0]['name']  # Override with user's industry
        
        # Get total count first (before filtering and pagination)
        count_query = supabase.table('companies').select('id', count='exact')
        
        if industry:
            count_query = count_query.ilike('industry', f'%{industry}%')
        elif user_industry_id and not is_super_user:
            # Regular user: Filter by active_industry_id (only if not super user)
            industry_lookup = supabase.table('industries').select('name').eq('id', user_industry_id).limit(1).execute()
            if industry_lookup.data:
                industry_name = industry_lookup.data[0]['name']
                count_query = count_query.ilike('industry', f'%{industry_name}%')
        
        if search:
            count_query = count_query.or_(f'name.ilike.%{search}%,domain.ilike.%{search}%,industry.ilike.%{search}%')
        
        # Execute count query
        count_response = count_query.execute()
        # Try multiple ways to get the count
        if hasattr(count_response, 'count') and count_response.count is not None:
            total_count = count_response.count
        elif hasattr(count_response, 'data') and count_response.data:
            total_count = len(count_response.data)
        else:
            # Fallback: query all matching records to count
            all_query = supabase.table('companies').select('id')
            if industry:
                all_query = all_query.ilike('industry', f'%{industry}%')
            elif user_industry_id and not is_super_user:
                industry_lookup = supabase.table('industries').select('name').eq('id', user_industry_id).limit(1).execute()
                if industry_lookup.data:
                    industry_name = industry_lookup.data[0]['name']
                    all_query = all_query.ilike('industry', f'%{industry_name}%')
            if search:
                all_query = all_query.or_(f'name.ilike.%{search}%,domain.ilike.%{search}%,industry.ilike.%{search}%')
            all_response = all_query.execute()
            total_count = len(all_response.data) if all_response.data else 0
        
        # Select companies
        query = supabase.table('companies').select('*')
        
        if industry:
            query = query.ilike('industry', f'%{industry}%')
        elif user_industry_id and not is_super_user:
            # Regular user: Filter by active_industry_id (only if not super user)
            industry_lookup = supabase.table('industries').select('name').eq('id', user_industry_id).limit(1).execute()
            if industry_lookup.data:
                industry_name = industry_lookup.data[0]['name']
                query = query.ilike('industry', f'%{industry_name}%')
        
        if search:
            query = query.or_(f'name.ilike.%{search}%,domain.ilike.%{search}%,industry.ilike.%{search}%')
        
        query = query.order('created_at', desc=True).limit(limit).offset(offset)
        response = query.execute()
        
        # Check for Supabase errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Supabase error listing companies: {response.error}")
            return jsonify({'error': str(response.error), 'success': False}), 500
        
        # Handle response data
        companies_data = response.data if hasattr(response, 'data') else []
        if companies_data is None:
            companies_data = []
        
        logger.debug(f"Found {len(companies_data)} companies")
        
        companies_list = []
        
        # Optimize: Get contact counts efficiently to avoid timeout issues
        # For large datasets, we'll skip contact counts to ensure fast loading
        company_ids = [str(c.get('id', '')) for c in companies_data if c.get('id')]
        contact_counts = {}
        
        # Performance optimization: Skip contact counts for large lists to avoid timeout
        # Contact counts can be loaded on-demand when viewing individual company details
        # This ensures the list loads quickly even with 1000+ companies
        skip_contact_counts = len(company_ids) > 50  # Skip counts if more than 50 companies
        
        if skip_contact_counts:
            logger.info(f"Skipping contact counts for {len(company_ids)} companies to ensure fast loading")
            # All counts will default to 0
        else:
            # For smaller lists (<=50), fetch contact counts with timeout protection
            try:
                import time
                start_time = time.time()
                timeout_seconds = 5  # Max 5 seconds for contact count queries
                
                for company_id in company_ids:
                    # Check timeout
                    if time.time() - start_time > timeout_seconds:
                        logger.warning(f"Contact count query timeout after {timeout_seconds}s, skipping remaining")
                        break
                    
                    try:
                        count_response = supabase.table('contacts')\
                            .select('id', count='exact')\
                            .eq('company_id', company_id)\
                            .limit(1)\
                            .execute()
                        
                        if hasattr(count_response, 'count') and count_response.count is not None:
                            contact_counts[company_id] = count_response.count
                        else:
                            contact_counts[company_id] = 0
                    except Exception as single_error:
                        # Skip this company's count if it times out or errors
                        logger.debug(f"Error getting contact count for company {company_id}: {single_error}")
                        contact_counts[company_id] = 0
                        continue
            except Exception as count_error:
                logger.warning(f"Error getting contact counts (will default to 0): {count_error}")
                # Continue without contact counts - they'll default to 0
        
        # Process companies and assign contact counts
        for c in companies_data:
            try:
                company = Company.from_dict(c).to_dict()
                company_id = str(company['id'])
                # Get contact count from our pre-fetched map, default to 0
                company['contact_count'] = contact_counts.get(company_id, 0)
                companies_list.append(company)
            except Exception as company_error:
                logger.warning(f"Error processing company {c.get('id', 'unknown')}: {company_error}")
                continue
        
        logger.info(f"Successfully listed {len(companies_list)} companies (total: {total_count})")
        return jsonify({
            'success': True,
            'companies': companies_list,
            'count': len(companies_list),
            'total': total_count
        })
        
    except Exception as e:
        logger.error(f"Error listing companies: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'success': False}), 500


@companies_bp.route('/api/companies/<uuid:company_id>', methods=['GET'])
@require_auth
@require_use_case('company_management')
def get_company(company_id):
    """Get company with associated contacts"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get company
        company_response = supabase.table('companies').select('*').eq('id', company_id).limit(1).execute()
        if not company_response.data:
            return jsonify({'error': 'Company not found'}), 404
        
        company = Company.from_dict(company_response.data[0])
        
        # Get associated contacts
        contacts_response = supabase.table('contacts').select('*').eq('company_id', company_id).limit(200).execute()
        contacts = contacts_response.data or []
        
        return jsonify({
            'success': True,
            'company': company.to_dict(),
            'contacts': contacts,
            'contact_count': len(contacts)
        })
        
    except Exception as e:
        logger.error(f"Error getting company {company_id}: {e}")
        return jsonify({'error': str(e)}), 500


@companies_bp.route('/api/companies', methods=['POST'])
@require_auth
@require_use_case('company_management')
def create_company():
    """Create a new company"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        company = Company.from_dict(data)
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        insert_data = company.to_dict()
        if 'id' in insert_data:
            del insert_data['id']  # Let database generate ID
        
        response = supabase.table('companies').insert(insert_data).execute()
        
        if not response.data:
            return jsonify({'error': 'Failed to create company'}), 500
        
        created_company = Company.from_dict(response.data[0])
        
        return jsonify({
            'success': True,
            'company': created_company.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating company: {e}")
        return jsonify({'error': str(e)}), 500


@companies_bp.route('/api/companies/<uuid:company_id>', methods=['PUT', 'PATCH'])
@require_auth
@require_use_case('company_management')
def update_company(company_id):
    """Update a company"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Remove id from update data
        update_data = {k: v for k, v in data.items() if k != 'id'}
        
        response = supabase.table('companies').update(update_data).eq('id', company_id).execute()
        
        if not response.data:
            return jsonify({'error': 'Company not found'}), 404
        
        updated_company = Company.from_dict(response.data[0])
        
        return jsonify({
            'success': True,
            'company': updated_company.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating company {company_id}: {e}")
        return jsonify({'error': str(e)}), 500


@companies_bp.route('/api/companies/<uuid:company_id>', methods=['DELETE'])
@require_auth
@require_use_case('company_management')
def delete_company(company_id):
    """Delete a company (with option to delete associated contacts or orphan them)"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Check if company has associated contacts
        contacts_response = supabase.table('contacts').select('id').eq('company_id', company_id).execute()
        contact_count = len(contacts_response.data) if contacts_response.data else 0
        
        # Get delete options from request
        data = request.get_json() or {}
        confirm_delete = data.get('confirm', False)
        delete_contacts = data.get('deleteContacts', False)
        
        if contact_count > 0 and not confirm_delete:
            return jsonify({
                'success': False,
                'error': f'Company has {contact_count} associated contact(s).',
                'affectedContacts': contact_count,
                'requiresConfirmation': True
            }), 400
        
        # Delete associated contacts if requested
        if delete_contacts and contact_count > 0:
            supabase.table('contacts').delete().eq('company_id', company_id).execute()
            logger.info(f"Deleted {contact_count} contacts associated with company {company_id}")
        elif contact_count > 0:
            # Orphan contacts by setting company_id to null
            supabase.table('contacts').update({'company_id': None}).eq('company_id', company_id).execute()
            logger.info(f"Orphaned {contact_count} contacts by removing company_id")
        
        # Delete company
        response = supabase.table('companies').delete().eq('id', company_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Company deleted successfully',
            'deletedContacts': contact_count if delete_contacts else 0,
            'orphanedContacts': contact_count if not delete_contacts and contact_count > 0 else 0
        })
        
    except Exception as e:
        logger.error(f"Error deleting company {company_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@companies_bp.route('/api/companies/backfill-domains', methods=['POST'])
@require_auth
@require_use_case('company_management')
def backfill_company_domains():
    """Backfill missing domains for companies by extracting from associated contact emails.
    Also maps contacts to companies if they're not already mapped."""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        from app.services.contact_service import extract_domain_from_email, find_or_create_company
        
        # Step 1: Map unmapped contacts to companies
        unmapped_contacts = supabase.table('contacts').select('id, email, company, company_name, company_id, industry').is_('company_id', 'null').not_.is_('email', 'null').limit(1000).execute()
        
        mapped_count = 0
        if unmapped_contacts.data:
            for contact in unmapped_contacts.data:
                email = contact.get('email')
                company_name = contact.get('company') or contact.get('company_name')
                industry = contact.get('industry')
                
                if email:
                    domain = extract_domain_from_email(email)
                    if domain or company_name:
                        try:
                            company_id = find_or_create_company(supabase, company_name, domain, industry)
                            if company_id:
                                supabase.table('contacts').update({'company_id': company_id}).eq('id', contact['id']).execute()
                                mapped_count += 1
                                logger.debug(f"Mapped contact {contact['id']} to company {company_id}")
                        except Exception as map_error:
                            logger.warning(f"Failed to map contact {contact['id']} to company: {map_error}")
        
        # Step 2: Backfill domains for companies without domains
        companies_without_domains = supabase.table('companies').select('id, name').is_('domain', 'null').execute()
        
        updated_count = 0
        if companies_without_domains.data:
            for company in companies_without_domains.data:
                company_id = company['id']
                # Get a contact with email for this company
                contact_response = supabase.table('contacts').select('email').eq('company_id', company_id).not_.is_('email', 'null').limit(1).execute()
                
                if contact_response.data and contact_response.data[0].get('email'):
                    email = contact_response.data[0]['email']
                    domain = extract_domain_from_email(email)
                    
                    if domain:
                        try:
                            supabase.table('companies').update({'domain': domain}).eq('id', company_id).execute()
                            updated_count += 1
                            logger.info(f"Backfilled domain '{domain}' for company {company_id}")
                        except Exception as update_error:
                            logger.warning(f"Failed to update domain for company {company_id}: {update_error}")
        
        return jsonify({
            'success': True,
            'message': f'Mapped {mapped_count} contacts to companies and backfilled domains for {updated_count} companies',
            'contacts_mapped': mapped_count,
            'domains_updated': updated_count,
            'total_companies_without_domains': len(companies_without_domains.data) if companies_without_domains.data else 0
        })
        
    except Exception as e:
        logger.error(f"Error backfilling company domains: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

