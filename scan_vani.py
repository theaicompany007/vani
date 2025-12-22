"""Comprehensive scan of VANI project for errors and bugs"""
import os
import sys
import ast
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple

class VaniScanner:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.errors = []
        self.warnings = []
        self.info = []
    
    def scan(self) -> Dict:
        """Run comprehensive scan"""
        print("=" * 60)
        print("VANI PROJECT SCAN")
        print("=" * 60)
        
        # 1. Check Python syntax
        print("\n[1/8] Checking Python syntax...")
        self.check_python_syntax()
        
        # 2. Check imports
        print("\n[2/8] Checking imports...")
        self.check_imports()
        
        # 3. Check required files
        print("\n[3/8] Checking required files...")
        self.check_required_files()
        
        # 4. Check environment variables
        print("\n[4/8] Checking environment variables...")
        self.check_env_vars()
        
        # 5. Check database migrations
        print("\n[5/8] Checking database migrations...")
        self.check_migrations()
        
        # 6. Check Flask app structure
        print("\n[6/8] Checking Flask app structure...")
        self.check_flask_structure()
        
        # 7. Check API routes
        print("\n[7/8] Checking API routes...")
        self.check_api_routes()
        
        # 8. Check for common issues
        print("\n[8/8] Checking for common issues...")
        self.check_common_issues()
        
        # Summary
        print("\n" + "=" * 60)
        print("SCAN SUMMARY")
        print("=" * 60)
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Info: {len(self.info)}")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if self.info:
            print("\nℹ️  INFO:")
            for i, info in enumerate(self.info, 1):
                print(f"  {i}. {info}")
        
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }
    
    def check_python_syntax(self):
        """Check Python syntax in all .py files"""
        py_files = list(self.root_dir.rglob('*.py'))
        py_files = [f for f in py_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                ast.parse(code)
            except SyntaxError as e:
                self.errors.append(f"Syntax error in {py_file.relative_to(self.root_dir)}: {e}")
            except Exception as e:
                self.warnings.append(f"Could not parse {py_file.relative_to(self.root_dir)}: {e}")
        
        self.info.append(f"Checked {len(py_files)} Python files")
    
    def check_imports(self):
        """Check for missing imports"""
        critical_files = [
            'app/__init__.py',
            'app/routes.py',
            'app/supabase_client.py',
            'app/auth/__init__.py',
            'run.py'
        ]
        
        for file_path in critical_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                self.errors.append(f"Missing file: {file_path}")
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for common import issues
                if 'from app.auth import' in content and not (self.root_dir / 'app' / 'auth' / '__init__.py').exists():
                    self.errors.append(f"{file_path} imports app.auth but module doesn't exist")
            except Exception as e:
                self.warnings.append(f"Could not check imports in {file_path}: {e}")
    
    def check_required_files(self):
        """Check for required files"""
        required = [
            'app/__init__.py',
            'app/routes.py',
            'app/supabase_client.py',
            'app/auth/__init__.py',
            'run.py',
            'requirements.txt',
            '.env.local'
        ]
        
        for file_path in required:
            full_path = self.root_dir / file_path
            if full_path.exists():
                self.info.append(f"✓ {file_path} exists")
            else:
                if file_path == '.env.local':
                    self.warnings.append(f"⚠ {file_path} not found (may be gitignored)")
                else:
                    self.errors.append(f"Missing required file: {file_path}")
    
    def check_env_vars(self):
        """Check for required environment variables"""
        env_file = self.root_dir / '.env.local'
        if not env_file.exists():
            self.warnings.append("Cannot check env vars - .env.local not found")
            return
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_vars = [
                'SUPABASE_URL',
                'SUPABASE_KEY',
                'SUPABASE_SERVICE_KEY',
                'RESEND_API_KEY',
                'TWILIO_ACCOUNT_SID',
                'TWILIO_AUTH_TOKEN',
                'OPENAI_API_KEY'
            ]
            
            for var in required_vars:
                if var in content:
                    self.info.append(f"✓ {var} found in .env.local")
                else:
                    self.warnings.append(f"⚠ {var} not found in .env.local")
        except Exception as e:
            self.warnings.append(f"Could not read .env.local: {e}")
    
    def check_migrations(self):
        """Check database migrations"""
        migrations_dir = self.root_dir / 'app' / 'migrations'
        if not migrations_dir.exists():
            self.errors.append("Migrations directory not found")
            return
        
        expected_migrations = [
            '001_create_tables.sql',
            '002_industries_tenants.sql',
            '003_auth_permissions.sql',
            '004_pitch_storage.sql',
            '005_add_industry_to_tables.sql'
        ]
        
        for migration in expected_migrations:
            if (migrations_dir / migration).exists():
                self.info.append(f"✓ Migration {migration} exists")
            else:
                self.errors.append(f"Missing migration: {migration}")
    
    def check_flask_structure(self):
        """Check Flask app structure"""
        app_init = self.root_dir / 'app' / '__init__.py'
        if not app_init.exists():
            self.errors.append("app/__init__.py not found")
            return
        
        try:
            with open(app_init, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for create_app function
            if 'def create_app' in content:
                self.info.append("✓ create_app function found")
            else:
                self.errors.append("create_app function not found in app/__init__.py")
            
            # Check for auth initialization
            if 'from .auth import init_auth' in content:
                auth_module = self.root_dir / 'app' / 'auth' / '__init__.py'
                if auth_module.exists():
                    self.info.append("✓ Auth module import and file exist")
                else:
                    self.errors.append("app/__init__.py imports app.auth but module doesn't exist")
        except Exception as e:
            self.errors.append(f"Could not check Flask structure: {e}")
    
    def check_api_routes(self):
        """Check API route files"""
        api_dir = self.root_dir / 'app' / 'api'
        if not api_dir.exists():
            self.warnings.append("app/api directory not found")
            return
        
        expected_routes = [
            'auth.py',
            'targets.py',
            'outreach.py',
            'dashboard.py',
            'message_generator.py',
            'permissions.py',
            'industries.py',
            'pitch.py'
        ]
        
        for route_file in expected_routes:
            if (api_dir / route_file).exists():
                self.info.append(f"✓ API route {route_file} exists")
            else:
                self.warnings.append(f"API route {route_file} not found")
    
    def check_common_issues(self):
        """Check for common issues"""
        # Check for hardcoded credentials
        py_files = list(self.root_dir.rglob('*.py'))
        py_files = [f for f in py_files if 'venv' not in str(f)]
        
        for py_file in py_files[:20]:  # Limit to first 20 files
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for hardcoded API keys
                if 'api_key' in content.lower() and 'os.getenv' not in content and 'os.environ' not in content:
                    self.warnings.append(f"Possible hardcoded API key in {py_file.relative_to(self.root_dir)}")
            except:
                pass

if __name__ == '__main__':
    root = Path(__file__).parent
    scanner = VaniScanner(root)
    results = scanner.scan()
    
    # Exit with error code if errors found
    sys.exit(1 if results['errors'] else 0)






















