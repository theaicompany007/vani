"""Assign all industries to super users"""
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

def assign_all_industries_to_super_users():
    """Assign all industries to all super users"""
    supabase = init_supabase(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))
    
    if not supabase:
        print("[ERROR] Failed to initialize Supabase client")
        return False
    
    try:
        # Get all super users
        super_users = supabase.table('app_users').select('*').eq('is_super_user', True).execute()
        
        if not super_users.data:
            print("[INFO] No super users found")
            return True
        
        print(f"\nFound {len(super_users.data)} super user(s)")
        
        # Get all industries
        industries = supabase.table('industries').select('*').execute()
        
        if not industries.data:
            print("[ERROR] No industries found in database")
            return False
        
        print(f"Found {len(industries.data)} industry(ies)")
        
        # For each super user, assign all industries
        for user in super_users.data:
            print(f"\nProcessing user: {user['email']}")
            
            # Check if user_industries table exists
            try:
                existing_assignments = supabase.table('user_industries').select('industry_id').eq('user_id', user['id']).execute()
                existing_industry_ids = set(str(a['industry_id']) for a in existing_assignments.data)
            except Exception as e:
                if 'PGRST205' in str(e) or 'user_industries' in str(e).lower():
                    print("  [INFO] user_industries table not found - creating assignments with default_industry_id only")
                    # Set first industry as default
                    if user.get('default_industry_id'):
                        print(f"  [OK] Already has default_industry_id: {user['default_industry_id']}")
                    else:
                        first_industry = industries.data[0]
                        supabase.table('app_users').update({'default_industry_id': first_industry['id']}).eq('id', user['id']).execute()
                        print(f"  [OK] Set default_industry_id to {first_industry['name']}")
                    continue
                else:
                    raise
            
            # Assign missing industries
            assigned_count = 0
            for industry in industries.data:
                industry_id_str = str(industry['id'])
                
                if industry_id_str in existing_industry_ids:
                    print(f"  [SKIP] {industry['name']} - already assigned")
                    continue
                
                try:
                    # Check if this should be the default (first assignment or no default set)
                    is_default = not user.get('default_industry_id') and assigned_count == 0
                    
                    supabase.table('user_industries').insert({
                        'user_id': str(user['id']),
                        'industry_id': str(industry['id']),
                        'is_default': is_default
                    }).execute()
                    
                    assigned_count += 1
                    print(f"  [OK] Assigned {industry['name']}{' (DEFAULT)' if is_default else ''}")
                    
                    # Update app_users default_industry_id if this is the first assignment
                    if is_default:
                        supabase.table('app_users').update({'default_industry_id': str(industry['id'])}).eq('id', user['id']).execute()
                    
                except Exception as e:
                    print(f"  [ERROR] Failed to assign {industry['name']}: {e}")
            
            if assigned_count > 0:
                print(f"  [SUMMARY] Assigned {assigned_count} new industry(ies)")
            else:
                print(f"  [INFO] Already has all industries assigned")
        
        print("\n[SUCCESS] All super users have been assigned all industries!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = assign_all_industries_to_super_users()
    sys.exit(0 if success else 1)

