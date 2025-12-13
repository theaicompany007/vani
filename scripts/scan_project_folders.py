#!/usr/bin/env python3
"""
Project Folder Scanner
Scans project folders (onlynereputation-agentic-app, vani, theaicompany-web) to extract
platform documentation from markdown, readme, and scripts.
"""
import os
import sys
import json
import logging
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
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

# Project to platform mapping
PROJECT_MAPPING = {
    'onlynereputation-agentic-app': {
        'platform': 'the_ai_company_revenue_growth',
        'name': 'Revenue Growth Platform',
        'company': 'The AI Company'
    },
    'vani': {
        'platform': 'the_ai_company_vani',
        'name': 'Project VANI',
        'company': 'The AI Company'
    },
    'theaicompany-web': {
        'platform': 'the_ai_company_genai_platform',
        'name': 'GenAI Platform',
        'company': 'The AI Company'
    },
    'neura360': {
        'platform': 'neura360',
        'name': 'Neura360 Platform',
        'company': 'The AI Company',
        'high_level_only': True
    },
    'happyreviews': {
        'platform': 'onlyne_reputation',
        'name': 'HappyReviews',
        'company': 'Onlyne Reputation'
    },
    'sohum': {
        'platform': 'onlyne_reputation',
        'name': 'Sohum',
        'company': 'Onlyne Reputation'
    },
    'onlynereputation': {
        'platform': 'onlyne_reputation',
        'name': 'Onlyne Reputation',
        'company': 'Onlyne Reputation'
    }
}

# Neura360 component capabilities mapping
NEURA360_COMPONENTS = {
    'neura360_signal': {
        'keywords': ['signal', 'listening', 'contextual', 'emotion', 'sarcasm'],
        'description': 'Contextual listening, emotion clustering, sarcasm detection'
    },
    'neura360_spark': {
        'keywords': ['spark', 'anomaly', 'early detection', 'opportunity'],
        'description': 'Spark engine for early anomaly and opportunity detection'
    },
    'neura360_risk': {
        'keywords': ['risk', 'crisis', 'foresight', 'mitigation'],
        'description': 'Crisis foresight, risk scoring, mitigation suggestions'
    },
    'neura360_narrative': {
        'keywords': ['narrative', 'influencer', 'counter-messaging', 'design'],
        'description': 'Narrative design, influencer levers, counter-messaging'
    },
    'neura360_trend': {
        'keywords': ['trend', 'whitespace', 'category', 'competitor', 'mining'],
        'description': 'Trend mining, category whitespace, competitor gaps'
    },
    'neura360_agents': {
        'keywords': ['agents', 'autonomous', 'workflow', 'response'],
        'description': 'Autonomous response and workflow agents embedded in channels'
    }
}

# Document patterns to extract
ARCHITECTURE_PATTERNS = [
    r'#+\s*[Aa]rchitecture',
    r'#+\s*[Ss]ystem\s+[Aa]rchitecture',
    r'#+\s*[Tt]echnical\s+[Aa]rchitecture',
    r'architecture\.md',
    r'ARCHITECTURE',
]

FEATURE_PATTERNS = [
    r'#+\s*[Ff]eatures?',
    r'#+\s*[Cc]apabilities?',
    r'#+\s*[Ff]unctionality',
    r'features?\.md',
    r'FEATURES',
]

TECH_STACK_PATTERNS = [
    r'#+\s*[Tt]echnology\s+[Ss]tack',
    r'#+\s*[Tt]ech\s+[Ss]tack',
    r'#+\s*[Tt]echnologies?',
    r'package\.json',
    r'requirements\.txt',
    r'requirements\.py',
]

API_PATTERNS = [
    r'#+\s*[Aa][Pp][Ii]',
    r'#+\s*[Aa][Pp][Ii]\s+[Dd]ocumentation',
    r'#+\s*[Ee]ndpoints?',
    r'api\.md',
    r'API\.md',
]

SETUP_PATTERNS = [
    r'#+\s*[Ss]etup',
    r'#+\s*[Ii]nstallation',
    r'#+\s*[Gg]etting\s+[Ss]tarted',
    r'#+\s*[Qq]uick\s+[Ss]tart',
    r'SETUP\.md',
    r'INSTALL\.md',
    r'README\.md',
]


def extract_markdown_sections(content: str, patterns: List[str]) -> List[Dict[str, Any]]:
    """Extract sections from markdown content based on patterns"""
    sections = []
    lines = content.split('\n')
    current_section = None
    current_content = []
    
    for i, line in enumerate(lines):
        # Check if line matches any pattern (heading)
        is_heading = False
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Save previous section if exists
                if current_section and current_content:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip(),
                        'line_start': i - len(current_content)
                    })
                # Start new section
                current_section = line.strip('#').strip()
                current_content = []
                is_heading = True
                break
        
        if not is_heading and current_section:
            current_content.append(line)
    
    # Save last section
    if current_section and current_content:
        sections.append({
            'title': current_section,
            'content': '\n'.join(current_content).strip(),
            'line_start': len(lines) - len(current_content)
        })
    
    return sections


def extract_from_readme(file_path: Path) -> Dict[str, Any]:
    """Extract information from README.md"""
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    
    result = {
        'architecture': [],
        'features': [],
        'tech_stack': [],
        'api': [],
        'setup': [],
        'general': content[:5000]  # First 5000 chars as general content
    }
    
    # Extract architecture sections
    arch_sections = extract_markdown_sections(content, ARCHITECTURE_PATTERNS)
    result['architecture'] = [s['content'] for s in arch_sections]
    
    # Extract feature sections
    feature_sections = extract_markdown_sections(content, FEATURE_PATTERNS)
    result['features'] = [s['content'] for s in feature_sections]
    
    # Extract tech stack (look for code blocks with dependencies)
    tech_stack_match = re.search(r'(package\.json|requirements\.txt|dependencies?|technologies?)[\s\S]{0,2000}', content, re.IGNORECASE)
    if tech_stack_match:
        result['tech_stack'] = [tech_stack_match.group(0)]
    
    # Extract API sections
    api_sections = extract_markdown_sections(content, API_PATTERNS)
    result['api'] = [s['content'] for s in api_sections]
    
    # Extract setup sections
    setup_sections = extract_markdown_sections(content, SETUP_PATTERNS)
    result['setup'] = [s['content'] for s in setup_sections]
    
    return result


def extract_from_markdown(file_path: Path) -> Dict[str, Any]:
    """Extract information from markdown file"""
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    filename_lower = file_path.name.lower()
    
    result = {
        'type': 'general',
        'content': content,
        'sections': []
    }
    
    # Determine document type from filename
    if 'architecture' in filename_lower:
        result['type'] = 'architecture'
    elif 'feature' in filename_lower:
        result['type'] = 'features'
    elif 'api' in filename_lower:
        result['type'] = 'api'
    elif 'setup' in filename_lower or 'install' in filename_lower:
        result['type'] = 'setup'
    elif 'capability' in filename_lower or 'capabilities' in filename_lower:
        result['type'] = 'capabilities'
    
    # Extract sections
    sections = extract_markdown_sections(content, ARCHITECTURE_PATTERNS + FEATURE_PATTERNS + API_PATTERNS + SETUP_PATTERNS)
    result['sections'] = sections
    
    return result


def extract_neura360_capabilities(
    project_path: Path,
    project_info: Dict[str, Any],
    extract_types: List[str]
) -> List[Dict[str, Any]]:
    """Extract high-level capabilities for Neura360 components"""
    documents = []
    
    # Look for capabilities documentation
    capability_files = list(project_path.rglob('*capabilit*.md')) + \
                      list(project_path.rglob('*capabilit*.txt')) + \
                      list(project_path.rglob('README.md'))
    
    for cap_file in capability_files:
        try:
            content = cap_file.read_text(encoding='utf-8', errors='ignore').lower()
            
            # Extract capabilities for each component
            for component_slug, component_info in NEURA360_COMPONENTS.items():
                # Check if this component is mentioned
                if any(keyword in content for keyword in component_info['keywords']):
                    # Extract relevant section
                    component_name = component_slug.replace('neura360_', '').replace('_', ' ').title()
                    
                    # Create capability summary
                    capability_summary = f"""# {component_name} - {component_info['description']}

## Component Overview
{component_info['description']}

## Key Capabilities
{_extract_capability_details(content, component_info['keywords'])}

## Source
Extracted from: {cap_file.name}
"""
                    
                    doc_type = 'platforms'
                    collection = f"{component_slug}_{doc_type}"
                    
                    documents.append({
                        'file_path': str(cap_file.relative_to(project_path)),
                        'type': 'capabilities',
                        'content': capability_summary,
                        'collection': collection,
                        'platform': component_slug,
                        'company': project_info['company'],
                        'document_type': doc_type,
                        'metadata': {
                            'source_file': cap_file.name,
                            'source_path': str(cap_file),
                            'project': project_path.name,
                            'component': component_name,
                            'extracted_at': datetime.utcnow().isoformat(),
                            'high_level_only': True
                        }
                    })
        except Exception as e:
            logger.error(f"Error processing capability file {cap_file}: {e}")
    
    # If no capability files found, create summaries from component info
    if not documents:
        for component_slug, component_info in NEURA360_COMPONENTS.items():
            component_name = component_slug.replace('neura360_', '').replace('_', ' ').title()
            capability_summary = f"""# {component_name}

## Description
{component_info['description']}

## High-Level Capabilities
This component is part of the Neura360 Platform - A neural, brain-like system for perception, prediction, and action across public narratives.

Tagline: "The neural layer for brand reality."

## Component Details
{component_info['description']}
"""
            
            doc_type = 'platforms'
            collection = f"{component_slug}_{doc_type}"
            
            documents.append({
                'file_path': 'neura360_capabilities.md',
                'type': 'capabilities',
                'content': capability_summary,
                'collection': collection,
                'platform': component_slug,
                'company': project_info['company'],
                'document_type': doc_type,
                'metadata': {
                    'source_file': 'neura360_capabilities.md',
                    'project': project_path.name,
                    'component': component_name,
                    'extracted_at': datetime.utcnow().isoformat(),
                    'high_level_only': True
                }
            })
    
    return documents


def _extract_capability_details(content: str, keywords: List[str]) -> str:
    """Extract capability details from content based on keywords"""
    # Simple extraction - look for sentences containing keywords
    sentences = content.split('.')
    relevant_sentences = []
    
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in keywords):
            relevant_sentences.append(sentence.strip())
    
    return '. '.join(relevant_sentences[:5])  # Limit to 5 sentences


def extract_from_requirements(file_path: Path) -> Dict[str, Any]:
    """Extract technology stack from requirements.txt or package.json"""
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    
    return {
        'type': 'tech_stack',
        'content': content,
        'dependencies': content.split('\n')[:100]  # First 100 lines
    }


def detect_project_type(folder_path: Path) -> Optional[Dict[str, Any]]:
    """Detect project type from folder name"""
    folder_name = folder_path.name.lower()
    
    for project_key, project_info in PROJECT_MAPPING.items():
        if project_key in folder_name:
            return project_info
    
    return None


def scan_project_folder(
    project_path: Path,
    extract_types: List[str] = None,
    upload_to_rag: bool = False
) -> List[Dict[str, Any]]:
    """Scan a project folder and extract documentation"""
    extract_types = extract_types or ['all']
    documents = []
    
    # Detect project type
    project_info = detect_project_type(project_path)
    if not project_info:
        logger.warning(f"Could not detect project type for: {project_path}")
        return documents
    
    logger.info(f"Scanning project: {project_info['name']} ({project_path.name})")
    
    # Special handling for Neura360 - only extract high-level capabilities
    if project_info.get('high_level_only'):
        return extract_neura360_capabilities(project_path, project_info, extract_types)
    
    # Find all markdown files
    md_files = list(project_path.rglob('*.md')) + list(project_path.rglob('*.MD'))
    readme_files = [f for f in md_files if f.name.upper() in ['README.MD', 'README.md', 'readme.md']]
    other_md_files = [f for f in md_files if f not in readme_files]
    
    # Find requirements files
    req_files = list(project_path.rglob('requirements.txt')) + list(project_path.rglob('package.json'))
    
    # Process README files
    for readme_file in readme_files:
        logger.debug(f"Processing README: {readme_file}")
        try:
            info = extract_from_readme(readme_file)
            
            # Create documents for each section type
            for section_type, contents in info.items():
                if section_type == 'general' or (extract_types != ['all'] and section_type not in extract_types):
                    continue
                
                for content in contents:
                    if content and len(content.strip()) > 100:  # Only meaningful content
                        doc_type = 'platforms'  # Platform documentation goes to platforms collection
                        collection = f"{project_info['platform']}_{doc_type}"
                        
                        documents.append({
                            'file_path': str(readme_file.relative_to(project_path)),
                            'type': section_type,
                            'content': content,
                            'collection': collection,
                            'platform': project_info['platform'],
                            'company': project_info['company'],
                            'document_type': doc_type,
                            'metadata': {
                                'source_file': readme_file.name,
                                'source_path': str(readme_file),
                                'project': project_path.name,
                                'extracted_at': datetime.utcnow().isoformat()
                            }
                        })
        except Exception as e:
            logger.error(f"Error processing README {readme_file}: {e}")
    
    # Process other markdown files
    for md_file in other_md_files:
        logger.debug(f"Processing markdown: {md_file}")
        try:
            info = extract_from_markdown(md_file)
            
            doc_type = 'platforms'
            collection = f"{project_info['platform']}_{doc_type}"
            
            documents.append({
                'file_path': str(md_file.relative_to(project_path)),
                'type': info['type'],
                'content': info['content'],
                'collection': collection,
                'platform': project_info['platform'],
                'company': project_info['company'],
                'document_type': doc_type,
                'metadata': {
                    'source_file': md_file.name,
                    'source_path': str(md_file),
                    'project': project_path.name,
                    'extracted_at': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error processing markdown {md_file}: {e}")
    
    # Process requirements files
    for req_file in req_files:
        logger.debug(f"Processing requirements: {req_file}")
        try:
            info = extract_from_requirements(req_file)
            
            doc_type = 'platforms'
            collection = f"{project_info['platform']}_{doc_type}"
            
            documents.append({
                'file_path': str(req_file.relative_to(project_path)),
                'type': 'tech_stack',
                'content': info['content'],
                'collection': collection,
                'platform': project_info['platform'],
                'company': project_info['company'],
                'document_type': doc_type,
                'metadata': {
                    'source_file': req_file.name,
                    'source_path': str(req_file),
                    'project': project_path.name,
                    'extracted_at': datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error processing requirements {req_file}: {e}")
    
    logger.info(f"Extracted {len(documents)} documents from {project_path.name}")
    return documents


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
            if break_point > max_chunk_size * 0.5:
                chunk = text[start:start + break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    return chunks


def upload_document_to_rag(
    collection: str,
    content: str,
    metadata: Dict[str, Any],
    rag_service_url: str,
    rag_api_key: str
) -> bool:
    """Upload document to RAG service"""
    import requests
    
    # Chunk the content
    chunks = chunk_text(content)
    
    # Prepare documents and metadatas
    documents = []
    metadatas = []
    
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        chunk_metadata = {
            **metadata,
            'chunk_index': i,
            'total_chunks': len(chunks),
            'source': 'project_scan'
        }
        metadatas.append(chunk_metadata)
    
    # Upload to RAG
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
    parser = argparse.ArgumentParser(description='Scan project folders for documentation')
    parser.add_argument('--projects-root', help='Root folder containing project folders')
    parser.add_argument('--project', help='Specific project folder name to scan')
    parser.add_argument('--project-path', help='Direct path to project folder')
    parser.add_argument('--extract-types', help='Comma-separated list of types to extract (architecture,features,capabilities,api,setup) or "all"')
    parser.add_argument('--upload-to-rag', action='store_true', help='Upload extracted documents to RAG')
    parser.add_argument('--output-folder', help='Output folder to save extracted documents (JSON)')
    
    args = parser.parse_args()
    
    # Get RAG configuration
    rag_service_url = os.getenv('RAG_SERVICE_URL', 'https://rag.kcube-consulting.com')
    rag_api_key = os.getenv('RAG_API_KEY')
    
    if args.upload_to_rag and not rag_api_key:
        logger.error("RAG_API_KEY not found. Cannot upload to RAG.")
        sys.exit(1)
    
    # Parse extract types
    extract_types = [t.strip() for t in args.extract_types.split(',')] if args.extract_types else ['all']
    
    all_documents = []
    
    if args.project_path:
        # Scan specific project
        project_path = Path(args.project_path)
        if not project_path.exists():
            logger.error(f"Project path does not exist: {project_path}")
            sys.exit(1)
        
        documents = scan_project_folder(project_path, extract_types, args.upload_to_rag)
        all_documents.extend(documents)
    
    elif args.project:
        # Find project in projects root
        if not args.projects_root:
            logger.error("--projects-root required when using --project")
            sys.exit(1)
        
        projects_root = Path(args.projects_root)
        project_path = projects_root / args.project
        
        if not project_path.exists():
            logger.error(f"Project folder does not exist: {project_path}")
            sys.exit(1)
        
        documents = scan_project_folder(project_path, extract_types, args.upload_to_rag)
        all_documents.extend(documents)
    
    elif args.projects_root:
        # Scan all projects
        projects_root = Path(args.projects_root)
        
        for project_key in PROJECT_MAPPING.keys():
            project_path = projects_root / project_key
            if project_path.exists() and project_path.is_dir():
                documents = scan_project_folder(project_path, extract_types, args.upload_to_rag)
                all_documents.extend(documents)
            else:
                logger.warning(f"Project folder not found: {project_path}")
    
    else:
        logger.error("Must specify --projects-root, --project, or --project-path")
        sys.exit(1)
    
    # Upload to RAG if requested
    if args.upload_to_rag:
        logger.info(f"Uploading {len(all_documents)} documents to RAG...")
        success_count = 0
        for doc in all_documents:
            try:
                if upload_document_to_rag(
                    doc['collection'],
                    doc['content'],
                    doc['metadata'],
                    rag_service_url,
                    rag_api_key
                ):
                    success_count += 1
                    logger.info(f"✓ Uploaded: {doc['file_path']} → {doc['collection']}")
                else:
                    logger.warning(f"✗ Failed: {doc['file_path']}")
            except Exception as e:
                logger.error(f"Error uploading {doc['file_path']}: {e}")
        
        logger.info(f"Uploaded {success_count}/{len(all_documents)} documents")
    
    # Save to output folder if specified
    if args.output_folder:
        output_folder = Path(args.output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        output_file = output_folder / f"project_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_documents': len(all_documents),
                'documents': all_documents
            }, f, indent=2)
        
        logger.info(f"Saved extracted documents to: {output_file}")
    
    logger.info(f"\nTotal documents extracted: {len(all_documents)}")


if __name__ == '__main__':
    main()

