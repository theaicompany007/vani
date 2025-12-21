#!/usr/bin/env python3
"""
Knowledge Base Upload Script
Uploads PDF, DOC, and TXT files to RAG knowledge base with platform-specific collection mapping.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env.local')
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Platform keywords mapping
PLATFORM_KEYWORDS = {
    'the_ai_company_genai_platform': ['genai', 'agentic', 'genai platform', 'theaicompany'],
    'the_ai_company_revenue_growth': ['revenue growth', 'revenue', 'rgp', 'onlynereputation-agentic-app'],
    'the_ai_company_vani': ['vani', 'virtual agent', 'project vani'],
    'neura360_signal': ['neura signal', 'signal', 'listening', 'contextual'],
    'neura360_spark': ['neura spark', 'spark', 'anomaly', 'early detection'],
    'neura360_risk': ['neura risk', 'risk', 'crisis', 'foresight'],
    'neura360_narrative': ['neura narrative', 'narrative', 'influencer', 'counter-messaging'],
    'neura360_trend': ['neura trend', 'trend', 'whitespace', 'category'],
    'neura360_agents': ['neura agents', 'agents', 'autonomous', 'workflow'],
}

# Document type keywords
DOCUMENT_TYPE_KEYWORDS = {
    'case_studies': ['case study', 'case_study', 'case-study', 'success story', 'client story'],
    'services': ['service', 'services', 'offering', 'offerings', 'solution', 'solutions'],
    'faqs': ['faq', 'faqs', 'frequently asked', 'questions', 'q&a', 'q and a'],
    'company_profiles': ['profile', 'company', 'about', 'overview'],
    'industry_insights': ['insight', 'insights', 'industry', 'trend', 'analysis', 'market'],
    'platforms': ['platform', 'documentation', 'api', 'architecture', 'technical', 'spec', 'guide'],
}

# Company detection
COMPANY_KEYWORDS = {
    'The AI Company': ['the ai company', 'theaicompany', 'ai company'],
    'Onlyne Reputation': ['onlyne reputation', 'onlynereputation', 'onlyne'],
}


def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into chunks with overlap"""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            if break_point > max_chunk_size * 0.5:  # Only break if we're at least halfway
                chunk = text[start:start + break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap  # Overlap for context
    
    return chunks


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except ImportError:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode text file with any supported encoding")


def extract_text_from_doc(file_path: str) -> str:
    """Extract text from DOC/DOCX file"""
    try:
        import docx
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
        return text
    except ImportError:
        logger.error("python-docx library not installed. Please install it with: pip install python-docx")
        raise
    except Exception as e:
        logger.error(f"Error extracting text from DOC/DOCX: {e}")
        raise


def detect_platform(file_path: Path, folder_path: Path, filename: str) -> Optional[str]:
    """Detect platform from file path and name"""
    path_str = str(file_path).lower()
    folder_str = str(folder_path).lower()
    filename_lower = filename.lower()
    
    # Check folder structure first
    for platform_slug, keywords in PLATFORM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in folder_str or keyword in path_str:
                return platform_slug
    
    # Check filename
    for platform_slug, keywords in PLATFORM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return platform_slug
    
    return None


def detect_company(file_path: Path, folder_path: Path) -> Optional[str]:
    """Detect company from file path"""
    path_str = str(file_path).lower()
    folder_str = str(folder_path).lower()
    
    for company, keywords in COMPANY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in folder_str or keyword in path_str:
                return company
    
    return None


def detect_document_type(file_path: Path, filename: str) -> str:
    """Detect document type from filename and path"""
    path_str = str(file_path).lower()
    filename_lower = filename.lower()
    
    for doc_type, keywords in DOCUMENT_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in filename_lower or keyword in path_str:
                return doc_type
    
    return 'company_profiles'  # Default


def create_collection_name(platform: Optional[str], document_type: str, company: Optional[str]) -> str:
    """Create collection name from platform and document type"""
    if platform:
        # Platform already includes company prefix
        return f"{platform}_{document_type}"
    elif company:
        # Use company slug
        company_slug = company.lower().replace(' ', '_').replace('-', '_')
        return f"{company_slug}_{document_type}"
    else:
        # Default fallback
        return f"general_{document_type}"


def upload_to_rag(
    collection: str,
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    rag_service_url: str,
    rag_api_key: str
) -> bool:
    """Upload documents to RAG service"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {rag_api_key}',
        'x-api-key': rag_api_key
    }
    
    payload = {
        'collection': collection,
        'documents': documents,
        'metadatas': metadatas
    }
    
    try:
        response = requests.post(
            f"{rag_service_url}/rag/add",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            return True
        else:
            logger.error(f"RAG service error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error uploading to RAG: {e}")
        return False


def process_file(
    file_path: Path,
    base_folder: Path,
    company: Optional[str] = None,
    platform: Optional[str] = None,
    document_type: Optional[str] = None,
    collection: Optional[str] = None,
    tags: List[str] = None,
    dry_run: bool = False,
    rag_service_url: str = None,
    rag_api_key: str = None
) -> Dict[str, Any]:
    """Process a single file and upload to RAG"""
    tags = tags or []
    result = {
        'filename': file_path.name,
        'file_path': str(file_path),
        'success': False,
        'error': None,
        'chunks_added': 0,
        'collection': None
    }
    
    try:
        # Detect platform, company, document type if not provided
        if not company:
            company = detect_company(file_path, base_folder)
        
        if not platform:
            platform = detect_platform(file_path, base_folder, file_path.name)
        
        if not document_type:
            document_type = detect_document_type(file_path, file_path.name)
        
        # Create collection name
        if not collection:
            collection = create_collection_name(platform, document_type, company)
        
        result['collection'] = collection
        result['platform'] = platform
        result['company'] = company
        result['document_type'] = document_type
        
        # Extract text based on file extension
        file_ext = file_path.suffix.lower()
        if file_ext == '.pdf':
            text = extract_text_from_pdf(str(file_path))
        elif file_ext in ['.doc', '.docx']:
            text = extract_text_from_doc(str(file_path))
        elif file_ext == '.txt':
            text = extract_text_from_txt(str(file_path))
        else:
            result['error'] = f'Unsupported file type: {file_ext}'
            return result
        
        if not text or not text.strip():
            result['error'] = 'Could not extract text from file'
            return result
        
        # Chunk the text
        chunks = chunk_text(text)
        result['chunks_added'] = len(chunks)
        
        if dry_run:
            result['success'] = True
            result['message'] = f'Would upload {len(chunks)} chunk(s) to collection {collection}'
            return result
        
        # Prepare documents and metadatas
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            chunk_metadata = {
                'filename': file_path.name,
                'file_path': str(file_path.relative_to(base_folder)),
                'file_size': file_path.stat().st_size,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'tags': ','.join(tags) if tags else '',
                'source': 'file_upload',
                'uploaded_at': datetime.utcnow().isoformat(),
                'company': company or 'unknown',
                'platform': platform or 'unknown',
                'document_type': document_type
            }
            metadatas.append(chunk_metadata)
        
        # Upload to RAG
        if upload_to_rag(collection, documents, metadatas, rag_service_url, rag_api_key):
            result['success'] = True
            result['message'] = f'Successfully uploaded {len(chunks)} chunk(s) to collection {collection}'
        else:
            result['error'] = 'Failed to upload to RAG service'
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        result['error'] = str(e)
    
    return result


def check_folder_structure(folder: Path) -> Dict[str, Any]:
    """Check if folder follows recommended structure"""
    result = {
        'exists': False,
        'missing': [],
        'found': []
    }
    
    # Check for company folders
    ai_company_folder = folder / 'The AI Company'
    onlyne_folder = folder / 'Onlyne Reputation'
    
    if ai_company_folder.exists():
        result['found'].append('The AI Company')
    else:
        result['missing'].append('The AI Company')
    
    if onlyne_folder.exists():
        result['found'].append('Onlyne Reputation')
    else:
        result['missing'].append('Onlyne Reputation')
    
    # If at least one company folder exists, structure is partially there
    result['exists'] = len(result['found']) > 0
    
    return result


def scan_folder(
    folder: Path,
    company: Optional[str] = None,
    platform: Optional[str] = None,
    recursive: bool = True,
    tags: List[str] = None
) -> List[Path]:
    """Scan folder for PDF, DOC, DOCX, and TXT files"""
    files = []
    extensions = {'.pdf', '.doc', '.docx', '.txt'}
    
    pattern = '**/*' if recursive else '*'
    for file_path in folder.glob(pattern):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            files.append(file_path)
    
    return files


def main():
    parser = argparse.ArgumentParser(description='Upload files to RAG knowledge base')
    parser.add_argument('--folder', required=True, help='Source folder path')
    parser.add_argument('--company', help='Filter by company (The AI Company or Onlyne Reputation)')
    parser.add_argument('--platform', help='Filter by specific platform/product')
    parser.add_argument('--collection', help='Override auto-detected collection name')
    parser.add_argument('--document-type', help='Override auto-detected document type')
    parser.add_argument('--dry-run', action='store_true', help='Preview without uploading')
    parser.add_argument('--tags', help='Add custom tags (comma-separated)')
    parser.add_argument('--recursive', action='store_true', default=True, help='Scan subfolders recursively')
    parser.add_argument('--no-recursive', dest='recursive', action='store_false', help='Do not scan subfolders')
    
    args = parser.parse_args()
    
    # Get RAG configuration
    rag_service_url = os.getenv('RAG_SERVICE_URL', 'https://rag.theaicompany.co')
    rag_api_key = os.getenv('RAG_API_KEY')
    
    if not rag_api_key and not args.dry_run:
        logger.error("RAG_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Parse tags
    tags = [tag.strip() for tag in args.tags.split(',')] if args.tags else []
    
    # Scan folder
    folder = Path(args.folder)
    if not folder.exists():
        logger.error(f"Folder does not exist: {folder}")
        sys.exit(1)
    
    # Check for recommended folder structure
    recommended_structure = check_folder_structure(folder)
    if not recommended_structure['exists']:
        logger.warning("⚠ Recommended folder structure not found!")
        logger.warning("Consider running: python scripts/setup_knowledge_base_folders.py --base-folder <path>")
        logger.warning("Files will still be processed, but organization may be suboptimal.")
    
    logger.info(f"Scanning folder: {folder}")
    files = scan_folder(folder, args.company, args.platform, args.recursive, tags)
    logger.info(f"Found {len(files)} files to process")
    
    if not files:
        logger.warning("No files found to process")
        return
    
    # Process files
    results = []
    for i, file_path in enumerate(files, 1):
        logger.info(f"Processing [{i}/{len(files)}]: {file_path.name}")
        result = process_file(
            file_path,
            folder,
            args.company,
            args.platform,
            args.document_type,
            args.collection,
            tags,
            args.dry_run,
            rag_service_url,
            rag_api_key
        )
        results.append(result)
        
        if result['success']:
            logger.info(f"✓ {result.get('message', 'Success')}")
        else:
            logger.warning(f"✗ {result.get('error', 'Failed')}")
    
    # Generate summary
    success_count = sum(1 for r in results if r.get('success'))
    failed_count = len(results) - success_count
    
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total files: {len(results)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {failed_count}")
    
    # Save report
    report_file = f"upload_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'folder': str(folder),
            'total_files': len(results),
            'successful': success_count,
            'failed': failed_count,
            'results': results
        }, f, indent=2)
    
    logger.info(f"Report saved to: {report_file}")
    
    if failed_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()

