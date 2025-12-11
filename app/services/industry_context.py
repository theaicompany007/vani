"""Industry context service for industry-specific configurations"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IndustryContext:
    """Industry-specific context and configurations"""
    name: str
    display_name: str
    pain_points: list
    common_roles: list
    challenges: list
    messaging_templates: Dict[str, str]
    solution_fit: Dict[str, float]  # Onlyne Reputation vs The AI Company fit scores


class IndustryContextService:
    """Service for managing industry-specific contexts"""
    
    # Industry configurations
    INDUSTRY_CONFIGS = {
        'FMCG': IndustryContext(
            name='FMCG',
            display_name='FMCG',
            pain_points=[
                'High cost to serve deep rural stores',
                'Losing market share to regional players',
                'Inefficient route-to-market coverage',
                'High cost of human sales visits',
                'Difficulty reaching bottom-tier retailers'
            ],
            common_roles=[
                'Sales Director',
                'National Sales Manager',
                'Customer Development Manager',
                'RTM Manager',
                'Distribution Head'
            ],
            challenges=[
                'Rural market penetration',
                'Cost-effective distribution',
                'Real-time order collection',
                'Inactive store reactivation',
                'Multi-language communication'
            ],
            messaging_templates={
                'pain_point': 'High cost to serve {company} stores makes serving deep rural areas unviable',
                'pitch_angle': 'Real-time coverage of remote areas without adding headcount',
                'solution_fit': 'The AI Company - Voice AI agent for autonomous order collection'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.9
            }
        ),
        'Food & Beverages': IndustryContext(
            name='Food & Beverages',
            display_name='Food & Beverages',
            pain_points=[
                'Aggressive expansion into new channels',
                'Weak salesforce in new markets',
                'High cost of hiring new sales teams',
                'Need for rapid market coverage',
                'Channel partner management'
            ],
            common_roles=[
                'Marketing VP',
                'Sales Development Manager',
                'Channel Head',
                'Business Development Manager',
                'National Sales Manager'
            ],
            challenges=[
                'New channel expansion',
                'Pharmacy and cosmetic store coverage',
                'Rapid market entry',
                'Digital sales force deployment',
                'Multi-channel management'
            ],
            messaging_templates={
                'pain_point': 'Expanding into {channel} requires massive new field force',
                'pitch_angle': 'Deploy digital sales force to cover new channels without hiring',
                'solution_fit': 'The AI Company - Voice AI agent for autonomous channel coverage'
            },
            solution_fit={
                'onlyne_reputation': 0.4,
                'the_ai_company': 0.8
            }
        ),
        'Technology': IndustryContext(
            name='Technology',
            display_name='Technology',
            pain_points=[
                'Digital reputation management',
                'Online review generation',
                'Sentiment analysis needs',
                'Brand monitoring',
                'Customer feedback management'
            ],
            common_roles=[
                'Marketing Director',
                'Brand Manager',
                'Digital Marketing Head',
                'Customer Success Manager',
                'Product Manager'
            ],
            challenges=[
                'Online reputation management',
                'Review generation and management',
                'Sentiment tracking',
                'Brand perception',
                'Customer feedback loops'
            ],
            messaging_templates={
                'pain_point': 'Managing online reputation and reviews across multiple platforms',
                'pitch_angle': 'Automated reputation management and review generation',
                'solution_fit': 'Onlyne Reputation - Digital reputation management platform'
            },
            solution_fit={
                'onlyne_reputation': 0.9,
                'the_ai_company': 0.5
            }
        )
    }
    
    @classmethod
    def get_industry_context(cls, industry_name: str) -> Optional[IndustryContext]:
        """
        Get industry context for a given industry
        
        Args:
            industry_name: Industry name (e.g., 'FMCG', 'Food & Beverages')
            
        Returns:
            IndustryContext object or None if not found
        """
        # Normalize industry name
        normalized = industry_name.strip()
        
        # Try exact match first
        if normalized in cls.INDUSTRY_CONFIGS:
            return cls.INDUSTRY_CONFIGS[normalized]
        
        # Try case-insensitive match
        for key, context in cls.INDUSTRY_CONFIGS.items():
            if key.lower() == normalized.lower():
                return context
        
        # Try partial match
        normalized_lower = normalized.lower()
        for key, context in cls.INDUSTRY_CONFIGS.items():
            if normalized_lower in key.lower() or key.lower() in normalized_lower:
                return context
        
        # Return default/fallback context
        logger.warning(f"No specific context found for industry: {industry_name}, using default")
        return cls._get_default_context(industry_name)
    
    @classmethod
    def _get_default_context(cls, industry_name: str) -> IndustryContext:
        """Get default industry context when specific config not found"""
        return IndustryContext(
            name=industry_name,
            display_name=industry_name,
            pain_points=[
                'Need for digital transformation',
                'Cost optimization',
                'Market expansion',
                'Customer engagement'
            ],
            common_roles=[
                'Director',
                'VP',
                'Manager',
                'Head'
            ],
            challenges=[
                'Digital transformation',
                'Operational efficiency',
                'Market growth',
                'Customer acquisition'
            ],
            messaging_templates={
                'pain_point': 'Industry-specific challenges in {industry}',
                'pitch_angle': 'Technology solutions for {industry} growth',
                'solution_fit': 'Both solutions may be relevant'
            },
            solution_fit={
                'onlyne_reputation': 0.5,
                'the_ai_company': 0.5
            }
        )
    
    @classmethod
    def get_all_industries(cls) -> list:
        """Get list of all configured industries"""
        return list(cls.INDUSTRY_CONFIGS.keys())


def get_industry_context(industry_name: str) -> Optional[IndustryContext]:
    """Get industry context for a given industry"""
    return IndustryContextService.get_industry_context(industry_name)





