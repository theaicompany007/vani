"""Signature formatting utility for different channels"""
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SignatureFormatter:
    """Format signatures for different communication channels"""
    
    @staticmethod
    def format_for_email(signature: Dict[str, Any]) -> str:
        """
        Format signature for email (HTML format)
        
        Args:
            signature: Signature profile dict with fields:
                - from_name: Sender name
                - from_email: Sender email
                - signature_json: JSON with title, company, phone, etc.
                - calendar_link: Optional calendar link
                - cta_text: Optional CTA text
                - cta_button: Optional CTA button text
                
        Returns:
            HTML formatted signature string
        """
        if not signature:
            return ''
        
        sig_html = '<div style="margin-top:24px;padding-top:24px;border-top:1px solid #e5e7eb">'
        
        # From name
        if signature.get('from_name'):
            sig_html += f'<div style="font-weight:600;margin-bottom:4px;color:#111111">{_escape_html(signature["from_name"])}</div>'
        
        # Title and company from signature_json
        sig_json = signature.get('signature_json', {})
        if isinstance(sig_json, str):
            import json
            try:
                sig_json = json.loads(sig_json)
            except:
                sig_json = {}
        
        if sig_json.get('title'):
            sig_html += f'<div style="color:#666666;font-size:13px;margin-bottom:2px">{_escape_html(sig_json["title"])}</div>'
        
        if sig_json.get('company'):
            sig_html += f'<div style="color:#666666;font-size:13px;margin-bottom:2px">{_escape_html(sig_json["company"])}</div>'
        
        # Email
        if signature.get('from_email'):
            sig_html += f'<div style="color:#666666;font-size:13px;margin-bottom:8px">{_escape_html(signature["from_email"])}</div>'
        
        # Phone
        if sig_json.get('phone'):
            sig_html += f'<div style="color:#666666;font-size:13px;margin-bottom:4px">📞 {_escape_html(sig_json["phone"])}</div>'
        
        # Website
        if sig_json.get('website'):
            website = sig_json["website"]
            if not website.startswith('http'):
                website = f'https://{website}'
            sig_html += f'<div style="color:#666666;font-size:13px;margin-bottom:4px">🌐 <a href="{_escape_html(website)}" style="color:#0a66c2;text-decoration:underline">{_escape_html(website)}</a></div>'
        
        # LinkedIn
        if sig_json.get('linkedin'):
            linkedin = sig_json["linkedin"]
            if not linkedin.startswith('http'):
                linkedin = f'https://{linkedin}'
            sig_html += f'<div style="color:#666666;font-size:13px;margin-bottom:4px">💼 <a href="{_escape_html(linkedin)}" style="color:#0a66c2;text-decoration:underline">LinkedIn</a></div>'
        
        # Calendar CTA
        if signature.get('calendar_link'):
            cta_text = signature.get('cta_text') or "Let's schedule a time to talk:"
            cta_button = signature.get('cta_button') or "Schedule a Meeting"
            sig_html += '<div style="margin-top:12px;padding:12px;background-color:#f9fafb;border-radius:6px">'
            sig_html += f'<div style="color:#374151;font-size:14px;margin-bottom:8px">{_escape_html(cta_text)}</div>'
            sig_html += f'<a href="{_escape_html(signature["calendar_link"])}" style="display:inline-block;padding:10px 20px;background-color:#0a66c2;color:#ffffff;text-decoration:none;border-radius:6px;font-weight:600">{_escape_html(cta_button)}</a>'
            sig_html += '</div>'
        
        sig_html += '</div>'
        
        return sig_html
    
    @staticmethod
    def format_for_whatsapp(signature: Dict[str, Any]) -> str:
        """
        Format signature for WhatsApp (plain text, concise)
        
        Args:
            signature: Signature profile dict
            
        Returns:
            Plain text signature string
        """
        if not signature:
            return ''
        
        lines = []
        
        # From name
        if signature.get('from_name'):
            lines.append(signature['from_name'])
        
        # Title and company
        sig_json = signature.get('signature_json', {})
        if isinstance(sig_json, str):
            import json
            try:
                sig_json = json.loads(sig_json)
            except:
                sig_json = {}
        
        title_company = []
        if sig_json.get('title'):
            title_company.append(sig_json['title'])
        if sig_json.get('company'):
            title_company.append(sig_json['company'])
        
        if title_company:
            lines.append(' | '.join(title_company))
        
        # Contact info (concise)
        contact_info = []
        if signature.get('from_email'):
            contact_info.append(f"📧 {signature['from_email']}")
        if sig_json.get('phone'):
            contact_info.append(f"📞 {sig_json['phone']}")
        if sig_json.get('website'):
            website = sig_json['website']
            if not website.startswith('http'):
                website = f'https://{website}'
            contact_info.append(f"🌐 {website}")
        
        if contact_info:
            lines.append(' | '.join(contact_info))
        
        # Calendar link (if available)
        if signature.get('calendar_link'):
            lines.append(f"📅 Schedule: {signature['calendar_link']}")
        
        return '\n'.join(lines) if lines else ''
    
    @staticmethod
    def format_for_linkedin(signature: Dict[str, Any]) -> str:
        """
        Format signature for LinkedIn (professional, concise)
        
        Args:
            signature: Signature profile dict
            
        Returns:
            Plain text signature string
        """
        if not signature:
            return ''
        
        lines = []
        
        # From name
        if signature.get('from_name'):
            lines.append(f"Best regards,\n{signature['from_name']}")
        else:
            lines.append("Best regards,")
        
        # Title and company
        sig_json = signature.get('signature_json', {})
        if isinstance(sig_json, str):
            import json
            try:
                sig_json = json.loads(sig_json)
            except:
                sig_json = {}
        
        if sig_json.get('title'):
            lines.append(sig_json['title'])
        if sig_json.get('company'):
            lines.append(sig_json['company'])
        
        # Contact info
        if signature.get('from_email'):
            lines.append(f"Email: {signature['from_email']}")
        if sig_json.get('phone'):
            lines.append(f"Phone: {sig_json['phone']}")
        if sig_json.get('website'):
            website = sig_json['website']
            if not website.startswith('http'):
                website = f'https://{website}'
            lines.append(f"Website: {website}")
        
        # LinkedIn profile
        if sig_json.get('linkedin'):
            linkedin = sig_json['linkedin']
            if not linkedin.startswith('http'):
                linkedin = f'https://{linkedin}'
            lines.append(f"LinkedIn: {linkedin}")
        
        return '\n'.join(lines) if lines else ''
    
    @staticmethod
    def format_for_channel(signature: Dict[str, Any], channel: str) -> str:
        """
        Format signature for a specific channel
        
        Args:
            signature: Signature profile dict
            channel: 'email', 'whatsapp', or 'linkedin'
            
        Returns:
            Formatted signature string
        """
        channel = channel.lower()
        
        if channel == 'email':
            return SignatureFormatter.format_for_email(signature)
        elif channel == 'whatsapp':
            return SignatureFormatter.format_for_whatsapp(signature)
        elif channel == 'linkedin':
            return SignatureFormatter.format_for_linkedin(signature)
        else:
            logger.warning(f"Unknown channel: {channel}, using email format")
            return SignatureFormatter.format_for_email(signature)


def _escape_html(text: str) -> str:
    """Escape HTML special characters"""
    if not text:
        return ''
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))




