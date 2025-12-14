"""
AI-Powered Target Industry Assignment
- Finds targets without industry_id
- Uses company name matching and AI to infer correct industry
- Updates targets with industry_id from industries table
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
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

class TargetIndustryAssigner:
    def __init__(self, use_ai=True):
        self.use_ai = use_ai
        self.openai_client = None
        self.industries_map = {}  # industry name -> industry_id
        self.industry_keywords = {}  # keywords -> industry name
        
        # Initialize OpenAI if available
        if self.use_ai:
            try:
                import openai
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized for AI industry inference")
                else:
                    logger.warning("OPENAI_API_KEY not found - AI features disabled")
                    self.use_ai = False
            except ImportError:
                logger.warning("OpenAI module not available - AI features disabled")
                self.use_ai = False
        
        self.stats = {
            'targets_processed': 0,
            'industries_assigned': 0,
            'ai_inferences': 0,
            'keyword_matches': 0,
            'errors': 0
        }
    
    def load_industries(self):
        """Load all industries from database and build keyword mapping"""
        logger.info("Loading industries from database...")
        
        try:
            response = supabase.table('industries').select('id, name').execute()
            industries = response.data or []
            
            for ind in industries:
                industry_id = ind['id']
                industry_name = ind['name'].lower()
                self.industries_map[industry_name] = industry_id
                
                # Build keyword mapping for common company name patterns
                name_lower = industry_name.lower()
                
                # Map keywords to industries
                if 'food' in name_lower or 'beverage' in name_lower or 'fmcg' in name_lower:
                    self.industry_keywords['food'] = industry_name
                    self.industry_keywords['beverage'] = industry_name
                    self.industry_keywords['fmcg'] = industry_name
                    self.industry_keywords['agro'] = industry_name
                    self.industry_keywords['restaurant'] = industry_name
                
                if 'financial' in name_lower or 'finance' in name_lower or 'banking' in name_lower:
                    self.industry_keywords['financial'] = industry_name
                    self.industry_keywords['bank'] = industry_name
                    self.industry_keywords['card'] = industry_name
                    self.industry_keywords['credit'] = industry_name
                
                if 'textile' in name_lower:
                    self.industry_keywords['textile'] = industry_name
                    self.industry_keywords['textiles'] = industry_name
                    self.industry_keywords['fabric'] = industry_name
                    self.industry_keywords['rswm'] = industry_name
                elif 'apparel' in name_lower or 'fashion' in name_lower:
                    self.industry_keywords['apparel'] = industry_name
                    self.industry_keywords['fashion'] = industry_name
                
                if 'manufacturing' in name_lower or 'industrial' in name_lower:
                    self.industry_keywords['manufacturing'] = industry_name
                    self.industry_keywords['industrial'] = industry_name
                    self.industry_keywords['heg'] = industry_name
                    self.industry_keywords['graphite'] = industry_name
                    self.industry_keywords['electrode'] = industry_name
            
            logger.info(f"Loaded {len(industries)} industries")
            logger.info(f"Built keyword mapping with {len(self.industry_keywords)} keywords")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load industries: {e}")
            return False
    
    def match_industry_by_keywords(self, company_name: str) -> Optional[str]:
        """Match industry using company name keywords"""
        if not company_name:
            return None
        
        company_lower = company_name.lower()
        
        # Direct company name matching (known companies)
        known_companies = {
            'parle agro': 'food & beverages',
            'parle': 'food & beverages',
            'sbi cards': 'financial services',
            'sbi card': 'financial services',
            'rswm': 'textiles',
            'rswm limited': 'textiles',
            'heg': 'manufacturing',
            'heg limited': 'manufacturing',
            'nirula': 'food & beverages',
            'food club': 'food & beverages',
            'bittoo tikki': 'food & beverages',
        }
        
        for key, industry in known_companies.items():
            if key in company_lower:
                if industry in self.industries_map:
                    self.stats['keyword_matches'] += 1
                    return self.industries_map[industry]
        
        # Keyword-based matching
        for keyword, industry_name in self.industry_keywords.items():
            if keyword in company_lower:
                if industry_name in self.industries_map:
                    self.stats['keyword_matches'] += 1
                    return self.industries_map[industry_name]
        
        return None
    
    def infer_industry_with_ai(self, company_name: str, role: Optional[str] = None) -> Optional[str]:
        """Use AI to infer industry from company name and role"""
        if not self.use_ai or not self.openai_client:
            return None
        
        try:
            context_parts = [f"Company: {company_name}"]
            if role:
                context_parts.append(f"Role: {role}")
            
            context = "\n".join(context_parts)
            
            # Get list of available industries for the prompt
            available_industries = ", ".join(sorted(self.industries_map.keys()))
            
            prompt = f"""Based on the following company information, infer the most likely industry sector.
Return ONLY ONE industry name from this list (case-insensitive match): {available_industries}

Company Information:
{context}

Industry (exact match from list above):"""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are an expert at classifying companies into industry sectors. Always respond with exactly one industry name from this list: {available_industries}. Match the format exactly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=30
            )
            
            inferred_industry = response.choices[0].message.content.strip().lower()
            
            # Find matching industry in our map
            for industry_name, industry_id in self.industries_map.items():
                if industry_name.lower() == inferred_industry or inferred_industry in industry_name.lower():
                    logger.debug(f"AI inferred industry '{industry_name}' for {company_name}")
                    self.stats['ai_inferences'] += 1
                    return industry_id
            
            logger.warning(f"AI inferred '{inferred_industry}' but it doesn't match any known industry")
            return None
            
        except Exception as e:
            logger.warning(f"AI industry inference failed for {company_name}: {e}")
            return None
    
    def assign_industry_to_target(self, target: Dict[str, Any]) -> bool:
        """Assign industry_id to a target"""
        target_id = target.get('id')
        company_name = target.get('company_name', '')
        role = target.get('role')
        
        # Try keyword matching first (faster and free)
        industry_id = self.match_industry_by_keywords(company_name)
        
        # If no keyword match and AI is enabled, try AI
        if not industry_id and self.use_ai:
            industry_id = self.infer_industry_with_ai(company_name, role)
        
        if not industry_id:
            logger.warning(f"Could not determine industry for {company_name} (Target ID: {target_id})")
            return False
        
        # Update target with industry_id
        try:
            response = supabase.table('targets').update({
                'industry_id': industry_id
            }).eq('id', target_id).execute()
            
            if response.data:
                industry_name = next((name for name, id in self.industries_map.items() if id == industry_id), 'Unknown')
                logger.info(f"Assigned industry '{industry_name}' to {company_name} (Target ID: {target_id})")
                self.stats['industries_assigned'] += 1
                return True
            else:
                logger.error(f"Failed to update target {target_id}")
                self.stats['errors'] += 1
                return False
                
        except Exception as e:
            logger.error(f"Error updating target {target_id}: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_all_targets(self, dry_run: bool = False):
        """Find and process all targets without industry_id"""
        logger.info(f"\n{'='*70}")
        logger.info(f"AI-POWERED TARGET INDUSTRY ASSIGNMENT")
        logger.info(f"{'='*70}\n")
        
        if dry_run:
            logger.info("[DRY RUN MODE - No changes will be made]\n")
        
        # Load industries
        if not self.load_industries():
            return False
        
        # Find targets without industry_id
        logger.info("Finding targets without industry_id...")
        try:
            response = supabase.table('targets').select(
                'id, company_name, role, industry_id'
            ).is_('industry_id', 'null').execute()
            
            targets = response.data or []
            
            if not targets:
                logger.info("No targets found without industry_id. All targets are assigned!")
                return True
            
            logger.info(f"Found {len(targets)} targets without industry_id\n")
            
            # Process each target
            for i, target in enumerate(targets, 1):
                company_name = target.get('company_name', 'Unknown')
                logger.info(f"[{i}/{len(targets)}] Processing: {company_name}")
                
                if not dry_run:
                    self.assign_industry_to_target(target)
                else:
                    # Dry run: just show what would be assigned
                    industry_id = self.match_industry_by_keywords(company_name)
                    if not industry_id and self.use_ai:
                        industry_id = self.infer_industry_with_ai(company_name, target.get('role'))
                    
                    if industry_id:
                        industry_name = next((name for name, id in self.industries_map.items() if id == industry_id), 'Unknown')
                        logger.info(f"  Would assign: {industry_name}")
                    else:
                        logger.warning(f"  Could not determine industry")
                
                self.stats['targets_processed'] += 1
            
            # Print summary
            logger.info(f"\n{'='*70}")
            logger.info(f"ASSIGNMENT SUMMARY")
            logger.info(f"{'='*70}")
            logger.info(f"Targets processed: {self.stats['targets_processed']}")
            if not dry_run:
                logger.info(f"Industries assigned: {self.stats['industries_assigned']}")
                logger.info(f"Keyword matches: {self.stats['keyword_matches']}")
                logger.info(f"AI inferences: {self.stats['ai_inferences']}")
                logger.info(f"Errors: {self.stats['errors']}")
            logger.info(f"{'='*70}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing targets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-powered target industry assignment')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be assigned without making changes')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI industry inference (use keyword matching only)')
    
    args = parser.parse_args()
    
    assigner = TargetIndustryAssigner(use_ai=not args.no_ai)
    success = assigner.process_all_targets(dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

