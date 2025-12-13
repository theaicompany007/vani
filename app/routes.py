"""Application routes"""
from flask import jsonify, render_template, redirect, url_for
import logging
from app.auth import require_auth, get_current_user

logger = logging.getLogger(__name__)

def init_routes(app):
    """Initialize application routes"""
    
    # Register API blueprints
    from app.api import targets, outreach, dashboard, message_generator, auth
    from app.api import permissions, industries, pitch, companies, contacts, jobs, admin, signatures
    from app.api import user_industries, knowledge_base, meetings, health
    from app.webhooks import resend_handler, twilio_handler, cal_com_handler
    
    app.register_blueprint(health.health_bp)
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(permissions.permissions_bp)
    app.register_blueprint(industries.industries_bp)
    app.register_blueprint(user_industries.user_industries_bp)
    app.register_blueprint(pitch.pitch_bp)
    app.register_blueprint(companies.companies_bp)
    app.register_blueprint(contacts.contacts_bp)
    app.register_blueprint(jobs.jobs_bp)
    app.register_blueprint(admin.admin_bp)
    app.register_blueprint(signatures.signatures_bp)
    app.register_blueprint(knowledge_base.knowledge_base_bp)
    app.register_blueprint(meetings.meetings_bp)
    app.register_blueprint(targets.targets_bp)
    app.register_blueprint(outreach.outreach_bp)
    app.register_blueprint(dashboard.dashboard_bp)
    app.register_blueprint(message_generator.message_gen_bp)
    app.register_blueprint(resend_handler.resend_webhook_bp)
    app.register_blueprint(twilio_handler.twilio_webhook_bp)
    app.register_blueprint(cal_com_handler.cal_com_webhook_bp)
    
    @app.route('/')
    def index():
        """Home page - redirect to login or command center"""
        user = get_current_user()
        if user:
            return redirect(url_for('command_center'))
        return redirect(url_for('login'))
    
    @app.route('/login')
    def login():
        """Login page"""
        user = get_current_user()
        if user:
            return redirect(url_for('command_center'))
        return render_template('login.html')
    
    @app.route('/command-center')
    @require_auth
    def command_center():
        """Command center dashboard"""
        return render_template('command_center.html')

