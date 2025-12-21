"""Health check API endpoint for system status"""
from flask import Blueprint, jsonify, current_app
import logging
import os
import requests
from app.supabase_client import get_supabase_client
from app.auth import get_supabase_auth_client

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)


@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """Check system health and return status - No auth required for health checks"""
    try:
        status = {
            'overall': 'operational',
            'services': {},
            'message': 'All systems operational'
        }
        
        all_healthy = True
        
        # Check Supabase Database
        try:
            supabase = get_supabase_client(current_app)
            if supabase:
                # Try a simple query
                result = supabase.table('industries').select('id').limit(1).execute()
                status['services']['database'] = {
                    'status': 'operational',
                    'message': 'Database connection successful'
                }
            else:
                status['services']['database'] = {
                    'status': 'degraded',
                    'message': 'Database client not configured'
                }
                all_healthy = False
        except Exception as e:
            status['services']['database'] = {
                'status': 'offline',
                'message': f'Database error: {str(e)[:100]}'
            }
            all_healthy = False
        
        # Check Supabase Auth
        try:
            auth_client = get_supabase_auth_client()
            if auth_client:
                status['services']['auth'] = {
                    'status': 'operational',
                    'message': 'Authentication service available'
                }
            else:
                status['services']['auth'] = {
                    'status': 'degraded',
                    'message': 'Auth client not configured'
                }
                all_healthy = False
        except Exception as e:
            status['services']['auth'] = {
                'status': 'offline',
                'message': f'Auth error: {str(e)[:100]}'
            }
            all_healthy = False
        
        # Check OpenAI API (if configured)
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                # Just check if key exists and looks valid (starts with sk-)
                if openai_key.startswith('sk-'):
                    status['services']['openai'] = {
                        'status': 'operational',
                        'message': 'OpenAI API key configured'
                    }
                else:
                    status['services']['openai'] = {
                        'status': 'degraded',
                        'message': 'OpenAI API key format invalid'
                    }
                    all_healthy = False
            except Exception as e:
                status['services']['openai'] = {
                    'status': 'degraded',
                    'message': f'OpenAI check error: {str(e)[:100]}'
                }
        else:
            status['services']['openai'] = {
                'status': 'degraded',
                'message': 'OpenAI API key not configured'
            }
        
        # Check Gemini API (if configured)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                # Just check if key exists
                if len(gemini_key) > 10:
                    status['services']['gemini'] = {
                        'status': 'operational',
                        'message': 'Gemini API key configured'
                    }
                else:
                    status['services']['gemini'] = {
                        'status': 'degraded',
                        'message': 'Gemini API key format invalid'
                    }
            except Exception as e:
                status['services']['gemini'] = {
                    'status': 'degraded',
                    'message': f'Gemini check error: {str(e)[:100]}'
                }
        else:
            status['services']['gemini'] = {
                'status': 'degraded',
                'message': 'Gemini API key not configured (optional)'
            }
        
        # Check RAG Service (non-blocking, shorter timeout)
        rag_service_url = os.getenv('RAG_SERVICE_URL', 'https://rag.theaicompany.co')
        rag_api_key = os.getenv('RAG_API_KEY')
        
        if rag_api_key:
            try:
                headers = {
                    'Authorization': f'Bearer {rag_api_key}',
                    'x-api-key': rag_api_key
                }
                response = requests.get(
                    f"{rag_service_url}/health",
                    headers=headers,
                    timeout=2  # Shorter timeout to avoid blocking
                )
                if response.status_code == 200:
                    status['services']['rag'] = {
                        'status': 'operational',
                        'message': 'RAG service responding'
                    }
                else:
                    status['services']['rag'] = {
                        'status': 'degraded',
                        'message': f'RAG service returned {response.status_code}'
                    }
                    # Don't mark as unhealthy for RAG (it's optional)
            except requests.exceptions.Timeout:
                status['services']['rag'] = {
                    'status': 'degraded',
                    'message': 'RAG service timeout (optional service)'
                }
                # Don't mark as unhealthy for RAG timeout
            except requests.exceptions.ConnectionError:
                status['services']['rag'] = {
                    'status': 'degraded',
                    'message': 'RAG service unreachable (optional service)'
                }
                # Don't mark as unhealthy for RAG connection error
            except Exception as e:
                status['services']['rag'] = {
                    'status': 'degraded',
                    'message': f'RAG service error: {str(e)[:100]}'
                }
                # Don't mark as unhealthy for RAG errors
        else:
            status['services']['rag'] = {
                'status': 'degraded',
                'message': 'RAG API key not configured (optional)'
            }
        
        # Determine overall status
        if not all_healthy:
            # Check if critical services are down
            critical_down = any(
                svc['status'] == 'offline' 
                for svc in status['services'].values() 
                if svc.get('status') == 'offline'
            )
            
            if critical_down:
                status['overall'] = 'offline'
                status['message'] = 'Critical services unavailable'
            else:
                status['overall'] = 'degraded'
                status['message'] = 'Some services unavailable'
        
        return jsonify(status)
    
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'overall': 'offline',
            'services': {},
            'message': f'Health check failed: {str(e)[:200]}',
            'error': str(e)
        }), 500

