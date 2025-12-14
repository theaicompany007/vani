"""Industry to VANI Persona mapping service"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IndustryPersonaContext:
    """Industry-specific persona context"""
    industry: str
    vani_persona: str
    persona_description: str
    pain_points: List[str]
    use_case_examples: List[str]
    value_proposition_template: str
    common_use_cases: List[str]


class IndustryPersonaMapping:
    """Maps industries to VANI Personas and provides context"""
    
    # Industry to Persona mapping
    INDUSTRY_PERSONA_MAP = {
        # FMCG / Beverage / Retail Distribution
        'FMCG': 'Digital Sales Officer',
        'Beverage': 'Digital Sales Officer',
        'Food & Beverages': 'Digital Sales Officer',
        'Retail': 'Digital Sales Officer',
        'Retail Distribution': 'Digital Sales Officer',
        
        # Financial Services
        'Financial Services': 'Activation Concierge',
        'Banking': 'Activation Concierge',
        'FinTech': 'Activation Concierge',
        'Credit Cards': 'Activation Concierge',
        
        # B2B / Manufacturing / Exports
        'Manufacturing': 'Global Sales Associate',
        'B2B': 'Global Sales Associate',
        'Exports': 'Global Sales Associate',
        'Conglomerate': 'Global Sales Associate',
        'Textiles': 'Global Sales Associate',
        'Graphite': 'Global Sales Associate',
        'Power': 'Global Sales Associate',
        'Logistics': 'Logistics Automator',
        'Supply Chain': 'Logistics Automator',
        
        # Other industries
        'Healthcare': 'Patient Engagement Assistant',
        'Education': 'Student Onboarding Concierge',
        'Real Estate': 'Lead Qualification Specialist',
        'Technology': 'Sales Development Rep',
        'SaaS': 'Activation Concierge',
        'Information Technology': 'Sales Development Rep',
    }
    
    # Persona definitions with context
    PERSONA_CONTEXTS = {
        'Digital Sales Officer': IndustryPersonaContext(
            industry='FMCG/Beverage/Retail',
            vani_persona='Digital Sales Officer',
            persona_description='AI-powered sales officer for distribution and retail outreach',
            pain_points=[
                'Dead/Dormant Retailers (outlets stop ordering)',
                'Stock-Outs (retailers wait for salesman visits)',
                'New Product Launch Delays (slow rollout to outlets)',
                'Last-Mile Reach (rural/semi-urban coverage)',
                'High cost of human sales visits (₹300/visit)',
                'Inefficient route-to-market coverage'
            ],
            use_case_examples=[
                'Rural distribution and retailer reactivation',
                'Instant product launches to thousands of outlets',
                'Zero-cost coverage of bottom 80% of retailers',
                'Automated stock replenishment calls',
                'Multi-language retailer communication'
            ],
            value_proposition_template='Cover the "unvisited" 80% of retailers at 1/10th the cost (₹5 per call vs ₹300 per visit)',
            common_use_cases=[
                'Retailer reactivation',
                'Stock replenishment',
                'New product launches',
                'Route-to-market coverage',
                'Rural distribution'
            ]
        ),
        
        'Activation Concierge': IndustryPersonaContext(
            industry='Financial Services/Banking/FinTech',
            vani_persona='Activation Concierge',
            persona_description='AI concierge for product activation and onboarding',
            pain_points=[
                'Activation Gap (users don\'t activate products/services)',
                'Regulatory Compliance (deadlines for activation)',
                'Call Center Costs (expensive human agents)',
                'Onboarding Drop-off (users abandon during setup)',
                'Low activation rates affecting CAC'
            ],
            use_case_examples=[
                'Card activation within 24 hours of delivery',
                'Account onboarding with personalized guidance',
                'Product activation with multi-channel nudges',
                'PIN setup assistance via secure voice call',
                'First transaction guidance'
            ],
            value_proposition_template='Boost activation rates by 20-30% with automated, personalized guidance within 24 hours',
            common_use_cases=[
                'Card activation',
                'Account onboarding',
                'Product activation',
                'Service setup',
                'User onboarding'
            ]
        ),
        
        'Global Sales Associate': IndustryPersonaContext(
            industry='B2B/Manufacturing/Exports',
            vani_persona='Global Sales Associate',
            persona_description='24/7 global sales associate for B2B lead qualification and exports',
            pain_points=[
                'Lead Qualification (filtering serious buyers)',
                'Global Time Zones (24/7 coverage needed)',
                'Vendor/Supplier Management (constant follow-up)',
                'Export Coordination (multi-timezone operations)',
                'Window shoppers consuming sales engineer time'
            ],
            use_case_examples=[
                'B2B lead qualification for export sales',
                '24/7 response to global buyer inquiries',
                'Supplier coordination and dispatch follow-up',
                'Export documentation and logistics coordination',
                'Initial inquiry filtering and qualification'
            ],
            value_proposition_template='24/7 response for global operations; ensure experts only talk to serious buyers',
            common_use_cases=[
                'B2B lead qualification',
                'Export management',
                'Supplier coordination',
                'Global inquiry handling',
                'Vendor management'
            ]
        ),
        
        'Logistics Automator': IndustryPersonaContext(
            industry='Logistics/Supply Chain',
            vani_persona='Logistics Automator',
            persona_description='AI automator for logistics and supply chain coordination',
            pain_points=[
                'Vendor/Supplier Follow-up (constant status checks)',
                'Dispatch Coordination (tracking shipments)',
                'Multi-party Communication (suppliers, transporters, warehouses)',
                'Real-time Status Updates (where is the truck?)',
                'Documentation Coordination (export/import docs)'
            ],
            use_case_examples=[
                'Automated supplier dispatch follow-up',
                'Real-time shipment status updates',
                'Multi-party logistics coordination',
                'Export documentation automation',
                'Warehouse coordination'
            ],
            value_proposition_template='Automate logistics coordination; free procurement teams from manual follow-up',
            common_use_cases=[
                'Supplier coordination',
                'Dispatch tracking',
                'Logistics automation',
                'Documentation management',
                'Multi-party coordination'
            ]
        ),
        
        'Patient Engagement Assistant': IndustryPersonaContext(
            industry='Healthcare',
            vani_persona='Patient Engagement Assistant',
            persona_description='AI assistant for patient engagement and healthcare outreach',
            pain_points=[
                'Appointment Reminders (no-shows)',
                'Medication Adherence (follow-up calls)',
                'Patient Onboarding (new patient setup)',
                'Health Check Reminders (preventive care)',
                'Post-treatment Follow-up'
            ],
            use_case_examples=[
                'Appointment reminder calls',
                'Medication adherence follow-up',
                'New patient onboarding',
                'Health check reminders',
                'Post-treatment care coordination'
            ],
            value_proposition_template='Improve patient engagement and reduce no-shows with automated, personalized outreach',
            common_use_cases=[
                'Appointment reminders',
                'Medication adherence',
                'Patient onboarding',
                'Health check reminders',
                'Care coordination'
            ]
        ),
        
        'Student Onboarding Concierge': IndustryPersonaContext(
            industry='Education',
            vani_persona='Student Onboarding Concierge',
            persona_description='AI concierge for student onboarding and engagement',
            pain_points=[
                'Admission Follow-up (applicants don\'t complete)',
                'Orientation Attendance (low participation)',
                'Documentation Collection (incomplete submissions)',
                'Fee Payment Reminders (delayed payments)',
                'Course Enrollment (drop-off during process)'
            ],
            use_case_examples=[
                'Admission process guidance',
                'Orientation reminder calls',
                'Documentation collection follow-up',
                'Fee payment reminders',
                'Course enrollment assistance'
            ],
            value_proposition_template='Improve student onboarding completion rates with automated, helpful guidance',
            common_use_cases=[
                'Admission follow-up',
                'Orientation reminders',
                'Documentation collection',
                'Fee payment',
                'Course enrollment'
            ]
        ),
        
        'Lead Qualification Specialist': IndustryPersonaContext(
            industry='Real Estate',
            vani_persona='Lead Qualification Specialist',
            persona_description='AI specialist for real estate lead qualification',
            pain_points=[
                'Lead Qualification (filtering serious buyers)',
                'Property Inquiry Follow-up (time-sensitive)',
                'Site Visit Scheduling (coordination overhead)',
                'Documentation Collection (KYC, financial docs)',
                'Window shoppers consuming agent time'
            ],
            use_case_examples=[
                'Initial lead qualification calls',
                'Property inquiry follow-up',
                'Site visit scheduling',
                'Documentation collection',
                'Buyer qualification'
            ],
            value_proposition_template='Qualify leads instantly; ensure agents only engage with serious buyers',
            common_use_cases=[
                'Lead qualification',
                'Inquiry follow-up',
                'Site visit scheduling',
                'Documentation collection',
                'Buyer qualification'
            ]
        ),
        
        'Sales Development Rep': IndustryPersonaContext(
            industry='Technology/SaaS',
            vani_persona='Sales Development Rep',
            persona_description='AI sales development representative for tech/SaaS outreach',
            pain_points=[
                'Lead Qualification (filtering qualified opportunities)',
                'Demo Scheduling (coordination overhead)',
                'Trial Activation (users don\'t activate)',
                'Onboarding Drop-off (users abandon setup)',
                'Follow-up Coordination (multiple touchpoints)'
            ],
            use_case_examples=[
                'B2B lead qualification',
                'Demo scheduling and reminders',
                'Trial activation assistance',
                'Onboarding guidance',
                'Follow-up coordination'
            ],
            value_proposition_template='Qualify leads and activate trials faster; ensure sales team focuses on high-value opportunities',
            common_use_cases=[
                'Lead qualification',
                'Demo scheduling',
                'Trial activation',
                'User onboarding',
                'Follow-up coordination'
            ]
        ),
    }
    
    @classmethod
    def get_persona_for_industry(cls, industry: str) -> Optional[str]:
        """Get VANI Persona for a given industry"""
        # Normalize industry name
        industry_normalized = industry.strip().title()
        
        # Direct match
        if industry_normalized in cls.INDUSTRY_PERSONA_MAP:
            return cls.INDUSTRY_PERSONA_MAP[industry_normalized]
        
        # Partial match (case-insensitive)
        for key, persona in cls.INDUSTRY_PERSONA_MAP.items():
            if key.lower() in industry.lower() or industry.lower() in key.lower():
                return persona
        
        # Default fallback
        logger.warning(f"No persona mapping found for industry: {industry}, using default")
        return 'Global Sales Associate'  # Default persona
    
    @classmethod
    def get_industry_context(cls, industry: str, supabase_client=None) -> Optional[IndustryPersonaContext]:
        """Get full industry context including persona, pain points, use cases
        Checks database first for custom mappings, falls back to hardcoded defaults
        """
        # Try to get from database if supabase_client is provided
        if supabase_client:
            try:
                result = supabase_client.table('industry_persona_mappings').select('*').eq('industry_name', industry).limit(1).execute()
                if result.data and len(result.data) > 0:
                    mapping = result.data[0]
                    logger.debug(f"Found custom persona mapping for {industry} in database")
                    
                    # Parse JSONB fields
                    import json
                    pain_points = mapping.get('pain_points', [])
                    use_case_examples = mapping.get('use_case_examples', [])
                    common_use_cases = mapping.get('common_use_cases', [])
                    
                    # Handle JSONB (might be string or already parsed)
                    if isinstance(pain_points, str):
                        pain_points = json.loads(pain_points)
                    if isinstance(use_case_examples, str):
                        use_case_examples = json.loads(use_case_examples)
                    if isinstance(common_use_cases, str):
                        common_use_cases = json.loads(common_use_cases)
                    
                    return IndustryPersonaContext(
                        industry=industry,
                        vani_persona=mapping.get('vani_persona', 'Global Sales Associate'),
                        persona_description=mapping.get('persona_description', ''),
                        pain_points=pain_points or [],
                        use_case_examples=use_case_examples or [],
                        value_proposition_template=mapping.get('value_proposition_template', ''),
                        common_use_cases=common_use_cases or []
                    )
            except Exception as e:
                logger.warning(f"Error fetching persona mapping from database for {industry}: {e}. Falling back to defaults.")
        
        # Fallback to hardcoded defaults
        persona = cls.get_persona_for_industry(industry)
        if persona and persona in cls.PERSONA_CONTEXTS:
            context = cls.PERSONA_CONTEXTS[persona]
            # Update industry name to match requested industry
            context.industry = industry
            return context
        
        # Return default context if persona not found
        logger.warning(f"No context found for persona: {persona}, using default")
        default = cls.PERSONA_CONTEXTS.get('Global Sales Associate')
        if default:
            default.industry = industry
        return default
    
    @classmethod
    def get_pain_points(cls, industry: str, supabase_client=None) -> List[str]:
        """Get pain points for an industry"""
        context = cls.get_industry_context(industry, supabase_client=supabase_client)
        return context.pain_points if context else []
    
    @classmethod
    def get_use_cases(cls, industry: str, supabase_client=None) -> List[str]:
        """Get use case examples for an industry"""
        context = cls.get_industry_context(industry, supabase_client=supabase_client)
        return context.use_case_examples if context else []
    
    @classmethod
    def get_value_proposition_template(cls, industry: str, supabase_client=None) -> str:
        """Get value proposition template for an industry"""
        context = cls.get_industry_context(industry, supabase_client=supabase_client)
        return context.value_proposition_template if context else 'AI-powered automation for operational efficiency'
    
    @classmethod
    def list_available_industries(cls) -> List[str]:
        """List all industries with persona mappings"""
        return list(cls.INDUSTRY_PERSONA_MAP.keys())
    
    @classmethod
    def list_available_personas(cls) -> List[str]:
        """List all available VANI Personas"""
        return list(cls.PERSONA_CONTEXTS.keys())



