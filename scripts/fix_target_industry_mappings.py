"""
Fix Target Industry Mappings
- Re-evaluates all targets and corrects their industry_id based on linked contacts/companies
- Uses exact industry name matching (not partial) to ensure accuracy
- Updates targets with correct industry_id from industries table
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path
basedir = Path(__file__).parent.parent
sys.path.insert(0, str(basedir))

# Load environment
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

from flask import Flask
from app.supabase_client import init_supabase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app and Supabase
app = Flask(__name__)
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    logger.error("SUPABASE_URL and SUPABASE_KEY must be set")
    sys.exit(1)

app.config['SUPABASE_URL'] = supabase_url
app.config['SUPABASE_KEY'] = supabase_key
app.supabase = init_supabase(supabase_url, supabase_key)
supabase = app.supabase

def get_industry_id_from_name(industry_name: str) -> Optional[str]:
    """Get industry_id from industry name using exact case-insensitive match"""
    if not industry_name or not industry_name.strip():
        return None
    
    try:
        # Use exact case-insensitive match (no wildcards)
        response = supabase.table('industries').select('id').ilike('name', industry_name.strip()).limit(1).execute()
        if response.data:
            return str(response.data[0]['id'])
    except Exception as e:
        logger.warning(f"Error looking up industry '{industry_name}': {e}")
    
    return None

def fix_target_industry(target: Dict[str, Any], dry_run: bool = False) -> bool:
    """Fix industry_id for a target based on linked contact/company"""
    target_id = target.get('id')
    company_name = target.get('company_name', 'Unknown')
    current_industry_id = target.get('industry_id')
    
    # Priority: 1. Contact industry, 2. Company industry, 3. Keep existing if valid
    correct_industry_id = None
    source = None
    
    # Check linked contact
    contact = target.get('contacts')
    if contact and contact.get('industry'):
        contact_industry = contact['industry']
        correct_industry_id = get_industry_id_from_name(contact_industry)
        if correct_industry_id:
            source = f"contact industry '{contact_industry}'"
    
    # Check linked company (if contact didn't provide industry)
    if not correct_industry_id:
        company = target.get('companies')
        if company and company.get('industry'):
            company_industry = company['industry']
            correct_industry_id = get_industry_id_from_name(company_industry)
            if correct_industry_id:
                source = f"company industry '{company_industry}'"
    
    # If no industry found from contact/company, keep existing if it exists
    if not correct_industry_id:
        if current_industry_id:
            logger.debug(f"Target {company_name}: No contact/company industry found, keeping existing industry_id")
            return False  # No change needed
        else:
            logger.warning(f"Target {company_name}: No industry found from contact/company and no existing industry_id")
            return False  # Can't fix without data
    
    # Check if update is needed
    if str(current_industry_id) == str(correct_industry_id):
        logger.debug(f"Target {company_name}: Industry already correct ({current_industry_id})")
        return False  # No change needed
    
    # Update target
    if dry_run:
        logger.info(f"Target {company_name}: Would update industry_id from {current_industry_id} to {correct_industry_id} (from {source})")
        return True
    
    try:
        response = supabase.table('targets').update({
            'industry_id': correct_industry_id
        }).eq('id', target_id).execute()
        
        if response.data:
            # Get industry name for logging
            industry_response = supabase.table('industries').select('name').eq('id', correct_industry_id).limit(1).execute()
            industry_name = industry_response.data[0]['name'] if industry_response.data else 'Unknown'
            logger.info(f"Target {company_name}: Updated industry_id to {industry_name} ({correct_industry_id}) from {source}")
            return True
        else:
            logger.error(f"Target {company_name}: Failed to update industry_id")
            return False
            
    except Exception as e:
        logger.error(f"Target {company_name}: Error updating industry_id: {e}")
        return False

def fix_all_targets(dry_run: bool = False):
    """Fix industry mappings for all targets"""
    logger.info(f"\n{'='*70}")
    logger.info(f"FIX TARGET INDUSTRY MAPPINGS")
    logger.info(f"{'='*70}\n")
    
    if dry_run:
        logger.info("[DRY RUN MODE - No changes will be made]\n")
    
    stats = {
        'total_targets': 0,
        'updated': 0,
        'no_change_needed': 0,
        'no_industry_data': 0,
        'errors': 0
    }
    
    try:
        # Fetch all targets with their linked contacts and companies
        logger.info("Fetching all targets with linked contacts and companies...")
        response = supabase.table('targets').select(
            'id, company_name, industry_id, contact_id, company_id, '
            'contacts(industry, id), companies(industry, id)'
        ).execute()
        
        targets = response.data or []
        stats['total_targets'] = len(targets)
        
        if not targets:
            logger.info("No targets found")
            return True
        
        logger.info(f"Found {len(targets)} targets to check\n")
        
        # Process each target
        for i, target in enumerate(targets, 1):
            company_name = target.get('company_name', 'Unknown')
            logger.info(f"[{i}/{len(targets)}] Processing: {company_name}")
            
            try:
                updated = fix_target_industry(target, dry_run=dry_run)
                if updated:
                    stats['updated'] += 1
                elif target.get('industry_id'):
                    stats['no_change_needed'] += 1
                else:
                    stats['no_industry_data'] += 1
            except Exception as e:
                logger.error(f"Error processing target {company_name}: {e}")
                stats['errors'] += 1
        
        # Print summary
        logger.info(f"\n{'='*70}")
        logger.info(f"FIX SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Total targets: {stats['total_targets']}")
        if not dry_run:
            logger.info(f"Updated: {stats['updated']}")
        else:
            logger.info(f"Would update: {stats['updated']}")
        logger.info(f"No change needed: {stats['no_change_needed']}")
        logger.info(f"No industry data available: {stats['no_industry_data']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing targets: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix target industry mappings based on linked contacts/companies')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    
    args = parser.parse_args()
    
    success = fix_all_targets(dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()




