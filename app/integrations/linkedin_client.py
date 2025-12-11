"""LinkedIn integration for sending messages"""
import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LinkedInClient:
    """LinkedIn API client wrapper
    
    Note: LinkedIn messaging requires OAuth 2.0 authentication and API access.
    This is a placeholder implementation that can be extended with actual LinkedIn API.
    """
    
    def __init__(self):
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI')
        self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')  # OAuth token
        
        if not self.client_id or not self.client_secret:
            logger.warning("LinkedIn credentials not configured")
    
    def send_message(
        self,
        recipient_urn: str,  # LinkedIn URN (e.g., "urn:li:person:123456")
        message: str,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a LinkedIn message using LinkedIn Messaging API v2
        
        Args:
            recipient_urn: LinkedIn URN of the recipient (e.g., "urn:li:person:123456")
            message: Message content (plain text or HTML)
            subject: Optional subject line
            
        Returns:
            Response dict with success status and message ID
        """
        if not self.access_token:
            return {
                'success': False,
                'error': 'LinkedIn access token not configured. OAuth authentication required.'
            }
        
        if not recipient_urn:
            return {
                'success': False,
                'error': 'Recipient URN is required'
            }
        
        try:
            # Step 1: Find or create a conversation
            # LinkedIn requires finding an existing conversation or creating a new one
            conversation_url = "https://api.linkedin.com/v2/messaging/conversations"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            # Try to find existing conversation
            # Note: LinkedIn API may require different approach based on API version
            # For now, we'll attempt to create a new conversation and send message
            
            # Step 2: Create conversation (if needed) and send message
            # LinkedIn Messaging API v2 structure
            conversation_payload = {
                "participants": [recipient_urn],
                "eventCreate": {
                    "value": {
                        "com.linkedin.common.MessageCreate": {
                            "body": message,
                            "subject": subject or "Project VANI Outreach",
                            "attachments": []
                        }
                    }
                }
            }
            
            response = requests.post(conversation_url, headers=headers, json=conversation_payload)
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                return {
                    'success': True,
                    'message_id': response_data.get('id') or response_data.get('value', {}).get('id'),
                    'conversation_id': response_data.get('id'),
                    'response': response_data
                }
            else:
                error_msg = response.text
                logger.error(f"LinkedIn API error ({response.status_code}): {error_msg}")
                
                # Try alternative approach: Use messaging/conversations endpoint
                if response.status_code == 400 or response.status_code == 404:
                    # Alternative: Try direct messaging endpoint
                    alt_url = f"https://api.linkedin.com/v2/messaging/conversations?action=create"
                    alt_payload = {
                        "recipients": [recipient_urn],
                        "subject": subject or "Project VANI Outreach",
                        "body": message
                    }
                    
                    alt_response = requests.post(alt_url, headers=headers, json=alt_payload)
                    if alt_response.status_code in [200, 201]:
                        return {
                            'success': True,
                            'message_id': alt_response.json().get('id'),
                            'response': alt_response.json()
                        }
                
                return {
                    'success': False,
                    'error': f"LinkedIn API error ({response.status_code}): {error_msg}",
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"LinkedIn API request failed: {str(e)}")
            return {
                'success': False,
                'error': f"Network error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Failed to send LinkedIn message: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_profile(self, person_urn: str) -> Dict[str, Any]:
        """Get LinkedIn profile information"""
        if not self.access_token:
            return {
                'success': False,
                'error': 'LinkedIn access token not configured'
            }
        
        try:
            url = f"https://api.linkedin.com/v2/people/{person_urn}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'profile': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': response.text
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def is_configured(self) -> bool:
        """Check if LinkedIn is properly configured"""
        return bool(self.client_id and self.client_secret and self.access_token)
    
    def extract_urn_from_url(self, linkedin_url: str) -> Optional[str]:
        """
        Extract LinkedIn URN from a LinkedIn profile URL
        
        Args:
            linkedin_url: LinkedIn profile URL (e.g., "https://www.linkedin.com/in/johndoe/")
            
        Returns:
            LinkedIn URN if extractable, None otherwise
        """
        if not linkedin_url:
            return None
        
        # If already a URN, return as-is
        if linkedin_url.startswith('urn:li:'):
            return linkedin_url
        
        # Try to extract from URL
        # Note: LinkedIn URNs require API access to resolve from URLs
        # For now, we'll need the URN directly or use the profile lookup
        try:
            # LinkedIn profile URLs typically: https://www.linkedin.com/in/username/
            # We'd need to use the Profile API to get the URN from username
            # For now, return None and require URN directly
            logger.warning(f"Cannot extract URN from URL: {linkedin_url}. Please provide URN directly.")
            return None
        except Exception as e:
            logger.error(f"Error extracting URN from URL: {e}")
            return None

