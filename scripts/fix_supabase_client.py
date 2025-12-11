"""Fix Supabase client compatibility by monkey-patching httpx"""
import sys

# Monkey patch httpx.Client to ignore proxy parameter
# This fixes the compatibility issue between gotrue and httpx
try:
    import httpx
    
    # Store original __init__
    original_init = httpx.Client.__init__
    
    def patched_init(self, *args, **kwargs):
        # Remove proxy if it exists and httpx version doesn't support it
        if 'proxy' in kwargs:
            # Check if this version supports proxy
            import inspect
            sig = inspect.signature(original_init)
            if 'proxy' not in sig.parameters:
                # This version doesn't support proxy, remove it
                kwargs.pop('proxy', None)
        return original_init(self, *args, **kwargs)
    
    # Apply patch
    httpx.Client.__init__ = patched_init
    # Patch applied silently (compatibility issue resolved)
    
except Exception as e:
    # Silently continue if patch fails
    pass


# Import this module before importing supabase
if __name__ == '__main__':
    print("This module should be imported before supabase")
    print("Usage: import scripts.fix_supabase_client; from supabase import create_client")

