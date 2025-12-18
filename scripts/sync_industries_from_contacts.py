"""Sync all industries from contacts to industries table"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
basedir = Path(__file__).parent.parent
sys.path.insert(0, str(basedir))

# Load environment
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

from app.supabase_client import init_supabase

def sync_industries():
    """Sync industries from contacts to industries table"""
    supabase = init_supabase(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
    
    if not supabase:
        print("[ERROR] Failed to initialize Supabase client")
        return False
    
    try:
        # Get all unique industries from contacts
        print("Scanning contacts for industries...")
        contacts = supabase.table('contacts').select('industry').execute()
        unique_industries = set(c.get('industry') for c in contacts.data if c.get('industry'))
        
        print(f"Found {len(unique_industries)} unique industries in contacts")
        
        # Get existing industries
        existing = supabase.table('industries').select('*').execute()
        existing_codes = {ind['code'].lower(): ind for ind in existing.data}
        existing_names = {ind['name'].lower(): ind for ind in existing.data}
        
        print(f"Found {len(existing.data)} industries in industries table")
        
        # Add missing industries
        added_count = 0
        for industry_name in sorted(unique_industries):
            industry_code = industry_name.upper().replace(' ', '_').replace('&', 'AND').replace('-', '_')
            
            # Check if already exists (by code or name)
            if industry_code.lower() in existing_codes or industry_name.lower() in existing_names:
                print(f"  [SKIP] {industry_name} (already exists)")
                continue
            
            try:
                result = supabase.table('industries').insert({
                    'code': industry_code,
                    'name': industry_name.title(),
                    'description': f'{industry_name.title()} industry'
                }).execute()
                print(f"  [OK] Added {industry_name} as {industry_code}")
                added_count += 1
            except Exception as e:
                print(f"  [ERROR] Failed to add {industry_name}: {e}")
        
        print(f"\n[SUCCESS] Added {added_count} new industries to industries table")
        
        # Show final list
        print("\n=== ALL INDUSTRIES ===")
        result = supabase.table('industries').select('*').order('name').execute()
        print(f"Total: {len(result.data)}")
        for ind in result.data:
            print(f"  - {ind['code']}: {ind['name']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = sync_industries()
    sys.exit(0 if success else 1)













