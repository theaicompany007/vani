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
        # Default to gemini-2.0-flash (widely available and stable)
        # Fallback models in order of preference
        default_model = 'gemini-2.0-flash'
        fallback_models = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-pro']
        model_name = os.getenv('GEMINI_MODEL', default_model)
        notebook_lm_enabled = os.getenv('GEMINI_NOTEBOOK_LM_ENABLED', 'false').lower() == 'true'
        
        if not api_key:
            logger.warning("GEMINI_API_KEY not found - Gemini queries will be disabled")
            self.enabled = False
            self.client = None
            self.model = None
        else:
            # Validate API key format
            api_key = api_key.strip()
            if not self._validate_api_key_format(api_key):
                logger.error("GEMINI_API_KEY format is invalid. Expected format: starts with 'AIza' and ~39 characters")
                logger.error(f"API key preview: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''} (length: {len(api_key)})")
                logger.error("Get a valid API key from: https://aistudio.google.com/app/apikey")
                self.enabled = False
                self.client = None
                self.model = None
                return
            # Store and temporarily remove proxy environment variables
            # Some libraries may try to use these and pass them as parameters
            old_proxy_vars = {}
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            for var in proxy_vars:
                if var in os.environ:
                    old_proxy_vars[var] = os.environ[var]
                    del os.environ[var]
            
            try:
                # Configure Gemini API - only pass supported parameters
                # Explicitly avoid passing proxies or other unsupported parameters
                # The library may try to read proxies from environment variables, so we ensure clean initialization
                genai.configure(api_key=api_key)
                
                # Try to create model with configured name, fallback to alternatives if not available
                models_to_try = [model_name] + [m for m in fallback_models if m != model_name]
                client = None
                working_model = None
                
                for test_model in models_to_try:
                    try:
                        # Create GenerativeModel - ensure no unsupported parameters
                        # Some versions of google-generativeai may not support all Client parameters
                        # We explicitly pass only the model name to avoid any parameter issues
                        test_client = genai.GenerativeModel(test_model)
                        # Actually test with a real API call to verify model is available
                        # This catches cases where model object creation succeeds but model isn't actually available
                        test_response = test_client.generate_content(
                            "test",
                            generation_config={'temperature': 0.1, 'max_output_tokens': 10}
                        )
                        # If we get here, the model works
                        client = test_client
                        working_model = test_model
                        logger.info(f"Successfully initialized and tested Gemini model: {test_model}")
                        break
                    except Exception as model_error:
                        error_str = str(model_error)
                        if 'not found' in error_str.lower() or '404' in error_str or 'not supported' in error_str.lower():
                            logger.debug(f"Model {test_model} not available: {error_str[:100]}")
                            continue
                        else:
                            # Other errors (like API key issues) should be raised
                            raise
                
                if not client or not working_model:
                    raise ValueError(f"None of the attempted models are available: {models_to_try}")
                
                self.client = client
                self.model = working_model
                self.enabled = True
                self.notebook_lm_enabled = notebook_lm_enabled
                
                if working_model != model_name:
                    logger.warning(f"Requested model '{model_name}' not available, using '{working_model}' instead")
                    logger.info(f"Gemini client initialized with model: {working_model}")
                else:
                    logger.info(f"Gemini client initialized with model: {model_name}")
                logger.debug(f"API key format: {api_key[:8]}...{api_key[-4:]} (length: {len(api_key)})")
            except (TypeError, ValueError) as e:
                # Handle case where Client doesn't accept certain parameters (like proxies)
                error_msg = str(e).lower()
                if 'proxies' in error_msg or 'unexpected keyword argument' in error_msg:
                    logger.error(f"Gemini client initialization failed due to unsupported parameter: {e}")
                    logger.warning("This may be caused by environment variables or library version mismatch.")
                    logger.warning("Proxies have been cleared. If error persists, check google-generativeai version.")
                    # Proxies already cleared above, so just log and disable
                    self.enabled = False
                    self.client = None
                    self.model = None
                else:
                    # Restore proxy environment variables before re-raising
                    for var, value in old_proxy_vars.items():
                        os.environ[var] = value
                    raise
            except Exception as e:
                error_str = str(e)
                # Check for API key invalid errors
                if 'API key not valid' in error_str or 'API_KEY_INVALID' in error_str or 'API key' in error_str.lower():
                    logger.error("=" * 60)
                    logger.error("GEMINI API KEY VALIDATION FAILED")
                    logger.error("=" * 60)
                    logger.error(f"Error: {error_str}")
                    logger.error(f"API key preview: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''} (length: {len(api_key)})")
                    logger.error("")
                    logger.error("TROUBLESHOOTING STEPS:")
                    logger.error("1. Verify your API key is correct and not expired")
                    logger.error("2. Get a new API key from: https://aistudio.google.com/app/apikey")
                    logger.error("3. Ensure the API key is properly set in your .env.local file")
                    logger.error("4. Check that the API key has not been revoked or restricted")
                    logger.error("5. Verify API key format: should start with 'AIza' and be ~39 characters")
                    logger.error("=" * 60)
                elif 'not found' in error_str.lower() or '404' in error_str or 'not supported' in error_str.lower():
                    logger.error("=" * 60)
                    logger.error("GEMINI MODEL NOT AVAILABLE")
                    logger.error("=" * 60)
                    logger.error(f"Error: {error_str}")
                    logger.error(f"Requested model: {model_name}")
                    logger.error("")
                    logger.error("TROUBLESHOOTING STEPS:")
                    logger.error("1. The model name may be incorrect or not available in your API version")
                    logger.error("2. Try setting GEMINI_MODEL to one of these:")
                    logger.error("   - gemini-1.5-flash (recommended, fast and available)")
                    logger.error("   - gemini-pro (stable, widely available)")
                    logger.error("   - gemini-1.5-pro-latest (if available)")
                    logger.error("3. List available models by running:")
                    logger.error("   python -c \"import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); [print(m.name) for m in genai.list_models()]\"")
                    logger.error("4. Check Google AI Studio for current model availability")
                    logger.error("=" * 60)
                else:
                    logger.error(f"Failed to initialize Gemini client: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                self.enabled = False
                self.client = None
                self.model = None
            finally:
                # Always restore proxy environment variables
                for var, value in old_proxy_vars.items():
                    os.environ[var] = value
    
    def _validate_api_key_format(self, api_key: str) -> bool:
        """
        Validate Gemini API key format
        
        Args:
            api_key: The API key to validate
            
        Returns:
            True if format looks valid, False otherwise
        """
        if not api_key:
            return False
        
        # Gemini API keys typically start with 'AIza' and are around 39 characters
        # Allow some flexibility in length (35-45 characters) but require 'AIza' prefix
        if not api_key.startswith('AIza'):
            return False
        
        if len(api_key) < 35 or len(api_key) > 45:
            logger.warning(f"API key length ({len(api_key)}) is outside typical range (35-45 characters)")
            # Don't fail on length alone, but warn
        
        return True
    
    def get_available_models(self) -> List[str]:
        """
        List all available Gemini models for this API key
        
        Returns:
            List of available model names
        """
        if not self.enabled:
            return []
        
        try:
            models = genai.list_models()
            available = []
            for model in models:
                # Only include models that support generateContent
                if 'generateContent' in model.supported_generation_methods:
                    # Extract just the model name (e.g., "models/gemini-pro" -> "gemini-pro")
                    model_name = model.name.split('/')[-1] if '/' in model.name else model.name
                    available.append(model_name)
            return available
        except Exception as e:
            logger.error(f"Failed to list available models: {e}")
            return []
    
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
            error_str = str(e)
            # Check for API key invalid errors
            if 'API key not valid' in error_str or 'API_KEY_INVALID' in error_str or 'API key' in error_str.lower():
                logger.error("=" * 60)
                logger.error("GEMINI API KEY ERROR DURING QUERY")
                logger.error("=" * 60)
                logger.error(f"Error: {error_str}")
                logger.error("")
                logger.error("TROUBLESHOOTING STEPS:")
                logger.error("1. Verify your API key is correct and not expired")
                logger.error("2. Get a new API key from: https://aistudio.google.com/app/apikey")
                logger.error("3. Ensure the API key is properly set in your .env.local file")
                logger.error("4. Check that the API key has not been revoked or restricted")
                logger.error("5. Restart the application after updating the API key")
                logger.error("=" * 60)
            else:
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










