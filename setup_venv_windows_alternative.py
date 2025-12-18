#!/usr/bin/env python3
"""
VANI App - Windows Virtual Environment Setup (Alternative Python Script)
This script handles the psycopg2-binary installation issue on Windows.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description, ignore_error=False):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"[STEP] {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0 and not ignore_error:
        print(f"[ERROR] {description} failed!")
        if result.stderr:
            print(result.stderr)
        return False
    
    return True

def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("[WARNING] Python 3.11+ is recommended for VANI")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    return True

def main():
    """Main setup function."""
    print("""
    ============================================================
      VANI App - Windows Virtual Environment Setup            
      Alternative Python-based Installer                      
    ============================================================
    """)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not os.path.exists('requirements.txt'):
        print("[ERROR] requirements.txt not found!")
        print("Please run this script from the vani-app directory")
        sys.exit(1)
    
    # Remove old venv if exists
    venv_path = Path('venv')
    if venv_path.exists():
        print("\n[INFO] Removing old virtual environment...")
        import shutil
        shutil.rmtree(venv_path, ignore_errors=True)
    
    # Create virtual environment
    if not run_command(
        f'"{sys.executable}" -m venv venv',
        "Creating virtual environment"
    ):
        sys.exit(1)
    
    # Determine the pip executable path
    if sys.platform == 'win32':
        pip_exe = os.path.join('venv', 'Scripts', 'pip.exe')
        python_exe = os.path.join('venv', 'Scripts', 'python.exe')
    else:
        pip_exe = os.path.join('venv', 'bin', 'pip')
        python_exe = os.path.join('venv', 'bin', 'python')
    
    # Upgrade pip
    if not run_command(
        f'"{python_exe}" -m pip install --upgrade pip setuptools wheel',
        "Upgrading pip, setuptools, and wheel"
    ):
        sys.exit(1)
    
    # Try to install psycopg2-binary with pre-built wheels first
    print("\n[INFO] Attempting to install psycopg2-binary with pre-built wheels...")
    
    # Try multiple versions that are known to have Windows wheels
    psycopg2_versions = [
        'psycopg2-binary',  # Latest
        'psycopg2-binary==2.9.9',
        'psycopg2-binary==2.9.5',
        'psycopg2-binary==2.9.3'
    ]
    
    psycopg2_installed = False
    for version in psycopg2_versions:
        print(f"\n[ATTEMPT] Trying {version}...")
        result = subprocess.run(
            f'"{pip_exe}" install {version} --only-binary :all:',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"[SUCCESS] Installed {version}")
            psycopg2_installed = True
            break
        else:
            print(f"[FAILED] Could not install {version}")
    
    if not psycopg2_installed:
        print("\n" + "="*60)
        print("[ERROR] Could not install psycopg2-binary with pre-built wheels")
        print("="*60)
        print("\nSOLUTION OPTIONS:")
        print("1. Install Microsoft C++ Build Tools:")
        print("   https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        print("\n2. Install Visual Studio Community (includes Build Tools):")
        print("   https://visualstudio.microsoft.com/downloads/")
        print("\n3. Continue without psycopg2-binary (may cause issues)")
        print("="*60)
        
        response = input("\nContinue without psycopg2-binary? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Install remaining dependencies
    print("\n[INFO] Installing remaining dependencies from requirements.txt...")
    
    # Read requirements and filter out psycopg2-binary if already installed
    with open('requirements.txt', 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Filter out psycopg2-binary from requirements
    filtered_requirements = [req for req in requirements if 'psycopg2' not in req.lower()]
    
    # Write temporary requirements file
    temp_req_file = 'requirements_temp.txt'
    with open(temp_req_file, 'w') as f:
        f.write('\n'.join(filtered_requirements))
    
    if not run_command(
        f'"{pip_exe}" install -r {temp_req_file}',
        "Installing dependencies"
    ):
        os.remove(temp_req_file)
        sys.exit(1)
    
    # Clean up
    os.remove(temp_req_file)
    
    # Verify installation
    print("\n[INFO] Verifying installation...")
    verification_code = """
import sys
try:
    import flask
    import supabase
    import dotenv
    print('[SUCCESS] Core packages installed successfully!')
    sys.exit(0)
except ImportError as e:
    print(f'[ERROR] Import failed: {e}')
    sys.exit(1)
"""
    
    with open('verify_install.py', 'w') as f:
        f.write(verification_code)
    
    result = subprocess.run(
        f'"{python_exe}" verify_install.py',
        shell=True,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    os.remove('verify_install.py')
    
    if result.returncode != 0:
        print("[ERROR] Verification failed!")
        sys.exit(1)
    
    # Success message
    print(f"""
    ============================================================
      SUCCESS! Virtual Environment Setup Complete             
    ============================================================
    
    To activate the virtual environment:
    
    Windows (PowerShell):
        .\\venv\\Scripts\\Activate.ps1
    
    Windows (Command Prompt):
        venv\\Scripts\\activate.bat
    
    Then run VANI:
        python run.py
    
    Or use the existing VANI.bat file
    ============================================================
    """)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

