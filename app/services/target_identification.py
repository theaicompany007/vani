"""AI-powered target identification service"""
import logging
import os
from typing import List, Optional, Dict, Any
from openai import OpenAI
from app.models.target_recommendation import TargetRecommendation
from app.services.industry_context import get_industry_context
from app.integrations.rag_client import get_rag_client
from app.integrations.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)


class TargetIdentificationService:
    """Service for AI-powered target identification"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.openai_client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.rag_client = get_rag_client()
        self.gemini_client = get_gemini_client()
    
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
            
            if len(recommendations) >= limit:
                break
        
        # Filter by min_seniority and sort by confidence
        filtered = [
            r for r in recommendations
            if r.seniority_score >= min_seniority
        ]
        
        # Sort by confidence score (descending)
        sorted_recommendations = sorted(
            filtered,
            key=lambda x: x.confidence_score,
            reverse=True
        )
        
        return sorted_recommendations[:limit]
    
    def _get_rag_knowledge(self, industry: str) -> Dict[str, Any]:
        """Get RAG knowledge for industry"""
        try:
            # Query case studies
            case_studies = self.rag_client.query_case_studies(industry, top_k=3)
            
            # Query services
            services = self.rag_client.query_services(industry, top_k=3)
            
            # Query industry insights
            insights = self.rag_client.query_industry_insights(industry, top_k=3)
            
            return {
                'case_studies': case_studies,
                'services': services,
                'insights': insights
            }
        except Exception as e:
            logger.warning(f"Failed to get RAG knowledge: {e}")
            return {
                'case_studies': [],
                'services': [],
                'insights': []
            }
    
    def _get_gemini_insights(self, industry: str) -> Dict[str, Any]:
        """Get Gemini/Notebook LM insights for industry"""
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
        """Analyze a batch of contacts using OpenAI"""
        try:
            # Build prompt with all context
            prompt = self._build_analysis_prompt(
                contacts,
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
            import json
            analysis = json.loads(result_text)
            
            # Parse recommendations
            recommendations = []
            if 'recommendations' in analysis:
                for rec_data in analysis['recommendations']:
                    try:
                        recommendation = TargetRecommendation(
                            contact_id=rec_data.get('contact_id', ''),
                            contact_name=rec_data.get('contact_name', ''),
                            company_name=rec_data.get('company_name', ''),
                            role=rec_data.get('role'),
                            email=rec_data.get('email'),
                            phone=rec_data.get('phone'),
                            linkedin_url=rec_data.get('linkedin_url'),
                            seniority_score=float(rec_data.get('seniority_score', 0.5)),
                            solution_fit=rec_data.get('solution_fit', 'both'),
                            confidence_score=float(rec_data.get('confidence_score', 0.5)),
                            identified_gaps=rec_data.get('identified_gaps', []),
                            recommended_pitch_angle=rec_data.get('recommended_pitch_angle'),
                            pain_points=rec_data.get('pain_points', []),
                            reasoning=rec_data.get('reasoning', ''),
                            industry=industry
                        )
                        recommendations.append(recommendation)
                    except Exception as e:
                        logger.warning(f"Failed to parse recommendation: {e}")
                        continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error analyzing contact batch: {e}")
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
        
        # Format RAG knowledge
        rag_text = ""
        if rag_knowledge.get('case_studies'):
            rag_text += "RAG Case Studies:\n"
            for cs in rag_knowledge['case_studies'][:3]:
                rag_text += f"- {cs.get('title', 'Case Study')}: {cs.get('content', '')[:200]}...\n"
        
        if rag_knowledge.get('services'):
            rag_text += "\nRAG Services:\n"
            for svc in rag_knowledge['services'][:3]:
                rag_text += f"- {svc.get('title', 'Service')}: {svc.get('content', '')[:200]}...\n"
        
        if rag_knowledge.get('insights'):
            rag_text += "\nRAG Industry Insights:\n"
            for insight in rag_knowledge['insights'][:3]:
                rag_text += f"- {insight.get('content', '')[:200]}...\n"
        
        # Format Gemini insights
        gemini_text = ""
        if gemini_insights.get('customer_examples'):
            gemini_text += "Gemini Customer Examples:\n"
            for ex in gemini_insights['customer_examples'][:2]:
                gemini_text += f"- {ex.get('company', 'Customer')}: {ex.get('content', '')[:200]}...\n"
        
        if gemini_insights.get('industry_insights'):
            gemini_text += "\nGemini Industry Insights:\n"
            for insight in gemini_insights['industry_insights'][:3]:
                gemini_text += f"- {insight}\n"
        
        # Format contacts
        contacts_text = ""
        for i, contact in enumerate(contacts):
            contacts_text += f"\nContact {i+1}:\n"
            contacts_text += f"- Name: {contact.get('name', 'Unknown')}\n"
            contacts_text += f"- Role: {contact.get('role', 'Unknown')}\n"
            contacts_text += f"- Company: {contact.get('company', contact.get('company_name', 'Unknown'))}\n"
            contacts_text += f"- Email: {contact.get('email', 'N/A')}\n"
            contacts_text += f"- LinkedIn: {contact.get('linkedin', contact.get('linkedin_url', 'N/A'))}\n"
            contacts_text += f"- Industry: {contact.get('industry', industry)}\n"
        
        prompt = f"""You are analyzing contacts in the {industry} industry to identify high-value targets for two solutions:

1. Onlyne Reputation (onlynereputation.com): Digital/AI reputation management, review generation, sentiment analysis
2. The AI Company (theaicompany.ngrok.app): GenAI Agentic Platform, Revenue Growth Platform, automation solutions

Industry Context: {industry_context.display_name}
- Typical pain points: {', '.join(industry_context.pain_points[:3])}
- Common decision-makers: {', '.join(industry_context.common_roles[:3])}
- Industry-specific challenges: {', '.join(industry_context.challenges[:3])}

{rag_text}

{gemini_text}

Contacts to Analyze:
{contacts_text}

For each contact, analyze and return JSON with:
{{
  "recommendations": [
    {{
      "contact_id": "contact UUID",
      "contact_name": "Full name",
      "company_name": "Company name",
      "role": "Job title",
      "email": "email if available",
      "phone": "phone if available",
      "linkedin_url": "LinkedIn URL if available",
      "seniority_score": 0.0-1.0,  // Industry-appropriate: C-suite=0.9+, VP=0.7-0.9, Director=0.5-0.7
      "solution_fit": "onlyne_reputation | the_ai_company | both",
      "confidence_score": 0.0-1.0,
      "identified_gaps": ["gap1", "gap2"],  // Industry-specific enterprise gaps
      "recommended_pitch_angle": "Industry-specific outreach strategy",
      "pain_points": ["pain1", "pain2"],  // Industry-relevant pain points
      "reasoning": "Brief explanation with industry context and RAG/Gemini examples"
    }}
  ]
}}

Focus on:
- Seniority appropriate for {industry} industry
- Solution fit based on industry patterns and RAG/Gemini examples
- Industry-specific gaps and pain points
- High confidence recommendations only

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
        
        if gemini_insights.get('customer_examples'):
            examples_text += "\nGemini Customer Examples:\n"
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





