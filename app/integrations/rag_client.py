"""RAG service client for querying rag.theaicompany.co"""
import os
import logging
import requests
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class RAGClient:
    """Client for querying RAG service at rag.theaicompany.co"""
    
    def __init__(self):
        self.service_url = os.getenv('RAG_SERVICE_URL', 'https://rag.theaicompany.co')
        self.api_key = os.getenv('RAG_API_KEY')
        
        if not self.api_key:
            logger.warning("RAG_API_KEY not found - RAG queries will be disabled")
            self.enabled = False
        else:
            self.enabled = True
    
    def query(
        self,
        query: str,
        industry: Optional[str] = None,
        collections: Optional[List[str]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Query RAG service for relevant content
        
        Args:
            query: Search query text
            industry: Optional industry filter for metadata
            collections: List of collection names to search (default: all relevant collections)
            top_k: Number of results per collection
            
        Returns:
            Dict with query results organized by collection
        """
        if not self.enabled:
            logger.debug("RAG service not enabled, returning empty results")
            return {
                'query': query,
                'results': {},
                'total_results': 0
            }
        
        if not collections:
            collections = ['case_studies', 'services', 'company_profiles', 'industry_insights']
        
        try:
            # Build request payload
            payload = {
                'query': query,
                'collections': collections,
                'top_k': top_k
            }
            
            # Add industry filter to metadata if provided
            if industry:
                payload['contact_context'] = {
                    'industry': industry
                }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
                'x-api-key': self.api_key
            }
            
            # Try /rag/query endpoint first, fallback to /query
            endpoints = [
                f"{self.service_url}/rag/query",
                f"{self.service_url}/query"
            ]
            
            last_error = None
            for endpoint in endpoints:
                try:
                    response = requests.post(
                        endpoint,
                        json=payload,
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.debug(f"RAG query successful: {data.get('total_results', 0)} results")
                        return data
                    elif response.status_code != 404:
                        # 404 means endpoint doesn't exist, try next one
                        last_error = f"HTTP {response.status_code}: {response.text}"
                        break
                        
                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    continue
            
            logger.warning(f"RAG query failed: {last_error}")
            return {
                'query': query,
                'results': {},
                'total_results': 0,
                'error': last_error
            }
            
        except Exception as e:
            logger.error(f"Error querying RAG service: {e}")
            return {
                'query': query,
                'results': {},
                'total_results': 0,
                'error': str(e)
            }
    
    def query_case_studies(
        self,
        industry: Optional[str] = None,
        query: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Query case studies collection"""
        search_query = query or f"{industry} case study success story" if industry else "case study"
        result = self.query(search_query, industry, ['case_studies'], top_k)
        return result.get('results', {}).get('case_studies', [])
    
    def query_services(
        self,
        industry: Optional[str] = None,
        query: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Query services collection"""
        search_query = query or f"{industry} service solution" if industry else "service"
        result = self.query(search_query, industry, ['services'], top_k)
        return result.get('results', {}).get('services', [])
    
    def query_industry_insights(
        self,
        industry: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Query industry insights collection"""
        result = self.query(f"{industry} industry insights pain points challenges", industry, ['industry_insights'], top_k)
        return result.get('results', {}).get('industry_insights', [])


# Global instance
_rag_client = None

def get_rag_client() -> RAGClient:
    """Get or create the global RAG client instance"""
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGClient()
    return _rag_client

















