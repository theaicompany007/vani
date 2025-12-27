"""Pitch generation using OpenAI with RAG and Gemini integration"""
import os
import logging
import json
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class PitchGenerator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        # Initialize RAG and Gemini clients (optional)
        try:
            from app.integrations.rag_client import get_rag_client
            from app.integrations.gemini_client import get_gemini_client
            from app.services.industry_context import get_industry_context
            from app.services.industry_persona_mapping import IndustryPersonaMapping
            self.rag_client = get_rag_client()
            self.gemini_client = get_gemini_client()
            self.get_industry_context = get_industry_context  # Store function reference, don't call it yet
            self.persona_mapping = IndustryPersonaMapping
        except ImportError:
            logger.warning("RAG/Gemini clients not available. Pitch generation will use OpenAI only.")
            self.rag_client = None
            self.gemini_client = None
            self.get_industry_context = None
            self.persona_mapping = None

    def generate_pitch(self, target_data: Dict[str, Any], industry_name: str) -> Dict[str, Any]:
        """
        Generates a structured pitch based on target and industry data.
        Enhanced with RAG and Gemini for industry-specific insights.
        """
        company_name = target_data.get('company_name', 'Unknown Company')
        contact_name = target_data.get('contact_name', 'Valued Contact')
        role = target_data.get('role', 'Decision Maker')
        pain_point = target_data.get('pain_point', 'general distribution challenges')
        pitch_angle = target_data.get('pitch_angle', 'improve last-mile reach')
        
        # Gather industry context and persona mapping
        industry_config = {}
        persona_context = None
        rag_insights = ""
        gemini_insights = ""
        
        # Get VANI Persona for this industry
        if self.persona_mapping and industry_name:
            try:
                persona_context = self.persona_mapping.get_industry_context(industry_name)
                if persona_context:
                    logger.info(f"Using VANI Persona: {persona_context.vani_persona} for industry: {industry_name}")
            except Exception as e:
                logger.warning(f"Failed to get persona context for {industry_name}: {e}")
        
        # Get traditional industry context (for backward compatibility)
        if self.get_industry_context and industry_name:
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
                import traceback
                logger.warning(traceback.format_exc())
                industry_config = {}
        
        # Merge persona context pain points with industry config
        if persona_context:
            # Use persona pain points if available, otherwise fall back to industry config
            persona_pain_points = persona_context.pain_points if persona_context.pain_points else []
            if persona_pain_points:
                industry_config['pain_points'] = persona_pain_points
                industry_config['persona'] = persona_context.vani_persona
                industry_config['persona_description'] = persona_context.persona_description
                industry_config['use_case_examples'] = persona_context.use_case_examples
                industry_config['value_proposition_template'] = persona_context.value_proposition_template
        
        # Query RAG for industry-specific case studies and solutions
        if self.rag_client and self.rag_client.enabled:
            try:
                # Enhanced query with explicit industry context
                rag_query = f"What are successful case studies, solutions, and pain points for {company_name} in the {industry_name} sector? Focus on distribution, sales, and digital transformation challenges specific to {industry_name} industry."
                # Always pass industry to RAG queries for proper filtering
                rag_response = self.rag_client.query(rag_query, industry=industry_name, top_k=5)
                logger.info(f"RAG query for {company_name} in {industry_name}: {rag_response.get('total_results', 0)} results")
                if rag_response.get('success') and rag_response.get('data'):
                    rag_results = rag_response['data'].get('results', [])
                    rag_insights = "\n".join([r.get('content', '') for r in rag_results[:3]])
                    logger.info(f"Retrieved {len(rag_results)} RAG insights for {company_name}")
            except Exception as e:
                logger.warning(f"RAG query failed: {e}")
        
        # Query Gemini for customer-specific content (if applicable)
        if self.gemini_client and self.gemini_client.enabled:
            try:
                # Check if this is a known customer
                known_customers = ["Royal Enfield", "IndiGo Airlines", "ITQ Technologies", "EaseMyTrip"]
                if any(customer.lower() in company_name.lower() for customer in known_customers):
                    gemini_query = f"Retrieve relevant customer content and insights for {company_name} related to sales, distribution, and digital transformation challenges in {industry_name}."
                    gemini_response = self.gemini_client.get_notebook_lm_content(gemini_query, company_name)
                    if gemini_response.get('success'):
                        gemini_insights = gemini_response.get('content', '')
                        logger.info(f"Retrieved Gemini insights for {company_name}")
            except Exception as e:
                logger.warning(f"Gemini query failed: {e}")
        
        # Build enhanced system prompt with industry context and persona
        industry_pain_points = industry_config.get('pain_points', [])
        industry_pitch_angles = industry_config.get('pitch_angles', [])
        vani_persona = industry_config.get('persona', 'AI Sales Assistant')
        persona_description = industry_config.get('persona_description', 'AI-powered sales automation')
        use_case_examples = industry_config.get('use_case_examples', [])
        value_prop_template = industry_config.get('value_proposition_template', 'AI-powered automation for operational efficiency')
        
        system_prompt = f"""
        You are an expert sales strategist for "Project VANI" (Virtual Agent Network Interface), an Agentic AI Voice Sales Officer.
        Your goal is to generate a compelling, industry-specific pitch for a B2B client.
        The pitch should be structured into:
        - title: A catchy, benefit-driven title that includes the VANI Persona name: "{vani_persona}".
        - problem: A concise description of the market reality and the client's pain point, specific to the {industry_name} industry.
        - solution: How VANI solves this problem using the "{vani_persona}" persona. Emphasize "Don't App. Just Call." where relevant.
        - hit_list: A specific, customized "Hit List" card for the target company, highlighting their pain and VANI's pitch. Format as readable text, NOT JSON. Use clear, engaging language.
        - trojan_horse: Explain the low-risk pilot approach (e.g., "Give us 5,000 'Dead Stores'" for distribution, or similar industry-appropriate pilot).

        The client operates in the {industry_name} industry.
        
        VANI Persona: {vani_persona}
        Persona Description: {persona_description}
        
        Industry Context:
        - Common pain points: {', '.join(industry_pain_points[:5]) if industry_pain_points else 'General business challenges'}
        - Use case examples: {', '.join(use_case_examples[:3]) if use_case_examples else 'Industry-specific automation'}
        - Value proposition template: {value_prop_template}
        - Effective pitch angles: {', '.join(industry_pitch_angles[:3]) if industry_pitch_angles else 'Value-driven solutions'}
        
        IMPORTANT: 
        - The title should include "{vani_persona} for [Company Name]" format
        - The hit_list should be formatted as readable, engaging text (like a marketing card description), NOT as a JSON object. Use natural language.
        - The solution should emphasize how the {vani_persona} persona specifically addresses {company_name}'s challenges.
        - DO NOT mention "RAG" or "Gemini" as brand names or customer collaborations. These are internal tools, not customer brands.
        - DO NOT reference "successful collaborations with brands such as RAG and Gemini" or similar phrases.
        - Focus on real customer success stories and industry examples, not internal tools or technologies.
        
        Return your response as a JSON object with these exact keys: title, problem, solution, hit_list, trojan_horse.
        """

        # Build enhanced user prompt with RAG and Gemini insights
        user_prompt = f"""
        Generate a pitch for {company_name}, targeting {contact_name} ({role}).
        Their primary pain point is: "{pain_point}".
        Our unique pitch angle for them is: "{pitch_angle}".

        Ensure the pitch is highly relevant to the {industry_name} industry and {company_name}'s specific context.
        The "hit_list" section should be a readable, engaging description (like a marketing card) for {company_name}, highlighting their pain point and VANI's solution. Format as natural text, NOT JSON.
        
        Example hit_list format: "For {company_name}, facing [pain point], VANI offers [solution]. This enables [benefit]."
        """
        
        # Add RAG insights if available
        if rag_insights:
            user_prompt += f"\n\nIndustry Knowledge Base Insights:\n{rag_insights}\n\nUse these insights to make the pitch more relevant and compelling."
        
        # Add Gemini insights if available
        if gemini_insights:
            user_prompt += f"\n\nCustomer-Specific Insights:\n{gemini_insights}\n\nIncorporate these insights to personalize the pitch further."
        
        user_prompt += "\n\nReturn a JSON object with keys: title, problem, solution, hit_list, trojan_horse. All values should be strings (text), not nested JSON objects."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            pitch_content = response.choices[0].message.content
            # Parse JSON response
            try:
                pitch_dict = json.loads(pitch_content)
                return pitch_dict
            except json.JSONDecodeError:
                logger.warning("OpenAI did not return valid JSON. Attempting to parse...")
                # Fallback parsing
                return self._parse_pitch_content(pitch_content)

        except Exception as e:
            logger.error(f"Error generating pitch with OpenAI: {e}")
            raise

    def _parse_pitch_content(self, raw_content: str) -> Dict[str, Any]:
        """
        Parses the raw string content from OpenAI into a structured dictionary.
        Fallback if JSON parsing fails.
        """
        pitch = {
            "title": "Strategic Pitch for Your Company",
            "problem": "",
            "solution": "",
            "hit_list": "",
            "trojan_horse": ""
        }
        
        # Try to extract sections
        sections = {
            "title": ["Title", "title"],
            "problem": ["Problem", "problem"],
            "solution": ["Solution", "solution"],
            "hit_list": ["Hit List", "hit list", "hit_list"],
            "trojan_horse": ["Trojan Horse", "trojan horse", "trojan_horse"]
        }
        
        current_section = None
        for line in raw_content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            found_section = False
            for key, headers in sections.items():
                for header in headers:
                    if line.startswith(header + ":") or line.startswith("## " + header):
                        current_section = key
                        pitch[key] = line[len(header + ":"):].strip() if line.startswith(header + ":") else ""
                        found_section = True
                        break
                if found_section:
                    break
            
            if not found_section and current_section:
                if pitch[current_section]:
                    pitch[current_section] += "\n" + line
                else:
                    pitch[current_section] = line
        
        return pitch

