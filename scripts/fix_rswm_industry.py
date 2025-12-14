"""Fix RSWM Limited industry assignment to Textiles"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).parent.parent
sys.path.insert(0, str(basedir))

load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

from flask import Flask
from app.supabase_client import init_supabase

app = Flask(__name__)
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

app.config['SUPABASE_URL'] = supabase_url
app.config['SUPABASE_KEY'] = supabase_key
app.supabase = init_supabase(supabase_url, supabase_key)
supabase = app.supabase

# Find Fashion industry (closest to Textiles)
print("Finding Fashion/Textiles industry...")
industries_response = supabase.table('industries').select('id, name').ilike('name', '%fashion%').execute()
fashion_industries = industries_response.data or []

if not fashion_industries:
    print("ERROR: No Fashion industry found. Checking all industries...")
    all_response = supabase.table('industries').select('id, name').execute()
    all_industries = all_response.data or []
    print("\nAvailable industries:")
    for ind in sorted(all_industries, key=lambda x: x['name']):
        print(f"  - {ind['name']}")
    sys.exit(1)

textile_industry = fashion_industries[0]
print(f"Found: {textile_industry['name']} (ID: {textile_industry['id']}) - using as closest match to Textiles")

# Find RSWM Limited targets
print("\nFinding RSWM Limited targets...")
targets_response = supabase.table('targets').select('id, company_name, industry_id').ilike('company_name', '%rswm%').execute()
rswm_targets = targets_response.data or []

if not rswm_targets:
    print("No RSWM targets found")
    sys.exit(0)

print(f"Found {len(rswm_targets)} RSWM targets")

# Update each target
updated = 0
for target in rswm_targets:
    target_id = target['id']
    current_industry_id = target.get('industry_id')
    
    if str(current_industry_id) == str(textile_industry['id']):
        print(f"  Target {target_id}: Already has Fashion/Textiles industry")
        continue
    
    print(f"  Updating target {target_id}...")
    try:
        response = supabase.table('targets').update({
            'industry_id': textile_industry['id']
        }).eq('id', target_id).execute()
        
        if response.data:
            updated += 1
            print(f"    [OK] Updated to Fashion (Textiles)")
        else:
            print(f"    [FAILED] Failed to update")
    except Exception as e:
        print(f"    [ERROR] Error: {e}")

print(f"\n[SUCCESS] Updated {updated} RSWM targets to Fashion/Textiles industry")

