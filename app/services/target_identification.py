"""AI-powered target identification service"""
import logging
import os
import json
import re
from typing import List, Optional, Dict, Any
from openai import OpenAI
import google.generativeai as genai
from app.models.target_recommendation import TargetRecommendation
from app.services.industry_context import get_industry_context
from app.integrations.rag_client import get_rag_client
from app.integrations.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)


def repair_json(text: str) -> str:
    """
    Attempt to repair malformed/incomplete JSON
    
    Args:
        text: Potentially malformed JSON string
        
    Returns:
        Repaired JSON string
    """
    # Remove markdown code blocks if present
    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    else:
        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
    
    # Try to close incomplete JSON structures
    # Count open/close braces
    open_braces = text.count('{')
    close_braces = text.count('}')
    
    # If we have more open braces, try to close them
    if open_braces > close_braces:
        text += '}' * (open_braces - close_braces)
    
    # Count open/close brackets
    open_brackets = text.count('[')
    close_brackets = text.count(']')
    
    # If we have more open brackets, try to close them
    if open_brackets > close_brackets:
        text += ']' * (open_brackets - close_brackets)
    
    # Try to close incomplete strings (find unclosed strings)
    # This is a simple heuristic - look for strings that aren't closed
    lines = text.split('\n')
    repaired_lines = []
    for line in lines:
        # If line ends with a quote but no comma/brace/bracket, it might be incomplete
        if line.strip().endswith('"') and not any(line.strip().endswith(c) for c in [',', '}', ']', '",', '"}', '"]']):
            # Check if it's part of an array or object
            if '"' in line and line.count('"') % 2 == 1:  # Odd number of quotes
                line = line.rstrip('"').rstrip() + '",'  # Add comma for array/object
        repaired_lines.append(line)
    
    text = '\n'.join(repaired_lines)
    
    # Remove trailing commas before closing braces/brackets
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    return text.strip()


class TargetIdentificationService:
    """Service for AI-powered target identification"""
    
    def __init__(self):
        # Determine AI provider priority from environment variable
        # Format: "gemini,openai" or "openai,gemini" (comma-separated, order matters)
        ai_priority = os.getenv('AI_PROVIDER_PRIORITY', 'gemini,openai').lower()
        self.ai_providers = [p.strip() for p in ai_priority.split(',')]
        logger.info(f"AI Provider Priority: {self.ai_providers}")
        
        # Initialize OpenAI client (may not be used if Gemini is first)
        api_key = os.getenv('OPENAI_API_KEY')
        self.openai_client = None
        self.openai_available = False
        if api_key:
            # Store and temporarily remove proxy environment variables
            # Some libraries may try to use these and pass them as parameters
            old_proxy_vars = {}
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            for var in proxy_vars:
                if var in os.environ:
                    old_proxy_vars[var] = os.environ[var]
                    del os.environ[var]
            
            try:
                # Initialize OpenAI client - only pass api_key to avoid unsupported parameters
                # Do not pass proxies or other parameters that may cause issues
                # The OpenAI library should handle api_key only
                self.openai_client = OpenAI(api_key=api_key)
                self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
                self.openai_available = True
            except (TypeError, ValueError) as e:
                # Handle case where Client doesn't accept certain parameters (like proxies)
                error_msg = str(e).lower()
                if 'proxies' in error_msg or 'unexpected keyword argument' in error_msg:
                    logger.error(f"OpenAI client initialization failed due to unsupported parameter: {e}")
                    logger.warning("This may be caused by environment variables or library version mismatch.")
                    logger.warning("Proxies have been cleared. If error persists, check openai library version.")
                    # Restore proxy environment variables before raising
                    for var, value in old_proxy_vars.items():
                        os.environ[var] = value
                    logger.warning(f"OpenAI client initialization failed: {e}. Will use fallback if available.")
                    self.openai_available = False
                else:
                    # Restore proxy environment variables before re-raising
                    for var, value in old_proxy_vars.items():
                        os.environ[var] = value
                    raise
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Restore proxy environment variables before raising
                for var, value in old_proxy_vars.items():
                    os.environ[var] = value
                self.openai_available = False
            finally:
                # Always restore proxy environment variables
                for var, value in old_proxy_vars.items():
                    os.environ[var] = value
        else:
            logger.warning("OPENAI_API_KEY not configured. OpenAI will not be available.")
        
        # Initialize RAG and Gemini clients with error handling
        try:
            self.rag_client = get_rag_client()
        except Exception as e:
            logger.warning(f"RAG client initialization failed: {e}")
            self.rag_client = None
        
        try:
            self.gemini_client = get_gemini_client()
            self.gemini_available = self.gemini_client and self.gemini_client.enabled
        except Exception as e:
            logger.warning(f"Gemini client initialization failed: {e}")
            self.gemini_client = None
            self.gemini_available = False
        
        # Validate at least one AI provider is available
        if not self.openai_available and not self.gemini_available:
            raise ValueError("No AI providers available. Configure OPENAI_API_KEY or GEMINI_API_KEY.")
    
    def identify_targets(
        self,
        industry: str,
        contacts: List[Dict[str, Any]],
        limit: int = 50,
        min_seniority: float = 0.5
    ) -> List[TargetRecommendation]:
        """
        Identify high-value targets from contacts using AI
        
        Args:
            industry: Industry name to filter and analyze
            contacts: List of contact dictionaries from database
            limit: Maximum number of recommendations to return
            min_seniority: Minimum seniority score (0-1)
            
        Returns:
            List of TargetRecommendation objects
        """
        if not contacts:
            logger.warning(f"No contacts provided for industry {industry}")
            return []
        
        # Get industry context
        industry_context = get_industry_context(industry)
        if not industry_context:
            logger.warning(f"No industry context found for {industry}")
            return []
        
        # Query RAG service for industry knowledge
        rag_knowledge = self._get_rag_knowledge(industry)
        
        # Query Gemini for customer examples
        gemini_insights = self._get_gemini_insights(industry)
        
        # Analyze contacts in batches
        recommendations = []
        batch_size = 10  # Process contacts in batches to avoid token limits
        
        # Process ALL contacts first, then filter and rank
        # This ensures we don't miss contacts that might rank higher after full analysis
        for i in range(0, len(contacts), batch_size):
            batch = contacts[i:i + batch_size]
            batch_recommendations = self._analyze_contact_batch(
                batch,
                industry,
                industry_context,
                rag_knowledge,
                gemini_insights
            )
            recommendations.extend(batch_recommendations)
            logger.debug(f"Processed batch {i//batch_size + 1}: {len(batch_recommendations)} recommendations from {len(batch)} contacts")
        
        logger.info(f"Total recommendations generated: {len(recommendations)} from {len(contacts)} contacts")
        
        # Filter by min_seniority and sort by confidence
        filtered = [
            r for r in recommendations
            if r.seniority_score >= min_seniority
        ]
        
        logger.info(f"After min_seniority filter (>= {min_seniority}): {len(filtered)} recommendations")
        
        # Log specific contacts for debugging (e.g., Nikhil Kumar)
        for r in recommendations[:50]:  # Check first 50 for debugging
            if 'nikhil' in r.contact_name.lower() or 'kumar' in r.contact_name.lower():
                logger.info(f"Found Nikhil Kumar: seniority={r.seniority_score:.2f}, confidence={r.confidence_score:.2f}, overall={r.overall_score:.2f}, matches_min_seniority={r.seniority_score >= min_seniority}")
        
        # Sort by confidence score (descending)
        sorted_recommendations = sorted(
            filtered,
            key=lambda x: x.confidence_score,
            reverse=True
        )
        
        # Log top recommendations for debugging
        if sorted_recommendations:
            logger.info(f"Top 5 recommendations: {[(r.contact_name, r.confidence_score, r.seniority_score) for r in sorted_recommendations[:5]]}")
        
        return sorted_recommendations[:limit]
    
    def _get_rag_knowledge(self, industry: str) -> Dict[str, Any]:
        """Get RAG knowledge for industry - enhanced with multiple collections"""
        if not self.rag_client:
            logger.warning("RAG client not available, returning empty knowledge")
            return {
                'case_studies': [],
                'services': [],
                'insights': [],
                'platforms': [],
                'company_profiles': [],
                'raw_results': {}
            }
        
        try:
            # Query multiple collections for comprehensive knowledge
            collections = ['case_studies', 'services', 'industry_insights', 'platforms', 'company_profiles']
            
            # Query all collections at once
            query_text = f"{industry} case study service solution platform"
            rag_result = self.rag_client.query(
                query=query_text,
                industry=industry,
                collections=collections,
                top_k=5
            )
            
            results = rag_result.get('results', {})
            
            # Extract case studies
            case_studies = results.get('case_studies', [])
            
            # Extract services
            services = results.get('services', [])
            
            # Extract industry insights
            insights = results.get('industry_insights', [])
            
            # Extract platforms (The AI Company platforms)
            platforms = results.get('platforms', [])
            
            # Extract company profiles
            company_profiles = results.get('company_profiles', [])
            
            return {
                'case_studies': case_studies,
                'services': services,
                'insights': insights,
                'platforms': platforms,
                'company_profiles': company_profiles,
                'raw_results': results
            }
        except Exception as e:
            logger.warning(f"Failed to get RAG knowledge: {e}")
            return {
                'case_studies': [],
                'services': [],
                'insights': [],
                'platforms': [],
                'company_profiles': [],
                'raw_results': {}
            }
    
    def _get_gemini_insights(self, industry: str) -> Dict[str, Any]:
        """Get Gemini/Notebook LM insights for industry"""
        if not self.gemini_client or not self.gemini_client.enabled:
            logger.debug("Gemini client not available, returning empty insights")
            return {
                'customer_examples': [],
                'company_profiles': [],
                'industry_insights': [],
                'case_studies': []
            }
        
        try:
            result = self.gemini_client.query_notebook_lm(
                query=f"{industry} industry customer examples case studies",
                industry=industry
            )
            return result
        except Exception as e:
            logger.warning(f"Failed to get Gemini insights: {e}")
            return {
                'customer_examples': [],
                'company_profiles': [],
                'industry_insights': [],
                'case_studies': []
            }
    
    def _analyze_contact_batch(
        self,
        contacts: List[Dict[str, Any]],
        industry: str,
        industry_context: Any,
        rag_knowledge: Dict[str, Any],
        gemini_insights: Dict[str, Any]
    ) -> List[TargetRecommendation]:
        """Analyze a batch of contacts using configured AI provider priority"""
        # Build prompt with all context
        prompt = self._build_analysis_prompt(
            contacts,
            industry,
            industry_context,
            rag_knowledge,
            gemini_insights
        )
        
        # Create contacts map for fallback matching
        contacts_map = {str(c.get('id', c.get('contact_id', ''))): c for c in contacts if c.get('id') or c.get('contact_id')}
        
        # Try providers in priority order
        for provider in self.ai_providers:
            if provider == 'gemini' and self.gemini_available:
                try:
                    logger.info("Using Gemini for contact analysis (priority provider)")
                    return self._analyze_contact_batch_with_gemini(
                        contacts,
                        industry,
                        industry_context,
                        rag_knowledge,
                        gemini_insights,
                        contacts_map
                    )
                except Exception as e:
                    logger.warning(f"Gemini analysis failed: {e}. Trying next provider...")
                    continue
            
            elif provider == 'openai' and self.openai_available:
                try:
                    logger.info("Using OpenAI for contact analysis")
                    response = self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert B2B sales analyst. Analyze contacts to identify high-value targets. Return only valid JSON."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.3,
                        max_tokens=4000,
                        response_format={"type": "json_object"}
                    )
                    
                    result_text = response.choices[0].message.content.strip()
                    analysis = json.loads(result_text)
                    
                    return self._parse_recommendations(analysis, industry, rag_knowledge, contacts_map)
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    logger.warning(f"OpenAI analysis failed: {e}. Trying next provider...")
                    continue
        
        # If all providers failed
        logger.error("All AI providers failed. Cannot analyze contacts.")
        return []
    
    def _parse_recommendations(
        self,
        analysis: Dict[str, Any],
        industry: str,
        rag_knowledge: Dict[str, Any],
        contacts_map: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[TargetRecommendation]:
        """Parse recommendations from AI analysis response"""
        # Extract relevant knowledge base content for recommendations
        # Handle different RAG response structures
        case_studies_list = rag_knowledge.get('case_studies', [])
        services_list = rag_knowledge.get('services', [])
        insights_list = rag_knowledge.get('insights', [])
        platforms_list = rag_knowledge.get('platforms', [])
        
        # Extract case study titles/names
        related_case_studies = []
        for cs in case_studies_list[:5]:
            if isinstance(cs, dict):
                title = cs.get('metadata', {}).get('title') or cs.get('title') or cs.get('document', '')[:100]
                if title:
                    related_case_studies.append(title)
            elif isinstance(cs, str):
                related_case_studies.append(cs[:100])
        
        # Extract service names/types
        relevant_services = []
        for svc in services_list[:5]:
            if isinstance(svc, dict):
                service_name = svc.get('metadata', {}).get('service_type') or svc.get('service_type') or svc.get('title') or svc.get('document', '')[:100]
                if service_name:
                    relevant_services.append(service_name)
            elif isinstance(svc, str):
                relevant_services.append(svc[:100])
        
        # Extract platform names
        relevant_platforms = []
        for platform in platforms_list[:3]:
            if isinstance(platform, dict):
                platform_name = platform.get('metadata', {}).get('platform') or platform.get('platform') or platform.get('title') or platform.get('document', '')[:100]
                if platform_name:
                    relevant_platforms.append(platform_name)
            elif isinstance(platform, str):
                relevant_platforms.append(platform[:100])
        
        # Extract insights
        relevant_insights = []
        for insight in insights_list[:3]:
            if isinstance(insight, dict):
                insight_text = insight.get('document') or insight.get('content') or insight.get('text', '')[:200]
                if insight_text:
                    relevant_insights.append(insight_text)
            elif isinstance(insight, str):
                relevant_insights.append(insight[:200])
        
        # Parse recommendations
        recommendations = []
        if 'recommendations' in analysis:
            for rec_data in analysis['recommendations']:
                try:
                    # Get contact_id - try from AI response, fallback to matching by name/email
                    contact_id = rec_data.get('contact_id', '')
                    if not contact_id and contacts_map:
                        # Try to find contact by name and company
                        contact_name = rec_data.get('contact_name', '')
                        company_name = rec_data.get('company_name', '')
                        for cid, contact in contacts_map.items():
                            if (contact.get('name', '').lower() == contact_name.lower() and 
                                (contact.get('company', '').lower() == company_name.lower() or 
                                 contact.get('company_name', '').lower() == company_name.lower())):
                                contact_id = str(cid)
                                logger.info(f"Matched contact by name/company: {contact_name} at {company_name} -> {contact_id}")
                                break
                    
                    if not contact_id:
                        logger.warning(f"Could not determine contact_id for recommendation: {rec_data.get('contact_name', 'Unknown')}")
                        continue
                    
                    # Calculate overall score (weighted average of seniority and confidence)
                    seniority = float(rec_data.get('seniority_score', 0.5))
                    confidence = float(rec_data.get('confidence_score', 0.5))
                    overall_score = (seniority * 0.6 + confidence * 0.4)  # Weight seniority more
                    
                    recommendation = TargetRecommendation(
                        contact_id=str(contact_id),
                        contact_name=rec_data.get('contact_name', ''),
                        company_name=rec_data.get('company_name', ''),
                        role=rec_data.get('role'),
                        email=rec_data.get('email'),
                        phone=rec_data.get('phone'),
                        linkedin_url=rec_data.get('linkedin_url'),
                        seniority_score=seniority,
                        solution_fit=rec_data.get('solution_fit', 'both'),
                        confidence_score=confidence,
                        overall_score=overall_score,  # Include overall_score in the model
                        identified_gaps=rec_data.get('identified_gaps', []),
                        recommended_pitch_angle=rec_data.get('recommended_pitch_angle'),
                        pain_points=rec_data.get('pain_points', []),
                        reasoning=rec_data.get('reasoning', ''),
                        industry=industry,
                        knowledge_base_context={
                            'case_studies': case_studies_list[:3] if case_studies_list else [],
                            'services': services_list[:3] if services_list else [],
                            'insights': insights_list[:3] if insights_list else [],
                            'platforms': platforms_list[:2] if platforms_list else [],
                            'company_profiles': rag_knowledge.get('company_profiles', [])[:2]
                        },
                        related_case_studies=related_case_studies[:5],
                        relevant_services=relevant_services[:5],
                        relevant_platforms=relevant_platforms[:3],
                        relevant_insights=relevant_insights[:3] if relevant_insights else []
                    )
                    recommendations.append(recommendation)
                except Exception as e:
                    logger.warning(f"Failed to parse recommendation: {e}")
                    continue
        
        return recommendations
    
    def _analyze_contact_batch_with_gemini(
        self,
        contacts: List[Dict[str, Any]],
        industry: str,
        industry_context: Any,
        rag_knowledge: Dict[str, Any],
        gemini_insights: Dict[str, Any],
        contacts_map: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[TargetRecommendation]:
        """Analyze a batch of contacts using Gemini"""
        if not contacts_map:
            contacts_map = {str(c.get('id', c.get('contact_id', ''))): c for c in contacts if c.get('id') or c.get('contact_id')}
        
        try:
            # Build prompt with all context
            prompt = self._build_analysis_prompt(
                contacts,
                industry,
                industry_context,
                rag_knowledge,
                gemini_insights
            )
            
            # Enhanced system instruction for detailed Gemini analysis
            system_instruction = """You are an expert B2B sales analyst preparing a comprehensive target analysis report. 
            
Your analysis should be DETAILED and ACTIONABLE, similar to a professional B2B sales analysis report. For each contact, provide:

1. **Identified Gaps**: 3-5 specific enterprise gaps (e.g., "Enterprise-scale reputation monitoring across 2,700+ employees", "Automation opportunities for SKU proliferation (100+ products)")
2. **Pain Points**: 3-5 industry-relevant pain points (e.g., "Rising labor and input costs in snacks manufacturing", "Productivity optimization across manufacturing and retail distribution")
3. **Recommended Pitch Angle**: Strategic entry angle (2-3 sentences, reference RAG/Gemini examples)
4. **Reasoning**: Comprehensive explanation (3-5 sentences) with industry context, RAG examples, company scale, and solution fit rationale
5. **Confidence Score**: Based on seniority, solution fit, and company scale (0.60-0.95 range)

CRITICAL: You MUST use the exact "Contact ID" value from each contact above. Do NOT use indices or generate new IDs.

CRITICAL JSON FORMATTING REQUIREMENTS:
- Return ONLY valid, complete JSON - no markdown, no code blocks, no additional text
- Ensure ALL strings are properly escaped and closed with double quotes
- Ensure ALL arrays are properly closed with ]
- Ensure ALL objects are properly closed with }
- Ensure the entire JSON response is complete - do not truncate
- If the response is too long, prioritize completing the JSON structure over adding more detail

Return your response as a valid JSON object with a 'recommendations' array. Each recommendation must include:
- contact_id (EXACT Contact ID from contact data - UUID string)
- contact_name, company_name, role, email, phone, linkedin_url
- seniority_score (0.0-1.0): C-suite=0.9+, VP=0.7-0.9, Director=0.5-0.7
- solution_fit: "onlyne_reputation" | "the_ai_company" | "both"
- confidence_score (0.0-1.0): 0.90-0.95=highest priority, 0.80-0.89=high, 0.70-0.79=moderate-high
- identified_gaps: Array of 3-5 specific enterprise gaps (keep strings concise to avoid truncation)
- recommended_pitch_angle: 2-3 sentence strategic pitch (keep concise)
- pain_points: Array of 3-5 industry-relevant pain points (keep strings concise)
- reasoning: 3-5 sentence comprehensive explanation with RAG/Gemini context (keep concise)"""
            
            full_prompt = f"{system_instruction}\n\n{prompt}\n\nCRITICAL: Return ONLY valid, complete JSON. Ensure all strings are properly closed, all arrays and objects are properly closed, and the JSON is complete. Do not truncate the response. Return the full JSON object with all recommendations."
            
            # Try to generate content, with fallback to other models if current one fails
            response = None
            result_text = None
            # Get fallback models - use common fallbacks
            fallback_models = ['gemini-pro', 'gemini-1.5-pro-latest', 'gemini-2.0-flash-exp']
            models_to_try = [self.gemini_client.model] + [m for m in fallback_models if m != self.gemini_client.model]
            
            # Ensure genai is configured (it should be, but just in case)
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            if gemini_api_key:
                genai.configure(api_key=gemini_api_key)
            
            for model_name in models_to_try:
                try:
                    # Create a new model instance for this attempt
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(
                        full_prompt,
                        generation_config={
                            'temperature': 0.3,
                            'max_output_tokens': 8000,  # Increased for larger responses
                        }
                    )
                    result_text = response.text.strip()
                    if model_name != self.gemini_client.model:
                        logger.warning(f"Original model {self.gemini_client.model} failed, successfully used {model_name} instead")
                        # Update the client to use the working model
                        self.gemini_client.client = model
                        self.gemini_client.model = model_name
                    break
                except Exception as model_error:
                    error_str = str(model_error)
                    if 'not found' in error_str.lower() or '404' in error_str or 'not supported' in error_str.lower():
                        logger.debug(f"Model {model_name} failed: {error_str[:100]}")
                        if model_name == models_to_try[-1]:
                            # Last model failed, raise the error
                            raise
                        continue
                    else:
                        # Other errors should be raised
                        raise
            
            if not response or not result_text:
                raise ValueError("Failed to generate content with any available model")
            
            # Try to extract and repair JSON from response
            try:
                # First, try to extract JSON
                json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(1)
                else:
                    # Try to find JSON object in the text
                    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                    if json_match:
                        result_text = json_match.group(0)
                
                # Try to parse directly first
                try:
                    analysis = json.loads(result_text)
                except json.JSONDecodeError:
                    # If parsing fails, try to repair the JSON
                    logger.warning("JSON parsing failed, attempting to repair...")
                    repaired_json = repair_json(result_text)
                    try:
                        analysis = json.loads(repaired_json)
                        logger.info("Successfully repaired JSON")
                    except json.JSONDecodeError as repair_error:
                        # If repair failed, log the error with more context
                        logger.error(f"Failed to repair JSON: {repair_error}")
                        logger.error(f"Original response length: {len(result_text)} characters")
                        logger.error(f"Response preview (first 1000 chars): {result_text[:1000]}")
                        logger.error(f"Response preview (last 500 chars): {result_text[-500:]}")
                        # Try to extract just the recommendations array if possible
                        rec_match = re.search(r'"recommendations"\s*:\s*\[(.*?)\]', result_text, re.DOTALL)
                        if rec_match:
                            # Try to parse just the recommendations
                            try:
                                partial_json = '{"recommendations": [' + rec_match.group(1) + ']}'
                                analysis = json.loads(partial_json)
                                logger.warning("Parsed partial JSON (recommendations only)")
                            except:
                                raise repair_error
                        else:
                            raise repair_error
            except json.JSONDecodeError as e:
                # Final fallback - log full error and re-raise
                logger.error(f"JSON parsing failed after all attempts: {e}")
                logger.error(f"Error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
                logger.error(f"Response length: {len(result_text)} characters")
                logger.error(f"Response (first 2000 chars): {result_text[:2000]}")
                if len(result_text) > 2000:
                    logger.error(f"Response (last 500 chars): {result_text[-500:]}")
                raise
            
            logger.info("Successfully used Gemini fallback for contact analysis")
            return self._parse_recommendations(analysis, industry, rag_knowledge, contacts_map)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}. Response: {result_text[:500]}")
            return []
        except Exception as e:
            error_str = str(e)
            # Check for API key invalid errors
            if 'API key not valid' in error_str or 'API_KEY_INVALID' in error_str or 'API key' in error_str.lower():
                logger.error("=" * 60)
                logger.error("GEMINI API KEY ERROR - FALLING BACK TO OPENAI")
                logger.error("=" * 60)
                logger.error(f"Error: {error_str}")
                logger.error("The system will attempt to use OpenAI as a fallback if configured.")
                logger.error("To fix: Update GEMINI_API_KEY in .env.local and restart the application")
                logger.error("=" * 60)
                # Don't return empty list - let the caller handle fallback
                raise
            else:
                logger.error(f"Error analyzing contact batch with Gemini: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # For other errors, return empty list to allow fallback
                return []
    
    def _build_analysis_prompt(
        self,
        contacts: List[Dict[str, Any]],
        industry: str,
        industry_context: Any,
        rag_knowledge: Dict[str, Any],
        gemini_insights: Dict[str, Any]
    ) -> str:
        """Build OpenAI prompt for contact analysis"""
        
        # Format RAG knowledge with more detail
        rag_text = ""
        if rag_knowledge.get('case_studies'):
            rag_text += "=== RAG CASE STUDIES (Reference these in your analysis) ===\n"
            for i, cs in enumerate(rag_knowledge['case_studies'][:5], 1):
                title = cs.get('metadata', {}).get('title') if isinstance(cs, dict) else (cs.get('title') if isinstance(cs, dict) else str(cs)[:50])
                content = cs.get('document') if isinstance(cs, dict) else (cs.get('content') if isinstance(cs, dict) else str(cs))
                metadata = cs.get('metadata', {}) if isinstance(cs, dict) else {}
                company = metadata.get('company', '') if metadata else ''
                industry_info = metadata.get('industry', '') if metadata else ''
                rag_text += f"{i}. {title}"
                if company:
                    rag_text += f" (Company: {company})"
                if industry_info:
                    rag_text += f" (Industry: {industry_info})"
                rag_text += f"\n   Content: {str(content)[:300]}...\n\n"
        
        if rag_knowledge.get('services'):
            rag_text += "\n=== RAG SERVICES (Available solutions to recommend) ===\n"
            for i, svc in enumerate(rag_knowledge['services'][:5], 1):
                title = svc.get('metadata', {}).get('title') if isinstance(svc, dict) else (svc.get('title') if isinstance(svc, dict) else (svc.get('service_type') if isinstance(svc, dict) else str(svc)[:50]))
                content = svc.get('document') if isinstance(svc, dict) else (svc.get('content') if isinstance(svc, dict) else str(svc))
                metadata = svc.get('metadata', {}) if isinstance(svc, dict) else {}
                platform = metadata.get('platform', '') if metadata else ''
                rag_text += f"{i}. {title}"
                if platform:
                    rag_text += f" (Platform: {platform})"
                rag_text += f"\n   Description: {str(content)[:300]}...\n\n"
        
        if rag_knowledge.get('platforms'):
            rag_text += "\n=== RAG PLATFORMS (The AI Company platforms) ===\n"
            for i, platform in enumerate(rag_knowledge['platforms'][:5], 1):
                title = platform.get('metadata', {}).get('platform') if isinstance(platform, dict) else (platform.get('platform') if isinstance(platform, dict) else (platform.get('title') if isinstance(platform, dict) else str(platform)[:50]))
                content = platform.get('document') if isinstance(platform, dict) else (platform.get('content') if isinstance(platform, dict) else str(platform))
                rag_text += f"{i}. {title}\n   Description: {str(content)[:300]}...\n\n"
        
        if rag_knowledge.get('insights'):
            rag_text += "\n=== RAG INDUSTRY INSIGHTS ===\n"
            for i, insight in enumerate(rag_knowledge['insights'][:5], 1):
                content = insight.get('document') if isinstance(insight, dict) else (insight.get('content') if isinstance(insight, dict) else (insight.get('text') if isinstance(insight, dict) else str(insight)))
                rag_text += f"{i}. {str(content)[:300]}...\n\n"
        
        # Format knowledge base insights (from Gemini or other sources)
        gemini_text = ""
        if gemini_insights.get('customer_examples'):
            gemini_text += "Customer Examples:\n"
            for ex in gemini_insights['customer_examples'][:2]:
                gemini_text += f"- {ex.get('company', 'Customer')}: {ex.get('content', '')[:200]}...\n"
        
        if gemini_insights.get('industry_insights'):
            gemini_text += "\nIndustry Insights:\n"
            for insight in gemini_insights['industry_insights'][:3]:
                gemini_text += f"- {insight}\n"
        
        # Format contacts - IMPORTANT: Include contact_id so AI can return it
        contacts_text = ""
        for i, contact in enumerate(contacts):
            contact_id = contact.get('id', contact.get('contact_id', ''))
            contacts_text += f"\nContact {i+1} (ID: {contact_id}):\n"
            contacts_text += f"- Contact ID: {contact_id}\n"
            contacts_text += f"- Name: {contact.get('name', 'Unknown')}\n"
            contacts_text += f"- Role: {contact.get('role', 'Unknown')}\n"
            contacts_text += f"- Company: {contact.get('company', contact.get('company_name', 'Unknown'))}\n"
            contacts_text += f"- Email: {contact.get('email', 'N/A')}\n"
            contacts_text += f"- LinkedIn: {contact.get('linkedin', contact.get('linkedin_url', 'N/A'))}\n"
            contacts_text += f"- Industry: {contact.get('industry', industry)}\n"
        
        prompt = f"""You are an expert B2B sales analyst preparing a comprehensive target analysis report for the {industry} industry.

SOLUTIONS TO POSITION:
1. Onlyne Reputation (onlynereputation.com): Digital/AI reputation management, review generation, sentiment analysis, online brand protection
2. The AI Company (theaicompany.ngrok.app): GenAI Agentic Platform, Revenue Growth Platform, automation solutions, operational efficiency

INDUSTRY CONTEXT: {industry_context.display_name}
- Typical pain points: {', '.join(industry_context.pain_points[:5])}
- Common decision-makers: {', '.join(industry_context.common_roles[:5])}
- Industry-specific challenges: {', '.join(industry_context.challenges[:5])}

KNOWLEDGE BASE CONTEXT (RAG):
{rag_text if rag_text else "No RAG knowledge available"}

KNOWLEDGE BASE INSIGHTS:
{gemini_text if gemini_text else "No additional insights available"}

CONTACTS TO ANALYZE:
{contacts_text}

ANALYSIS REQUIREMENTS:
For each contact, provide a COMPREHENSIVE analysis similar to a B2B sales analysis report. Include:

1. **Detailed Company Profile**: Company size, revenue range, market position
2. **Identified Gaps**: 3-5 specific enterprise gaps (e.g., "Enterprise-scale reputation monitoring across 2,700+ employees", "Automation opportunities for SKU proliferation")
3. **Pain Points**: 3-5 industry-relevant pain points (e.g., "Rising labor and input costs", "Productivity optimization across manufacturing")
4. **Recommended Pitch Angle**: Strategic entry angle (1-2 sentences, reference RAG/Gemini examples)
5. **Business Case**: Why this company/contact is a good fit (scale, budget, strategic need)
6. **Reasoning**: Detailed explanation with industry context, RAG examples, and solution fit rationale

CRITICAL: You MUST use the exact "Contact ID" value from each contact above. Do NOT use indices or generate new IDs.

Return JSON in this format:
{{
  "recommendations": [
    {{
      "contact_id": "EXACT Contact ID from contact data (UUID string)",
      "contact_name": "Full name",
      "company_name": "Company name",
      "role": "Job title",
      "email": "email if available",
      "phone": "phone if available",
      "linkedin_url": "LinkedIn URL if available",
      "seniority_score": 0.0-1.0,
      "solution_fit": "onlyne_reputation | the_ai_company | both",
      "confidence_score": 0.0-1.0,
      "identified_gaps": ["Specific gap 1", "Specific gap 2", "Specific gap 3"],
      "recommended_pitch_angle": "Detailed strategic pitch angle (2-3 sentences)",
      "pain_points": ["Specific pain point 1", "Specific pain point 2", "Specific pain point 3"],
      "reasoning": "Comprehensive explanation (3-5 sentences) with industry context, RAG examples, company scale, and solution fit rationale"
    }}
  ]
}}

SENIORITY SCORING GUIDE:
- C-suite (MD/CEO/President) = 0.9-0.95
- VP/Director = 0.7-0.9
- Operational heads = 0.65-0.7
- Manager = 0.5-0.65

CONFIDENCE SCORING GUIDE:
- 0.90-0.95: Highest priority - C-suite authority, proven budget cycles, strong solution fit
- 0.80-0.89: High priority - C-suite, good solution fit, growth trajectory
- 0.70-0.79: Moderate-high - VP/operational head, clear pain point, escalation path
- 0.60-0.69: Moderate - operational validation, needs escalation

Focus on generating DETAILED, ACTIONABLE recommendations with specific gaps, pain points, and business cases. Reference RAG case studies and Gemini insights in your reasoning.

Return only valid JSON."""
        
        return prompt
    
    def generate_target_content(
        self,
        recommendation: TargetRecommendation,
        industry: str,
        industry_context: Any,
        rag_knowledge: Dict[str, Any],
        gemini_insights: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate pain point, pitch angle, and script for a target recommendation
        
        Returns:
            Dict with 'pain_point', 'pitch_angle', 'script'
        """
        try:
            prompt = self._build_content_generation_prompt(
                recommendation,
                industry,
                industry_context,
                rag_knowledge,
                gemini_insights
            )
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert B2B sales strategist. Generate compelling pain points, pitch angles, and outreach scripts. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            import json
            content = json.loads(result_text)
            
            return {
                'pain_point': content.get('pain_point', ''),
                'pitch_angle': content.get('pitch_angle', ''),
                'script': content.get('script', '')
            }
            
        except Exception as e:
            logger.error(f"Error generating target content: {e}")
            return {
                'pain_point': recommendation.pain_points[0] if recommendation.pain_points else '',
                'pitch_angle': recommendation.recommended_pitch_angle or '',
                'script': ''
            }
    
    def _build_content_generation_prompt(
        self,
        recommendation: TargetRecommendation,
        industry: str,
        industry_context: Any,
        rag_knowledge: Dict[str, Any],
        gemini_insights: Dict[str, Any]
    ) -> str:
        """Build prompt for content generation"""
        
        # Format examples from RAG and Gemini
        examples_text = ""
        if rag_knowledge.get('case_studies'):
            examples_text += "RAG Case Study Examples:\n"
            for cs in rag_knowledge['case_studies'][:2]:
                examples_text += f"- {cs.get('content', '')[:300]}...\n"
        
        # Only include Gemini examples if they exist and are meaningful
        # Note: This is used for content generation, not the main analysis
        if gemini_insights.get('customer_examples'):
            examples_text += "\nRelevant Customer Examples:\n"
            for ex in gemini_insights['customer_examples'][:2]:
                examples_text += f"- {ex.get('content', '')[:300]}...\n"
        
        prompt = f"""Generate personalized content for a target in the {industry} industry:

Contact: {recommendation.contact_name} ({recommendation.role}) at {recommendation.company_name}
Industry: {industry}
Solution Fit: {recommendation.solution_fit}
Identified Gaps: {', '.join(recommendation.identified_gaps[:3])}
Pain Points: {', '.join(recommendation.pain_points[:3])}

Industry Context:
- Pain Points: {', '.join(industry_context.pain_points[:3])}
- Challenges: {', '.join(industry_context.challenges[:3])}

{examples_text}

Generate:
1. pain_point: A specific, personalized pain point for this contact (1-2 sentences, industry-specific)
2. pitch_angle: Strategic entry angle for outreach (1-2 sentences, reference RAG/Gemini examples)
3. script: LinkedIn outreach script (3-4 sentences, professional, industry-appropriate, include specific examples)

Return JSON:
{{
  "pain_point": "...",
  "pitch_angle": "...",
  "script": "..."
}}"""
        
        return prompt


# Global instance
_target_identification_service = None

def get_target_identification_service() -> TargetIdentificationService:
    """Get or create the global target identification service instance"""
    global _target_identification_service
    if _target_identification_service is None:
        _target_identification_service = TargetIdentificationService()
    return _target_identification_service






