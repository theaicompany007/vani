"""Script to seed targets from HTML file data into Supabase"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.supabase_client import init_supabase
from app.models.targets import Target, TargetStatus

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)

# Target data from the HTML file
TARGETS_DATA = [
    {
        'company_name': 'Hindustan Unilever',
        'contact_name': 'Arun Neelakantan',
        'role': 'ED, Customer Dev',
        'email': None,  # To be filled
        'phone': None,  # To be filled
        'linkedin_url': None,
        'pain_point': 'Need to drive usage of "Shikhar" app in deep rural areas where literacy is a barrier. Apps work for the top tier, but fail for the bottom tier.',
        'pitch_angle': '"Shikhar is great for the top tier. Let Vani drive the bottom tier who can\'t type but can talk."',
        'script': "Hi Arun, been following your work on HUL's digital transformation. We've built Vani, an Agentic AI Voice Sales Officer designed to capture orders from the bottom 50% of retailers who struggle with apps like Shikhar due to literacy or habit. Vani calls them, negotiates in native Hindi/Tamil, and punches orders directly. Would you be open to a pilot on 1,000 'inactive' rural stores to see if we can wake them up?",
        'status': TargetStatus.NEW
    },
    {
        'company_name': 'Britannia Ind.',
        'contact_name': 'Shantanu Gupta',
        'role': 'National Sales Dev Mgr',
        'email': None,
        'phone': None,
        'linkedin_url': None,
        'pain_point': 'Losing market share to regional players (Parle) in rural belts due to lack of real-time reach. Human visits (₹300) make serving deep rural stores unviable.',
        'pitch_angle': '"Real-time coverage of remote villages without adding headcount."',
        'script': "Hi Shantanu, I know RTM efficiency is a priority for Britannia. The cost of a human visit (₹300) often makes serving deep rural stores unviable. We solve this with Vani—an autonomous Voice AI agent that costs pennies per call. She can cover your 'dark' rural territories daily without adding headcount. Can we run a 30-day reactivation pilot on your dead stockist list?",
        'status': TargetStatus.NEW
    },
    {
        'company_name': 'Marico',
        'contact_name': 'Vaibhav Bhanchawat',
        'role': 'COO',
        'email': None,
        'phone': None,
        'linkedin_url': None,
        'pain_point': 'Aggressive expansion into Pharmacies and Cosmetic Stores—new channels where their current human salesforce is weak.',
        'pitch_angle': '"Don\'t hire 1,000 new agents for Pharmacies. Deploy Vani to call every chemist in India tomorrow."',
        'script': "Hi Vaibhav, congrats on the Foods growth. I know expanding into Pharmacies/Cosmetic outlets is key. Instead of hiring a massive new field force, have you considered a Digital Sales Force? Vani (our AI Agent) can call 10,000 pharmacies in a day to stock Saffola/Parachute. Zero latency, full negotiation capability. Happy to demo the voice capability if you have 5 mins.",
        'status': TargetStatus.NEW
    },
    {
        'company_name': 'Asian Paints',
        'contact_name': 'Yash Batra',
        'role': 'Chief Sales Exec',
        'email': None,
        'phone': None,
        'linkedin_url': None,
        'pain_point': 'High "Cost to Serve" for small hardware stores (selling putty/primer) compared to big "Beautiful Homes" dealers. 20k+ dealers don\'t justify a weekly visit.',
        'pitch_angle': '"Reactivate your 100k inactive dealers profitably."',
        'script': "Hi Yash, Asian Paints owns the dealer network, but the smaller hardware stores remain expensive to serve manually. We built Vani to fix this arbitrage. She is a Voice AI agent that can autonomously manage order collection from your bottom 20k dealers who don't order frequently enough to justify a weekly visit. Would love to show you how she handles 'Hinglish' negotiation.",
        'status': TargetStatus.NEW
    },
    {
        'company_name': 'ITC Limited',
        'contact_name': 'Hemant Malik',
        'role': 'Divisional Chief Exec',
        'email': None,
        'phone': None,
        'linkedin_url': None,
        'pain_point': 'Massive portfolio (Aashirvaad, Bingo, Sunfeast). Retailers forget to order half the SKUs because the human agent is in a rush.',
        'pitch_angle': '"Vani never forgets to upsell the new Bingo flavor."',
        'script': "Hi Hemant, the biggest challenge in General Trade is retailers forgetting to order the full SKU range. Humans rush the visit; Vani (our AI agent) doesn't. She memorizes purchase history and upsells specific SKUs (like Bingo or new launches) on every call. We are already seeing high conversion on 'dead' store pilots. Open to a quick chat?",
        'status': TargetStatus.NEW
    }
]


def seed_targets():
    """Seed targets into Supabase"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env.local")
        return False
    
    supabase = init_supabase(supabase_url, supabase_key)
    if not supabase:
        print("ERROR: Failed to initialize Supabase client")
        return False
    
    print(f"Seeding {len(TARGETS_DATA)} targets into Supabase...")
    
    seeded = 0
    for target_data in TARGETS_DATA:
        try:
            # Check if target already exists
            existing = supabase.table('targets').select('id').eq('company_name', target_data['company_name']).execute()
            
            if existing.data:
                print(f"  ⏭️  Skipping {target_data['company_name']} (already exists)")
                continue
            
            # Create target
            target = Target(**target_data)
            target_dict = target.to_dict()
            target_dict.pop('id', None)
            
            response = supabase.table('targets').insert(target_dict).execute()
            
            if response.data:
                print(f"  ✅ Seeded {target_data['company_name']}")
                seeded += 1
            else:
                print(f"  ❌ Failed to seed {target_data['company_name']}")
                
        except Exception as e:
            print(f"  ❌ Error seeding {target_data['company_name']}: {e}")
    
    print(f"\n✅ Successfully seeded {seeded} targets")
    return True


if __name__ == '__main__':
    seed_targets()

