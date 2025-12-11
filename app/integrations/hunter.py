"""Hunter.io API integration for email verification, finding, and enrichment"""
import logging
import os
import requests
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class EmailStatus(Enum):
    """Email verification status from Hunter.io"""
    VALID = "valid"
    INVALID = "invalid"
    ACCEPT_ALL = "accept_all"
    WEBMAIL = "webmail"
    DISPOSABLE = "disposable"
    UNKNOWN = "unknown"


class HunterIOClient:
    """Client for Hunter.io API v2"""
    
    BASE_URL = "https://api.hunter.io/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Hunter.io client
        
        Args:
            api_key: Hunter.io API key. If not provided, will try to get from HUNTER_API_KEY env var
        """
        self.api_key = api_key or os.getenv('HUNTER_API_KEY')
        if not self.api_key:
            logger.warning("HUNTER_API_KEY not found - Hunter.io features will be disabled")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Hunter.io client initialized")
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Make a request to Hunter.io API
        
        Args:
            endpoint: API endpoint (e.g., '/email-verifier')
            params: Query parameters
            
        Returns:
            Response data dict or None if error
        """
        if not self.enabled:
            logger.debug("Hunter.io client not enabled, skipping request")
            return None
        
        if not params:
            params = {}
        params['api_key'] = self.api_key
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            # Handle rate limits and usage limits
            if response.status_code == 429:
                logger.warning("Hunter.io rate limit reached - too many requests")
                return None
            
            if response.status_code == 403:
                logger.warning("Hunter.io rate limit reached - check your plan limits")
                return None
            
            if response.status_code == 401:
                logger.error("Hunter.io API key invalid or missing")
                return None
            
            if response.status_code != 200:
                logger.warning(f"Hunter.io API error {response.status_code}: {response.text[:200]}")
                return None
            
            data = response.json()
            
            # Check for errors in response
            if 'errors' in data:
                error_msg = data['errors'][0].get('details', 'Unknown error') if data['errors'] else 'Unknown error'
                error_code = data['errors'][0].get('code', 0) if data['errors'] else 0
                logger.warning(f"Hunter.io API error (code {error_code}): {error_msg}")
                return None
            
            return data.get('data')
            
        except requests.exceptions.Timeout:
            logger.warning("Hunter.io API request timed out after 10 seconds")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Hunter.io API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling Hunter.io API: {e}")
            return None
    
    def verify_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Verify an email address
        
        Args:
            email: Email address to verify
            
        Returns:
            Dict with verification results:
            {
                'status': 'valid'|'invalid'|'accept_all'|'webmail'|'disposable'|'unknown',
                'result': 'deliverable'|'undeliverable'|'risky'|'unknown',
                'score': int (0-100),
                'sources': List of sources,
                'smtp_check': bool,
                'mx_records': List of MX records,
                'smtp_server': str,
                'smtp_check_disabled': bool
            }
            Returns None if verification fails or API is disabled
        """
        if not email or '@' not in email:
            return None
        
        logger.debug(f"Verifying email: {email}")
        data = self._make_request('/email-verifier', {'email': email})
        
        if not data:
            return None
        
        result = {
            'status': data.get('result', 'unknown'),
            'result': data.get('result', 'unknown'),
            'score': data.get('score', 0),
            'sources': data.get('sources', []),
            'smtp_check': data.get('smtp_check', False),
            'mx_records': data.get('mx_records', []),
            'smtp_server': data.get('smtp_server'),
            'smtp_check_disabled': data.get('smtp_check_disabled', False)
        }
        
        # Map result to status
        result_mapping = {
            'deliverable': EmailStatus.VALID.value,
            'undeliverable': EmailStatus.INVALID.value,
            'risky': EmailStatus.ACCEPT_ALL.value,
            'unknown': EmailStatus.UNKNOWN.value
        }
        result['status'] = result_mapping.get(result['result'], EmailStatus.UNKNOWN.value)
        
        logger.info(f"Email {email} verification: {result['status']} (score: {result['score']})")
        return result
    
    def find_email(self, domain: str, first_name: Optional[str] = None, last_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Find email address from domain and name
        
        Args:
            domain: Company domain
            first_name: First name
            last_name: Last name
            
        Returns:
            Dict with email finding results:
            {
                'email': str,
                'score': int (0-100),
                'sources': List of sources,
                'domain': str,
                'first_name': str,
                'last_name': str,
                'position': str,
                'company': str,
                'country': str,
                'linkedin_url': str,
                'twitter_url': str,
                'phone_number': str
            }
            Returns None if email not found or API is disabled
        """
        if not domain:
            return None
        
        params = {'domain': domain}
        if first_name:
            params['first_name'] = first_name
        if last_name:
            params['last_name'] = last_name
        
        logger.debug(f"Finding email for {first_name} {last_name} at {domain}")
        data = self._make_request('/email-finder', params)
        
        if not data:
            return None
        
        result = {
            'email': data.get('email'),
            'score': data.get('score', 0),
            'sources': data.get('sources', []),
            'domain': data.get('domain', domain),
            'first_name': data.get('first_name', first_name),
            'last_name': data.get('last_name', last_name),
            'position': data.get('position'),
            'company': data.get('company'),
            'country': data.get('country'),
            'linkedin_url': data.get('linkedin_url'),
            'twitter_url': data.get('twitter_url'),
            'phone_number': data.get('phone_number')
        }
        
        if result['email']:
            logger.info(f"Found email {result['email']} for {first_name} {last_name} at {domain} (score: {result['score']})")
        else:
            logger.debug(f"No email found for {first_name} {last_name} at {domain}")
        
        return result
    
    def domain_search(self, domain: str, limit: int = 10, seniority: Optional[str] = None, 
                     department: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search for emails in a domain
        
        Args:
            domain: Company domain
            limit: Number of results (1-100, default 10)
            seniority: Filter by seniority (junior, senior, executive, etc.)
            department: Filter by department (executive, it, finance, etc.)
            
        Returns:
            Dict with domain search results:
            {
                'domain': str,
                'disposable': bool,
                'webmail': bool,
                'pattern': str,
                'organization': str,
                'country': str,
                'emails': List[{
                    'value': str,
                    'type': str,
                    'confidence': int,
                    'sources': List,
                    'first_name': str,
                    'last_name': str,
                    'position': str,
                    'seniority': str,
                    'department': str,
                    'linkedin_url': str,
                    'twitter_url': str,
                    'phone_number': str
                }],
                'linked_domains': List[str]
            }
            Returns None if search fails or API is disabled
        """
        if not domain:
            return None
        
        params = {'domain': domain, 'limit': min(limit, 100)}
        if seniority:
            params['seniority'] = seniority
        if department:
            params['department'] = department
        
        logger.debug(f"Searching domain: {domain}")
        data = self._make_request('/domain-search', params)
        
        if not data:
            return None
        
        result = {
            'domain': data.get('domain', domain),
            'disposable': data.get('disposable', False),
            'webmail': data.get('webmail', False),
            'pattern': data.get('pattern'),
            'organization': data.get('organization'),
            'country': data.get('country'),
            'emails': data.get('emails', []),
            'linked_domains': data.get('linked_domains', [])
        }
        
        logger.info(f"Domain search for {domain}: found {len(result['emails'])} emails")
        return result
    
    def enrich_person(self, email: Optional[str] = None, domain: Optional[str] = None,
                     first_name: Optional[str] = None, last_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Enrich person data
        
        Args:
            email: Email address
            domain: Company domain
            first_name: First name
            last_name: Last name
            
        Returns:
            Dict with enriched person data:
            {
                'email': str,
                'first_name': str,
                'last_name': str,
                'position': str,
                'company': str,
                'country': str,
                'linkedin_url': str,
                'twitter_url': str,
                'phone_number': str,
                'company_size': str,
                'industry': str,
                'confidence_score': int
            }
            Returns None if enrichment fails or API is disabled
        """
        params = {}
        if email:
            params['email'] = email
        if domain:
            params['domain'] = domain
        if first_name:
            params['first_name'] = first_name
        if last_name:
            params['last_name'] = last_name
        
        if not params:
            return None
        
        logger.debug(f"Enriching person data: {params}")
        data = self._make_request('/enrichment', params)
        
        if not data:
            return None
        
        result = {
            'email': data.get('email', email),
            'first_name': data.get('first_name', first_name),
            'last_name': data.get('last_name', last_name),
            'position': data.get('position'),
            'company': data.get('company'),
            'country': data.get('country'),
            'linkedin_url': data.get('linkedin_url'),
            'twitter_url': data.get('twitter_url'),
            'phone_number': data.get('phone_number'),
            'company_size': data.get('company_size'),
            'industry': data.get('industry'),
            'confidence_score': data.get('confidence_score', 0)
        }
        
        logger.info(f"Enriched person data for {email or f'{first_name} {last_name}'}")
        return result
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account information and remaining API calls
        
        Returns:
            Dict with account info:
            {
                'email': str,
                'plan_name': str,
                'plan_type': str,
                'reset_date': str,
                'calls': {
                    'used': int,
                    'available': int,
                    'limit': int
                }
            }
            Returns None if request fails
        """
        logger.debug("Getting Hunter.io account info")
        data = self._make_request('/account')
        
        if not data:
            return None
        
        return {
            'email': data.get('email'),
            'plan_name': data.get('plan_name'),
            'plan_type': data.get('plan_type'),
            'reset_date': data.get('reset_date'),
            'calls': data.get('calls', {})
        }


# Global instance
_hunter_client = None


def get_hunter_client() -> HunterIOClient:
    """Get or create the global Hunter.io client instance"""
    global _hunter_client
    if _hunter_client is None:
        _hunter_client = HunterIOClient()
    return _hunter_client

