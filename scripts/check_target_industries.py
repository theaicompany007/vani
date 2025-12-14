"""
Script to check which industries the imported targets belong to.
This helps identify which targets need industry assignment.
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local'))
load_dotenv()

from flask import Flask
from app.supabase_client import init_supabase

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    sys.exit(1)

# Initialize Flask app and Supabase client
app = Flask(__name__)
app.config['SUPABASE_URL'] = supabase_url
app.config['SUPABASE_KEY'] = supabase_key
app.supabase = init_supabase(supabase_url, supabase_key)
supabase = app.supabase

# Companies to check (from the import error logs)
companies_to_check = [
    "Parle Agro",
    "SBI Cards",
    "RSWM Limited",
    "HEG Limited",
    "Nirula's",
    "Food Club",
    "Bittoo Tikki Wala"
]

def main():
    with app.app_context():
        if not supabase:
            print("ERROR: Could not connect to Supabase")
            sys.exit(1)
        
        print("=" * 80)
        print("CHECKING TARGET INDUSTRIES")
        print("=" * 80)
        print()
        
        # Get all industries
        industries_response = supabase.table('industries').select('id, name').execute()
        industries = {ind['id']: ind for ind in (industries_response.data or [])}
        
        print(f"Found {len(industries)} industries in database")
        print()
        
        # Query targets for these companies
        print("Checking targets for imported companies...")
        print("-" * 80)
        
        for company_name in companies_to_check:
            # Search for targets with this company name
            targets_response = supabase.table('targets').select(
                'id, company_name, industry_id, contact_id, company_id'
            ).ilike('company_name', f'%{company_name}%').execute()
            
            targets = targets_response.data or []
            
            if targets:
                print(f"\n[COMPANY] {company_name}:")
                for target in targets:
                    industry_id = target.get('industry_id')
                    industry_info = "[NO INDUSTRY]"
                    
                    if industry_id:
                        industry = industries.get(industry_id)
                        if industry:
                            industry_info = f"[OK] {industry.get('name')} (ID: {industry_id})"
                        else:
                            industry_info = f"[INVALID] Invalid industry_id: {industry_id}"
                    
                    print(f"   Target ID: {target.get('id')}")
                    print(f"   Industry: {industry_info}")
                    print(f"   Contact ID: {target.get('contact_id') or 'None'}")
                    print(f"   Company ID: {target.get('company_id') or 'None'}")
                    print()
            else:
                print(f"\n[NOT FOUND] {company_name}: No targets found")
        
        # Summary: Count targets by industry
        print("\n" + "=" * 80)
        print("SUMMARY: Targets by Industry")
        print("=" * 80)
        
        all_targets_response = supabase.table('targets').select('id, company_name, industry_id').execute()
        all_targets = all_targets_response.data or []
        
        industry_counts = {}
        no_industry_count = 0
        
        for target in all_targets:
            industry_id = target.get('industry_id')
            if industry_id and industry_id in industries:
                industry_name = industries[industry_id].get('name')
                industry_counts[industry_name] = industry_counts.get(industry_name, 0) + 1
            else:
                no_industry_count += 1
        
        print(f"\nTotal targets: {len(all_targets)}")
        print(f"Targets without industry: {no_industry_count}")
        print(f"\nTargets by industry:")
        for industry_name, count in sorted(industry_counts.items()):
            print(f"  {industry_name}: {count}")
        
        if no_industry_count > 0:
            print(f"\n[WARNING] {no_industry_count} targets need industry assignment!")

if __name__ == '__main__':
    main()

