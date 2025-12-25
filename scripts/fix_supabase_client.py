"""Fix Supabase client compatibility by monkey-patching httpx"""
import sys

# Monkey patch httpx.Client to ignore unsupported proxy parameters
# This fixes the compatibility issue between gotrue and httpx
# IMPORTANT: Handles both 'proxy' (singular, used by Supabase) and 'proxies' (plural, used by OpenAI)
try:
    import httpx
    import inspect
    
    # Check if already patched to avoid double-patching
    _httpx_patch_applied = getattr(httpx.Client, '_supabase_patch_applied', False)
    
    if not _httpx_patch_applied:
        # Get the original __init__ method - use getattr to handle inheritance properly
        # Try __dict__ first (if it's defined on the class), otherwise use getattr
        if '__init__' in httpx.Client.__dict__:
            _original_httpx_client_init = httpx.Client.__dict__['__init__']
        else:
            _original_httpx_client_init = getattr(httpx.Client, '__init__')
        
        # Get the signature to check what parameters are supported
        try:
            sig = inspect.signature(_original_httpx_client_init)
            supported_params = set(sig.parameters.keys())
        except Exception:
            supported_params = set()
        
        # Create a closure to capture the original method
        def make_patched_init(original):
            def patched_init(self, *args, **kwargs):
                # IMPORTANT: Remove unsupported proxy-related parameters
                # This handles both 'proxy' (singular, used by Supabase/gotrue) 
                # and 'proxies' (plural, used by OpenAI) if not supported
                
                # First, try to remove parameters that are definitely not in the signature
                original_kwargs = kwargs.copy()
                if 'proxy' in kwargs and 'proxy' not in supported_params:
                    kwargs.pop('proxy', None)
                
                if 'proxies' in kwargs and 'proxies' not in supported_params:
                    kwargs.pop('proxies', None)
                
                # Try calling with cleaned kwargs
                try:
                    return original(self, *args, **kwargs)
                except TypeError as e:
                    # If we get a TypeError about unexpected keyword arguments,
                    # try removing proxy-related parameters even if they were in the signature
                    error_msg = str(e).lower()
                    if 'unexpected keyword argument' in error_msg:
                        # Try removing both proxy and proxies
                        kwargs = original_kwargs.copy()
                        kwargs.pop('proxy', None)
                        kwargs.pop('proxies', None)
                        try:
                            return original(self, *args, **kwargs)
                        except Exception:
                            # If it still fails, re-raise the original error
                            raise e
                    else:
                        # Not a parameter error, re-raise
                        raise
            return patched_init
        
        # Apply patch with the closure
        httpx.Client.__init__ = make_patched_init(_original_httpx_client_init)
        httpx.Client._supabase_patch_applied = True
        # Patch applied silently (compatibility issue resolved)
    
except Exception as e:
    # Silently continue if patch fails
    pass


# Import this module before importing supabase
if __name__ == '__main__':
    print("This module should be imported before supabase")
    print("Usage: import scripts.fix_supabase_client; from supabase import create_client")

