"""Message generation API with preview/approval"""
from flask import Blueprint, request, jsonify, current_app
import logging
from app.integrations.openai_client import OpenAIClient
from app.models.targets import Target
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_use_case

logger = logging.getLogger(__name__)

message_gen_bp = Blueprint('message_generator', __name__)


@message_gen_bp.route('/api/messages/generate', methods=['POST'])
@require_auth
@require_use_case('ai_message_generation')
def generate_message():
    """Generate outreach message with OpenAI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        target_id = data.get('target_id')
        channel = data.get('channel', 'email')  # email or whatsapp
        
        if not target_id:
            return jsonify({'error': 'target_id is required'}), 400
        
        # Validate that target_id is a valid UUID format
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        if not uuid_pattern.match(str(target_id)):
            logger.error(f"Invalid target_id format: {target_id}")
            return jsonify({'error': f'Invalid target_id format. Expected UUID, got: {target_id}'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get target
        try:
            target_response = supabase.table('targets').select('*').eq('id', target_id).execute()
            if not target_response.data:
                return jsonify({'error': 'Target not found'}), 404
        except Exception as db_error:
            logger.error(f"Database error fetching target {target_id}: {db_error}")
            return jsonify({'error': f'Database error: {str(db_error)}'}), 500
        
        target_data = target_response.data[0]
        target = Target.from_dict(target_data)
        
        # Get industry context
        from app.auth import get_current_industry
        industry = get_current_industry()
        industry_name = None
        if industry:
            if hasattr(industry, 'name'):
                industry_name = industry.name
            elif isinstance(industry, dict):
                industry_name = industry.get('name')
            # Also try to get from target's industry_id
            if not industry_name and target_data.get('industry_id'):
                industry_response = supabase.table('industries').select('name').eq('id', target_data['industry_id']).limit(1).execute()
                if industry_response.data:
                    industry_name = industry_response.data[0]['name']
        
        # Generate message with OpenAI (enhanced with industry context)
        try:
            openai_client = OpenAIClient()
        except Exception as init_error:
            logger.error(f"Failed to initialize OpenAIClient: {init_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Failed to initialize OpenAI client: {str(init_error)}'}), 500
        
        try:
            result = openai_client.generate_outreach_message(
            target_name=target.contact_name or '',
            contact_name=target.contact_name or '',
            role=target.role or '',
            company_name=target.company_name,
            pain_point=target.pain_point or '',
            pitch_angle=target.pitch_angle or '',
            channel=channel,
            base_script=target.script,
                industry_name=industry_name
            )
        except Exception as gen_error:
            logger.error(f"Error in generate_outreach_message: {gen_error}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Failed to generate message: {str(gen_error)}'}), 500
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Failed to generate message')}), 500
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'subject': result.get('subject'),
            'channel': channel,
            'target_id': target_id,
            'model': result.get('model'),
            'tokens_used': result.get('tokens_used')
        })
        
    except Exception as e:
        logger.error(f"Error generating message: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'details': traceback.format_exc() if current_app.debug else None}), 500


@message_gen_bp.route('/api/messages/preview', methods=['POST'])
@require_auth
@require_use_case('ai_message_generation')
def preview_message():
    """Preview a message before sending (stores in session/temp)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message')
        subject = data.get('subject')
        target_id = data.get('target_id')
        channel = data.get('channel', 'email')
        
        if not message or not target_id:
            return jsonify({'error': 'message and target_id are required'}), 400
        
        # Store preview in a temporary way (could use Redis/session in production)
        # For now, just return the preview data
        return jsonify({
            'success': True,
            'preview': {
                'message': message,
                'subject': subject,
                'channel': channel,
                'target_id': target_id
            }
        })
        
    except Exception as e:
        logger.error(f"Error previewing message: {e}")
        return jsonify({'error': str(e)}), 500

