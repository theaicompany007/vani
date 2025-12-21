#!/usr/bin/env python3
"""
Knowledge Base Web Scraping Script
Scrapes websites/platform URLs to extract FAQs and industry insights.
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
import requests
from bs4 import BeautifulSoup
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


def fetch_url_content(url: str) -> Optional[str]:
    """Fetch HTML content from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return None


def extract_faqs(html: str, url: str) -> List[Dict[str, Any]]:
    """Extract FAQs from HTML content"""
    soup = BeautifulSoup(html, 'html.parser')
    faqs = []
    
    # Common FAQ patterns
    # Pattern 1: Accordion-style FAQs
    accordions = soup.find_all(['div', 'section'], class_=re.compile(r'accordion|faq|question', re.I))
    for accordion in accordions:
        questions = accordion.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dt', 'div'], 
                                      class_=re.compile(r'question|q\s*:', re.I))
        for q in questions:
            question_text = q.get_text(strip=True)
            # Find answer (next sibling or in same container)
            answer_elem = q.find_next_sibling(['div', 'p', 'dd', 'span'])
            if not answer_elem:
                answer_elem = q.parent.find(['div', 'p', 'dd', 'span'], class_=re.compile(r'answer|a\s*:', re.I))
            answer_text = answer_elem.get_text(strip=True) if answer_elem else ""
            
            if question_text and answer_text:
                faqs.append({
                    'question': question_text,
                    'answer': answer_text,
                    'source_url': url
                })
    
    # Pattern 2: Q&A lists
    qa_lists = soup.find_all(['dl', 'ul', 'ol'], class_=re.compile(r'faq|q&a|questions', re.I))
    for qa_list in qa_lists:
        items = qa_list.find_all(['li', 'dt', 'dd'])
        current_question = None
        for item in items:
            text = item.get_text(strip=True)
            if text.startswith(('Q:', 'Question:', 'Q.', '?')) or len(text) < 100:
                current_question = text.lstrip('Q:Question:Q.?').strip()
            elif current_question and (text.startswith(('A:', 'Answer:', 'A.')) or len(text) > 50):
                answer = text.lstrip('A:Answer:A.').strip()
                if current_question and answer:
                    faqs.append({
                        'question': current_question,
                        'answer': answer,
                        'source_url': url
                    })
                current_question = None
    
    # Pattern 3: FAQ section headings
    faq_sections = soup.find_all(['section', 'div'], id=re.compile(r'faq|questions', re.I))
    for section in faq_sections:
        headings = section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for heading in headings:
            question_text = heading.get_text(strip=True)
            if '?' in question_text or len(question_text) < 150:
                # Find answer in next elements
                answer_parts = []
                for sibling in heading.next_siblings:
                    if isinstance(sibling, str):
                        continue
                    if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        break
                    if sibling.name in ['p', 'div', 'span']:
                        text = sibling.get_text(strip=True)
                        if text:
                            answer_parts.append(text)
                
                if answer_parts:
                    faqs.append({
                        'question': question_text,
                        'answer': ' '.join(answer_parts),
                        'source_url': url
                    })
    
    return faqs


def extract_industry_insights(html: str, url: str) -> List[Dict[str, Any]]:
    """Extract industry insights from HTML content"""
    soup = BeautifulSoup(html, 'html.parser')
    insights = []
    
    # Look for insight/trend sections
    insight_sections = soup.find_all(['section', 'div', 'article'], 
                                    class_=re.compile(r'insight|trend|analysis|market|industry', re.I))
    
    for section in insight_sections:
        # Extract headings and content
        headings = section.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        paragraphs = section.find_all('p')
        
        for heading in headings:
            title = heading.get_text(strip=True)
            # Find associated content
            content_parts = []
            for sibling in heading.next_siblings:
                if isinstance(sibling, str):
                    continue
                if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                if sibling.name == 'p':
                    text = sibling.get_text(strip=True)
                    if text:
                        content_parts.append(text)
            
            if title and content_parts:
                insights.append({
                    'title': title,
                    'content': ' '.join(content_parts),
                    'source_url': url
                })
        
        # Also extract standalone paragraphs with insight keywords
        for para in paragraphs:
            text = para.get_text(strip=True)
            if len(text) > 100 and any(keyword in text.lower() for keyword in 
                                      ['insight', 'trend', 'analysis', 'market', 'industry', 'growth']):
                insights.append({
                    'title': f"Insight from {url}",
                    'content': text,
                    'source_url': url
                })
    
    return insights


def auto_detect_type(html: str, url: str) -> str:
    """Auto-detect if content is FAQ or industry insights"""
    html_lower = html.lower()
    url_lower = url.lower()
    
    faq_indicators = ['faq', 'frequently asked', 'questions', 'q&a', 'q and a']
    insight_indicators = ['insight', 'trend', 'analysis', 'market', 'industry report']
    
    faq_score = sum(1 for indicator in faq_indicators if indicator in html_lower or indicator in url_lower)
    insight_score = sum(1 for indicator in insight_indicators if indicator in html_lower or indicator in url_lower)
    
    if faq_score > insight_score:
        return 'faq'
    elif insight_score > faq_score:
        return 'industry_insights'
    else:
        # Default to FAQ if unclear
        return 'faq'


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


def process_url(
    url: str,
    content_type: str = None,
    platform: str = None,
    auto_detect: bool = False,
    upload_to_rag_flag: bool = False,
    rag_service_url: str = None,
    rag_api_key: str = None
) -> Dict[str, Any]:
    """Process a URL and extract FAQs or industry insights"""
    result = {
        'url': url,
        'success': False,
        'type': None,
        'items_extracted': 0,
        'items': []
    }
    
    # Fetch content
    html = fetch_url_content(url)
    if not html:
        result['error'] = 'Could not fetch URL content'
        return result
    
    # Auto-detect type if requested
    if auto_detect:
        content_type = auto_detect_type(html, url)
    
    if not content_type:
        content_type = 'faq'  # Default
    
    result['type'] = content_type
    
    # Extract based on type
    if content_type == 'faq':
        items = extract_faqs(html, url)
        for item in items:
            result['items'].append({
                'question': item['question'],
                'answer': item['answer'],
                'source_url': url
            })
    elif content_type == 'industry_insights':
        items = extract_industry_insights(html, url)
        for item in items:
            result['items'].append({
                'title': item['title'],
                'content': item['content'],
                'source_url': url
            })
    
    result['items_extracted'] = len(result['items'])
    
    if result['items_extracted'] == 0:
        result['error'] = 'No FAQs or insights found'
        return result
    
    result['success'] = True
    
    # Upload to RAG if requested
    if upload_to_rag_flag and rag_api_key:
        # Determine collection
        if platform:
            platform_slug = platform.lower().replace(' ', '_').replace('-', '_')
            collection = f"{platform_slug}_{content_type}"
        else:
            collection = f"general_{content_type}"
        
        # Prepare documents and metadatas
        documents = []
        metadatas = []
        
        for item in result['items']:
            if content_type == 'faq':
                # Create one chunk per Q&A pair
                content = f"Q: {item['question']}\n\nA: {item['answer']}"
            else:
                content = f"{item['title']}\n\n{item['content']}"
            
            chunks = chunk_text(content)
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    'source_url': url,
                    'item_index': result['items'].index(item),
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'source': 'web_scraping',
                    'scraped_at': datetime.utcnow().isoformat(),
                    'type': content_type,
                    'platform': platform or 'unknown'
                })
        
        if upload_to_rag(collection, documents, metadatas, rag_service_url, rag_api_key):
            result['uploaded'] = True
            result['collection'] = collection
            logger.info(f"✓ Uploaded {len(documents)} chunks to {collection}")
        else:
            result['upload_error'] = 'Failed to upload to RAG'
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Scrape URLs for FAQs and industry insights')
    parser.add_argument('--url', help='Single URL to scrape')
    parser.add_argument('--urls-file', help='File containing URLs (one per line)')
    parser.add_argument('--type', choices=['faq', 'industry_insights'], help='Content type to extract')
    parser.add_argument('--auto-detect', action='store_true', help='Auto-detect content type')
    parser.add_argument('--platform', help='Platform name for collection mapping')
    parser.add_argument('--upload-to-rag', action='store_true', help='Upload extracted content to RAG')
    parser.add_argument('--output-file', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    if not args.url and not args.urls_file:
        logger.error("Must specify --url or --urls-file")
        sys.exit(1)
    
    # Get RAG configuration
    rag_service_url = os.getenv('RAG_SERVICE_URL', 'https://rag.theaicompany.co')
    rag_api_key = os.getenv('RAG_API_KEY')
    
    if args.upload_to_rag and not rag_api_key:
        logger.error("RAG_API_KEY not found. Cannot upload to RAG.")
        sys.exit(1)
    
    # Get URLs
    urls = []
    if args.url:
        urls.append(args.url)
    elif args.urls_file:
        urls_file = Path(args.urls_file)
        if not urls_file.exists():
            logger.error(f"URLs file does not exist: {urls_file}")
            sys.exit(1)
        urls = [line.strip() for line in urls_file.read_text().splitlines() if line.strip()]
    
    # Process URLs
    results = []
    for i, url in enumerate(urls, 1):
        logger.info(f"Processing [{i}/{len(urls)}]: {url}")
        result = process_url(
            url,
            args.type,
            args.platform,
            args.auto_detect,
            args.upload_to_rag,
            rag_service_url,
            rag_api_key
        )
        results.append(result)
        
        if result['success']:
            logger.info(f"✓ Extracted {result['items_extracted']} items ({result['type']})")
        else:
            logger.warning(f"✗ {result.get('error', 'Failed')}")
    
    # Save results
    if args.output_file:
        output_file = Path(args.output_file)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_urls': len(urls),
                'results': results
            }, f, indent=2)
        logger.info(f"Results saved to: {output_file}")
    
    # Summary
    total_items = sum(r['items_extracted'] for r in results)
    successful = sum(1 for r in results if r['success'])
    
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total URLs: {len(urls)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Total items extracted: {total_items}")


if __name__ == '__main__':
    main()






