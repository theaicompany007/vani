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
        ),
        'Retail': IndustryContext(
            name='Retail',
            display_name='Retail',
            pain_points=[
                'Online reputation and review management',
                'Customer experience optimization',
                'Brand perception across channels',
                'Review generation and management',
                'Multi-channel customer engagement'
            ],
            common_roles=[
                'Store Owner',
                'Retail Manager',
                'Marketing Director',
                'Customer Experience Manager',
                'Brand Manager',
                'Operations Manager',
                'Business Owner'
            ],
            challenges=[
                'Online reputation management',
                'Review generation across platforms',
                'Customer feedback management',
                'Brand consistency across channels',
                'Digital presence optimization'
            ],
            messaging_templates={
                'pain_point': 'Managing online reputation and customer reviews across multiple platforms',
                'pitch_angle': 'Automated reputation management and review generation for retail businesses',
                'solution_fit': 'Onlyne Reputation - Digital reputation management platform for retail'
            },
            solution_fit={
                'onlyne_reputation': 0.85,
                'the_ai_company': 0.4
            }
        ),
        'Travel': IndustryContext(
            name='Travel',
            display_name='Travel & Tourism',
            pain_points=[
                'Online reputation and review management across booking platforms',
                'Customer experience optimization',
                'Review generation and management (TripAdvisor, Booking.com, etc.)',
                'Brand perception across multiple channels',
                'Customer feedback management at scale'
            ],
            common_roles=[
                'Travel Manager',
                'Operations Director',
                'Marketing Director',
                'Customer Experience Manager',
                'Business Owner',
                'Hotel Manager',
                'Tour Operator'
            ],
            challenges=[
                'Online reputation management across platforms',
                'Review generation and management',
                'Customer feedback management',
                'Brand consistency across booking channels',
                'Digital presence optimization'
            ],
            messaging_templates={
                'pain_point': 'Managing online reputation and customer reviews across multiple booking platforms',
                'pitch_angle': 'Automated reputation management and review generation for travel businesses',
                'solution_fit': 'Onlyne Reputation - Digital reputation management platform for travel'
            },
            solution_fit={
                'onlyne_reputation': 0.9,
                'the_ai_company': 0.5
            }
        ),
        'Logistics': IndustryContext(
            name='Logistics',
            display_name='Logistics & Supply Chain',
            pain_points=[
                'Operational efficiency and cost optimization',
                'Route optimization and delivery management',
                'Customer communication and tracking',
                'Process automation',
                'Real-time visibility and coordination'
            ],
            common_roles=[
                'Operations Director',
                'Logistics Manager',
                'Supply Chain Head',
                'Transportation Manager',
                'VP Operations',
                'Business Owner'
            ],
            challenges=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Real-time coordination',
                'Customer communication'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and cost optimization in logistics operations',
                'pitch_angle': 'AI-powered automation for logistics and supply chain operations',
                'solution_fit': 'The AI Company - GenAI automation platform for logistics'
            },
            solution_fit={
                'onlyne_reputation': 0.4,
                'the_ai_company': 0.85
            }
        ),
        'Hospitality': IndustryContext(
            name='Hospitality',
            display_name='Hospitality',
            pain_points=[
                'Online reputation and review management',
                'Customer experience optimization',
                'Review generation and management (Google, TripAdvisor, etc.)',
                'Guest feedback management',
                'Brand perception across platforms'
            ],
            common_roles=[
                'Hotel Manager',
                'Restaurant Owner',
                'Operations Director',
                'Customer Experience Manager',
                'Marketing Director',
                'Business Owner',
                'General Manager'
            ],
            challenges=[
                'Online reputation management',
                'Review generation across platforms',
                'Guest feedback management',
                'Brand consistency',
                'Customer experience optimization'
            ],
            messaging_templates={
                'pain_point': 'Managing online reputation and guest reviews across multiple platforms',
                'pitch_angle': 'Automated reputation management and review generation for hospitality businesses',
                'solution_fit': 'Onlyne Reputation - Digital reputation management platform for hospitality'
            },
            solution_fit={
                'onlyne_reputation': 0.9,
                'the_ai_company': 0.5
            }
        ),
        'Healthcare': IndustryContext(
            name='Healthcare',
            display_name='Healthcare',
            pain_points=[
                'Patient review and reputation management',
                'Regulatory compliance and documentation',
                'Patient experience optimization',
                'Online presence and brand management',
                'Operational efficiency and cost optimization'
            ],
            common_roles=[
                'Hospital Administrator',
                'Medical Director',
                'Operations Manager',
                'Marketing Director',
                'Patient Experience Manager',
                'CEO',
                'COO'
            ],
            challenges=[
                'Patient review management',
                'Regulatory compliance',
                'Patient experience',
                'Operational efficiency',
                'Digital transformation'
            ],
            messaging_templates={
                'pain_point': 'Managing patient reviews and reputation while ensuring regulatory compliance',
                'pitch_angle': 'AI-powered reputation management and operational automation for healthcare',
                'solution_fit': 'Both solutions relevant - reputation for patient reviews, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.8,
                'the_ai_company': 0.7
            }
        ),
        'Education': IndustryContext(
            name='Education',
            display_name='Education',
            pain_points=[
                'Student and parent review management',
                'Admissions and enrollment optimization',
                'Brand reputation across platforms',
                'Student feedback management',
                'Operational efficiency'
            ],
            common_roles=[
                'Principal',
                'Director',
                'Administrator',
                'Marketing Director',
                'Admissions Head',
                'Operations Manager',
                'CEO'
            ],
            challenges=[
                'Student review management',
                'Admissions optimization',
                'Brand reputation',
                'Student engagement',
                'Operational efficiency'
            ],
            messaging_templates={
                'pain_point': 'Managing student and parent reviews while optimizing admissions processes',
                'pitch_angle': 'AI-powered reputation management and automation for educational institutions',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for admissions'
            },
            solution_fit={
                'onlyne_reputation': 0.85,
                'the_ai_company': 0.6
            }
        ),
        'Real Estate': IndustryContext(
            name='Real Estate',
            display_name='Real Estate',
            pain_points=[
                'Property listing and review management',
                'Client communication and follow-up',
                'Online reputation across platforms',
                'Lead management and conversion',
                'Operational efficiency'
            ],
            common_roles=[
                'Real Estate Agent',
                'Broker',
                'Property Manager',
                'Sales Director',
                'Marketing Manager',
                'Business Owner',
                'Operations Manager'
            ],
            challenges=[
                'Property review management',
                'Client communication',
                'Lead generation',
                'Reputation management',
                'Process automation'
            ],
            messaging_templates={
                'pain_point': 'Managing property reviews and client communication at scale',
                'pitch_angle': 'AI-powered reputation management and automation for real estate businesses',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for lead management'
            },
            solution_fit={
                'onlyne_reputation': 0.85,
                'the_ai_company': 0.7
            }
        ),
        'Manufacturing': IndustryContext(
            name='Manufacturing',
            display_name='Manufacturing',
            pain_points=[
                'Operational efficiency and cost optimization',
                'Supply chain automation',
                'Quality control and compliance',
                'Process automation',
                'Resource optimization'
            ],
            common_roles=[
                'Operations Director',
                'Plant Manager',
                'Supply Chain Head',
                'VP Operations',
                'General Manager',
                'CEO',
                'COO'
            ],
            challenges=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Supply chain management',
                'Quality control'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and cost optimization in manufacturing operations',
                'pitch_angle': 'AI-powered automation for manufacturing and supply chain operations',
                'solution_fit': 'The AI Company - GenAI automation platform for manufacturing'
            },
            solution_fit={
                'onlyne_reputation': 0.4,
                'the_ai_company': 0.9
            }
        ),
        'Construction': IndustryContext(
            name='Construction',
            display_name='Construction',
            pain_points=[
                'Project management and coordination',
                'Operational efficiency',
                'Cost optimization',
                'Resource management',
                'Client communication'
            ],
            common_roles=[
                'Project Manager',
                'Operations Director',
                'General Manager',
                'Site Manager',
                'Business Owner',
                'CEO',
                'VP Operations'
            ],
            challenges=[
                'Project coordination',
                'Operational efficiency',
                'Cost management',
                'Resource optimization',
                'Process automation'
            ],
            messaging_templates={
                'pain_point': 'Project management and operational efficiency in construction',
                'pitch_angle': 'AI-powered automation for construction project management',
                'solution_fit': 'The AI Company - GenAI automation platform for construction'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.85
            }
        ),
        'Agriculture': IndustryContext(
            name='Agriculture',
            display_name='Agriculture',
            pain_points=[
                'Operational efficiency',
                'Supply chain management',
                'Resource optimization',
                'Process automation',
                'Cost management'
            ],
            common_roles=[
                'Farm Manager',
                'Operations Director',
                'Supply Chain Manager',
                'Business Owner',
                'General Manager',
                'CEO'
            ],
            challenges=[
                'Operational efficiency',
                'Supply chain optimization',
                'Resource management',
                'Process automation',
                'Cost optimization'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and supply chain management in agriculture',
                'pitch_angle': 'AI-powered automation for agricultural operations and supply chain',
                'solution_fit': 'The AI Company - GenAI automation platform for agriculture'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.85
            }
        ),
        'Consulting': IndustryContext(
            name='Consulting',
            display_name='Consulting',
            pain_points=[
                'Client acquisition and lead management',
                'Online reputation and thought leadership',
                'Client communication and follow-up',
                'Business development',
                'Operational efficiency'
            ],
            common_roles=[
                'Partner',
                'Managing Director',
                'Business Development Manager',
                'Marketing Director',
                'CEO',
                'Principal',
                'Director'
            ],
            challenges=[
                'Client acquisition',
                'Reputation management',
                'Lead generation',
                'Client communication',
                'Business development'
            ],
            messaging_templates={
                'pain_point': 'Client acquisition and reputation management for consulting firms',
                'pitch_angle': 'AI-powered reputation management and automation for consulting businesses',
                'solution_fit': 'Both solutions relevant - reputation for thought leadership, automation for lead management'
            },
            solution_fit={
                'onlyne_reputation': 0.75,
                'the_ai_company': 0.7
            }
        ),
        'Information Technology': IndustryContext(
            name='Information Technology',
            display_name='Information Technology & Services',
            pain_points=[
                'Digital reputation and review management',
                'Client acquisition and lead management',
                'Online presence and brand management',
                'Operational efficiency',
                'Client communication automation'
            ],
            common_roles=[
                'CTO',
                'VP Engineering',
                'Director',
                'Business Development Manager',
                'Marketing Director',
                'CEO',
                'Sales Director'
            ],
            challenges=[
                'Online reputation',
                'Client acquisition',
                'Lead generation',
                'Operational efficiency',
                'Client communication'
            ],
            messaging_templates={
                'pain_point': 'Digital reputation and client acquisition for IT services',
                'pitch_angle': 'AI-powered reputation management and automation for IT businesses',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.8,
                'the_ai_company': 0.75
            }
        ),
        'Machinery': IndustryContext(
            name='Machinery',
            display_name='Machinery',
            pain_points=[
                'Operational efficiency',
                'Supply chain management',
                'Cost optimization',
                'Process automation',
                'Resource management'
            ],
            common_roles=[
                'Operations Director',
                'Plant Manager',
                'General Manager',
                'VP Operations',
                'CEO',
                'COO',
                'Supply Chain Manager'
            ],
            challenges=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Supply chain management',
                'Resource optimization'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and cost optimization in machinery operations',
                'pitch_angle': 'AI-powered automation for machinery and manufacturing operations',
                'solution_fit': 'The AI Company - GenAI automation platform for machinery'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.9
            }
        ),
        'Restaurants': IndustryContext(
            name='Restaurants',
            display_name='Restaurants',
            pain_points=[
                'Online reputation and review management',
                'Customer experience optimization',
                'Review generation (Google, Zomato, etc.)',
                'Guest feedback management',
                'Operational efficiency'
            ],
            common_roles=[
                'Restaurant Owner',
                'General Manager',
                'Operations Manager',
                'Marketing Manager',
                'Chef',
                'Business Owner',
                'Franchise Owner'
            ],
            challenges=[
                'Online reputation management',
                'Review generation',
                'Customer experience',
                'Operational efficiency',
                'Cost management'
            ],
            messaging_templates={
                'pain_point': 'Managing online reputation and customer reviews across multiple platforms',
                'pitch_angle': 'AI-powered reputation management and automation for restaurants',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.9,
                'the_ai_company': 0.6
            }
        ),
        'E-commerce': IndustryContext(
            name='E-commerce',
            display_name='E-commerce',
            pain_points=[
                'Online reputation and review management',
                'Customer experience optimization',
                'Review generation across platforms',
                'Operational efficiency',
                'Customer communication'
            ],
            common_roles=[
                'CEO',
                'Operations Director',
                'Marketing Director',
                'Customer Experience Manager',
                'E-commerce Manager',
                'Business Owner',
                'VP Operations'
            ],
            challenges=[
                'Online reputation',
                'Review management',
                'Customer experience',
                'Operational efficiency',
                'Customer communication'
            ],
            messaging_templates={
                'pain_point': 'Managing online reputation and customer reviews for e-commerce businesses',
                'pitch_angle': 'AI-powered reputation management and automation for e-commerce',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.9,
                'the_ai_company': 0.7
            }
        ),
        'Financial Services': IndustryContext(
            name='Financial Services',
            display_name='Financial Services',
            pain_points=[
                'Client acquisition and lead management',
                'Regulatory compliance',
                'Online reputation management',
                'Operational efficiency',
                'Client communication'
            ],
            common_roles=[
                'Managing Director',
                'VP',
                'Director',
                'Business Development Manager',
                'Operations Manager',
                'CEO',
                'COO'
            ],
            challenges=[
                'Client acquisition',
                'Regulatory compliance',
                'Reputation management',
                'Operational efficiency',
                'Client communication'
            ],
            messaging_templates={
                'pain_point': 'Client acquisition and reputation management while ensuring compliance',
                'pitch_angle': 'AI-powered reputation management and automation for financial services',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for compliance'
            },
            solution_fit={
                'onlyne_reputation': 0.7,
                'the_ai_company': 0.8
            }
        ),
        'Automotive': IndustryContext(
            name='Automotive',
            display_name='Automotive',
            pain_points=[
                'Operational efficiency',
                'Supply chain management',
                'Cost optimization',
                'Process automation',
                'Customer service'
            ],
            common_roles=[
                'Operations Director',
                'General Manager',
                'VP Operations',
                'Plant Manager',
                'CEO',
                'COO',
                'Supply Chain Manager'
            ],
            challenges=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Supply chain management',
                'Resource optimization'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and cost optimization in automotive operations',
                'pitch_angle': 'AI-powered automation for automotive manufacturing and operations',
                'solution_fit': 'The AI Company - GenAI automation platform for automotive'
            },
            solution_fit={
                'onlyne_reputation': 0.4,
                'the_ai_company': 0.85
            }
        ),
        'Pharmaceuticals': IndustryContext(
            name='Pharmaceuticals',
            display_name='Pharmaceuticals',
            pain_points=[
                'Regulatory compliance and documentation',
                'Operational efficiency',
                'Supply chain management',
                'Process automation',
                'Quality control'
            ],
            common_roles=[
                'Operations Director',
                'Regulatory Affairs Manager',
                'VP Operations',
                'General Manager',
                'CEO',
                'COO',
                'Quality Manager'
            ],
            challenges=[
                'Regulatory compliance',
                'Operational efficiency',
                'Process automation',
                'Supply chain management',
                'Quality control'
            ],
            messaging_templates={
                'pain_point': 'Regulatory compliance and operational efficiency in pharmaceutical operations',
                'pitch_angle': 'AI-powered automation for pharmaceutical operations and compliance',
                'solution_fit': 'The AI Company - GenAI automation platform for pharmaceuticals'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.9
            }
        ),
        'Energy': IndustryContext(
            name='Energy',
            display_name='Energy',
            pain_points=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Resource management',
                'Compliance and reporting'
            ],
            common_roles=[
                'Operations Director',
                'Plant Manager',
                'VP Operations',
                'General Manager',
                'CEO',
                'COO',
                'Energy Manager'
            ],
            challenges=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Resource management',
                'Compliance'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and cost optimization in energy operations',
                'pitch_angle': 'AI-powered automation for energy operations and resource management',
                'solution_fit': 'The AI Company - GenAI automation platform for energy'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.85
            }
        ),
        'Telecommunications': IndustryContext(
            name='Telecommunications',
            display_name='Telecommunications',
            pain_points=[
                'Customer service and support',
                'Operational efficiency',
                'Online reputation management',
                'Process automation',
                'Cost optimization'
            ],
            common_roles=[
                'Operations Director',
                'Customer Service Manager',
                'VP Operations',
                'General Manager',
                'CEO',
                'COO',
                'Service Delivery Manager'
            ],
            challenges=[
                'Customer service',
                'Operational efficiency',
                'Reputation management',
                'Process automation',
                'Cost optimization'
            ],
            messaging_templates={
                'pain_point': 'Customer service and operational efficiency in telecommunications',
                'pitch_angle': 'AI-powered reputation management and automation for telecommunications',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.7,
                'the_ai_company': 0.8
            }
        ),
        'Media & Entertainment': IndustryContext(
            name='Media & Entertainment',
            display_name='Media & Entertainment',
            pain_points=[
                'Online reputation and brand management',
                'Content distribution and management',
                'Audience engagement',
                'Operational efficiency',
                'Digital presence optimization'
            ],
            common_roles=[
                'CEO',
                'Marketing Director',
                'Content Director',
                'Operations Manager',
                'Business Development Manager',
                'General Manager',
                'VP'
            ],
            challenges=[
                'Reputation management',
                'Content management',
                'Audience engagement',
                'Operational efficiency',
                'Digital presence'
            ],
            messaging_templates={
                'pain_point': 'Online reputation and brand management for media and entertainment',
                'pitch_angle': 'AI-powered reputation management and automation for media businesses',
                'solution_fit': 'Both solutions relevant - reputation for brand, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.85,
                'the_ai_company': 0.6
            }
        ),
        'Professional Services': IndustryContext(
            name='Professional Services',
            display_name='Professional Services',
            pain_points=[
                'Client acquisition and lead management',
                'Online reputation and thought leadership',
                'Client communication',
                'Operational efficiency',
                'Business development'
            ],
            common_roles=[
                'Partner',
                'Managing Director',
                'Business Development Manager',
                'Marketing Director',
                'CEO',
                'Principal',
                'Director'
            ],
            challenges=[
                'Client acquisition',
                'Reputation management',
                'Lead generation',
                'Client communication',
                'Operational efficiency'
            ],
            messaging_templates={
                'pain_point': 'Client acquisition and reputation management for professional services',
                'pitch_angle': 'AI-powered reputation management and automation for professional services',
                'solution_fit': 'Both solutions relevant - reputation for thought leadership, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.75,
                'the_ai_company': 0.7
            }
        ),
        'Healthcare': IndustryContext(
            name='Healthcare',
            display_name='Healthcare',
            pain_points=[
                'Patient review and reputation management',
                'Regulatory compliance and documentation',
                'Patient experience optimization',
                'Online presence and brand management',
                'Operational efficiency and cost optimization'
            ],
            common_roles=[
                'Hospital Administrator',
                'Medical Director',
                'Operations Manager',
                'Marketing Director',
                'Patient Experience Manager',
                'CEO',
                'COO'
            ],
            challenges=[
                'Patient review management',
                'Regulatory compliance',
                'Patient experience',
                'Operational efficiency',
                'Digital transformation'
            ],
            messaging_templates={
                'pain_point': 'Managing patient reviews and reputation while ensuring regulatory compliance',
                'pitch_angle': 'AI-powered reputation management and operational automation for healthcare',
                'solution_fit': 'Both solutions relevant - reputation for patient reviews, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.8,
                'the_ai_company': 0.7
            }
        ),
        'Education': IndustryContext(
            name='Education',
            display_name='Education',
            pain_points=[
                'Student and parent review management',
                'Admissions and enrollment optimization',
                'Brand reputation across platforms',
                'Student feedback management',
                'Operational efficiency'
            ],
            common_roles=[
                'Principal',
                'Director',
                'Administrator',
                'Marketing Director',
                'Admissions Head',
                'Operations Manager',
                'CEO'
            ],
            challenges=[
                'Student review management',
                'Admissions optimization',
                'Brand reputation',
                'Student engagement',
                'Operational efficiency'
            ],
            messaging_templates={
                'pain_point': 'Managing student and parent reviews while optimizing admissions processes',
                'pitch_angle': 'AI-powered reputation management and automation for educational institutions',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for admissions'
            },
            solution_fit={
                'onlyne_reputation': 0.85,
                'the_ai_company': 0.6
            }
        ),
        'Real Estate': IndustryContext(
            name='Real Estate',
            display_name='Real Estate',
            pain_points=[
                'Property listing and review management',
                'Client communication and follow-up',
                'Online reputation across platforms',
                'Lead management and conversion',
                'Operational efficiency'
            ],
            common_roles=[
                'Real Estate Agent',
                'Broker',
                'Property Manager',
                'Sales Director',
                'Marketing Manager',
                'Business Owner',
                'Operations Manager'
            ],
            challenges=[
                'Property review management',
                'Client communication',
                'Lead generation',
                'Reputation management',
                'Process automation'
            ],
            messaging_templates={
                'pain_point': 'Managing property reviews and client communication at scale',
                'pitch_angle': 'AI-powered reputation management and automation for real estate businesses',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for lead management'
            },
            solution_fit={
                'onlyne_reputation': 0.85,
                'the_ai_company': 0.7
            }
        ),
        'Manufacturing': IndustryContext(
            name='Manufacturing',
            display_name='Manufacturing',
            pain_points=[
                'Operational efficiency and cost optimization',
                'Supply chain automation',
                'Quality control and compliance',
                'Process automation',
                'Resource optimization'
            ],
            common_roles=[
                'Operations Director',
                'Plant Manager',
                'Supply Chain Head',
                'VP Operations',
                'General Manager',
                'CEO',
                'COO'
            ],
            challenges=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Supply chain management',
                'Quality control'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and cost optimization in manufacturing operations',
                'pitch_angle': 'AI-powered automation for manufacturing and supply chain operations',
                'solution_fit': 'The AI Company - GenAI automation platform for manufacturing'
            },
            solution_fit={
                'onlyne_reputation': 0.4,
                'the_ai_company': 0.9
            }
        ),
        'Construction': IndustryContext(
            name='Construction',
            display_name='Construction',
            pain_points=[
                'Project management and coordination',
                'Operational efficiency',
                'Cost optimization',
                'Resource management',
                'Client communication'
            ],
            common_roles=[
                'Project Manager',
                'Operations Director',
                'General Manager',
                'Site Manager',
                'Business Owner',
                'CEO',
                'VP Operations'
            ],
            challenges=[
                'Project coordination',
                'Operational efficiency',
                'Cost management',
                'Resource optimization',
                'Process automation'
            ],
            messaging_templates={
                'pain_point': 'Project management and operational efficiency in construction',
                'pitch_angle': 'AI-powered automation for construction project management',
                'solution_fit': 'The AI Company - GenAI automation platform for construction'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.85
            }
        ),
        'Agriculture': IndustryContext(
            name='Agriculture',
            display_name='Agriculture',
            pain_points=[
                'Operational efficiency',
                'Supply chain management',
                'Resource optimization',
                'Process automation',
                'Cost management'
            ],
            common_roles=[
                'Farm Manager',
                'Operations Director',
                'Supply Chain Manager',
                'Business Owner',
                'General Manager',
                'CEO'
            ],
            challenges=[
                'Operational efficiency',
                'Supply chain optimization',
                'Resource management',
                'Process automation',
                'Cost optimization'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and supply chain management in agriculture',
                'pitch_angle': 'AI-powered automation for agricultural operations and supply chain',
                'solution_fit': 'The AI Company - GenAI automation platform for agriculture'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.85
            }
        ),
        'Consulting': IndustryContext(
            name='Consulting',
            display_name='Consulting',
            pain_points=[
                'Client acquisition and lead management',
                'Online reputation and thought leadership',
                'Client communication and follow-up',
                'Business development',
                'Operational efficiency'
            ],
            common_roles=[
                'Partner',
                'Managing Director',
                'Business Development Manager',
                'Marketing Director',
                'CEO',
                'Principal',
                'Director'
            ],
            challenges=[
                'Client acquisition',
                'Reputation management',
                'Lead generation',
                'Client communication',
                'Business development'
            ],
            messaging_templates={
                'pain_point': 'Client acquisition and reputation management for consulting firms',
                'pitch_angle': 'AI-powered reputation management and automation for consulting businesses',
                'solution_fit': 'Both solutions relevant - reputation for thought leadership, automation for lead management'
            },
            solution_fit={
                'onlyne_reputation': 0.75,
                'the_ai_company': 0.7
            }
        ),
        'Information Technology': IndustryContext(
            name='Information Technology',
            display_name='Information Technology & Services',
            pain_points=[
                'Digital reputation and review management',
                'Client acquisition and lead management',
                'Online presence and brand management',
                'Operational efficiency',
                'Client communication automation'
            ],
            common_roles=[
                'CTO',
                'VP Engineering',
                'Director',
                'Business Development Manager',
                'Marketing Director',
                'CEO',
                'Sales Director'
            ],
            challenges=[
                'Online reputation',
                'Client acquisition',
                'Lead generation',
                'Operational efficiency',
                'Client communication'
            ],
            messaging_templates={
                'pain_point': 'Digital reputation and client acquisition for IT services',
                'pitch_angle': 'AI-powered reputation management and automation for IT businesses',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.8,
                'the_ai_company': 0.75
            }
        ),
        'Machinery': IndustryContext(
            name='Machinery',
            display_name='Machinery',
            pain_points=[
                'Operational efficiency',
                'Supply chain management',
                'Cost optimization',
                'Process automation',
                'Resource management'
            ],
            common_roles=[
                'Operations Director',
                'Plant Manager',
                'General Manager',
                'VP Operations',
                'CEO',
                'COO',
                'Supply Chain Manager'
            ],
            challenges=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Supply chain management',
                'Resource optimization'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and cost optimization in machinery operations',
                'pitch_angle': 'AI-powered automation for machinery and manufacturing operations',
                'solution_fit': 'The AI Company - GenAI automation platform for machinery'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.9
            }
        ),
        'Restaurants': IndustryContext(
            name='Restaurants',
            display_name='Restaurants',
            pain_points=[
                'Online reputation and review management',
                'Customer experience optimization',
                'Review generation (Google, Zomato, etc.)',
                'Guest feedback management',
                'Operational efficiency'
            ],
            common_roles=[
                'Restaurant Owner',
                'General Manager',
                'Operations Manager',
                'Marketing Manager',
                'Chef',
                'Business Owner',
                'Franchise Owner'
            ],
            challenges=[
                'Online reputation management',
                'Review generation',
                'Customer experience',
                'Operational efficiency',
                'Cost management'
            ],
            messaging_templates={
                'pain_point': 'Managing online reputation and customer reviews across multiple platforms',
                'pitch_angle': 'AI-powered reputation management and automation for restaurants',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.9,
                'the_ai_company': 0.6
            }
        ),
        'E-commerce': IndustryContext(
            name='E-commerce',
            display_name='E-commerce',
            pain_points=[
                'Online reputation and review management',
                'Customer experience optimization',
                'Review generation across platforms',
                'Operational efficiency',
                'Customer communication'
            ],
            common_roles=[
                'CEO',
                'Operations Director',
                'Marketing Director',
                'Customer Experience Manager',
                'E-commerce Manager',
                'Business Owner',
                'VP Operations'
            ],
            challenges=[
                'Online reputation',
                'Review management',
                'Customer experience',
                'Operational efficiency',
                'Customer communication'
            ],
            messaging_templates={
                'pain_point': 'Managing online reputation and customer reviews for e-commerce businesses',
                'pitch_angle': 'AI-powered reputation management and automation for e-commerce',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.9,
                'the_ai_company': 0.7
            }
        ),
        'Financial Services': IndustryContext(
            name='Financial Services',
            display_name='Financial Services',
            pain_points=[
                'Client acquisition and lead management',
                'Regulatory compliance',
                'Online reputation management',
                'Operational efficiency',
                'Client communication'
            ],
            common_roles=[
                'Managing Director',
                'VP',
                'Director',
                'Business Development Manager',
                'Operations Manager',
                'CEO',
                'COO'
            ],
            challenges=[
                'Client acquisition',
                'Regulatory compliance',
                'Reputation management',
                'Operational efficiency',
                'Client communication'
            ],
            messaging_templates={
                'pain_point': 'Client acquisition and reputation management while ensuring compliance',
                'pitch_angle': 'AI-powered reputation management and automation for financial services',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for compliance'
            },
            solution_fit={
                'onlyne_reputation': 0.7,
                'the_ai_company': 0.8
            }
        ),
        'Automotive': IndustryContext(
            name='Automotive',
            display_name='Automotive',
            pain_points=[
                'Operational efficiency',
                'Supply chain management',
                'Cost optimization',
                'Process automation',
                'Customer service'
            ],
            common_roles=[
                'Operations Director',
                'General Manager',
                'VP Operations',
                'Plant Manager',
                'CEO',
                'COO',
                'Supply Chain Manager'
            ],
            challenges=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Supply chain management',
                'Resource optimization'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and cost optimization in automotive operations',
                'pitch_angle': 'AI-powered automation for automotive manufacturing and operations',
                'solution_fit': 'The AI Company - GenAI automation platform for automotive'
            },
            solution_fit={
                'onlyne_reputation': 0.4,
                'the_ai_company': 0.85
            }
        ),
        'Pharmaceuticals': IndustryContext(
            name='Pharmaceuticals',
            display_name='Pharmaceuticals',
            pain_points=[
                'Regulatory compliance and documentation',
                'Operational efficiency',
                'Supply chain management',
                'Process automation',
                'Quality control'
            ],
            common_roles=[
                'Operations Director',
                'Regulatory Affairs Manager',
                'VP Operations',
                'General Manager',
                'CEO',
                'COO',
                'Quality Manager'
            ],
            challenges=[
                'Regulatory compliance',
                'Operational efficiency',
                'Process automation',
                'Supply chain management',
                'Quality control'
            ],
            messaging_templates={
                'pain_point': 'Regulatory compliance and operational efficiency in pharmaceutical operations',
                'pitch_angle': 'AI-powered automation for pharmaceutical operations and compliance',
                'solution_fit': 'The AI Company - GenAI automation platform for pharmaceuticals'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.9
            }
        ),
        'Energy': IndustryContext(
            name='Energy',
            display_name='Energy',
            pain_points=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Resource management',
                'Compliance and reporting'
            ],
            common_roles=[
                'Operations Director',
                'Plant Manager',
                'VP Operations',
                'General Manager',
                'CEO',
                'COO',
                'Energy Manager'
            ],
            challenges=[
                'Operational efficiency',
                'Cost optimization',
                'Process automation',
                'Resource management',
                'Compliance'
            ],
            messaging_templates={
                'pain_point': 'Operational efficiency and cost optimization in energy operations',
                'pitch_angle': 'AI-powered automation for energy operations and resource management',
                'solution_fit': 'The AI Company - GenAI automation platform for energy'
            },
            solution_fit={
                'onlyne_reputation': 0.3,
                'the_ai_company': 0.85
            }
        ),
        'Telecommunications': IndustryContext(
            name='Telecommunications',
            display_name='Telecommunications',
            pain_points=[
                'Customer service and support',
                'Operational efficiency',
                'Online reputation management',
                'Process automation',
                'Cost optimization'
            ],
            common_roles=[
                'Operations Director',
                'Customer Service Manager',
                'VP Operations',
                'General Manager',
                'CEO',
                'COO',
                'Service Delivery Manager'
            ],
            challenges=[
                'Customer service',
                'Operational efficiency',
                'Reputation management',
                'Process automation',
                'Cost optimization'
            ],
            messaging_templates={
                'pain_point': 'Customer service and operational efficiency in telecommunications',
                'pitch_angle': 'AI-powered reputation management and automation for telecommunications',
                'solution_fit': 'Both solutions relevant - reputation for reviews, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.7,
                'the_ai_company': 0.8
            }
        ),
        'Media & Entertainment': IndustryContext(
            name='Media & Entertainment',
            display_name='Media & Entertainment',
            pain_points=[
                'Online reputation and brand management',
                'Content distribution and management',
                'Audience engagement',
                'Operational efficiency',
                'Digital presence optimization'
            ],
            common_roles=[
                'CEO',
                'Marketing Director',
                'Content Director',
                'Operations Manager',
                'Business Development Manager',
                'General Manager',
                'VP'
            ],
            challenges=[
                'Reputation management',
                'Content management',
                'Audience engagement',
                'Operational efficiency',
                'Digital presence'
            ],
            messaging_templates={
                'pain_point': 'Online reputation and brand management for media and entertainment',
                'pitch_angle': 'AI-powered reputation management and automation for media businesses',
                'solution_fit': 'Both solutions relevant - reputation for brand, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.85,
                'the_ai_company': 0.6
            }
        ),
        'Professional Services': IndustryContext(
            name='Professional Services',
            display_name='Professional Services',
            pain_points=[
                'Client acquisition and lead management',
                'Online reputation and thought leadership',
                'Client communication',
                'Operational efficiency',
                'Business development'
            ],
            common_roles=[
                'Partner',
                'Managing Director',
                'Business Development Manager',
                'Marketing Director',
                'CEO',
                'Principal',
                'Director'
            ],
            challenges=[
                'Client acquisition',
                'Reputation management',
                'Lead generation',
                'Client communication',
                'Operational efficiency'
            ],
            messaging_templates={
                'pain_point': 'Client acquisition and reputation management for professional services',
                'pitch_angle': 'AI-powered reputation management and automation for professional services',
                'solution_fit': 'Both solutions relevant - reputation for thought leadership, automation for operations'
            },
            solution_fit={
                'onlyne_reputation': 0.75,
                'the_ai_company': 0.7
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












