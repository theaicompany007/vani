"""OpenAI integration for message generation with RAG and Gemini"""
import os
import logging
from typing import Optional, Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client for generating outreach messages with industry context"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        # Initialize RAG and Gemini clients (optional)
        try:
            from app.integrations.rag_client import get_rag_client
            from app.integrations.gemini_client import get_gemini_client
            from app.services.industry_context import get_industry_context
            self.rag_client = get_rag_client()
            self.gemini_client = get_gemini_client()
            # Store function reference, don't call it yet - it requires industry_name argument
            self.get_industry_context = get_industry_context
        except ImportError as e:
            logger.warning(f"RAG/Gemini clients not available. Message generation will use OpenAI only. Error: {e}")
            self.rag_client = None
            self.gemini_client = None
            self.get_industry_context = None
        except Exception as e:
            logger.warning(f"Error initializing RAG/Gemini clients: {e}. Message generation will use OpenAI only.")
            self.rag_client = None
            self.gemini_client = None
            self.get_industry_context = None
    
    def generate_outreach_message(
        self,
        target_name: str,
        contact_name: str,
        role: str,
        company_name: str,
        pain_point: str,
        pitch_angle: str,
        channel: str = 'email',
        base_script: Optional[str] = None,
        industry_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate personalized outreach message using OpenAI
        
        Args:
            target_name: Contact person name
            contact_name: Full contact name
            role: Contact's role/title
            company_name: Company name
            pain_point: Their pain point
            pitch_angle: Our pitch angle
            channel: 'email' or 'whatsapp'
            base_script: Optional base script to refine
            
        Returns:
            Dict with generated message and metadata
        """
        try:
            # Gather industry context if available
            industry_config = {}
            rag_insights = ""
            gemini_insights = ""
            
            if industry_name and self.get_industry_context:
                try:
                    industry_context_obj = self.get_industry_context(industry_name)
                    if industry_context_obj:
                        # Convert IndustryContext dataclass to dict for easier access
                        industry_config = {
                            'pain_points': getattr(industry_context_obj, 'pain_points', []),
                            'pitch_angles': [industry_context_obj.messaging_templates.get('pitch_angle', '')] if hasattr(industry_context_obj, 'messaging_templates') else [],
                            'common_roles': getattr(industry_context_obj, 'common_roles', []),
                            'challenges': getattr(industry_context_obj, 'challenges', []),
                            'messaging_templates': getattr(industry_context_obj, 'messaging_templates', {})
                        }
                except Exception as e:
                    logger.warning(f"Failed to get industry context for {industry_name}: {e}")
                    industry_config = {}
            
            # Query RAG for industry-specific messaging insights
            if industry_name and self.rag_client and self.rag_client.enabled:
                try:
                    rag_query = f"What are effective messaging strategies and pain points for {company_name} in the {industry_name} sector? Focus on sales and distribution challenges."
                    rag_response = self.rag_client.query(rag_query, industry=industry_name, top_k=2)
                    if rag_response.get('success') and rag_response.get('data'):
                        rag_results = rag_response['data'].get('results', [])
                        rag_insights = "\n".join([r.get('content', '') for r in rag_results[:2]])
                except Exception as e:
                    logger.warning(f"RAG query failed: {e}")
            
            # Query Gemini for customer-specific content
            if industry_name and self.gemini_client and self.gemini_client.enabled:
                try:
                    known_customers = ["Royal Enfield", "IndiGo Airlines", "ITQ Technologies", "EaseMyTrip"]
                    if any(customer.lower() in company_name.lower() for customer in known_customers):
                        gemini_query = f"Retrieve messaging insights and communication preferences for {company_name} in {industry_name}."
                        gemini_response = self.gemini_client.get_notebook_lm_content(gemini_query, company_name)
                        if gemini_response.get('success'):
                            gemini_insights = gemini_response.get('content', '')
                except Exception as e:
                    logger.warning(f"Gemini query failed: {e}")
            
            # Build system message with industry context
            system_content = "You are an expert B2B sales outreach writer specializing in personalized messages that address specific pain points and create urgency."
            if industry_name and industry_config:
                system_content += f" The target operates in the {industry_name} industry. "
                if industry_config.get('pain_points'):
                    system_content += f"Common industry pain points include: {', '.join(industry_config['pain_points'][:3])}. "
            
            # Build prompt based on channel
            if channel == 'email':
                prompt = self._build_email_prompt(
                    target_name, contact_name, role, company_name,
                    pain_point, pitch_angle, base_script, industry_name,
                    rag_insights, gemini_insights
                )
            else:  # whatsapp
                prompt = self._build_whatsapp_prompt(
                    target_name, contact_name, role, company_name,
                    pain_point, pitch_angle, base_script, industry_name,
                    rag_insights, gemini_insights
                )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            generated_message = response.choices[0].message.content.strip()
            
            # Extract subject if email
            subject = None
            if channel == 'email':
                # Try to extract subject from message or generate one
                subject_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Generate a compelling email subject line (max 60 characters) for the following outreach message."
                        },
                        {
                            "role": "user",
                            "content": f"Message: {generated_message}"
                        }
                    ],
                    temperature=0.5,
                    max_tokens=20
                )
                subject = subject_response.choices[0].message.content.strip()
            
            logger.info(f"Generated {channel} message for {contact_name} at {company_name}")
            
            return {
                'success': True,
                'message': generated_message,
                'subject': subject,
                'model': self.model,
                'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else None
            }
            
        except Exception as e:
            logger.error(f"Failed to generate message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_email_prompt(
        self,
        target_name: str,
        contact_name: str,
        role: str,
        company_name: str,
        pain_point: str,
        pitch_angle: str,
        base_script: Optional[str],
        industry_name: Optional[str] = None,
        rag_insights: str = "",
        gemini_insights: str = ""
    ) -> str:
        """Build prompt for email generation with industry context"""
        prompt = f"""Generate a professional, personalized email outreach message with the following details:

Contact: {contact_name} ({role}) at {company_name}
Pain Point: {pain_point}
Our Pitch Angle: {pitch_angle}
"""
        
        if industry_name:
            prompt += f"Industry: {industry_name}\n"
        
        prompt += """
Requirements:
- Keep it concise (150-200 words)
- Address their specific pain point
- Include our pitch angle naturally
- Professional but conversational tone
- Include a clear call-to-action
- Personalize with their name and role
"""
        
        if rag_insights:
            prompt += f"\nIndustry Knowledge Base Insights:\n{rag_insights}\n\nUse these insights to make the message more relevant.\n"
        
        if gemini_insights:
            prompt += f"\nCustomer-Specific Insights:\n{gemini_insights}\n\nIncorporate these insights to personalize further.\n"
        
        if base_script:
            prompt += f"\nBase script to refine:\n{base_script}\n\nUse this as inspiration but make it more personalized and compelling.\n"
        
        prompt += "\nGenerate the email body only (no subject line, no greetings/signatures - just the message content)."
        
        return prompt
    
    def _build_whatsapp_prompt(
        self,
        target_name: str,
        contact_name: str,
        role: str,
        company_name: str,
        pain_point: str,
        pitch_angle: str,
        base_script: Optional[str],
        industry_name: Optional[str] = None,
        rag_insights: str = "",
        gemini_insights: str = ""
    ) -> str:
        """Build prompt for WhatsApp message generation with industry context"""
        prompt = f"""Generate a concise WhatsApp message for outreach with the following details:

Contact: {contact_name} ({role}) at {company_name}
Pain Point: {pain_point}
Our Pitch Angle: {pitch_angle}
"""
        
        if industry_name:
            prompt += f"Industry: {industry_name}\n"
        
        prompt += """
Requirements:
- Keep it very concise (100-150 words)
- WhatsApp-friendly format (can use line breaks)
- Address their specific pain point
- Include our pitch angle
- Conversational, friendly tone
- Include a clear call-to-action
- Personalize with their name
"""
        
        if rag_insights:
            prompt += f"\nIndustry Knowledge Base Insights:\n{rag_insights}\n\nUse these insights to make the message more relevant.\n"
        
        if gemini_insights:
            prompt += f"\nCustomer-Specific Insights:\n{gemini_insights}\n\nIncorporate these insights to personalize further.\n"
        
        if base_script:
            prompt += f"\nBase script to refine:\n{base_script}\n\nUse this as inspiration but make it more personalized and WhatsApp-appropriate.\n"
        
        prompt += "\nGenerate the WhatsApp message only (no greetings/signatures - just the message content)."
        
        return prompt

