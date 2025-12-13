"""
Backfill script to mark existing contacts as targets if they're already linked to targets.
Run this after migration 017_contact_processing_tracking.sql
"""
import os
import sys
from pathlib import Path

# Add app directory to path
basedir = Path(__file__).parent.parent
sys.path.insert(0, str(basedir))

from dotenv import load_dotenv
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

from supabase import create_client, Client

def backfill_contact_status():
    """Mark contacts as targets if they're linked to existing targets"""
    # Initialize Supabase directly
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase not configured")
        print(f"   SUPABASE_URL: {'Set' if supabase_url else 'Missing'}")
        print(f"   SUPABASE_KEY: {'Set' if supabase_key else 'Missing'}")
        return
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return
    
    print("🔄 Starting backfill of contact processing status...")
    
    # Get all targets with contact_id
    try:
        targets_response = supabase.table('targets').select('contact_id, created_at').not_('contact_id', 'is', None).execute()
    except Exception as e:
        print(f"❌ Failed to fetch targets: {e}")
        return
    
    if not targets_response.data:
        print("✅ No targets with contact_id found. Nothing to backfill.")
        return
    
    print(f"📊 Found {len(targets_response.data)} targets linked to contacts")
    
    # Group by contact_id to get earliest target creation date
    contact_target_map = {}
    for target in targets_response.data:
        contact_id = target.get('contact_id')
        if contact_id:
            contact_id_str = str(contact_id)
            if contact_id_str not in contact_target_map:
                contact_target_map[contact_id_str] = target.get('created_at')
            else:
                # Keep earliest date
                existing_date = contact_target_map[contact_id_str]
                new_date = target.get('created_at')
                if new_date and existing_date and new_date < existing_date:
                    contact_target_map[contact_id_str] = new_date
    
    print(f"📝 Updating {len(contact_target_map)} contacts...")
    
    updated = 0
    errors = 0
    
    for contact_id, earliest_target_date in contact_target_map.items():
        try:
            result = supabase.table('contacts').update({
                'is_target': True,
                'last_target_created_at': earliest_target_date
            }).eq('id', contact_id).execute()
            
            if result.data:
                updated += 1
            else:
                errors += 1
                print(f"⚠️  Failed to update contact {contact_id}")
        except Exception as e:
            errors += 1
            print(f"❌ Error updating contact {contact_id}: {e}")
    
    print(f"\n✅ Backfill complete!")
    print(f"   - Updated: {updated} contacts")
    print(f"   - Errors: {errors} contacts")
    print(f"   - Total processed: {len(contact_target_map)} contacts")

if __name__ == '__main__':
    backfill_contact_status()

