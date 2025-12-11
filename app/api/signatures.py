"""Signature profiles API routes"""
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_super_user
import json

logger = logging.getLogger(__name__)

signatures_bp = Blueprint('signatures', __name__)


@signatures_bp.route('/api/signatures', methods=['GET'])
@require_auth
def list_signatures():
    """List all signature profiles"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        response = supabase.table('signature_profiles').select('*').order('created_at', desc=True).execute()
        
        return jsonify({
            'success': True,
            'signatures': response.data or []
        })
        
    except Exception as e:
        logger.error(f"Error listing signatures: {e}")
        return jsonify({'error': str(e)}), 500


@signatures_bp.route('/api/signatures', methods=['POST'])
@require_auth
@require_super_user
def create_signature():
    """Create a new signature profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        from_name = data.get('from_name')
        from_email = data.get('from_email')
        
        if not from_name or not from_email:
            return jsonify({'error': 'from_name and from_email are required'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Normalize signature_json
        signature_json = data.get('signature_json', {})
        if isinstance(signature_json, str):
            try:
                signature_json = json.loads(signature_json)
            except:
                signature_json = {}
        
        # If is_default is True, unset other defaults
        is_default = data.get('is_default', False)
        if is_default:
            # Update all existing signatures that are currently default to set is_default = False
            supabase.table('signature_profiles').update({'is_default': False}).eq('is_default', True).execute()
        
        payload = {
            'name': data.get('name', from_name),
            'from_name': from_name,
            'from_email': from_email,
            'reply_to': data.get('reply_to'),
            'signature_json': signature_json,
            'calendar_link': data.get('calendar_link'),
            'cta_text': data.get('cta_text'),
            'cta_button': data.get('cta_button'),
            'is_default': is_default,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.table('signature_profiles').insert(payload).execute()
        
        if response.data:
            return jsonify({
                'success': True,
                'signature': response.data[0]
            }), 201
        else:
            return jsonify({'error': 'Failed to create signature'}), 500
        
    except Exception as e:
        logger.error(f"Error creating signature: {e}")
        return jsonify({'error': str(e)}), 500


@signatures_bp.route('/api/signatures/<signature_id>', methods=['PUT'])
@require_auth
@require_super_user
def update_signature(signature_id):
    """Update a signature profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Normalize signature_json
        if 'signature_json' in data:
            signature_json = data['signature_json']
            if isinstance(signature_json, str):
                try:
                    signature_json = json.loads(signature_json)
                except:
                    signature_json = {}
            data['signature_json'] = signature_json
        
        # If is_default is True, unset other defaults
        if data.get('is_default'):
            supabase.table('signature_profiles').update({'is_default': False}).neq('id', signature_id).execute()
        
        data['updated_at'] = datetime.utcnow().isoformat()
        
        response = supabase.table('signature_profiles').update(data).eq('id', signature_id).execute()
        
        if response.data:
            return jsonify({
                'success': True,
                'signature': response.data[0]
            })
        else:
            return jsonify({'error': 'Signature not found'}), 404
        
    except Exception as e:
        logger.error(f"Error updating signature: {e}")
        return jsonify({'error': str(e)}), 500


@signatures_bp.route('/api/signatures/<signature_id>', methods=['DELETE'])
@require_auth
@require_super_user
def delete_signature(signature_id):
    """Delete a signature profile"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        response = supabase.table('signature_profiles').delete().eq('id', signature_id).execute()
        
        return jsonify({
            'success': True,
            'message': 'Signature deleted'
        })
        
    except Exception as e:
        logger.error(f"Error deleting signature: {e}")
        return jsonify({'error': str(e)}), 500


@signatures_bp.route('/api/signatures/default', methods=['GET'])
@require_auth
def get_default_signature():
    """Get the default signature profile"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Try to get default signature
        response = supabase.table('signature_profiles').select('*').eq('is_default', True).limit(1).execute()
        
        if response.data:
            return jsonify({
                'success': True,
                'signature': response.data[0]
            })
        else:
            # Fallback to first available
            response = supabase.table('signature_profiles').select('*').limit(1).execute()
            if response.data:
                return jsonify({
                    'success': True,
                    'signature': response.data[0]
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'No signature profiles found'
                }), 404
        
    except Exception as e:
        logger.error(f"Error getting default signature: {e}")
        return jsonify({'error': str(e)}), 500

