#!/usr/bin/env python3
"""
Supabase Case Studies Import Script
Imports case studies from Supabase database + supplementary txt file.
"""
import os
import sys
import json
import logging
import argparse
import csv
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


def parse_txt_file(txt_file: Path) -> Dict[str, Any]:
    """Parse supplementary txt file - supports plain text, JSON, or CSV"""
    content = txt_file.read_text(encoding='utf-8', errors='ignore')
    
    # Try JSON first
    try:
        data = json.loads(content)
        return {'format': 'json', 'data': data}
    except json.JSONDecodeError:
        pass
    
    # Try CSV
    try:
        csv_reader = csv.DictReader(content.splitlines())
        rows = list(csv_reader)
        if rows:
            return {'format': 'csv', 'data': rows}
    except:
        pass
    
    # Default to plain text
    return {'format': 'text', 'data': content}


def connect_to_supabase(connection_string: str):
    """Connect to Supabase using connection string"""
    try:
        from supabase import create_client, Client
        import re
        
        # Parse connection string: postgresql://user:pass@host:port/db
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', connection_string)
        if not match:
            # Try alternative format or use Supabase client
            # For Supabase, we might need URL and key instead
            logger.warning("Could not parse connection string, trying Supabase client...")
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            if supabase_url and supabase_key:
                return create_client(supabase_url, supabase_key)
            else:
                raise ValueError("Could not connect to Supabase. Need SUPABASE_URL and SUPABASE_KEY or valid connection string.")
        
        # For direct PostgreSQL connection, use psycopg2
        import psycopg2
        user, password, host, port, database = match.groups()
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {e}")
        raise


def query_case_studies(
    connection,
    company: Optional[str] = None,
    platform: Optional[str] = None,
    industry: Optional[str] = None,
    date_from: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Query case studies from Supabase"""
    try:
        # Try Supabase client first
        if hasattr(connection, 'table'):
            query = connection.table('case_studies').select('*')
            
            if company:
                query = query.eq('company', company)
            if platform:
                query = query.eq('platform', platform)
            if industry:
                query = query.eq('industry', industry)
            if date_from:
                query = query.gte('created_at', date_from)
            
            result = query.execute()
            return result.data if hasattr(result, 'data') else result
        
        # Otherwise use direct PostgreSQL
        else:
            import psycopg2.extras
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            query = "SELECT * FROM case_studies WHERE 1=1"
            params = []
            
            if company:
                query += " AND company = %s"
                params.append(company)
            if platform:
                query += " AND platform = %s"
                params.append(platform)
            if industry:
                query += " AND industry = %s"
                params.append(industry)
            if date_from:
                query += " AND created_at >= %s"
                params.append(date_from)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    except Exception as e:
        logger.error(f"Error querying case studies: {e}")
        # If table doesn't exist, return empty list
        return []


def merge_case_study_data(
    case_study: Dict[str, Any],
    txt_data: Dict[str, Any]
) -> str:
    """Merge case study from database with supplementary txt file data"""
    # Build comprehensive case study document
    parts = []
    
    # Title
    title = case_study.get('title') or case_study.get('name') or 'Case Study'
    parts.append(f"# {title}\n")
    
    # Company/Client
    if case_study.get('company') or case_study.get('client'):
        parts.append(f"**Client:** {case_study.get('company') or case_study.get('client')}\n")
    
    # Industry
    if case_study.get('industry'):
        parts.append(f"**Industry:** {case_study.get('industry')}\n")
    
    # Platform
    if case_study.get('platform'):
        parts.append(f"**Platform:** {case_study.get('platform')}\n")
    
    # Description
    if case_study.get('description'):
        parts.append(f"\n## Description\n{case_study.get('description')}\n")
    
    # Merge with txt file data
    if txt_data['format'] == 'json':
        # JSON data - merge fields
        json_data = txt_data['data']
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if key not in ['title', 'company', 'client', 'industry', 'platform', 'description']:
                    parts.append(f"\n## {key.replace('_', ' ').title()}\n{value}\n")
        elif isinstance(json_data, list):
            # List of case studies - find matching one or use first
            matching = None
            for item in json_data:
                if isinstance(item, dict):
                    # Try to match by title or company
                    if (item.get('title') == title or 
                        item.get('company') == case_study.get('company')):
                        matching = item
                        break
            if not matching and json_data:
                matching = json_data[0]
            
            if matching:
                for key, value in matching.items():
                    if key not in ['title', 'company', 'client', 'industry', 'platform', 'description']:
                        parts.append(f"\n## {key.replace('_', ' ').title()}\n{value}\n")
    
    elif txt_data['format'] == 'csv':
        # CSV data - find matching row
        csv_data = txt_data['data']
        matching = None
        for row in csv_data:
            if (row.get('title') == title or 
                row.get('company') == case_study.get('company')):
                matching = row
                break
        
        if matching:
            for key, value in matching.items():
                if key not in ['title', 'company', 'client', 'industry', 'platform', 'description']:
                    parts.append(f"\n## {key.replace('_', ' ').title()}\n{value}\n")
    
    else:
        # Plain text - append as additional context
        parts.append(f"\n## Additional Context\n{txt_data['data']}\n")
    
    # Results/Outcomes
    if case_study.get('results') or case_study.get('outcomes'):
        parts.append(f"\n## Results\n{case_study.get('results') or case_study.get('outcomes')}\n")
    
    # Date
    if case_study.get('created_at') or case_study.get('date'):
        date_str = case_study.get('created_at') or case_study.get('date')
        parts.append(f"\n**Date:** {date_str}\n")
    
    return '\n'.join(parts)


def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into chunks with overlap"""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chunk_size
        chunk = text[start:end]
        
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            if break_point > max_chunk_size * 0.5:
                chunk = text[start:start + break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks


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
        
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error uploading to RAG: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Import case studies from Supabase')
    parser.add_argument('--connection-string', help='Supabase PostgreSQL connection string')
    parser.add_argument('--txt-file', required=True, help='Supplementary txt file with case study data')
    parser.add_argument('--company', help='Filter by company')
    parser.add_argument('--platform', help='Filter by platform')
    parser.add_argument('--industry', help='Filter by industry')
    parser.add_argument('--date-from', help='Filter by date from (YYYY-MM-DD)')
    parser.add_argument('--table-name', default='case_studies', help='Table name (default: case_studies)')
    parser.add_argument('--upload-to-rag', action='store_true', help='Upload to RAG after import')
    parser.add_argument('--output-file', help='Save imported case studies to JSON file')
    
    args = parser.parse_args()
    
    # Get connection string
    connection_string = args.connection_string or os.getenv('SUPABASE_DATABASE_URL') or os.getenv('DATABASE_URL')
    if not connection_string:
        logger.error("Connection string required. Use --connection-string or set SUPABASE_DATABASE_URL")
        sys.exit(1)
    
    # Get RAG configuration
    rag_service_url = os.getenv('RAG_SERVICE_URL', 'https://rag.kcube-consulting.com')
    rag_api_key = os.getenv('RAG_API_KEY')
    
    if args.upload_to_rag and not rag_api_key:
        logger.error("RAG_API_KEY not found. Cannot upload to RAG.")
        sys.exit(1)
    
    # Parse txt file
    txt_file = Path(args.txt_file)
    if not txt_file.exists():
        logger.error(f"Txt file does not exist: {txt_file}")
        sys.exit(1)
    
    logger.info(f"Parsing txt file: {txt_file}")
    txt_data = parse_txt_file(txt_file)
    logger.info(f"Txt file format: {txt_data['format']}")
    
    # Connect to Supabase
    logger.info("Connecting to Supabase...")
    try:
        connection = connect_to_supabase(connection_string)
        logger.info("✓ Connected to Supabase")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        sys.exit(1)
    
    # Query case studies
    logger.info("Querying case studies...")
    case_studies = query_case_studies(
        connection,
        args.company,
        args.platform,
        args.industry,
        args.date_from
    )
    
    logger.info(f"Found {len(case_studies)} case studies")
    
    if not case_studies:
        logger.warning("No case studies found. Check your filters and table name.")
        return
    
    # Process case studies
    processed_case_studies = []
    for i, case_study in enumerate(case_studies, 1):
        logger.info(f"Processing [{i}/{len(case_studies)}]: {case_study.get('title') or case_study.get('name') or 'Unknown'}")
        
        # Merge with txt data
        merged_content = merge_case_study_data(case_study, txt_data)
        
        # Determine collection
        platform = case_study.get('platform') or args.platform
        if platform:
            platform_slug = platform.lower().replace(' ', '_').replace('-', '_')
            collection = f"{platform_slug}_case_studies"
        elif args.company:
            company_slug = args.company.lower().replace(' ', '_').replace('-', '_')
            collection = f"{company_slug}_case_studies"
        else:
            collection = "general_case_studies"
        
        processed_case_study = {
            'original': case_study,
            'merged_content': merged_content,
            'collection': collection,
            'platform': platform,
            'company': case_study.get('company') or args.company
        }
        processed_case_studies.append(processed_case_study)
        
        # Upload to RAG if requested
        if args.upload_to_rag:
            chunks = chunk_text(merged_content)
            documents = []
            metadatas = []
            
            for j, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    'case_study_id': str(case_study.get('id', '')),
                    'title': case_study.get('title') or case_study.get('name', ''),
                    'company': case_study.get('company', ''),
                    'industry': case_study.get('industry', ''),
                    'platform': platform or '',
                    'chunk_index': j,
                    'total_chunks': len(chunks),
                    'source': 'supabase_import',
                    'imported_at': datetime.utcnow().isoformat()
                })
            
            if upload_to_rag(collection, documents, metadatas, rag_service_url, rag_api_key):
                logger.info(f"✓ Uploaded to {collection}")
            else:
                logger.warning(f"✗ Failed to upload to {collection}")
    
    # Save to output file
    if args.output_file:
        output_file = Path(args.output_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_case_studies': len(processed_case_studies),
                'case_studies': processed_case_studies
            }, f, indent=2)
        logger.info(f"Saved to: {output_file}")
    
    logger.info(f"\nProcessed {len(processed_case_studies)} case studies")


if __name__ == '__main__':
    main()





