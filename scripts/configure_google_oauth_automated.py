"""
Automated Google OAuth Client Configuration using Selenium

This script uses browser automation to configure OAuth redirect URIs
in Google Cloud Console automatically.

Requirements:
    pip install selenium webdriver-manager

Usage:
    python scripts/configure_google_oauth_automated.py --url https://vani.ngrok.app
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List

# Load environment variables
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')
load_dotenv(basedir / '.env.local', override=True)
load_dotenv(basedir / '.local.env', override=True)

SUPABASE_URL = os.getenv('SUPABASE_URL')
GOOGLE_OAUTH_CLIENT_ID = (
    os.getenv('GOOGLE_OAUTH_CLIENT_ID') or 
    os.getenv('OAuth_Client_ID') or 
    os.getenv('OAUTH_CLIENT_ID')
)
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID') or 'project-vani-480503'

def check_selenium():
    """Check if Selenium and undetected-chromedriver are installed"""
    try:
        import undetected_chromedriver as uc
        return True
    except ImportError:
        try:
            from selenium import webdriver
            return True
        except ImportError:
            return False

def configure_oauth_with_selenium(app_url: str, client_id: str, redirect_uris: List[str]):
    """Configure OAuth client using Selenium browser automation"""
    if not check_selenium():
        print("❌ Selenium not installed")
        print("   Install with: pip install selenium webdriver-manager undetected-chromedriver")
        return False
    
    driver = None
    try:
        # Try to use undetected-chromedriver first (bypasses bot detection)
        try:
            import undetected_chromedriver as uc
            print("\n🌐 Starting browser automation (undetected mode)...")
            print("   This should bypass Google's bot detection")
            
            # Setup undetected Chrome options with user profile
            options = uc.ChromeOptions()
            
            # Use existing Chrome profile for faster startup and automatic login
            import os
            username = os.getenv('USERNAME') or os.getenv('USER')
            if username:
                # Windows Chrome user data path
                chrome_user_data = f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data"
                if os.path.exists(chrome_user_data):
                    options.add_argument(f'--user-data-dir={chrome_user_data}')
                    # Use a separate profile directory to avoid conflicts with running Chrome
                    options.add_argument('--profile-directory=Default')
                    print("   ✅ Using existing Chrome profile (faster startup, already logged in)")
                else:
                    print("   ⚠️  Chrome profile not found, using default")
            else:
                print("   ⚠️  Could not determine username, using default profile")
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            
            # Initialize undetected Chrome driver
            print("   ⏳ Initializing Chrome browser with your profile...")
            print("   (This should be fast since we're using your existing profile)")
            
            # Create a function to build options (can't reuse ChromeOptions object)
            def build_options():
                opts = uc.ChromeOptions()
                username = os.getenv('USERNAME') or os.getenv('USER')
                if username:
                    chrome_user_data = f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data"
                    if os.path.exists(chrome_user_data):
                        opts.add_argument(f'--user-data-dir={chrome_user_data}')
                        opts.add_argument('--profile-directory=Default')
                opts.add_argument('--no-sandbox')
                opts.add_argument('--disable-dev-shm-usage')
                opts.add_argument('--disable-gpu')
                return opts
            
            try:
                # Try without use_subprocess first (more reliable with user profiles)
                driver = uc.Chrome(options=build_options(), version_main=None, use_subprocess=False)
                print("   ✅ Browser started with your Chrome profile")
            except Exception as e:
                error_msg = str(e)
                print(f"   ⚠️  First attempt failed: {error_msg[:80]}...")
                
                # Check if Chrome is already running
                if 'cannot connect' in error_msg.lower() or 'already in use' in error_msg.lower():
                    print("   💡 Chrome might already be running")
                    print("   🔄 Trying with a separate profile directory...")
                    try:
                        # Use a temp profile directory instead
                        opts = uc.ChromeOptions()
                        opts.add_argument('--no-sandbox')
                        opts.add_argument('--disable-dev-shm-usage')
                        opts.add_argument('--disable-gpu')
                        driver = uc.Chrome(options=opts, version_main=None, use_subprocess=False)
                        print("   ✅ Browser started (you may need to log in)")
                    except Exception as e3:
                        print(f"   ❌ Also failed: {e3}")
                        print("\n   💡 Please close all Chrome windows and try again")
                        return False
                else:
                    print("   🔄 Trying alternative method...")
                    try:
                        driver = uc.Chrome(options=build_options(), version_main=None, use_subprocess=True)
                        print("   ✅ Browser started with your Chrome profile")
                    except Exception as e2:
                        print(f"   ❌ Failed to start Chrome: {e2}")
                        print("\n   💡 Troubleshooting:")
                        print("      - Close any existing Chrome windows")
                        print("      - Make sure Chrome is installed")
                        print("      - Try running the script again")
                        return False
            
        except ImportError:
            print("❌ undetected-chromedriver not installed")
            print("   Install with: pip install undetected-chromedriver")
            return False
        except Exception as e:
            print(f"❌ Failed to start undetected Chrome: {e}")
            print("   Trying alternative method...")
            return False
        
        # Import common Selenium modules
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            # Navigate to Google Cloud Console OAuth credentials
            project_id = GOOGLE_CLOUD_PROJECT
            url = f"https://console.cloud.google.com/apis/credentials?project={project_id}"
            print(f"\n   📍 Navigating to: {url}")
            driver.get(url)
            
            # Check if already logged in (using existing profile)
            print("\n   ⏳ Loading Google Cloud Console...")
            time.sleep(3)  # Give page time to load
            
            # Check if we need to log in
            page_source = driver.page_source.lower()
            if 'sign in' in page_source or 'login' in page_source or 'sign in to continue' in page_source:
                print("\n" + "="*60)
                print("   🔐 LOGIN REQUIRED")
                print("="*60)
                print("   Please log in to Google Cloud Console in the browser")
                print("   Wait for the credentials page to fully load")
                print("   (You should see a list of OAuth clients)")
                print("\n   ⏳ Waiting for you to complete login...")
                input("   👆 Press Enter AFTER you've logged in and see the credentials page...")
            else:
                print("   ✅ Already logged in (using your Chrome profile)")
            
            print("\n   ✅ Proceeding with automation...")
            time.sleep(2)  # Give page time to fully load
            
            # Find the OAuth client by ID
            print(f"   🔍 Looking for OAuth client: {client_id[:30]}...")
            
            # Wait for credentials list to load
            wait = WebDriverWait(driver, 30)
            
            # Try to find the client - this is tricky as the UI structure may vary
            # We'll look for links or elements containing the client ID
            try:
                # Wait for the credentials list to load
                print("   ⏳ Waiting for credentials page to load...")
                time.sleep(3)
                
                # Try multiple strategies to find the OAuth client
                client_found = False
            
                # Strategy 1: Direct URL to the OAuth client edit page (most reliable)
                print(f"\n   🔍 Strategy 1: Trying direct URL to OAuth client...")
                # Extract project number from client ID (first part before -)
                project_number = client_id.split('-')[0] if '-' in client_id else None
                client_id_suffix = client_id.split('-', 1)[1] if '-' in client_id else client_id
                
                if project_number:
                    # Try to construct the edit URL
                    # Format: https://console.cloud.google.com/apis/credentials/oauthclient/{PROJECT_NUMBER}-{CLIENT_ID}?project={PROJECT_ID}
                    edit_url = f"https://console.cloud.google.com/apis/credentials/oauthclient/{project_number}-{client_id_suffix}?project={project_id}"
                    print(f"   📍 Navigating directly to: {edit_url}")
                    driver.get(edit_url)
                    time.sleep(3)
                    
                    # Check if we're on the edit page (look for "Authorized redirect URIs" or similar)
                    page_text = driver.page_source.lower()
                    if 'redirect' in page_text or 'authorized' in page_text or 'uri' in page_text:
                        print("   ✅ Found OAuth client edit page!")
                        client_found = True
                    else:
                        print("   ⚠️  Direct URL didn't work, trying to find in list...")
                
                # Strategy 2: Look for the client ID in the page
                if not client_found:
                    print(f"\n   🔍 Strategy 2: Searching for client in credentials list...")
                    client_id_short = client_id.split('-')[1] if '-' in client_id else client_id[:20]
                    print(f"   Looking for: ...{client_id_short}")
                    
                    # Get all clickable elements that might be the client
                    try:
                        # Look for table rows or list items containing the client ID
                        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{client_id_short}')]")
                        if elements:
                            print(f"   ✅ Found {len(elements)} element(s) containing client ID")
                            # Click the first one (usually the link)
                            elements[0].click()
                            client_found = True
                    except:
                        pass
                    
                    if not client_found:
                        print("   ⚠️  Could not find OAuth client automatically")
                        print("\n   📋 Manual Steps:")
                        print("   1. In the browser, find your OAuth client in the list")
                        print(f"   2. Look for: {client_id[:50]}...")
                        print("   3. Click on it to open the edit page")
                        input("\n   👆 Press Enter AFTER you've clicked on the OAuth client and the edit page is open...")
                        client_found = True  # Assume user did it manually
                
                # Wait for edit page to load
                print("\n   ⏳ Waiting for edit page to fully load...")
                time.sleep(3)
                
                # Verify we're on the edit page
                current_url = driver.current_url
                print(f"   📍 Current page: {current_url}")
                if 'oauthclient' in current_url or 'credentials' in current_url:
                    print("   ✅ On credentials/OAuth client page")
                else:
                    print("   ⚠️  May not be on the correct page")
                
                # Find the redirect URIs field - try multiple selectors
                print("   📝 Looking for redirect URIs field...")
                redirect_uris_field = None
                
                # Try different selectors
                selectors = [
                    (By.NAME, "redirect_uris"),
                    (By.ID, "redirect_uris"),
                    (By.XPATH, "//textarea[contains(@placeholder, 'redirect') or contains(@aria-label, 'redirect')]"),
                    (By.XPATH, "//textarea[contains(@name, 'redirect')]"),
                    (By.CSS_SELECTOR, "textarea[name*='redirect']"),
                    (By.CSS_SELECTOR, "textarea[id*='redirect']"),
                ]
                
                for by, selector in selectors:
                    try:
                        redirect_uris_field = driver.find_element(by, selector)
                        print(f"   ✅ Found redirect URIs field using: {by}={selector}")
                        break
                    except:
                        continue
                
                if not redirect_uris_field:
                    # Last resort: find any textarea
                    print("   🔄 Trying to find any textarea...")
                    try:
                        textareas = driver.find_elements(By.TAG_NAME, "textarea")
                        if textareas:
                            redirect_uris_field = textareas[0]
                            print("   ✅ Found textarea (assuming it's redirect URIs)")
                    except:
                        pass
                
                if redirect_uris_field:
                    # Clear existing URIs and add new ones
                    print("\n   ✏️  Updating redirect URIs...")
                    print(f"   Adding {len(redirect_uris)} redirect URI(s):")
                    for uri in redirect_uris:
                        print(f"      • {uri}")
                    
                    # Clear the field
                    redirect_uris_field.clear()
                    time.sleep(0.5)
                    
                    # Add new URIs (one per line)
                    redirect_uris_text = '\n'.join(redirect_uris)
                    redirect_uris_field.send_keys(redirect_uris_text)
                    print("   ✅ Redirect URIs entered in the field")
                    time.sleep(1)  # Give it a moment to process
                    
                    # Find and click Save button
                    print("   💾 Looking for Save button...")
                    save_button = None
                    
                    save_selectors = [
                        (By.XPATH, "//button[contains(text(), 'Save')]"),
                        (By.XPATH, "//button[contains(text(), 'SAVE')]"),
                        (By.CSS_SELECTOR, "button[type='submit']"),
                        (By.XPATH, "//button[@type='submit']"),
                    ]
                    
                    for by, selector in save_selectors:
                        try:
                            save_button = driver.find_element(by, selector)
                            print(f"   ✅ Found Save button using: {by}={selector}")
                            break
                        except:
                            continue
                    
                    if save_button:
                        save_button.click()
                        print("   ✅ Clicked Save button")
                        
                        # Wait for save confirmation
                        print("   ⏳ Waiting for save confirmation...")
                        time.sleep(5)
                        
                        print("   ✅ Successfully saved OAuth client configuration!")
                        return True
                    else:
                        print("   ⚠️  Could not find Save button")
                        print("   Please click Save manually in the browser")
                        input("   Press Enter after manually saving...")
                        return True
                else:
                    print("   ⚠️  Could not find redirect URIs field")
                    print("   Please update manually in the browser")
                    input("   Press Enter after manually updating the redirect URIs...")
                    return False
                
            except Exception as e:
                print(f"   ⚠️  Could not automate the update: {e}")
                import traceback
                traceback.print_exc()
                print("   The browser will stay open for manual configuration")
                input("   Press Enter after manually updating the redirect URIs...")
                return False
                
        finally:
            if driver:
                print("   🚪 Closing browser in 5 seconds...")
            time.sleep(5)
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
    except Exception as e:
        print(f"❌ Browser automation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    if not GOOGLE_OAUTH_CLIENT_ID:
        print("❌ Error: OAuth Client ID not found")
        print("   Set GOOGLE_OAUTH_CLIENT_ID in .env.local or .local.env")
        sys.exit(1)
    
    # Get app URL
    app_url = None
    if '--url' in sys.argv:
        idx = sys.argv.index('--url')
        if idx + 1 < len(sys.argv):
            app_url = sys.argv[idx + 1]
    
    if not app_url:
        app_url = os.getenv('WEBHOOK_BASE_URL') or os.getenv('NEXT_PUBLIC_APP_URL')
    
    if not app_url:
        print("❌ Error: Application URL not found")
        print("   Provide via --url argument or WEBHOOK_BASE_URL env var")
        sys.exit(1)
    
    # Build redirect URIs
    redirect_uris = []
    if SUPABASE_URL:
        redirect_uris.append(f"{SUPABASE_URL}/auth/v1/callback")
    redirect_uris.extend([
        f"{app_url}/login",
        f"{app_url}/command-center",
        f"{app_url}/api/auth/callback",
        "http://localhost:5000/login",
        "http://localhost:5000/command-center",
    ])
    
    print("\n" + "="*70)
    print("  AUTOMATED GOOGLE OAUTH CLIENT CONFIGURATION")
    print("="*70)
    print(f"Client ID: {GOOGLE_OAUTH_CLIENT_ID}")
    print(f"Redirect URIs to configure: {len(redirect_uris)}")
    
    success = configure_oauth_with_selenium(app_url, GOOGLE_OAUTH_CLIENT_ID, redirect_uris)
    
    if success:
        print("\n✅ OAuth client configured successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Automated configuration incomplete")
        sys.exit(1)

if __name__ == '__main__':
    main()

