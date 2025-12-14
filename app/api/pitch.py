"""Pitch generation and management API routes"""
from flask import Blueprint, request, jsonify, render_template
import logging
import json
import html
try:
    from app.integrations.pitch_generator import PitchGenerator
except ImportError:
    PitchGenerator = None
from app.supabase_client import get_supabase_client
from app.auth import require_auth, require_use_case, get_current_industry
from app.utils.signature_formatter import SignatureFormatter
from datetime import datetime
from flask import g, send_file
import io

logger = logging.getLogger(__name__)

pitch_bp = Blueprint('pitch', __name__)

@pitch_bp.route('/api/pitch/generate/<uuid:target_id>', methods=['POST'])
@require_auth
@require_use_case('pitch_presentation')
def generate_pitch(target_id):
    from flask import current_app
    supabase = get_supabase_client(current_app)
    if not supabase:
        return jsonify({'error': 'Supabase not configured'}), 503
    try:
        target_response = supabase.table('targets').select('*').eq('id', target_id).limit(1).execute()
        if not target_response.data:
            return jsonify({'error': 'Target not found'}), 404
        target = target_response.data[0]
        
        # Convert any UUID fields in target to strings for JSON serialization
        from uuid import UUID
        target_serializable = {}
        for key, value in target.items():
            if isinstance(value, UUID):
                target_serializable[key] = str(value)
            else:
                target_serializable[key] = value
        # Get industry name from target or current industry context
        industry_name = None
        
        # Try to get from target's industry_id first (highest priority)
        target_industry_id = target.get('industry_id')
        if target_industry_id:
            try:
                industry_response = supabase.table('industries').select('name').eq('id', target_industry_id).limit(1).execute()
                if industry_response.data and industry_response.data[0].get('name'):
                    industry_name = industry_response.data[0]['name']
                    logger.info(f"Using industry from target: {industry_name}")
            except Exception as e:
                logger.warning(f"Failed to get industry name from industry_id: {e}")
        
        # Fallback to current industry context if target doesn't have industry
        if not industry_name:
            industry = get_current_industry()
            if industry and hasattr(industry, 'name'):
                industry_name = industry.name
                logger.info(f"Using current active industry: {industry_name}")
            elif industry and isinstance(industry, dict):
                industry_name = industry.get('name')
                if industry_name:
                    logger.info(f"Using current active industry (dict): {industry_name}")
        
        # Final fallback
        if not industry_name:
            industry_name = "General Business"
            logger.warning(f"No industry found, using default: {industry_name}")
        
        # Ensure industry_name is always a non-empty string
        if not industry_name or not isinstance(industry_name, str):
            industry_name = "General Business"
            logger.warning(f"Invalid industry_name, using default: {industry_name}")
        
        if PitchGenerator is None:
            return jsonify({'error': 'Pitch generator not available. Please check OpenAI configuration.'}), 503
        
        pitch_generator = PitchGenerator()
        # Use target_serializable (with string UUIDs) for pitch generation
        generated_content = pitch_generator.generate_pitch(target_serializable, industry_name)
        
        # Helper function to safely convert content to string
        def safe_str(value, default=''):
            """Safely convert any value to string"""
            from uuid import UUID
            if value is None:
                return default
            # Handle UUID objects first
            if isinstance(value, UUID):
                return str(value)
            if isinstance(value, dict):
                # If it's a dict, convert to JSON string (but first convert any UUIDs)
                try:
                    # Recursively convert UUIDs in dict
                    dict_serializable = {}
                    for k, v in value.items():
                        if isinstance(v, UUID):
                            dict_serializable[k] = str(v)
                        else:
                            dict_serializable[k] = v
                    return json.dumps(dict_serializable, indent=2, ensure_ascii=False, default=str)
                except Exception:
                    return str(value)
            if isinstance(value, list):
                # Convert UUIDs in list
                return '\n'.join(str(item) for item in value)
            if not isinstance(value, str):
                return str(value)
            return value
        
        def safe_html(value, default=''):
            """Convert value to HTML-safe string, replacing newlines with <br>"""
            # First convert to string
            text = safe_str(value, default)
            # Ensure it's a string (defensive check)
            if not isinstance(text, str):
                text = str(text)
            # Escape HTML and replace newlines
            try:
                text = html.escape(text)
                text = text.replace('\n', '<br>')
            except Exception as e:
                logger.warning(f"Error in safe_html: {e}, value type: {type(text)}")
                text = str(text).replace('\n', '<br>')
            return text
        
        # Ensure all values in generated_content are strings (not dicts)
        # This prevents errors in template rendering or HTML generation
        # Also convert hit_list from JSON to readable text if needed
        sanitized_content = {}
        for key, value in generated_content.items():
            if key == 'hit_list' and isinstance(value, dict):
                # Convert JSON hit_list to readable text
                company = value.get('company', '')
                pain = value.get('pain_point', '')
                pitch = value.get('pitch', '')
                sanitized_content[key] = f"For {company}, facing {pain}. {pitch}" if company else safe_str(value, '')
            else:
                sanitized_content[key] = safe_str(value, '')
        
        # Generate HTML from pitch content (fallback if template doesn't exist)
        try:
            pitch_html = render_template('pitch_presentation.html', pitch=sanitized_content, target=target_serializable)
        except Exception as template_error:
            logger.warning(f"Could not render pitch template: {template_error}. Using generated content directly.")
            import traceback
            logger.warning(traceback.format_exc())
            # Fallback: create simple HTML from generated content
            title = safe_html(sanitized_content.get('title', 'Strategic Pitch'))
            problem = safe_html(sanitized_content.get('problem', ''))
            solution = safe_html(sanitized_content.get('solution', ''))
            hit_list = safe_html(sanitized_content.get('hit_list', ''))
            trojan_horse = safe_html(sanitized_content.get('trojan_horse', ''))
            
            pitch_html = f"""
            <div class="pitch-presentation p-6 bg-white rounded-lg shadow">
                <h1 class="text-3xl font-bold text-slate-900 mb-4">{title}</h1>
                <div class="space-y-6">
                    <section>
                        <h2 class="text-2xl font-bold text-slate-800 mb-2">Problem</h2>
                        <p class="text-slate-700">{problem}</p>
                    </section>
                    <section>
                        <h2 class="text-2xl font-bold text-slate-800 mb-2">Solution</h2>
                        <p class="text-slate-700">{solution}</p>
                    </section>
                    <section>
                        <h2 class="text-2xl font-bold text-slate-800 mb-2">Hit List</h2>
                        <div class="text-slate-700">{hit_list}</div>
                    </section>
                    <section>
                        <h2 class="text-2xl font-bold text-slate-800 mb-2">Trojan Horse Strategy</h2>
                        <p class="text-slate-700">{trojan_horse}</p>
                    </section>
                </div>
            </div>
            """
        # Store sanitized content (all values as strings) in database
        # Convert UUID to string for database
        target_id_str = str(target_id) if target_id else None
        
        # Map sanitized_content to database columns
        # The table has: title, problem_statement, solution_description, hit_list_content, trojan_horse_strategy
        # Store the full content in generation_metadata as JSONB
        # Note: Table uses 'created_at' with DEFAULT NOW(), so we don't need to set it
        insert_data = {
            'target_id': target_id_str,
            'html_content': pitch_html,
            'title': sanitized_content.get('title', ''),
            'problem_statement': sanitized_content.get('problem', ''),
            'solution_description': sanitized_content.get('solution', ''),
            'hit_list_content': sanitized_content.get('hit_list', ''),
            'trojan_horse_strategy': sanitized_content.get('trojan_horse', ''),
            'generation_metadata': sanitized_content  # Store full content as JSONB
        }
        
        # Note: 'generated_content' column doesn't exist in the table
        # Full content is stored in 'generation_metadata' JSONB column
        
        insert_response = supabase.table('generated_pitches').insert(insert_data).execute()
        if not insert_response.data:
            return jsonify({'error': 'Failed to save generated pitch'}), 500
        
        # Convert UUID to string for JSON response
        from uuid import UUID
        pitch_id = insert_response.data[0]['id']
        pitch_id_str = str(pitch_id) if isinstance(pitch_id, UUID) else (str(pitch_id) if pitch_id else None)
        
        return jsonify({
            'success': True,
            'pitch_id': pitch_id_str,
            'generated_content': sanitized_content,  # Use sanitized version
            'generated_html': pitch_html
        })
    except Exception as e:
        logger.error(f"Error generating pitch for target {target_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'details': traceback.format_exc() if current_app.debug else None}), 500

@pitch_bp.route('/api/pitch/history/<uuid:target_id>', methods=['GET'])
@require_auth
@require_use_case('pitch_presentation')
def get_pitch_history(target_id):
    from flask import current_app
    supabase = get_supabase_client(current_app)
    if not supabase:
        return jsonify({'error': 'Supabase not configured'}), 503
    try:
        # Get all pitches for this target, ordered by creation date (newest first)
        pitch_response = supabase.table('generated_pitches').select('id, title, problem_statement, solution_description, created_at, sent_at, sent_channel').eq('target_id', str(target_id)).order('created_at', desc=True).execute()
        
        pitches = []
        if pitch_response.data:
            from uuid import UUID
            for pitch in pitch_response.data:
                pitch_id = pitch['id']
                pitch_id_str = str(pitch_id) if isinstance(pitch_id, UUID) else (str(pitch_id) if pitch_id else None)
                pitches.append({
                    'id': pitch_id_str,
                    'title': pitch.get('title', ''),
                    'problem_statement': pitch.get('problem_statement', ''),
                    'solution_description': pitch.get('solution_description', ''),
                    'created_at': pitch.get('created_at'),
                    'sent_at': pitch.get('sent_at'),
                    'sent_channel': pitch.get('sent_channel')
                })
        
        return jsonify({
            'success': True,
            'pitches': pitches
        })
    except Exception as e:
        logger.error(f"Error retrieving pitch history for target {target_id}: {e}")
        return jsonify({'error': str(e)}), 500

@pitch_bp.route('/api/pitch/preview/<uuid:pitch_id>', methods=['GET'])
@require_auth
@require_use_case('pitch_presentation')
def preview_pitch(pitch_id):
    from flask import current_app
    supabase = get_supabase_client(current_app)
    if not supabase:
        return jsonify({'error': 'Supabase not configured'}), 503
    try:
        pitch_response = supabase.table('generated_pitches').select('*').eq('id', pitch_id).limit(1).execute()
        if not pitch_response.data:
            return jsonify({'error': 'Pitch not found'}), 404
        generated_pitch = pitch_response.data[0]
        # Convert UUID to string for JSON response
        from uuid import UUID
        pitch_id = generated_pitch['id']
        pitch_id_str = str(pitch_id) if isinstance(pitch_id, UUID) else (str(pitch_id) if pitch_id else None)
        
        # Reconstruct generated_content from individual columns if needed
        generated_content = generated_pitch.get('generated_content')
        if not generated_content:
            # Fallback: reconstruct from individual columns
            generated_content = {
                'title': generated_pitch.get('title', ''),
                'problem': generated_pitch.get('problem_statement', ''),
                'solution': generated_pitch.get('solution_description', ''),
                'hit_list': generated_pitch.get('hit_list_content', ''),
                'trojan_horse': generated_pitch.get('trojan_horse_strategy', '')
            }
        
        # Check if pitch has been sent
        sent_at = generated_pitch.get('sent_at')
        sent_channel = generated_pitch.get('sent_channel')
        
        return jsonify({
            'success': True,
            'pitch_id': pitch_id_str,
            'generated_content': generated_content,
            'generated_html': generated_pitch.get('html_content'),
            'sent_at': sent_at,
            'sent_channel': sent_channel
        })
    except Exception as e:
        logger.error(f"Error retrieving pitch preview {pitch_id}: {e}")
        return jsonify({'error': str(e)}), 500

@pitch_bp.route('/api/pitch/send/<uuid:pitch_id>', methods=['POST'])
@require_auth
@require_use_case('pitch_presentation')
def send_pitch(pitch_id):
    from flask import current_app
    try:
        data = request.get_json() or {}
    except Exception as e:
        logger.error(f"Error parsing request JSON: {e}")
        return jsonify({'error': 'Invalid JSON in request body'}), 400
    
    channel = data.get('channel')
    if not channel:
        logger.warning(f"Send pitch request missing channel parameter. Data: {data}")
        return jsonify({'error': 'Channel is required (email, whatsapp, linkedin)'}), 400
    
    if channel not in ['email', 'whatsapp', 'linkedin']:
        logger.warning(f"Invalid channel specified: {channel}")
        return jsonify({'error': f'Invalid channel: {channel}. Must be one of: email, whatsapp, linkedin'}), 400
    supabase = get_supabase_client(current_app)
    if not supabase:
        return jsonify({'error': 'Supabase not configured'}), 503
    try:
        pitch_response = supabase.table('generated_pitches').select('*, targets(*)').eq('id', pitch_id).limit(1).execute()
        if not pitch_response.data:
            logger.warning(f"Pitch not found: {pitch_id}")
            return jsonify({'error': 'Pitch not found'}), 404
        
        generated_pitch_data = pitch_response.data[0]
        target = generated_pitch_data.get('targets', {})
        
        if not target:
            logger.warning(f"Pitch {pitch_id} has no associated target")
            return jsonify({'error': 'Pitch has no associated target'}), 400
        
        generated_html = generated_pitch_data.get('html_content', '')
        
        logger.debug(f"Sending pitch {pitch_id} via {channel}. Target: {target.get('company_name', 'Unknown')}")
        
        # Get signature profile (default or first available)
        signature = None
        try:
            # Try to get default signature first
            sig_response = supabase.table('signature_profiles').select('*').eq('is_default', True).limit(1).execute()
            if sig_response.data:
                signature = sig_response.data[0]
            else:
                # Fallback to first available signature
                sig_response = supabase.table('signature_profiles').select('*').limit(1).execute()
                if sig_response.data:
                    signature = sig_response.data[0]
        except Exception as e:
            logger.warning(f"Could not fetch signature profile: {e}")
        
        # Format signature for the channel
        signature_text = ''
        if signature:
            signature_text = SignatureFormatter.format_for_channel(signature, channel)
        
        # If target is linked to contact, use contact's email/phone/linkedin
        contact_id = target.get('contact_id')
        if contact_id:
            contact_response = supabase.table('contacts').select('*').eq('id', contact_id).limit(1).execute()
            if contact_response.data:
                contact = contact_response.data[0]
                # Override target fields with contact data
                target['email'] = contact.get('email') or target.get('email')
                target['phone'] = contact.get('phone') or target.get('phone')
                target['linkedin_url'] = contact.get('linkedin') or target.get('linkedin_url')
                target['contact_name'] = contact.get('name') or target.get('contact_name')
        
        # Get edited content from request, or use generated content as fallback
        edited_message = data.get('message')  # User-edited message
        edited_subject = data.get('subject')  # User-edited subject (for email)
        edited_from = data.get('from')  # User-edited from name (for email)
        
        # Get generated_content, or reconstruct from individual columns
        generated_content = generated_pitch_data.get('generated_content', {})
        if not generated_content:
            generated_content = {
                'title': generated_pitch_data.get('title', ''),
                'problem': generated_pitch_data.get('problem_statement', ''),
                'solution': generated_pitch_data.get('solution_description', ''),
                'hit_list': generated_pitch_data.get('hit_list_content', ''),
                'trojan_horse': generated_pitch_data.get('trojan_horse_strategy', '')
            }
        if channel == 'email':
            from app.integrations.resend_client import ResendClient
            resend_client = ResendClient()
            
            # Use edited subject or fallback to default
            subject = edited_subject or f"A Strategic Pitch for {target.get('company_name', 'Unknown')} from Project VANI"
            
            # Use edited from name or fallback to signature
            from_name = edited_from or (signature.get('from_name') if signature else 'Project VANI Team')
            from_email = signature.get('from_email') if signature else None
            
            to_email = target.get('email')
            if not to_email:
                return jsonify({'error': 'Target email not available'}), 400
            
            # Use edited message or convert generated HTML to plain text
            if edited_message:
                # Convert markdown to HTML for email
                try:
                    import markdown
                    message_html = markdown.markdown(edited_message, extensions=['nl2br', 'fenced_code'])
                except ImportError:
                    # Fallback: simple markdown conversion if markdown library not available
                    message_html = edited_message.replace('\n\n', '</p><p>').replace('\n', '<br>')
                    message_html = message_html.replace('**', '<strong>').replace('**', '</strong>')
                    message_html = message_html.replace('*', '<em>').replace('*', '</em>')
                    message_html = f'<p>{message_html}</p>'
                except Exception as e:
                    logger.warning(f"Markdown conversion failed: {e}, using simple conversion")
                    message_html = edited_message.replace('\n\n', '</p><p>').replace('\n', '<br>')
                    message_html = message_html.replace('**', '<strong>').replace('**', '</strong>')
                    message_html = message_html.replace('*', '<em>').replace('*', '</em>')
                    message_html = f'<p>{message_html}</p>'
            else:
                message_html = generated_html
            
            # Append signature to HTML if available
            final_html = message_html
            if signature_text:
                final_html = f"{message_html}\n{signature_text}"
            
            # Send email with from_name if provided
            if from_email:
                resend_client.send_email(to=to_email, subject=subject, html=final_html, from_email=from_email, from_name=from_name)
            else:
                resend_client.send_email(to=to_email, subject=subject, html=final_html)
            message = f"Email pitch sent to {to_email}"
        elif channel == 'whatsapp':
            from app.integrations.twilio_client import TwilioClient
            try:
                twilio_client = TwilioClient()
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                return jsonify({'error': f'Twilio not configured: {str(e)}'}), 400
            
            to_phone = target.get('phone')
            if not to_phone:
                return jsonify({'error': 'Target phone not available'}), 400
            
            # Use edited message or build from pitch content
            if edited_message:
                whatsapp_message = edited_message
            else:
                # Build WhatsApp message from pitch content
                contact_name = target.get('contact_name', 'there')
                company_name = target.get('company_name', 'your company')
                pitch_title = generated_content.get('title', 'Strategic Pitch')
                pitch_problem = generated_content.get('problem', '')
                pitch_solution = generated_content.get('solution', '')
                
                whatsapp_message = f"""Hi {contact_name}! 👋

I have a strategic pitch for {company_name} from Project VANI.

*{pitch_title}*

*Problem:*
{pitch_problem}

*Solution:*
{pitch_solution}

Would you be open to a quick conversation about how VANI can help {company_name}?"""
            
            # Append signature if available
            if signature_text:
                whatsapp_message = f"{whatsapp_message}\n\n{signature_text}"
            else:
                whatsapp_message = f"{whatsapp_message}\n\nBest regards,\nProject VANI Team"
            
            result = twilio_client.send_whatsapp(to=to_phone, message=whatsapp_message)
            
            if result.get('success'):
                message = f"WhatsApp pitch sent to {contact_name} ({to_phone})"
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"WhatsApp send failed: {error_msg}")
                return jsonify({'error': f'Failed to send WhatsApp message: {error_msg}'}), 500
        elif channel == 'linkedin':
            from app.integrations.linkedin_client import LinkedInClient
            linkedin_client = LinkedInClient()
            
            if not linkedin_client.is_configured():
                return jsonify({'error': 'LinkedIn not configured. Please set LINKEDIN_ACCESS_TOKEN in environment variables.'}), 400
            
            # Get LinkedIn profile URL or URN from target
            # Database column is 'linkedin_url' (from migration 001_create_tables.sql)
            linkedin_profile_url = target.get('linkedin_url') or target.get('linkedin_profile_url')
            linkedin_urn = target.get('linkedin_urn')  # Direct URN if available
            
            if not linkedin_urn and linkedin_profile_url:
                # Try to extract URN from URL (may require API call)
                linkedin_urn = linkedin_client.extract_urn_from_url(linkedin_profile_url)
            
            if not linkedin_urn:
                return jsonify({
                    'error': 'Target LinkedIn URN or profile URL not available. Please add linkedin_url (profile URL) or linkedin_urn (URN) to target in database.'
                }), 400
            
            # Create LinkedIn message from pitch content
            contact_name = target.get('contact_name', 'there')
            company_name = target.get('company_name', 'your company')
            
            # Use edited message or build from pitch content
            if edited_message:
                linkedin_message = edited_message
            else:
                # Build message text from pitch content
                pitch_title = generated_content.get('title', 'Strategic Pitch')
                pitch_problem = generated_content.get('problem', '')
                pitch_solution = generated_content.get('solution', '')
                
                linkedin_message = f"""Hi {contact_name},

I have a strategic pitch for {company_name} from Project VANI.

{pitch_title}

Problem:
{pitch_problem}

Solution:
{pitch_solution}

Would you be open to a quick conversation about how VANI can help {company_name}?"""
            
            # Append signature if available
            if signature_text:
                linkedin_message = f"{linkedin_message}\n\n{signature_text}"
            else:
                linkedin_message = f"{linkedin_message}\n\nBest regards,\nProject VANI Team"
            
            # Send LinkedIn message
            result = linkedin_client.send_message(
                recipient_urn=linkedin_urn,
                message=linkedin_message,
                subject=f"Strategic Pitch for {company_name}"
            )
            
            if result.get('success'):
                message = f"LinkedIn pitch sent to {contact_name} ({linkedin_urn})"
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"LinkedIn send failed: {error_msg}")
                return jsonify({'error': f'Failed to send LinkedIn message: {error_msg}'}), 500
        else:
            return jsonify({'error': 'Invalid channel specified'}), 400
        supabase.table('generated_pitches').update({
            'sent_at': datetime.utcnow().isoformat(),
            'sent_channel': channel
        }).eq('id', pitch_id).execute()
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        logger.error(f"Error sending pitch {pitch_id} via {channel}: {e}")
        return jsonify({'error': str(e)}), 500

@pitch_bp.route('/api/pitch/export-pdf/<uuid:pitch_id>', methods=['GET'])
@require_auth
@require_use_case('pitch_presentation')
def export_pitch_pdf(pitch_id):
    """Export pitch as PDF"""
    from flask import current_app, send_file
    import io
    try:
        from app.integrations.pitch_exporter import PitchExporter
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get pitch data
        pitch_response = supabase.table('generated_pitches').select('*, targets(*)').eq('id', pitch_id).limit(1).execute()
        if not pitch_response.data:
            return jsonify({'error': 'Pitch not found'}), 404
        
        pitch_data = pitch_response.data[0]
        target = pitch_data.get('targets', {})
        
        # Reconstruct pitch content
        generated_content = pitch_data.get('generation_metadata', {})
        if not generated_content:
            generated_content = {
                'title': pitch_data.get('title', ''),
                'problem': pitch_data.get('problem_statement', ''),
                'solution': pitch_data.get('solution_description', ''),
                'hit_list': pitch_data.get('hit_list_content', ''),
                'trojan_horse': pitch_data.get('trojan_horse_strategy', '')
            }
        
        company_name = target.get('company_name', 'Unknown Company')
        contact_name = target.get('contact_name')
        
        # Generate PDF
        pdf_bytes = PitchExporter.export_to_pdf(
            pitch_content=generated_content,
            company_name=company_name,
            contact_name=contact_name
        )
        
        # Return as file download
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'VANI_Pitch_{company_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.pdf'
        )
        
    except ImportError as e:
        logger.error(f"Export library not available: {e}")
        return jsonify({'error': 'PDF export not available. Please install weasyprint.'}), 503
    except Exception as e:
        logger.error(f"Error exporting pitch PDF {pitch_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@pitch_bp.route('/api/pitch/export-ppt/<uuid:pitch_id>', methods=['GET'])
@require_auth
@require_use_case('pitch_presentation')
def export_pitch_ppt(pitch_id):
    """Export pitch as PowerPoint"""
    from flask import current_app, send_file
    import io
    try:
        from app.integrations.pitch_exporter import PitchExporter
        
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get pitch data
        pitch_response = supabase.table('generated_pitches').select('*, targets(*)').eq('id', pitch_id).limit(1).execute()
        if not pitch_response.data:
            return jsonify({'error': 'Pitch not found'}), 404
        
        pitch_data = pitch_response.data[0]
        target = pitch_data.get('targets', {})
        
        # Reconstruct pitch content
        generated_content = pitch_data.get('generation_metadata', {})
        if not generated_content:
            generated_content = {
                'title': pitch_data.get('title', ''),
                'problem': pitch_data.get('problem_statement', ''),
                'solution': pitch_data.get('solution_description', ''),
                'hit_list': pitch_data.get('hit_list_content', ''),
                'trojan_horse': pitch_data.get('trojan_horse_strategy', '')
            }
        
        company_name = target.get('company_name', 'Unknown Company')
        contact_name = target.get('contact_name')
        
        # Generate PowerPoint
        pptx_bytes = PitchExporter.export_to_pptx(
            pitch_content=generated_content,
            company_name=company_name,
            contact_name=contact_name
        )
        
        # Return as file download
        return send_file(
            io.BytesIO(pptx_bytes),
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            as_attachment=True,
            download_name=f'VANI_Pitch_{company_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.pptx'
        )
        
    except ImportError as e:
        logger.error(f"Export library not available: {e}")
        return jsonify({'error': 'PowerPoint export not available. Please install python-pptx.'}), 503
    except Exception as e:
        logger.error(f"Error exporting pitch PowerPoint {pitch_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@pitch_bp.route('/api/pitch/industry-context/<industry>', methods=['GET'])
@require_auth
@require_use_case('pitch_presentation')
def get_industry_context_api(industry):
    """Get industry-specific context (persona, pain points, use cases)"""
    try:
        from urllib.parse import unquote
        from app.services.industry_persona_mapping import IndustryPersonaMapping
        
        # Decode URL-encoded industry name
        industry_decoded = unquote(industry)
        logger.debug(f"Getting industry context for: {industry_decoded} (original: {industry})")
        
        # Pass supabase client to check for custom mappings
        supabase = get_supabase_client(current_app)
        persona_context = IndustryPersonaMapping.get_industry_context(industry_decoded, supabase_client=supabase)
        
        if not persona_context:
            logger.warning(f"No persona context found for industry: {industry_decoded}")
            # Return 200 with success=false instead of 404, so frontend can handle it gracefully
            return jsonify({
                'success': False,
                'error': f'No persona mapping found for industry: {industry_decoded}',
                'industry': industry_decoded,
                'vani_persona': None
            }), 200
        
        return jsonify({
            'success': True,
            'industry': industry_decoded,
            'vani_persona': persona_context.vani_persona,
            'persona_description': persona_context.persona_description,
            'pain_points': persona_context.pain_points,
            'use_case_examples': persona_context.use_case_examples,
            'value_proposition_template': persona_context.value_proposition_template,
            'common_use_cases': persona_context.common_use_cases
        })
        
    except Exception as e:
        logger.error(f"Error getting industry context for {industry}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'industry': industry
        }), 500


@pitch_bp.route('/api/pitch/industry-context/<industry>', methods=['PUT', 'PATCH'])
@require_auth
@require_use_case('pitch_presentation')
def update_industry_context_api(industry):
    """Update industry-specific persona mapping (pain points, use cases, value proposition)"""
    from flask import current_app
    from urllib.parse import unquote
    from app.auth import get_current_user
    
    try:
        supabase = get_supabase_client(current_app)
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 503
        
        # Get current user for audit trail
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Decode URL-encoded industry name
        industry_decoded = unquote(industry)
        logger.info(f"Updating persona mapping for industry: {industry_decoded}")
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['vani_persona', 'pain_points', 'use_case_examples', 'value_proposition_template']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Prepare update data
        update_data = {
            'industry_name': industry_decoded,
            'vani_persona': data['vani_persona'],
            'persona_description': data.get('persona_description', ''),
            'pain_points': json.dumps(data['pain_points']) if isinstance(data['pain_points'], list) else data['pain_points'],
            'use_case_examples': json.dumps(data['use_case_examples']) if isinstance(data['use_case_examples'], list) else data['use_case_examples'],
            'value_proposition_template': data['value_proposition_template'],
            'common_use_cases': json.dumps(data.get('common_use_cases', [])) if isinstance(data.get('common_use_cases'), list) else data.get('common_use_cases', '[]'),
            'is_custom': True,
            'updated_by': str(user.id),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Check if mapping already exists
        existing = supabase.table('industry_persona_mappings').select('id').eq('industry_name', industry_decoded).limit(1).execute()
        
        if existing.data:
            # Update existing mapping
            mapping_id = existing.data[0]['id']
            result = supabase.table('industry_persona_mappings').update(update_data).eq('id', mapping_id).execute()
            
            if result.data:
                logger.info(f"Updated persona mapping for {industry_decoded}")
                return jsonify({
                    'success': True,
                    'message': 'Persona mapping updated successfully',
                    'industry': industry_decoded
                })
            else:
                return jsonify({'error': 'Failed to update persona mapping'}), 500
        else:
            # Create new mapping
            update_data['created_by'] = str(user.id)
            update_data['created_at'] = datetime.utcnow().isoformat()
            result = supabase.table('industry_persona_mappings').insert(update_data).execute()
            
            if result.data:
                logger.info(f"Created new persona mapping for {industry_decoded}")
                return jsonify({
                    'success': True,
                    'message': 'Persona mapping created successfully',
                    'industry': industry_decoded
                }), 201
            else:
                return jsonify({'error': 'Failed to create persona mapping'}), 500
                
    except Exception as e:
        logger.error(f"Error updating persona mapping for {industry}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'industry': industry
        }), 500
