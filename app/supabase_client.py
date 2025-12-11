"""Supabase client initialization and utilities"""
# Fix compatibility issue before importing supabase
try:
    import sys
    from pathlib import Path
    fix_path = Path(__file__).parent.parent / 'scripts' / 'fix_supabase_client.py'
    if fix_path.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("fix_supabase_client", fix_path)
        fix_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fix_module)
except Exception:
    pass  # If fix fails, continue anyway

from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

def init_supabase(url: str, key: str) -> Client | None:
    """
    Initialize and return Supabase client
    
    Args:
        url: Supabase project URL
        key: Supabase anon/service key
        
    Returns:
        Supabase client instance or None if initialization fails
    """
    if not url or not key:
        logger.warning("Supabase URL or KEY not configured. Supabase features will be disabled.")
        return None
    
    try:
        supabase: Client = create_client(url, key)
        logger.info("Supabase client initialized successfully")
        return supabase
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def get_supabase_client(app=None) -> Client | None:
    """
    Get Supabase client from Flask app context
    
    Args:
        app: Flask application instance (optional, uses current_app if not provided)
        
    Returns:
        Supabase client instance or None
    """
    from flask import current_app
    
    if app is None:
        app = current_app
    
    return getattr(app, 'supabase', None)

