"""
Script to update existing FMCG targets with Pain Points, Pitch Angles, and LinkedIn Scripts.

Usage:
    python scripts/update_fmcg_targets.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

# Target data from the hardcoded list
TARGET_DATA = {
    'Hindustan Unilever': {
        'contact_name': 'Arun Neelakantan',
        'role': 'ED, Customer Dev',
        'pain_point': 'Need to drive usage of "Shikhar" app in deep rural areas where literacy is a barrier. Apps work for the top tier, but fail for the bottom tier.',
        'pitch_angle': '"Shikhar is great for the top tier. Let Vani drive the bottom tier who can\'t type but can talk."',
        'script': "Hi Arun, been following your work on HUL's digital transformation. We've built Vani, an Agentic AI Voice Sales Officer designed to capture orders from the bottom 50% of retailers who struggle with apps like Shikhar due to literacy or habit. Vani calls them, negotiates in native Hindi/Tamil, and punches orders directly. Would you be open to a pilot on 1,000 'inactive' rural stores to see if we can wake them up?"
    },
    'Britannia Ind.': {
        'contact_name': 'Shantanu Gupta',
        'role': 'National Sales Dev Mgr',
        'pain_point': 'Losing market share to regional players (Parle) in rural belts due to lack of real-time reach. Human visits (₹300) make serving deep rural stores unviable.',
        'pitch_angle': '"Real-time coverage of remote villages without adding headcount."',
        'script': "Hi Shantanu, I know RTM efficiency is a priority for Britannia. The cost of a human visit (₹300) often makes serving deep rural stores unviable. We solve this with Vani—an autonomous Voice AI agent that costs pennies per call. She can cover your 'dark' rural territories daily without adding headcount. Can we run a 30-day reactivation pilot on your dead stockist list?"
    },
    'Marico': {
        'contact_name': 'Vaibhav Bhanchawat',
        'role': 'COO',
        'pain_point': 'Aggressive expansion into Pharmacies and Cosmetic Stores—new channels where their current human salesforce is weak.',
        'pitch_angle': '"Don\'t hire 1,000 new agents for Pharmacies. Deploy Vani to call every chemist in India tomorrow."',
        'script': "Hi Vaibhav, congrats on the Foods growth. I know expanding into Pharmacies/Cosmetic outlets is key. Instead of hiring a massive new field force, have you considered a Digital Sales Force? Vani (our AI Agent) can call 10,000 pharmacies in a day to stock Saffola/Parachute. Zero latency, full negotiation capability. Happy to demo the voice capability if you have 5 mins."
    },
    'Asian Paints': {
        'contact_name': 'Yash Batra',
        'role': 'Chief Sales Exec',
        'pain_point': 'High "Cost to Serve" for small hardware stores (selling putty/primer) compared to big "Beautiful Homes" dealers. 20k+ dealers don\'t justify a weekly visit.',
        'pitch_angle': '"Reactivate your 100k inactive dealers profitably."',
        'script': "Hi Yash, Asian Paints owns the dealer network, but the smaller hardware stores remain expensive to serve manually. We built Vani to fix this arbitrage. She is a Voice AI agent that can autonomously manage order collection from your bottom 20k dealers who don't order frequently enough to justify a weekly visit. Would love to show you how she handles 'Hinglish' negotiation."
    },
    'ITC Limited': {
        'contact_name': 'Hemant Malik',
        'role': 'Divisional Chief Exec',
        'pain_point': 'Massive portfolio (Aashirvaad, Bingo, Sunfeast). Retailers forget to order half the SKUs because the human agent is in a rush.',
        'pitch_angle': '"Vani never forgets to upsell the new Bingo flavor."',
        'script': "Hi Hemant, the biggest challenge in General Trade is retailers forgetting to order the full SKU range. Humans rush the visit; Vani (our AI agent) doesn't. She memorizes purchase history and upsells specific SKUs (like Bingo or new launches) on every call. We are already seeing high conversion on 'dead' store pilots. Open to a quick chat?"
    }
}

def update_fmcg_targets():
    """Update existing FMCG targets with complete data"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_service_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY required in .env.local")
        return False
    
    headers = {
        'apikey': supabase_service_key,
        'Authorization': f'Bearer {supabase_service_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'  # Return updated rows
    }
    
    try:
        # Step 1: Get FMCG industry ID
        print("\n🔍 Looking up FMCG industry...")
        industry_response = requests.get(
            f"{supabase_url}/rest/v1/industries?name=eq.FMCG&select=id,name",
            headers=headers
        )
        
        if not industry_response.ok:
            print(f"❌ Error looking up industry: {industry_response.status_code}")
            return False
        
        industries = industry_response.json()
        if not industries:
            print("❌ FMCG industry not found")
            return False
        
        fmcg_industry_id = industries[0]['id']
        print(f"✅ Found FMCG industry: {industries[0]['name']} (ID: {fmcg_industry_id})")
        
        # Step 2: Get all FMCG targets
        print("\n🔍 Fetching existing FMCG targets...")
        targets_response = requests.get(
            f"{supabase_url}/rest/v1/targets?industry_id=eq.{fmcg_industry_id}&select=id,company_name,contact_name,role,pain_point,pitch_angle,script",
            headers=headers
        )
        
        if not targets_response.ok:
            print(f"❌ Error fetching targets: {targets_response.status_code} - {targets_response.text}")
            return False
        
        existing_targets = targets_response.json()
        print(f"✅ Found {len(existing_targets)} existing FMCG targets")
        
        # Step 3: Match and update/create targets
        updated_count = 0
        created_count = 0
        
        for company_name, target_data in TARGET_DATA.items():
            print(f"\n📝 Processing: {company_name} - {target_data['contact_name']}")
            
            # Try to find matching target by company name and contact name
            matching_target = None
            for target in existing_targets:
                target_company = (target.get('company_name') or '').strip()
                target_contact = (target.get('contact_name') or '').strip()
                
                # Match by company name (exact or partial) and contact name
                if (company_name.lower() in target_company.lower() or 
                    target_company.lower() in company_name.lower()):
                    if target_data['contact_name'].lower() in target_contact.lower() or \
                       target_contact.lower() in target_data['contact_name'].lower():
                        matching_target = target
                        break
            
            if matching_target:
                # Update existing target
                target_id = matching_target['id']
                print(f"   Found existing target (ID: {target_id}), updating...")
                
                update_data = {
                    'company_name': company_name,
                    'contact_name': target_data['contact_name'],
                    'role': target_data['role'],
                    'pain_point': target_data['pain_point'],
                    'pitch_angle': target_data['pitch_angle'],
                    'script': target_data['script'],
                    'industry_id': fmcg_industry_id
                }
                
                update_response = requests.patch(
                    f"{supabase_url}/rest/v1/targets?id=eq.{target_id}",
                    headers=headers,
                    json=update_data
                )
                
                if update_response.ok:
                    print(f"   ✅ Updated successfully")
                    updated_count += 1
                else:
                    print(f"   ❌ Update failed: {update_response.status_code} - {update_response.text}")
                    # If update fails, try to create instead
                    print(f"   Attempting to create new target instead...")
                    matching_target = None  # Fall through to create logic
            
            if not matching_target:
                # Create new target (either no match found, or update failed)
                print(f"   Creating new target...")
                
                insert_data = {
                    'company_name': company_name,
                    'contact_name': target_data['contact_name'],
                    'role': target_data['role'],
                    'pain_point': target_data['pain_point'],
                    'pitch_angle': target_data['pitch_angle'],
                    'script': target_data['script'],
                    'industry_id': fmcg_industry_id,
                    'status': 'new'  # Must be lowercase per CHECK constraint
                }
                
                insert_response = requests.post(
                    f"{supabase_url}/rest/v1/targets",
                    headers=headers,
                    json=insert_data
                )
                
                if insert_response.ok:
                    try:
                        created_target = insert_response.json()
                        if isinstance(created_target, list) and len(created_target) > 0:
                            created_target = created_target[0]
                        print(f"   ✅ Created successfully (ID: {created_target.get('id', 'unknown')})")
                        created_count += 1
                    except:
                        print(f"   ✅ Created successfully")
                        created_count += 1
                else:
                    error_text = insert_response.text
                    print(f"   ❌ Creation failed: {insert_response.status_code}")
                    print(f"   Error: {error_text[:200]}")
        
        print(f"\n✅ Summary:")
        print(f"   - Updated: {updated_count} targets")
        print(f"   - Created: {created_count} targets")
        print(f"   - Total processed: {updated_count + created_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n=== Update FMCG Targets ===")
    if update_fmcg_targets():
        print("\n✅ FMCG targets update completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ FMCG targets update failed.")
        sys.exit(1)

