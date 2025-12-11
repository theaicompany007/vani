"""Google Gemini API client for Notebook LM queries"""
import os
import logging
from typing import Optional, Dict, Any, List
import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for querying Google Gemini API (Notebook LM content)"""
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        model_name = os.getenv('GEMINI_MODEL', 'gemini-pro')
        notebook_lm_enabled = os.getenv('GEMINI_NOTEBOOK_LM_ENABLED', 'false').lower() == 'true'
        
        if not api_key:
            logger.warning("GEMINI_API_KEY not found - Gemini queries will be disabled")
            self.enabled = False
            self.client = None
            self.model = None
        else:
            try:
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(model_name)
                self.model = model_name
                self.enabled = True
                self.notebook_lm_enabled = notebook_lm_enabled
                logger.info(f"Gemini client initialized with model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                self.enabled = False
                self.client = None
                self.model = None
    
    def query_notebook_lm(
        self,
        query: str,
        company_name: Optional[str] = None,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query Notebook LM content through Gemini API
        
        Args:
            query: Search query text
            company_name: Optional company name to search for (Royal Enfield, IndiGo, ITQ, EaseMyTrip, etc.)
            industry: Optional industry context
            
        Returns:
            Dict with customer insights, case studies, and company profiles
        """
        if not self.enabled:
            logger.debug("Gemini client not enabled, returning empty results")
            return {
                'customer_examples': [],
                'company_profiles': [],
                'industry_insights': [],
                'case_studies': []
            }
        
        try:
            # Build prompt for Notebook LM query
            prompt_parts = []
            
            if company_name:
                prompt_parts.append(f"Find information about {company_name}")
                # Known customer companies
                if company_name.lower() in ['royal enfield', 'royalenfield']:
                    prompt_parts.append("Include details from Royal Enfield customer data")
                elif company_name.lower() in ['indigo', 'indigo airlines', 'indigoairlines']:
                    prompt_parts.append("Include details from IndiGo Airlines customer data")
                elif 'itq' in company_name.lower():
                    prompt_parts.append("Include details from ITQ Technologies customer data")
                elif 'easemytrip' in company_name.lower():
                    prompt_parts.append("Include details from EaseMyTrip customer data")
            
            if industry:
                prompt_parts.append(f"Focus on {industry} industry context")
            
            prompt_parts.append(f"Query: {query}")
            prompt_parts.append("\nProvide:")
            prompt_parts.append("- Customer-specific case studies and success stories")
            prompt_parts.append("- Company profiles and business information")
            prompt_parts.append("- Industry-specific insights and pain points")
            prompt_parts.append("- Relevant use cases and examples")
            
            full_prompt = "\n".join(prompt_parts)
            
            response = self.client.generate_content(
                full_prompt,
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': 2000,
                }
            )
            
            result_text = response.text.strip()
            
            # Parse response (Gemini returns text, we'll structure it)
            # In a real implementation, you might use structured output or parse JSON
            return {
                'customer_examples': self._extract_customer_examples(result_text, company_name),
                'company_profiles': self._extract_company_profiles(result_text, company_name),
                'industry_insights': self._extract_industry_insights(result_text, industry),
                'case_studies': self._extract_case_studies(result_text),
                'raw_response': result_text
            }
            
        except Exception as e:
            logger.error(f"Error querying Gemini/Notebook LM: {e}")
            return {
                'customer_examples': [],
                'company_profiles': [],
                'industry_insights': [],
                'case_studies': [],
                'error': str(e)
            }
    
    def _extract_customer_examples(self, text: str, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract customer examples from Gemini response"""
        # Simple extraction - in production, use structured output or better parsing
        examples = []
        if company_name and company_name.lower() in text.lower():
            examples.append({
                'company': company_name,
                'content': text[:500] if len(text) > 500 else text,
                'source': 'notebook_lm'
            })
        return examples
    
    def _extract_company_profiles(self, text: str, company_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract company profiles from Gemini response"""
        profiles = []
        if company_name:
            profiles.append({
                'company': company_name,
                'description': text[:500] if len(text) > 500 else text,
                'source': 'notebook_lm'
            })
        return profiles
    
    def _extract_industry_insights(self, text: str, industry: Optional[str] = None) -> List[str]:
        """Extract industry insights from Gemini response"""
        # Simple extraction - split by sentences or paragraphs
        insights = []
        sentences = text.split('. ')
        for sentence in sentences[:5]:  # Top 5 insights
            if sentence.strip():
                insights.append(sentence.strip())
        return insights
    
    def _extract_case_studies(self, text: str) -> List[Dict[str, Any]]:
        """Extract case studies from Gemini response"""
        case_studies = []
        # Look for case study indicators in text
        if any(keyword in text.lower() for keyword in ['case study', 'success', 'result', 'achievement']):
            case_studies.append({
                'title': 'Customer Success Story',
                'content': text[:1000] if len(text) > 1000 else text,
                'source': 'notebook_lm'
            })
        return case_studies


# Global instance
_gemini_client = None

def get_gemini_client() -> GeminiClient:
    """Get or create the global Gemini client instance"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client





