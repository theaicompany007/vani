from flask import Flask
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

# Load environment variables (.env.local takes priority over .env)
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
dot_env_path = os.path.join(basedir, '.env')
dot_env_local_path = os.path.join(basedir, '.env.local')
load_dotenv(dot_env_path)  # Load .env first
load_dotenv(dot_env_local_path, override=True)  # Override with .env.local if exists

def create_app(debug=False):
    """Factory function to create and configure the Flask app"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.debug = debug
    
    # Configure app settings
    from datetime import timedelta
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        SUPABASE_URL=os.getenv('SUPABASE_URL', ''),
        SUPABASE_KEY=os.getenv('SUPABASE_KEY', '') or os.getenv('SUPABASE_ANON_KEY', ''),
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),  # Session lasts 7 days
        SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max file size for imports
    )
    
    # Configure logging
    configure_logging(debug)
    
    # Initialize Supabase client
    from .supabase_client import init_supabase
    app.supabase = init_supabase(app.config['SUPABASE_URL'], app.config['SUPABASE_KEY'])
    
    # Initialize authentication
    from .auth import init_auth
    init_auth(app)
    
    # Register routes
    from .routes import init_routes
    init_routes(app)
    
    return app

def configure_logging(debug_mode):
    """Configure application logging"""
    os.makedirs('logs', exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # File handler
    file_handler = RotatingFileHandler(
        'logs/application.log',
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8',
        delay=True
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    root_logger.addHandler(file_handler)
    
    # Console handler for debug mode
    if debug_mode:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(
            '[%(levelname)s] %(name)s: %(message)s'
        ))
        root_logger.addHandler(console_handler)
    
    # Configure werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.addFilter(type('', (logging.Filter,), {
        'filter': lambda r: not r.getMessage().startswith('GET /static/')
    }))
    
    # Suppress verbose httpcore and httpx debug logs
    httpcore_logger = logging.getLogger('httpcore')
    httpcore_logger.setLevel(logging.WARNING)
    
    httpx_logger = logging.getLogger('httpx')
    httpx_logger.setLevel(logging.WARNING)
    
    # Suppress hpack (HTTP/2 header compression) debug logs
    hpack_logger = logging.getLogger('hpack')
    hpack_logger.setLevel(logging.WARNING)
    
    # Suppress supabase client debug logs
    supabase_logger = logging.getLogger('supabase')
    supabase_logger.setLevel(logging.WARNING)

