"""Admin API routes for super users - script execution and system management"""
from flask import Blueprint, request, jsonify, current_app
import logging
import subprocess
import os
import json
from pathlib import Path
from datetime import datetime
from app.auth import require_auth, require_super_user
from app.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/admin/scripts/run', methods=['POST'])
@require_auth
@require_super_user
def run_script():
    """Run a script with parameters (super admin only)"""
    try:
        data = request.get_json()
        script_name = data.get('script')
        script_args = data.get('args', [])
        script_kwargs = data.get('kwargs', {})
        
        if not script_name:
            return jsonify({'error': 'Script name is required'}), 400
        
        # Validate script exists
        script_path = Path(__file__).parent.parent.parent / 'scripts' / script_name
        if not script_path.exists():
            return jsonify({'error': f'Script not found: {script_name}'}), 404
        
        # Build command
        cmd = ['python', str(script_path)]
        
        # Add positional arguments
        for arg in script_args:
            cmd.append(str(arg))
        
        # Add keyword arguments
        for key, value in script_kwargs.items():
            if isinstance(value, bool) and value:
                cmd.append(f'--{key}')
            elif not isinstance(value, bool):
                cmd.append(f'--{key}')
                cmd.append(str(value))
        
        logger.info(f"Executing script: {' '.join(cmd)}")
        
        # Run script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        return jsonify({
            'success': True,
            'script': script_name,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'command': ' '.join(cmd)
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'error': 'Script execution timed out (1 hour limit)',
            'script': script_name
        }), 500
    except Exception as e:
        logger.error(f"Error running script: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/admin/scripts/list', methods=['GET'])
@require_auth
@require_super_user
def list_scripts():
    """List available scripts (super admin only)"""
    try:
        scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
        scripts = []
        
        for script_file in scripts_dir.glob('*.py'):
            if script_file.name.startswith('_'):
                continue
            
            # Read script docstring for description
            description = ''
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    first_lines = f.read(500)
                    if '"""' in first_lines:
                        doc_start = first_lines.find('"""') + 3
                        doc_end = first_lines.find('"""', doc_start)
                        if doc_end > doc_start:
                            description = first_lines[doc_start:doc_end].strip()
            except:
                pass
            
            scripts.append({
                'name': script_file.name,
                'path': str(script_file),
                'description': description or 'No description available',
                'size': script_file.stat().st_size,
                'modified': datetime.fromtimestamp(script_file.stat().st_mtime).isoformat()
            })
        
        return jsonify({
            'success': True,
            'scripts': sorted(scripts, key=lambda x: x['name'])
        })
        
    except Exception as e:
        logger.error(f"Error listing scripts: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/admin/scripts/import-contacts', methods=['POST'])
@require_auth
@require_super_user
def import_contacts_script():
    """Run batch contact import script via API (super admin only)"""
    try:
        data = request.get_json()
        excel_file = data.get('excel_file')
        batch_size = data.get('batch_size', 100)
        threads = data.get('threads', 4)
        update_existing = data.get('update_existing', False)
        import_only_new = data.get('import_only_new', False)
        sheet = data.get('sheet')
        dry_run = data.get('dry_run', False)
        
        if not excel_file:
            return jsonify({'error': 'excel_file is required'}), 400
        
        # Validate file exists
        file_path = Path(excel_file)
        if not file_path.is_absolute():
            # Try relative to data directory
            file_path = Path(__file__).parent.parent.parent / 'data' / excel_file
        
        if not file_path.exists():
            return jsonify({'error': f'Excel file not found: {excel_file}'}), 404
        
        # Build command
        cmd = [
            'python',
            str(Path(__file__).parent.parent.parent / 'scripts' / 'import_contacts_batch.py'),
            str(file_path),
            '--batch-size', str(batch_size),
            '--threads', str(threads)
        ]
        
        if update_existing:
            cmd.append('--update-existing')
        if import_only_new:
            cmd.append('--import-only-new')
        if sheet:
            cmd.extend(['--sheet', sheet])
        if dry_run:
            cmd.append('--dry-run')
        
        logger.info(f"Executing batch import: {' '.join(cmd)}")
        
        # Run script in background (non-blocking)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        
        return jsonify({
            'success': True,
            'message': 'Batch import started',
            'process_id': process.pid,
            'command': ' '.join(cmd),
            'note': 'Check logs for progress'
        })
        
    except Exception as e:
        logger.error(f"Error starting batch import: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/api/admin/system/info', methods=['GET'])
@require_auth
@require_super_user
def system_info():
    """Get system information (super admin only)"""
    try:
        import platform
        import sys
        
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': sys.version.split()[0],  # Just version number
            'python_full_version': sys.version,
        }
        
        # Try to get psutil info, but don't fail if it's not available
        try:
            import psutil
            info.update({
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'memory_available_gb': round(psutil.virtual_memory().available / (1024**3), 2),
                'memory_used_percent': psutil.virtual_memory().percent,
            })
            
            # Get disk usage for project directory
            try:
                import os
                if os.name == 'nt':  # Windows
                    # On Windows, use the root drive directly (e.g., C:\)
                    project_dir = Path(__file__).parent.parent.parent
                    project_path = project_dir.resolve()
                    # Get the drive letter (e.g., 'C:')
                    drive_letter = os.path.splitdrive(str(project_path))[0]
                    if not drive_letter:
                        # Fallback to current working directory drive
                        drive_letter = os.path.splitdrive(os.getcwd())[0]
                    # Format as C:\ for psutil
                    disk_path = drive_letter + os.sep
                    disk = psutil.disk_usage(disk_path)
                else:
                    # Unix-like systems - use project directory
                    project_dir = Path(__file__).parent.parent.parent
                    project_path = project_dir.resolve()
                    disk = psutil.disk_usage(str(project_path))
                
                info['disk_usage'] = {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'percent': round((disk.used / disk.total) * 100, 2)
                }
            except Exception as disk_error:
                logger.warning(f"Could not get disk usage: {disk_error}", exc_info=True)
                info['disk_usage'] = {
                    'total_gb': 'N/A',
                    'used_gb': 'N/A',
                    'free_gb': 'N/A',
                    'percent': 'N/A'
                }
        except ImportError:
            logger.warning("psutil not available, system info will be limited")
            info.update({
                'cpu_count': 'N/A (psutil not installed)',
                'memory_total_gb': 'N/A (psutil not installed)',
                'memory_available_gb': 'N/A (psutil not installed)',
                'memory_used_percent': 'N/A (psutil not installed)',
                'disk_usage': {
                    'total_gb': 'N/A (psutil not installed)',
                    'used_gb': 'N/A (psutil not installed)',
                    'free_gb': 'N/A (psutil not installed)',
                    'percent': 'N/A (psutil not installed)'
                }
            })
        except Exception as psutil_error:
            logger.warning(f"Error getting psutil info: {psutil_error}")
            info.update({
                'cpu_count': f'Error: {str(psutil_error)[:50]}',
                'memory_total_gb': 'N/A',
                'memory_available_gb': 'N/A',
                'memory_used_percent': 'N/A',
                'disk_usage': {
                    'total_gb': 'N/A',
                    'used_gb': 'N/A',
                    'free_gb': 'N/A',
                    'percent': 'N/A'
                }
            })
        
        return jsonify({
            'success': True,
            'system_info': info
        })
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}", exc_info=True)
        return jsonify({'error': str(e), 'details': str(e)}), 500

