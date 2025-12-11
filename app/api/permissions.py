"""Permissions API routes"""
from flask import Blueprint, request, jsonify
import logging
from app.auth import get_supabase_auth_client, require_super_user, require_auth, get_current_user

logger = logging.getLogger(__name__)

permissions_bp = Blueprint('permissions', __name__)

@permissions_bp.route('/api/permissions/use-cases', methods=['GET'])
@require_auth
def list_use_cases():
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    try:
        response = supabase.table('use_cases').select('*').execute()
        return jsonify({'success': True, 'use_cases': response.data})
    except Exception as e:
        logger.error(f"Error listing use cases: {e}")
        return jsonify({'error': str(e)}), 500

@permissions_bp.route('/api/permissions/user/<uuid:user_id>', methods=['GET'])
@require_auth
@require_super_user
def get_user_permissions(user_id):
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    try:
        response = supabase.table('user_permissions').select('*, use_cases(code, name), industries(name)').eq('user_id', user_id).execute()
        permissions = []
        for p in response.data:
            perm = {
                'id': p.get('id'),
                'user_id': p.get('user_id'),
                'use_case_id': p.get('use_case_id'),
                'industry_id': p.get('industry_id'),
                'granted_at': p.get('granted_at'),
                'use_case_code': p.get('use_cases', {}).get('code') if p.get('use_cases') else None,
                'use_case_name': p.get('use_cases', {}).get('name') if p.get('use_cases') else None,
                'industry_name': p.get('industries', {}).get('name') if p.get('industries') else 'Global'
            }
            permissions.append(perm)
        return jsonify({'success': True, 'permissions': permissions})
    except Exception as e:
        logger.error(f"Error getting permissions for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@permissions_bp.route('/api/permissions/user/<uuid:user_id>/grant', methods=['POST'])
@require_auth
@require_super_user
def grant_permission(user_id):
    data = request.get_json()
    use_case_id = data.get('use_case_id')
    industry_id = data.get('industry_id')
    if not use_case_id:
        return jsonify({'error': 'use_case_id is required'}), 400
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    try:
        query = supabase.table('user_permissions').select('id').eq('user_id', user_id).eq('use_case_id', use_case_id)
        if industry_id:
            query = query.eq('industry_id', industry_id)
        else:
            query = query.is_('industry_id', 'null')
        existing_permission = query.execute()
        if existing_permission.data:
            return jsonify({'success': False, 'message': 'Permission already exists'}), 409
        current_user = get_current_user()
        supabase.table('user_permissions').insert({
            'user_id': str(user_id),
            'use_case_id': str(use_case_id),
            'industry_id': str(industry_id) if industry_id else None,
            'granted_by': str(current_user.id) if current_user and hasattr(current_user, 'id') else None
        }).execute()
        return jsonify({'success': True, 'message': 'Permission granted successfully'})
    except Exception as e:
        logger.error(f"Error granting permission to user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@permissions_bp.route('/api/permissions/user/<uuid:user_id>/revoke', methods=['POST'])
@require_auth
@require_super_user
def revoke_permission(user_id):
    data = request.get_json()
    use_case_id = data.get('use_case_id')
    industry_id = data.get('industry_id')
    if not use_case_id:
        return jsonify({'error': 'use_case_id is required'}), 400
    supabase = get_supabase_auth_client()
    if not supabase:
        return jsonify({'error': 'Authentication service unavailable'}), 503
    try:
        query = supabase.table('user_permissions').delete().eq('user_id', user_id).eq('use_case_id', use_case_id)
        if industry_id:
            query = query.eq('industry_id', industry_id)
        else:
            query = query.is_('industry_id', 'null')
        query.execute()
        return jsonify({'success': True, 'message': 'Permission revoked successfully'})
    except Exception as e:
        logger.error(f"Error revoking permission from user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500