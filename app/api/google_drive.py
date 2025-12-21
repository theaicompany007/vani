"""Google Drive API routes for RAG integration"""
from flask import Blueprint, request, jsonify, current_app
import logging
import os
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.auth import require_auth, require_super_user, get_current_user
import requests

logger = logging.getLogger(__name__)

google_drive_bp = Blueprint('google_drive', __name__)

# Supported MIME types
SUPPORTED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
    'text/markdown': '.md',
    'application/vnd.google-apps.document': '.docx',  # Google Docs exported as DOCX
}


def get_google_drive_service():
    """Get authenticated Google Drive service"""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Get service account credentials
        service_account_json = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON')
        service_account_path = os.getenv('GOOGLE_DRIVE_SERVICE_ACCOUNT_PATH')
        
        if not service_account_json and not service_account_path:
            raise ValueError('Google Drive service account not configured')
        
        if service_account_path:
            credentials_path = Path(service_account_path)
            if not credentials_path.exists():
                raise FileNotFoundError(f'Service account file not found: {credentials_path}')
            credentials = service_account.Credentials.from_service_account_file(
                str(credentials_path),
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
        else:
            credentials_dict = json.loads(service_account_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
        
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Error initializing Google Drive service: {e}")
        raise


@google_drive_bp.route('/api/drive/list', methods=['GET'])
@require_auth
@require_super_user
def list_drive_files():
    """List files and folders from Google Drive"""
    try:
        folder_id = request.args.get('folderId', 'root')
        mime_type = request.args.get('mimeType')
        
        drive_service = get_google_drive_service()
        
        # Build query
        query = f"'{folder_id}' in parents and trashed=false"
        if mime_type:
            query += f" and mimeType='{mime_type}'"
        else:
            # Filter for supported file types or folders
            query += " and (mimeType='application/vnd.google-apps.folder' or mimeType='application/pdf' or mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document' or mimeType='text/plain' or mimeType='text/markdown')"
        
        results = drive_service.files().list(
            q=query,
            fields='files(id, name, mimeType, size, modifiedTime, webViewLink)',
            orderBy='folder,name',
            pageSize=1000
        ).execute()
        
        files = []
        for file in results.get('files', []):
            files.append({
                'id': file.get('id'),
                'name': file.get('name', 'Unknown'),
                'mimeType': file.get('mimeType', ''),
                'size': int(file.get('size', 0)) if file.get('size') else None,
                'modifiedTime': file.get('modifiedTime'),
                'isFolder': file.get('mimeType') == 'application/vnd.google-apps.folder',
                'webViewLink': file.get('webViewLink'),
            })
        
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        logger.error(f"Error listing Drive files: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@google_drive_bp.route('/api/drive/file/<file_id>', methods=['GET'])
@require_auth
@require_super_user
def get_drive_file(file_id):
    """Get file metadata from Google Drive"""
    try:
        drive_service = get_google_drive_service()
        
        file = drive_service.files().get(
            fileId=file_id,
            fields='id, name, mimeType, size, modifiedTime, webViewLink, parents'
        ).execute()
        
        return jsonify({
            'success': True,
            'id': file.get('id'),
            'name': file.get('name', 'Unknown'),
            'mimeType': file.get('mimeType', ''),
            'size': int(file.get('size', 0)) if file.get('size') else None,
            'modifiedTime': file.get('modifiedTime'),
            'isFolder': file.get('mimeType') == 'application/vnd.google-apps.folder',
            'webViewLink': file.get('webViewLink'),
            'parents': file.get('parents', []),
        })
    except Exception as e:
        logger.error(f"Error getting Drive file: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@google_drive_bp.route('/api/drive/sync', methods=['POST'])
@require_auth
@require_super_user
def sync_drive_files():
    """Sync selected files from Google Drive to RAG"""
    try:
        data = request.get_json()
        file_ids = data.get('fileIds', [])
        
        if not file_ids or not isinstance(file_ids, list):
            return jsonify({'success': False, 'error': 'fileIds array is required'}), 400
        
        drive_service = get_google_drive_service()
        
        # Get RAG service configuration
        rag_service_url = os.getenv('RAG_SERVICE_URL', 'https://rag.theaicompany.co')
        rag_api_key = os.getenv('RAG_API_KEY')
        
        if not rag_api_key:
            return jsonify({'success': False, 'error': 'RAG service not configured'}), 500
        
        rag_headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {rag_api_key}',
            'x-api-key': rag_api_key
        }
        
        # Helper function to get folder path
        def get_folder_path(parent_id: Optional[str]) -> List[str]:
            """Get folder path from parent folder ID"""
            path = []
            current_id = parent_id
            
            while current_id and current_id != 'root':
                try:
                    file = drive_service.files().get(
                        fileId=current_id,
                        fields='id, name, parents'
                    ).execute()
                    if file.get('name'):
                        path.insert(0, file.get('name'))
                    current_id = file.get('parents', [None])[0] if file.get('parents') else None
                except:
                    break
            return path
        
        # Helper function to sanitize collection name
        def sanitize_collection_name(name: str, max_length: int = 50) -> str:
            """Sanitize folder/file name for collection name"""
            sanitized = ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in name.lower())
            sanitized = '_'.join(filter(None, sanitized.split('_')))
            if len(sanitized) > max_length:
                sanitized = sanitized[:max_length]
            return sanitized
        
        # Helper function to get collection name
        def get_collection_name(folder_path: List[str], doc_type: str = 'company_profiles') -> str:
            """Generate collection name from folder path"""
            if not folder_path:
                return f'google_drive_research_{doc_type}'
            sanitized = '_'.join([sanitize_collection_name(f) for f in folder_path])
            return f'{sanitized}_{doc_type}'
        
        results = []
        collections = set()
        
        for file_id in file_ids:
            try:
                # Get file metadata
                file_meta = drive_service.files().get(
                    fileId=file_id,
                    fields='id, name, mimeType, parents'
                ).execute()
                
                mime_type = file_meta.get('mimeType', '')
                file_name = file_meta.get('name', 'unknown')
                parent_id = file_meta.get('parents', [None])[0] if file_meta.get('parents') else None
                
                # Skip folders
                if mime_type == 'application/vnd.google-apps.folder':
                    continue
                
                # Skip unsupported file types
                if mime_type not in SUPPORTED_MIME_TYPES:
                    results.append({
                        'id': file_id,
                        'name': file_name,
                        'success': False,
                        'chunks': 0,
                        'collection': '',
                        'error': f'Unsupported file type: {mime_type}',
                    })
                    continue
                
                # Get folder path for collection naming
                folder_path = get_folder_path(parent_id)
                collection = get_collection_name(folder_path, 'company_profiles')
                collections.add(collection)
                
                # Download file
                ext = SUPPORTED_MIME_TYPES.get(mime_type, '.txt')
                tmp_path = None
                
                try:
                    from io import BytesIO
                    from googleapiclient.http import MediaIoBaseDownload
                    
                    file_handle = BytesIO()
                    
                    if mime_type == 'application/vnd.google-apps.document':
                        # Export Google Docs as DOCX
                        request = drive_service.files().export_media(
                            fileId=file_id,
                            mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                        )
                    else:
                        # Download regular files
                        request = drive_service.files().get_media(fileId=file_id)
                    
                    # Download file content
                    downloader = MediaIoBaseDownload(file_handle, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            logger.debug(f"Download progress: {int(status.progress() * 100)}%")
                    
                    # Write to temp file
                    file_handle.seek(0)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                        tmp_path = tmp_file.name
                        tmp_file.write(file_handle.read())
                    
                    # Process file (extract text, chunk, upload)
                    try:
                        # Extract text using existing knowledge base functions
                        from app.api.knowledge_base import (
                            extract_text_from_pdf,
                            extract_text_from_txt,
                            extract_text_from_doc
                        )
                        
                        if mime_type == 'application/pdf':
                            text = extract_text_from_pdf(tmp_path)
                        elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.google-apps.document']:
                            text = extract_text_from_doc(tmp_path)
                        else:
                            text = extract_text_from_txt(tmp_path)
                        
                        if not text or len(text.strip()) < 10:
                            raise ValueError('No text extracted or text too short')
                        
                        # Chunk text (simple chunking - 500 chars with 50 overlap)
                        def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
                            chunks = []
                            i = 0
                            while i < len(text):
                                chunk = text[i:i + chunk_size]
                                if chunk.strip():
                                    chunks.append(chunk)
                                i += chunk_size - overlap
                            return chunks
                        
                        chunks = chunk_text(text)
                        if not chunks:
                            raise ValueError('No chunks generated from text')
                        
                        # Prepare documents and metadatas
                        documents = chunks
                        metadatas = []
                        for i, chunk in enumerate(chunks):
                            metadatas.append({
                                'source': 'google_drive',
                                'filename': file_name,
                                'title': file_name,
                                'tags': 'google_drive,research',
                                'chunk_index': i,
                                'folder_path': '/'.join(folder_path) if folder_path else 'root',
                            })
                        
                        # Upload to RAG service
                        payload = {
                            'collection': collection,
                            'documents': documents,
                            'metadatas': metadatas
                        }
                        
                        rag_response = requests.post(
                            f"{rag_service_url}/rag/add",
                            json=payload,
                            headers=rag_headers,
                            timeout=60
                        )
                        
                        if rag_response.status_code == 200:
                            results.append({
                                'id': file_id,
                                'name': file_name,
                                'success': True,
                                'chunks': len(chunks),
                                'collection': collection,
                            })
                        else:
                            raise ValueError(f'RAG upload failed: {rag_response.status_code} - {rag_response.text}')
                
                    except Exception as process_error:
                        logger.error(f"Error processing file {file_id}: {process_error}")
                        results.append({
                            'id': file_id,
                            'name': file_name,
                            'success': False,
                            'chunks': 0,
                            'collection': collection,
                            'error': str(process_error),
                        })
                    finally:
                        # Clean up temp file
                        if tmp_path:
                            try:
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                            except Exception as cleanup_error:
                                logger.warning(f"Could not clean up temp file {tmp_path}: {cleanup_error}")
                
                except Exception as download_error:
                    logger.error(f"Error downloading file {file_id}: {download_error}")
                    results.append({
                        'id': file_id,
                        'name': file_name,
                        'success': False,
                        'chunks': 0,
                        'collection': '',
                        'error': f'Download failed: {str(download_error)}',
                    })
            
            except Exception as error:
                logger.error(f"Failed to process file {file_id}: {error}")
                results.append({
                    'id': file_id,
                    'name': 'unknown',
                    'success': False,
                    'chunks': 0,
                    'collection': '',
                    'error': str(error),
                })
        
        synced = sum(1 for r in results if r['success'])
        failed = sum(1 for r in results if not r['success'])
        
        return jsonify({
            'success': True,
            'synced': synced,
            'failed': failed,
            'collections': list(collections),
            'results': results,
        })
    
    except Exception as e:
        logger.error(f"Error syncing Drive files: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

