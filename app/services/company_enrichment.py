"""Company enrichment service using OpenAI to get company details from domain"""
import logging
import os
from typing import Optional, Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class CompanyEnrichmentService:
    """Service to enrich company data using OpenAI from domain"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OPENAI_API_KEY not found - company enrichment will be disabled")
            self.client = None
            self.model = None
        else:
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    def enrich_from_domain(
        self,
        domain: str,
        existing_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Enrich company data from domain using OpenAI.
        
        Args:
            domain: Company domain (e.g., 'example.com')
            existing_name: Optional existing company name to validate/improve
            
        Returns:
            Dict with enriched company data: {name, industry, location, description}
            Returns None if enrichment fails or OpenAI is not configured
        """
        if not self.client:
            logger.debug("OpenAI client not available, skipping enrichment")
            return None
        
        if not domain:
            return None
        
        try:
            # Build prompt for company enrichment
            prompt = f"""Given the domain "{domain}", provide company information in JSON format.

If you know this company, return:
{{
    "name": "Official company name",
    "industry": "Primary industry/sector",
    "location": "Headquarters location (city, country)",
    "description": "Brief company description (1-2 sentences)"
}}

If you don't recognize this domain or it's a generic email provider (gmail.com, outlook.com, etc.), return:
{{
    "name": null,
    "industry": null,
    "location": null,
    "description": null,
    "error": "Unknown or generic domain"
}}

Requirements:
- Use real, verifiable information only
- If uncertain, set fields to null rather than guessing
- For generic email providers, return null for all fields
- Keep descriptions concise (max 200 characters)

Domain: {domain}
"""
            
            if existing_name:
                prompt += f"\nNote: There's an existing company name '{existing_name}' - validate if it matches the domain and use the more accurate name."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a business intelligence assistant. Provide accurate company information based on domain names. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            enriched_data = json.loads(result_text)
            
            # Validate and clean the data
            if enriched_data.get('error') == "Unknown or generic domain":
                logger.debug(f"Domain {domain} is generic or unknown, skipping enrichment")
                return None
            
            # Only return if we got useful data
            if enriched_data.get('name') or enriched_data.get('industry'):
                logger.info(f"Enriched company data for domain {domain}: name={enriched_data.get('name')}, industry={enriched_data.get('industry')}")
                return {
                    'name': enriched_data.get('name'),
                    'industry': enriched_data.get('industry'),
                    'location': enriched_data.get('location'),
                    'description': enriched_data.get('description')
                }
            else:
                logger.debug(f"No useful enrichment data for domain {domain}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to enrich company from domain {domain}: {e}")
            return None
    
    def enrich_contact_from_linkedin(
        self,
        linkedin_url: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Enrich contact data from LinkedIn URL using OpenAI.
        Note: This uses OpenAI's knowledge, not actual LinkedIn API access.
        
        Args:
            linkedin_url: LinkedIn profile URL
            name: Contact name
            email: Contact email
            
        Returns:
            Dict with enriched contact data: {role, company, industry, location}
        """
        if not self.client:
            return None
        
        # For now, we'll use OpenAI to extract info from LinkedIn URL if provided
        # In the future, this could integrate with LinkedIn API or web scraping
        
        if not linkedin_url and not (name and email):
            return None
        
        try:
            prompt = f"""Given the following contact information, provide enriched contact details in JSON format.

Contact Info:
- Name: {name or 'Unknown'}
- Email: {email or 'Unknown'}
- LinkedIn: {linkedin_url or 'Not provided'}

If you can infer or know information about this person, return:
{{
    "role": "Job title/role",
    "company": "Current company name",
    "industry": "Company industry",
    "location": "Location (city, country)"
}}

If you cannot determine reliable information, return:
{{
    "role": null,
    "company": null,
    "industry": null,
    "location": null,
    "error": "Insufficient information"
}}

Requirements:
- Use only information that can be reasonably inferred from the provided data
- If uncertain, set fields to null
- Keep it factual and accurate

Return only valid JSON."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a contact enrichment assistant. Extract and infer contact information from provided data. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            import json
            enriched_data = json.loads(result_text)
            
            if enriched_data.get('error') == "Insufficient information":
                return None
            
            if any(enriched_data.get(k) for k in ['role', 'company', 'industry', 'location']):
                logger.info(f"Enriched contact data: {enriched_data}")
                return enriched_data
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to enrich contact: {e}")
            return None


# Global instance
_enrichment_service = None

def get_enrichment_service() -> CompanyEnrichmentService:
    """Get or create the global enrichment service instance"""
    global _enrichment_service
    if _enrichment_service is None:
        _enrichment_service = CompanyEnrichmentService()
    return _enrichment_service



















