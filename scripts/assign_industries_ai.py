"""
AI-Powered Industry Assignment Script
Assigns industries to contacts and companies that don't have industry set.

Usage:
    python scripts/assign_industries_ai.py [--batch-size 100] [--dry-run]
    
Options:
    --batch-size: Number of records to process at a time (default: 100)
    --dry-run: Show what would be assigned without making changes
    --contacts-only: Only process contacts
    --companies-only: Only process companies
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import requests
import logging
from typing import Dict, List, Optional, Tuple

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def get_headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def get_openai_industry(company_name: str, domain: str = None, description: str = None) -> Optional[str]:
    """Use OpenAI to determine industry for a company"""
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set, skipping AI industry assignment")
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""Determine the primary industry for this company. Return ONLY the industry name (e.g., "FMCG", "Technology", "Food & Beverages", "Healthcare", "Education", "Manufacturing", "Retail", "Finance", "Real Estate", "Energy", "Transportation", "Telecommunications", "Media", "Entertainment", "Hospitality", "Construction", "Agriculture", "Pharmaceuticals", "Automotive", "Aerospace", "Defense", "Consulting", "Legal", "Government", "Non-profit").

Company Name: {company_name}
Domain: {domain or 'N/A'}
Description: {description or 'N/A'}

Return only the industry name, nothing else."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at classifying companies into industries. Return only the industry name."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        industry = response.choices[0].message.content.strip()
        # Clean up response (remove quotes, extra text)
        industry = industry.strip('"\'')
        industry = industry.split('\n')[0].strip()
        
        return industry
    except Exception as e:
        logger.error(f"Error getting industry from OpenAI for {company_name}: {e}")
        return None

def get_or_create_industry(industry_name: str, headers: Dict) -> Optional[str]:
    """Get industry ID by name, or create if it doesn't exist"""
    if not industry_name:
        return None
    
    # Normalize industry name
    industry_name = industry_name.strip()
    
    # First, try to find existing industry
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/industries?name=eq.{industry_name}&select=id,name",
        headers=headers
    )
    
    if response.ok and response.json():
        return str(response.json()[0]['id'])
    
    # Try case-insensitive search
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/industries?name=ilike.{industry_name}&select=id,name",
        headers=headers
    )
    
    if response.ok and response.json():
        return str(response.json()[0]['id'])
    
    # Create new industry
    try:
        create_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/industries",
            headers=headers,
            json={'name': industry_name}
        )
        
        if create_response.ok and create_response.json():
            logger.info(f"Created new industry: {industry_name}")
            return str(create_response.json()[0]['id'])
    except Exception as e:
        logger.warning(f"Failed to create industry {industry_name}: {e}")
    
    return None

def assign_industry_to_companies(batch_size: int = 100, dry_run: bool = False) -> Tuple[int, int]:
    """Assign industries to companies missing industry"""
    headers = get_headers()
    
    # Get companies without industry
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/companies?industry=is.null&select=id,name,domain&limit={batch_size}",
        headers=headers
    )
    
    if not response.ok:
        logger.error(f"Error fetching companies: {response.status_code} - {response.text}")
        return 0, 0
    
    companies = response.json()
    if not companies:
        logger.info("No companies without industry found")
        return 0, 0
    
    logger.info(f"Found {len(companies)} companies without industry")
    
    updated = 0
    failed = 0
    
    for company in companies:
        company_id = company['id']
        company_name = company.get('name', 'Unknown')
        domain = company.get('domain')
        
        logger.info(f"Processing company: {company_name} (domain: {domain})")
        
        # Get industry from AI
        industry_name = get_openai_industry(company_name, domain)
        
        if not industry_name:
            logger.warning(f"Could not determine industry for {company_name}")
            failed += 1
            continue
        
        # Get or create industry
        industry_id = get_or_create_industry(industry_name, headers)
        
        if not industry_id:
            logger.warning(f"Could not get/create industry '{industry_name}' for {company_name}")
            failed += 1
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would assign {company_name} to industry: {industry_name}")
            updated += 1
        else:
            # Update company
            update_response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/companies?id=eq.{company_id}",
                headers=headers,
                json={'industry': industry_name}
            )
            
            if update_response.ok:
                logger.info(f"✅ Assigned {company_name} to industry: {industry_name}")
                updated += 1
            else:
                logger.error(f"Failed to update {company_name}: {update_response.status_code} - {update_response.text}")
                failed += 1
    
    return updated, failed

def assign_industry_to_contacts(batch_size: int = 100, dry_run: bool = False) -> Tuple[int, int]:
    """Assign industries to contacts missing industry"""
    headers = get_headers()
    
    # Get contacts without industry (and their company info if available)
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/contacts?industry=is.null&select=id,name,email,company,company_id,companies(name,domain,industry)&limit={batch_size}",
        headers=headers
    )
    
    if not response.ok:
        logger.error(f"Error fetching contacts: {response.status_code} - {response.text}")
        return 0, 0
    
    contacts = response.json()
    if not contacts:
        logger.info("No contacts without industry found")
        return 0, 0
    
    logger.info(f"Found {len(contacts)} contacts without industry")
    
    updated = 0
    failed = 0
    
    for contact in contacts:
        contact_id = contact['id']
        contact_name = contact.get('name', 'Unknown')
        company_name = contact.get('company')
        company_data = contact.get('companies', {})
        
        # If company has industry, use that
        if company_data and company_data.get('industry'):
            industry_name = company_data['industry']
            logger.info(f"Using company industry for {contact_name}: {industry_name}")
        else:
            # Try to get from company name or domain
            if company_data:
                company_name = company_data.get('name') or company_name
                domain = company_data.get('domain')
            else:
                domain = None
            
            # Get industry from AI
            industry_name = get_openai_industry(company_name or contact_name, domain)
        
        if not industry_name:
            logger.warning(f"Could not determine industry for {contact_name}")
            failed += 1
            continue
        
        # Get or create industry
        industry_id = get_or_create_industry(industry_name, headers)
        
        if not industry_id:
            logger.warning(f"Could not get/create industry '{industry_name}' for {contact_name}")
            failed += 1
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would assign {contact_name} to industry: {industry_name}")
            updated += 1
        else:
            # Update contact
            update_response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/contacts?id=eq.{contact_id}",
                headers=headers,
                json={'industry': industry_name}
            )
            
            if update_response.ok:
                logger.info(f"✅ Assigned {contact_name} to industry: {industry_name}")
                updated += 1
            else:
                logger.error(f"Failed to update {contact_name}: {update_response.status_code} - {update_response.text}")
                failed += 1
    
    return updated, failed

def main():
    parser = argparse.ArgumentParser(description='AI-Powered Industry Assignment')
    parser.add_argument('--batch-size', type=int, default=100, help='Number of records to process at a time')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be assigned without making changes')
    parser.add_argument('--contacts-only', action='store_true', help='Only process contacts')
    parser.add_argument('--companies-only', action='store_true', help='Only process companies')
    
    args = parser.parse_args()
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env.local")
        sys.exit(1)
    
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set. AI industry assignment will be skipped.")
    
    logger.info("=" * 60)
    logger.info("AI-Powered Industry Assignment")
    logger.info("=" * 60)
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    logger.info("")
    
    total_updated = 0
    total_failed = 0
    
    # Process companies
    if not args.contacts_only:
        logger.info("Processing Companies...")
        logger.info("-" * 60)
        updated, failed = assign_industry_to_companies(args.batch_size, args.dry_run)
        total_updated += updated
        total_failed += failed
        logger.info(f"Companies: {updated} updated, {failed} failed\n")
    
    # Process contacts
    if not args.companies_only:
        logger.info("Processing Contacts...")
        logger.info("-" * 60)
        updated, failed = assign_industry_to_contacts(args.batch_size, args.dry_run)
        total_updated += updated
        total_failed += failed
        logger.info(f"Contacts: {updated} updated, {failed} failed\n")
    
    logger.info("=" * 60)
    logger.info(f"Summary: {total_updated} updated, {total_failed} failed")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("\nThis was a dry run. Run without --dry-run to apply changes.")

if __name__ == '__main__':
    main()
















