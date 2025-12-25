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
        
        # If no collections specified, fetch all available collections from RAG service
        if not collections:
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}',
                    'x-api-key': self.api_key
                }
                # Try multiple endpoints to get collections
                collection_endpoints = [
                    f"{self.service_url}/rag/collections",
                    f"{self.service_url}/collections",
                    f"{self.service_url}/api/collections"
                ]
                
                for endpoint in collection_endpoints:
                    try:
                        response = requests.get(endpoint, headers=headers, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            logger.debug(f"Raw collections response from RAG service: {type(data)} - {data}")
                            
                            # Handle different response formats
                            fetched_collections = []
                            if isinstance(data, list):
                                fetched_collections = data
                                logger.debug("Collections response is a list")
                            elif isinstance(data, dict):
                                # Handle different dict response formats
                                # Check if there's a 'collections' key with nested dict structure
                                # Format: {'collections': {'case_studies': {'count': 5}, ...}, 'total_collections': 12}
                                if 'collections' in data and isinstance(data['collections'], dict):
                                    collections_dict = data['collections']
                                    # Check if the nested dict has values that are dicts (with 'count' keys)
                                    first_nested_value = next(iter(collections_dict.values())) if collections_dict else None
                                    if first_nested_value and isinstance(first_nested_value, dict):
                                        # Extract collection names from the nested dict keys
                                        fetched_collections = list(collections_dict.keys())
                                        logger.debug(f"Extracted collection names from nested 'collections' dict: {fetched_collections}")
                                    else:
                                        # The 'collections' value might be a list
                                        fetched_collections = collections_dict if isinstance(collections_dict, list) else []
                                else:
                                    # Check if top-level values are dicts (format: {'case_studies': {'count': 5}})
                                    sample_value = next(iter(data.values())) if data else None
                                    if data and sample_value and isinstance(sample_value, dict):
                                        # Check if nested value is also a dict (indicating {'collection': {'count': N}})
                                        first_nested = next(iter(sample_value.values())) if sample_value else None
                                        if first_nested and isinstance(first_nested, dict):
                                            # This is the nested format, extract from top-level keys
                                            fetched_collections = list(data.keys())
                                        else:
                                            # Top-level dict with simple values, extract keys
                                            fetched_collections = list(data.keys())
                                        logger.debug(f"Extracted collection names from dict format: {fetched_collections}")
                                    else:
                                        # Try common keys for list of collections
                                        fetched_collections = data.get('collections') or data.get('data') or data.get('result') or data.get('items') or []
                                        logger.debug(f"Tried common keys, got: {fetched_collections}")
                            else:
                                fetched_collections = []
                                logger.debug(f"Unexpected response type: {type(data)}")
                            
                            if fetched_collections and isinstance(fetched_collections, list):
                                collections = fetched_collections
                                logger.info(f"Fetched {len(collections)} collections from RAG service: {collections}")
                                break
                            else:
                                logger.warning(f"Failed to extract collections list. Got: {type(fetched_collections)} - {fetched_collections}")
                    except Exception as e:
                        logger.debug(f"Failed to fetch collections from {endpoint}: {e}")
                        continue
                
                # Fallback to default collections if fetching failed
                if not collections:
                    logger.warning("Could not fetch collections from RAG service, using default collections")
                    logger.warning("NOTE: Google Drive collections may not be included in default list")
                    collections = ['case_studies', 'services', 'company_profiles', 'industry_insights']
            except Exception as e:
                logger.warning(f"Error fetching collections: {e}, using default collections")
                collections = ['case_studies', 'services', 'company_profiles', 'industry_insights']
        
        # Final safety check: ensure collections is a list before building payload
        if collections and isinstance(collections, dict):
            logger.warning(f"RAG Client: Collections is still a dict! Converting to list. Dict keys: {list(collections.keys())[:5]}...")
            collections = list(collections.keys())
            logger.info(f"RAG Client: Converted to list: {collections}")
        elif collections and not isinstance(collections, list):
            logger.error(f"RAG Client: Collections is not a list! Type: {type(collections)}")
            collections = None
        
        try:
            # Build request payload
            payload = {
                'query': query,
                'collections': collections,
                'top_k': top_k
            }
            
            logger.debug(f"RAG query payload: query='{query}', collections={collections}, top_k={top_k}")
            
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
                        total_results = data.get('total_results', 0)
                        logger.info(f"RAG query successful: {total_results} results from {len(collections)} collections: {collections}")
                        logger.debug(f"RAG query response: {data}")
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

















