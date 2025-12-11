"""Contact service module for company and contact management"""
import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)

# Import enrichment service
try:
    from app.services.company_enrichment import get_enrichment_service
    ENRICHMENT_AVAILABLE = True
except ImportError:
    ENRICHMENT_AVAILABLE = False
    logger.warning("Company enrichment service not available")

# Import Hunter.io client - DISABLED (no paid subscription)
# try:
#     from app.integrations.hunter import get_hunter_client
#     HUNTER_AVAILABLE = True
# except ImportError:
#     HUNTER_AVAILABLE = False
#     logger.warning("Hunter.io integration not available")
HUNTER_AVAILABLE = False  # Disabled - no Hunter.io subscription


def normalize_email(email: Optional[str]) -> str:
    """Normalize email to lowercase and trim"""
    if not email:
        return ""
    return str(email).strip().lower()


def normalize_phone(phone: Optional[str]) -> str:
    """Normalize phone number by removing non-digits"""
    if not phone:
        return ""
    return re.sub(r'\D+', '', str(phone))


def extract_domain_from_email(email: Optional[str]) -> Optional[str]:
    """Extract domain from email address"""
    if not email:
        return None
    try:
        parts = str(email).strip().lower().split('@')
        if len(parts) == 2:
            return parts[1]
    except Exception:
        pass
    return None


def resolve_best_domain(domain: Optional[str] = None, email: Optional[str] = None) -> Optional[str]:
    """Resolve best domain from provided domain or email"""
    if domain:
        return str(domain).strip().lower()
    if email:
        return extract_domain_from_email(email)
    return None


def find_or_create_company(
    supabase,
    company_name: Optional[str] = None,
    domain: Optional[str] = None,
    industry: Optional[str] = None
) -> Optional[str]:
    """
    Find company by domain/name or create new.
    Returns company ID or None.
    """
    if not company_name and not domain:
        return None

    # Don't generate company name here - we'll try enrichment first, then fallback

    # First, try to find by domain if provided
    if domain:
        normalized_domain = str(domain).strip().lower()
        try:
            response = supabase.table('companies').select('id').eq('domain', normalized_domain).limit(1).execute()
            if response.data and len(response.data) > 0:
                company_id = response.data[0]['id']
                logger.debug(f"Found company by domain '{domain}': {company_id}")
                return company_id
        except Exception as e:
            logger.debug(f"Error finding company by domain {domain}: {e}")

    # Next, try to find by company name
    if company_name:
        normalized_name = str(company_name).strip()
        try:
            # Use ilike with proper pattern matching
            response = supabase.table('companies').select('id, domain').ilike('name', f'%{normalized_name}%').limit(1).execute()
            if response.data and len(response.data) > 0:
                company_id = response.data[0]['id']
                logger.debug(f"Found company by name '{company_name}': {company_id}")
                # If we found by name and have a domain from contact sheet, update company domain if it's missing
                if domain and not response.data[0].get('domain'):
                    try:
                        supabase.table('companies').update({'domain': str(domain).strip().lower()}).eq('id', company_id).execute()
                        logger.debug(f"Updated company domain to '{domain}'")
                    except Exception as update_error:
                        logger.debug(f"Could not update company domain: {update_error}")
                # Also try to extract domain from contacts if company domain is still missing
                elif not response.data[0].get('domain'):
                    try:
                        # Get a contact for this company and extract domain from their email
                        contact_with_email = supabase.table('contacts').select('email').eq('company_id', company_id).not_.is_('email', 'null').limit(1).execute()
                        if contact_with_email.data and contact_with_email.data[0].get('email'):
                            extracted_domain = extract_domain_from_email(contact_with_email.data[0]['email'])
                            if extracted_domain:
                                supabase.table('companies').update({'domain': extracted_domain}).eq('id', company_id).execute()
                                logger.debug(f"Backfilled company domain '{extracted_domain}' from contact email")
                    except Exception as backfill_error:
                        logger.debug(f"Could not backfill company domain: {backfill_error}")
                return company_id
        except Exception as e:
            logger.debug(f"Error finding company by name {company_name}: {e}")

    # Try to enrich company data from domain if name is missing
    enriched_data = None
    if not company_name and domain and ENRICHMENT_AVAILABLE:
        try:
            enrichment_service = get_enrichment_service()
            enriched_data = enrichment_service.enrich_from_domain(domain)
            if enriched_data and enriched_data.get('name'):
                company_name = enriched_data.get('name')
                logger.info(f"Enriched company name '{company_name}' from domain '{domain}'")
                # Use enriched industry if we don't have one
                if not industry and enriched_data.get('industry'):
                    industry = enriched_data.get('industry')
        except Exception as enrich_error:
            logger.debug(f"Enrichment failed for domain {domain}: {enrich_error}")
    
    # Fallback: Generate company name from domain if still not provided
    if not company_name:
        if domain:
            # Generate from domain if not provided (fallback)
            domain_parts = str(domain).strip().lower().split('.')
            company_name = domain_parts[0].title() if domain_parts else str(domain).strip().title()
            logger.debug(f"Generated fallback company name '{company_name}' from domain '{domain}'")
        else:
            logger.warning(f"Cannot create company: no name or domain provided")
            return None
    
    # Ensure name is not empty after stripping (but allow None for optional field)
    if company_name:
        company_name = str(company_name).strip()
        if not company_name:
            company_name = None
    
    try:
        insert_data = {}
        # Name is now optional, but include it if we have it
        if company_name:
            insert_data['name'] = company_name
        if domain:
            insert_data['domain'] = str(domain).strip().lower()
        # If domain is missing but we have company_name, try to extract from name or use as fallback
        elif company_name:
            # Try to extract domain-like string from company name (e.g., "Google Inc" -> "google.com")
            # This is a fallback - ideally domain should come from email
            logger.debug(f"No domain provided for company '{company_name}', will be set to null")
        if industry:
            insert_data['industry'] = str(industry).strip()
        # Add enriched location if available
        if enriched_data and enriched_data.get('location'):
            insert_data['location'] = enriched_data.get('location')
        
        # Must have at least domain or name
        if not insert_data:
            logger.warning(f"Cannot create company: no data to insert")
            return None
        
        # Insert and return the id
        logger.debug(f"Attempting to create company: {insert_data}")
        # Supabase Python client: insert returns data by default, no need for .select()
        # Pass data as dict (not list) to match other working inserts in codebase
        response = supabase.table('companies').insert(insert_data).execute()
        if response.data and len(response.data) > 0:
            company_id = response.data[0]['id']
            logger.info(f"Successfully created company '{company_name}' with ID {company_id}")
            return company_id
        else:
            logger.warning(f"Company insert returned no data: {insert_data}")
    except Exception as e:
        # Log the full error for debugging
        error_str = str(e).lower()
        error_details = str(e)
        
        # Check if it's a duplicate/unique constraint error
        is_duplicate = 'duplicate' in error_str or 'unique' in error_str or '23505' in error_str
        
        if is_duplicate:
            logger.debug(f"Company '{company_name}' already exists (duplicate): {error_details}")
        else:
            logger.error(f"Error creating company '{company_name}' / domain '{domain}': {error_details}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Try to find it again if it was created by another process or if there's a duplicate
        if company_name:
            try:
                logger.debug(f"Retrying find by name after creation error: {company_name}")
                response = supabase.table('companies').select('id').ilike('name', f'%{company_name}%').limit(1).execute()
                if response.data and len(response.data) > 0:
                    found_id = response.data[0]['id']
                    logger.info(f"Found existing company '{company_name}' with ID {found_id}")
                    return found_id
            except Exception as find_error:
                logger.debug(f"Error finding company after creation failure: {find_error}")
        
        # Also try by domain if we have one
        if domain:
            try:
                logger.debug(f"Retrying find by domain after creation error: {domain}")
                response = supabase.table('companies').select('id').eq('domain', str(domain).strip().lower()).limit(1).execute()
                if response.data and len(response.data) > 0:
                    found_id = response.data[0]['id']
                    logger.info(f"Found existing company by domain '{domain}' with ID {found_id}")
                    return found_id
            except Exception as find_error:
                logger.debug(f"Error finding company by domain after creation failure: {find_error}")
    
    logger.warning(f"Failed to create/find company for '{company_name}' / domain '{domain}' - returning None")
    return None


def find_duplicates(
    supabase,
    rows: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Find duplicate contacts by email/phone.
    Returns tuple of (duplicates, uniques).
    """
    emails = [normalize_email(r.get('email')) for r in rows if r.get('email')]
    phones = [normalize_phone(r.get('phone')) for r in rows if r.get('phone')]

    existing_emails = []
    existing_phones = []

    # Guard against empty arrays
    if emails:
        try:
            # Supabase Python client uses .in_() method
            response = supabase.table('contacts').select('*').in_('email', emails).execute()
            existing_emails = response.data or []
        except Exception as e:
            logger.warning(f"Error checking existing emails: {e}")
            existing_emails = []

    if phones:
        try:
            response = supabase.table('contacts').select('*').in_('phone', phones).execute()
            existing_phones = response.data or []
        except Exception as e:
            logger.warning(f"Error checking existing phones: {e}")
            existing_phones = []

    duplicates = []
    uniques = []

    for row in rows:
        row_email = normalize_email(row.get('email'))
        row_phone = normalize_phone(row.get('phone'))
        
        email_match = None
        if row_email:
            email_match = next(
                (e for e in existing_emails if e.get('email') and normalize_email(e['email']) == row_email),
                None
            )
        
        phone_match = None
        if row_phone:
            phone_match = next(
                (p for p in existing_phones if p.get('phone') and normalize_phone(p['phone']) == row_phone),
                None
            )

        if email_match or phone_match:
            match_type = 'email' if email_match else 'phone'
            duplicates.append({
                'row': row,
                'match': email_match or phone_match,
                'match_type': match_type
            })
        else:
            uniques.append(row)

    return duplicates, uniques


def upsert_contacts(
    supabase,
    rows: List[Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Bulk upsert contacts with deduplication logic.
    Similar to Next.js implementation with chunked processing.
    
    Returns dict with: imported, errors, data, report
    """
    update_existing = options.get('updateExisting', False) if options else False
    chunk_size = 25  # Reduced chunk size to avoid ON CONFLICT collisions
    
    errors = []
    imported = 0
    returned_rows = []
    per_row_report = []
    
    allowed_columns = [
        "company_id", "name", "role", "email", "linkedin", "phone",
        "lead_source", "company", "city", "industry", "sheet"
    ]
    
    # Normalize and prepare rows
    full_prepared = []
    for idx, r in enumerate(rows):
        row = {**r}
        
        # Ensure name exists
        if not row.get('name'):
            first = row.get('first_name') or row.get('firstname') or ''
            last = row.get('last_name') or row.get('lastname') or ''
            row['name'] = f"{first} {last}".strip() if (first or last) else (row.get('email', '').split('@')[0] if row.get('email') else 'Unnamed')
        
        # Resolve company and normalize domain
        domain = resolve_best_domain(row.get('domain'), row.get('email'))
        company_name = row.get('company') or row.get('company_name')
        
        # Don't generate company name here - let find_or_create_company handle enrichment
        # It will use OpenAI to enrich from domain if name is missing
        
        if domain:
            row['domain'] = domain
        
        # Normalize lead_source
        if row.get('leadSource') and not row.get('lead_source'):
            row['lead_source'] = row['leadSource']
        if not row.get('lead_source') and not row.get('leadSource') and row.get('sheet'):
            row['lead_source'] = row['sheet']
        
        # Normalize email and phone
        row['__normalized_email'] = normalize_email(row.get('email'))
        row['__normalized_phone'] = normalize_phone(row.get('phone'))
        row['__skip_no_key'] = not (row['__normalized_email'] or row['__normalized_phone'])
        row['__orig_index'] = idx
        
        full_prepared.append(row)
    
    # Process in chunks
    total_chunks = (len(full_prepared) + chunk_size - 1) // chunk_size
    logger.info(f"Processing {len(full_prepared)} contacts in {total_chunks} chunks of {chunk_size}")
    for chunk_idx, i in enumerate(range(0, len(full_prepared), chunk_size)):
        chunk = full_prepared[i:i + chunk_size]
        # Only log every 10 chunks or first/last chunk to reduce noise
        if chunk_idx == 0 or chunk_idx % 10 == 0 or chunk_idx == total_chunks - 1:
            logger.info(f"Processing chunk {chunk_idx + 1}/{total_chunks}: {len(chunk)} contacts")
        
        prepared = []
        for r in chunk:
            if r['__skip_no_key']:
                per_row_report.append({
                    'index': r['__orig_index'],
                    'email': r.get('email'),
                    'phone': r.get('phone'),
                    'status': 'skipped',
                    'error': 'missing email and phone'
                })
                continue
            
            row = {**r}
            
            # Resolve company_id
            domain = row.get('domain')
            # Extract domain from email if domain not provided
            if not domain and row.get('email'):
                domain = extract_domain_from_email(row.get('email'))
                if domain:
                    row['domain'] = domain
                    logger.debug(f"Extracted domain '{domain}' from email {row.get('email')}")
            company_name = row.get('company') or row.get('company_name')
            industry = row.get('industry')
            linkedin = row.get('linkedin')
            
            # Try to enrich contact from LinkedIn if available
            if linkedin and ENRICHMENT_AVAILABLE and (not company_name or not industry):
                try:
                    enrichment_service = get_enrichment_service()
                    contact_enriched = enrichment_service.enrich_contact_from_linkedin(
                        linkedin_url=linkedin,
                        name=row.get('name'),
                        email=row.get('email')
                    )
                    if contact_enriched:
                        # Use enriched company name if we don't have one
                        if not company_name and contact_enriched.get('company'):
                            company_name = contact_enriched.get('company')
                            logger.debug(f"Enriched company name '{company_name}' from LinkedIn")
                        # Use enriched industry if we don't have one
                        if not industry and contact_enriched.get('industry'):
                            industry = contact_enriched.get('industry')
                            logger.debug(f"Enriched industry '{industry}' from LinkedIn")
                        # Update role if missing
                        if not row.get('role') and contact_enriched.get('role'):
                            row['role'] = contact_enriched.get('role')
                except Exception as enrich_error:
                    logger.debug(f"LinkedIn enrichment failed: {enrich_error}")
            
            # Hunter.io integration: DISABLED - no paid subscription
            # if HUNTER_AVAILABLE:
            #     try:
            #         hunter_client = get_hunter_client()
            #         if hunter_client.enabled:
            #             current_email = row.get('email')
            #             current_name = row.get('name', '')
            #             name_parts = current_name.split(maxsplit=1) if current_name else []
            #             first_name = name_parts[0] if name_parts else None
            #             last_name = name_parts[1] if len(name_parts) > 1 else None
            #             
            #             # 1. Find email if missing but we have name and domain
            #             if not current_email and domain and (first_name or last_name):
            #                 try:
            #                     found_email = hunter_client.find_email(
            #                         domain=domain,
            #                         first_name=first_name,
            #                         last_name=last_name
            #                     )
            #                     if found_email and found_email.get('email'):
            #                         row['email'] = found_email['email']
            #                         logger.info(f"Found email {found_email['email']} for {current_name} at {domain} (score: {found_email.get('score', 0)})")
            #                         # Update other fields from found email data
            #                         if not row.get('role') and found_email.get('position'):
            #                             row['role'] = found_email.get('position')
            #                         if not row.get('linkedin') and found_email.get('linkedin_url'):
            #                             row['linkedin'] = found_email.get('linkedin_url')
            #                         if not row.get('phone') and found_email.get('phone_number'):
            #                             row['phone'] = found_email.get('phone_number')
            #                         if not company_name and found_email.get('company'):
            #                             company_name = found_email.get('company')
            #                 except Exception as find_error:
            #                     logger.debug(f"Hunter.io email finder failed: {find_error}")
            #             
            #             # 2. Verify email if we have one
            #             if row.get('email'):
            #                 try:
            #                     verification = hunter_client.verify_email(row['email'])
            #                     if verification:
            #                         # Mark invalid emails for review (but don't skip them)
            #                         if verification.get('result') == 'undeliverable':
            #                             logger.warning(f"Email {row['email']} is undeliverable (score: {verification.get('score', 0)})")
            #                             # Store verification status in a comment field if available
            #                             row['__email_verification'] = f"invalid (score: {verification.get('score', 0)})"
            #                         elif verification.get('result') == 'risky':
            #                             logger.info(f"Email {row['email']} is risky/accept-all (score: {verification.get('score', 0)})")
            #                             row['__email_verification'] = f"risky (score: {verification.get('score', 0)})"
            #                         else:
            #                             logger.debug(f"Email {row['email']} verified as {verification.get('result')} (score: {verification.get('score', 0)})")
            #                 except Exception as verify_error:
            #                     logger.debug(f"Hunter.io email verification failed: {verify_error}")
            #             
            #             # 3. Enrich contact data if email exists
            #             if row.get('email') and (not row.get('role') or not row.get('phone') or not row.get('linkedin')):
            #                 try:
            #                     enriched = hunter_client.enrich_person(
            #                         email=row.get('email'),
            #                         domain=domain,
            #                         first_name=first_name,
            #                         last_name=last_name
            #                     )
            #                     if enriched:
            #                         # Fill in missing fields
            #                         if not row.get('role') and enriched.get('position'):
            #                             row['role'] = enriched.get('position')
            #                         if not row.get('phone') and enriched.get('phone_number'):
            #                             row['phone'] = enriched.get('phone_number')
            #                         if not row.get('linkedin') and enriched.get('linkedin_url'):
            #                             row['linkedin'] = enriched.get('linkedin_url')
            #                         if not company_name and enriched.get('company'):
            #                             company_name = enriched.get('company')
            #                         if not industry and enriched.get('industry'):
            #                             industry = enriched.get('industry')
            #                         logger.debug(f"Enriched contact data for {row.get('email')}")
            #                 except Exception as enrich_error:
            #                     logger.debug(f"Hunter.io enrichment failed: {enrich_error}")
            #     except Exception as hunter_error:
            #         logger.debug(f"Hunter.io integration error: {hunter_error}")
            
            # Don't generate fallback name here - let find_or_create_company handle enrichment
            # It will use OpenAI to enrich from domain if name is missing
            
            if domain or company_name:
                try:
                    company_id = find_or_create_company(supabase, company_name, domain, industry)
                    if company_id:
                        row['company_id'] = company_id
                        logger.debug(f"Resolved company_id {company_id} for company '{company_name}' / domain '{domain}'")
                        # Also update company industry if contact has industry and company doesn't
                        if industry and company_id:
                            try:
                                # Check if company has industry, if not update it
                                company_check = supabase.table('companies').select('industry').eq('id', company_id).limit(1).execute()
                                if company_check.data and not company_check.data[0].get('industry'):
                                    supabase.table('companies').update({'industry': str(industry).strip()}).eq('id', company_id).execute()
                            except Exception as update_error:
                                logger.debug(f"Could not update company industry: {update_error}")
                    else:
                        logger.warning(f"Failed to create/find company for '{company_name}' / domain '{domain}'")
                except Exception as company_error:
                    logger.error(f"Error resolving company for '{company_name}' / domain '{domain}': {company_error}")
            
            # Clean internal fields
            clean_row = {k: v for k, v in row.items() if not k.startswith('__')}
            
            # Normalize email, phone, and industry in final row
            if clean_row.get('email'):
                clean_row['email'] = normalize_email(clean_row['email'])
            if clean_row.get('phone'):
                clean_row['phone'] = normalize_phone(clean_row['phone'])
            if clean_row.get('industry'):
                clean_row['industry'] = str(clean_row['industry']).strip().lower()
            
            # Pick only allowed columns
            final_row = {k: v for k, v in clean_row.items() if k in allowed_columns}
            prepared.append(final_row)
        
        if not prepared:
            continue
        
        # Perform upsert
        try:
            # Split into email-keyed and phone-only rows
            email_rows = [r for r in prepared if r.get('email')]
            phone_only_rows = [r for r in prepared if not r.get('email') and r.get('phone')]
            
            # Upsert email-keyed rows - optimized batch processing
            if email_rows:
                try:
                    # Batch fetch all existing emails at once
                    email_norms = [normalize_email(erow.get('email')) for erow in email_rows if normalize_email(erow.get('email'))]
                    existing_emails_map = {}
                    
                    if email_norms:
                        # Query all existing emails in one go (Supabase supports IN queries)
                        try:
                            # Split into smaller batches if too many (Supabase has query size limits)
                            batch_size = 50
                            for batch_start in range(0, len(email_norms), batch_size):
                                batch_emails = email_norms[batch_start:batch_start + batch_size]
                                existing_query = supabase.table('contacts').select('id, email').in_('email', batch_emails).execute()
                                if existing_query.data:
                                    for existing_contact in existing_query.data:
                                        existing_emails_map[normalize_email(existing_contact.get('email'))] = existing_contact.get('id')
                        except Exception as batch_error:
                            logger.warning(f"Batch email lookup failed, falling back to individual queries: {batch_error}")
                            existing_emails_map = {}
                    
                    # Now process each row
                    for erow_idx, erow in enumerate(email_rows):
                        try:
                            email_norm = normalize_email(erow.get('email'))
                            if not email_norm:
                                continue
                            
                            contact_id = existing_emails_map.get(email_norm)
                            
                            if contact_id:
                                # Update existing
                                try:
                                    update_response = supabase.table('contacts').update(erow).eq('id', contact_id).execute()
                                    if update_response.data:
                                        imported += 1
                                        returned_rows.extend(update_response.data)
                                        # Find original index from the chunk
                                        orig_idx = i + erow_idx
                                        for orig_row in chunk:
                                            if orig_row.get('__normalized_email') == email_norm:
                                                orig_idx = orig_row.get('__orig_index', orig_idx)
                                                break
                                        
                                        per_row_report.append({
                                            'index': orig_idx,
                                            'email': erow.get('email'),
                                            'phone': erow.get('phone'),
                                            'status': 'ok',
                                            'id': contact_id
                                        })
                                except Exception as update_error:
                                    logger.error(f"Error updating contact {contact_id}: {update_error}")
                                    per_row_report.append({
                                        'index': i + erow_idx,
                                        'email': erow.get('email'),
                                        'phone': erow.get('phone'),
                                        'status': 'error',
                                        'error': str(update_error)
                                    })
                            else:
                                # Insert new - batch insert if possible
                                try:
                                    insert_response = supabase.table('contacts').insert([erow]).execute()
                                    if insert_response.data:
                                        imported += 1
                                        returned_rows.extend(insert_response.data)
                                        new_id = insert_response.data[0].get('id')
                                        # Update map for potential duplicates in same batch
                                        existing_emails_map[email_norm] = new_id
                                        per_row_report.append({
                                            'index': i + erow_idx,
                                            'email': erow.get('email'),
                                            'phone': erow.get('phone'),
                                            'status': 'ok',
                                            'id': new_id
                                        })
                                except Exception as insert_error:
                                    logger.error(f"Error inserting contact: {insert_error}")
                                    per_row_report.append({
                                        'index': i + erow_idx,
                                        'email': erow.get('email'),
                                        'phone': erow.get('phone'),
                                        'status': 'error',
                                        'error': str(insert_error)
                                    })
                        except Exception as row_error:
                            logger.error(f"Error processing email row {erow_idx}: {row_error}")
                            per_row_report.append({
                                'index': i + erow_idx,
                                'email': erow.get('email', ''),
                                'phone': erow.get('phone', ''),
                                'status': 'error',
                                'error': str(row_error)
                            })
                except Exception as e:
                    logger.error(f"Error upserting email rows: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    errors.append({'index': i, 'message': str(e)})
            
            # Handle phone-only rows (find and update or insert)
            for pidx, row in enumerate(phone_only_rows):
                try:
                    phone_norm = normalize_phone(row.get('phone'))
                    if not phone_norm:
                        continue
                    
                    # Look for existing contact by phone
                    existing_response = supabase.table('contacts').select('*').eq('phone', phone_norm).limit(1).execute()
                    
                    if existing_response.data and len(existing_response.data) > 0:
                        # Update existing
                        contact_id = existing_response.data[0]['id']
                        update_response = supabase.table('contacts').update(row).eq('id', contact_id).execute()
                        if update_response.data:
                            imported += 1
                            returned_rows.extend(update_response.data)
                            per_row_report.append({
                                'index': i + len(email_rows) + pidx,
                                'email': row.get('email'),
                                'phone': row.get('phone'),
                                'status': 'ok',
                                'id': contact_id
                            })
                    else:
                        # Insert new
                        insert_response = supabase.table('contacts').insert([row]).execute()
                        if insert_response.data:
                            imported += 1
                            returned_rows.extend(insert_response.data)
                            per_row_report.append({
                                'index': i + len(email_rows) + pidx,
                                'email': row.get('email'),
                                'phone': row.get('phone'),
                                'status': 'ok',
                                'id': insert_response.data[0].get('id')
                            })
                except Exception as e:
                    logger.error(f"Error processing phone-only row: {e}")
                    errors.append({'index': i + len(email_rows) + pidx, 'message': str(e)})
        
        except Exception as e:
            logger.error(f"Error in chunk processing: {e}")
            errors.append({'index': i, 'message': str(e)})
    
    return {
        'imported': imported,
        'errors': errors,
        'data': returned_rows,
        'report': per_row_report
    }

