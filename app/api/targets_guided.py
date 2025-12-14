"""Guided target creation endpoints"""
from flask import Blueprint, request, jsonify, current_app
import logging
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_use_case, get_current_user, get_current_industry

logger = logging.getLogger(__name__)

guided_bp = Blueprint('guided_targets', __name__)

@guided_bp.route('/api/targets/guided-create', methods=['POST'])
@require_auth
@require_use_case('target_management')
def guided_create_target():
    """Guided target creation with industry context loading"""
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        data = request.get_json() or {}
        
        # Required fields
        company_name = data.get('company_name')
        industry = data.get('industry')
        contacts = data.get('contacts', [])  # List of contact objects
        
        if not company_name:
            return jsonify({'error': 'company_name is required'}), 400
        if not industry:
            return jsonify({'error': 'industry is required'}), 400
        
        # Get industry context (persona, pain points, use cases)
        from app.services.industry_persona_mapping import IndustryPersonaMapping
        persona_context = IndustryPersonaMapping.get_industry_context(industry)
        
        # Get current user and industry
        user = get_current_user()
        current_industry = get_current_industry()
        industry_id = None
        
        if current_industry:
            if hasattr(current_industry, 'id'):
                industry_id = str(current_industry.id)
            elif isinstance(current_industry, dict):
                industry_id = current_industry.get('id')
        
        # If no industry_id, try to get from industries table
        if not industry_id:
            industry_response = supabase.table('industries').select('id').ilike('name', f'%{industry}%').limit(1).execute()
            if industry_response.data:
                industry_id = industry_response.data[0]['id']
        
        # Create company first (if not exists)
        company_response = supabase.table('companies').select('id').ilike('name', company_name).limit(1).execute()
        company_id = None
        
        if company_response.data:
            company_id = company_response.data[0]['id']
        else:
            # Create new company
            new_company = {
                'name': company_name,
                'industry': industry,
                'website': data.get('website'),
                'description': data.get('description')
            }
            if industry_id:
                new_company['industry_id'] = industry_id
            
            company_insert = supabase.table('companies').insert(new_company).execute()
            if company_insert.data:
                company_id = company_insert.data[0]['id']
        
        if not company_id:
            return jsonify({'error': 'Failed to create or find company'}), 500
        
        # Create contacts
        contact_ids = []
        for contact_data in contacts:
            contact_name = contact_data.get('name')
            if not contact_name:
                continue
            
            # Check if contact exists
            contact_check = supabase.table('contacts').select('id').eq('company_id', company_id).ilike('name', contact_name).limit(1).execute()
            
            if contact_check.data:
                contact_ids.append(contact_check.data[0]['id'])
            else:
                # Create new contact
                new_contact = {
                    'company_id': company_id,
                    'name': contact_name,
                    'role': contact_data.get('designation', contact_data.get('role', '')),
                    'email': contact_data.get('email'),
                    'phone': contact_data.get('phone'),
                    'linkedin': contact_data.get('linkedin_url', contact_data.get('linkedin')),
                    'industry': industry,
                    'lead_source': 'Manual Entry'
                }
                
                contact_insert = supabase.table('contacts').insert(new_contact).execute()
                if contact_insert.data:
                    contact_ids.append(contact_insert.data[0]['id'])
        
        # Create target (use first contact as primary)
        target_data = {
            'company_id': company_id,
            'company_name': company_name,
            'industry_id': industry_id,
            'status': 'new',
            'pain_point': data.get('pain_point', ', '.join(persona_context.pain_points[:2]) if persona_context else ''),
            'pitch_angle': data.get('pitch_angle', persona_context.value_proposition_template if persona_context else ''),
            'notes': data.get('notes', '')
        }
        
        if contact_ids:
            target_data['contact_id'] = contact_ids[0]
            # Get contact name for target
            contact_response = supabase.table('contacts').select('name').eq('id', contact_ids[0]).limit(1).execute()
            if contact_response.data:
                target_data['contact_name'] = contact_response.data[0]['name']
        
        target_insert = supabase.table('targets').insert(target_data).execute()
        
        if not target_insert.data:
            return jsonify({'error': 'Failed to create target'}), 500
        
        target = target_insert.data[0]
        
        # Return response with industry context
        response_data = {
            'success': True,
            'target': target,
            'company_id': company_id,
            'contact_ids': contact_ids,
            'industry_context': {
                'vani_persona': persona_context.vani_persona if persona_context else None,
                'persona_description': persona_context.persona_description if persona_context else None,
                'pain_points': persona_context.pain_points if persona_context else [],
                'use_case_examples': persona_context.use_case_examples if persona_context else [],
                'value_proposition_template': persona_context.value_proposition_template if persona_context else None
            } if persona_context else None
        }
        
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Error in guided target creation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@guided_bp.route('/api/targets/industry-context/<industry>', methods=['GET'])
@require_auth
@require_use_case('target_management')
def get_target_industry_context(industry):
    """Get industry context for target creation"""
    try:
        from app.services.industry_persona_mapping import IndustryPersonaMapping
        
        persona_context = IndustryPersonaMapping.get_industry_context(industry)
        
        if not persona_context:
            return jsonify({
                'error': f'No context found for industry: {industry}',
                'industry': industry
            }), 404
        
        return jsonify({
            'success': True,
            'industry': industry,
            'vani_persona': persona_context.vani_persona,
            'persona_description': persona_context.persona_description,
            'pain_points': persona_context.pain_points,
            'use_case_examples': persona_context.use_case_examples,
            'value_proposition_template': persona_context.value_proposition_template,
            'common_use_cases': persona_context.common_use_cases
        })
        
    except Exception as e:
        logger.error(f"Error getting industry context for {industry}: {e}")
        return jsonify({'error': str(e)}), 500





