#!/usr/bin/env python3
"""
Knowledge Base Folder Structure Setup Script
Creates recommended folder structure for organizing knowledge base documents.
"""
import os
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Document types
DOCUMENT_TYPES = [
    'case_studies',
    'services',
    'company_profiles',
    'industry_insights',
    'faqs',
    'platforms'
]

# The AI Company platforms
AI_COMPANY_PLATFORMS = [
    'GenAI Platform',
    'Revenue Growth Platform',
    'VANI',
    'Neura360'
]

# Neura360 sub-products
NEURA360_PRODUCTS = [
    'Neura Signal',
    'Neura Spark',
    'Neura Risk',
    'Neura Narrative',
    'Neura Trend',
    'Neura Agents'
]


def create_readme(folder_path: Path, company: str = None, platform: str = None, doc_type: str = None):
    """Create README.md file in folder explaining organization"""
    readme_content = f"""# {folder_path.name}

## Purpose
This folder contains {doc_type.replace('_', ' ').title()} documents{f' for {platform}' if platform else ''}{f' ({company})' if company else ''}.

## Collection Mapping
Documents in this folder will be uploaded to the RAG knowledge base collection:
- **Collection Name**: `{_get_collection_name(company, platform, doc_type)}`

## Document Types
{f'- **{doc_type.replace("_", " ").title()}**: ' + _get_doc_type_description(doc_type) if doc_type else 'Various document types'}

## Naming Conventions
- Use descriptive filenames
- Include platform/product name if applicable
- Use underscores or hyphens for spaces
- Examples:
  - `genai_platform_architecture.pdf`
  - `vani_api_documentation.md`
  - `case_study_fmcg_2024.txt`

## Upload Instructions
Use the upload script to process files in this folder:
```bash
python scripts/upload_knowledge_base.py --folder "{folder_path}"
```
"""
    
    readme_path = folder_path / 'README.md'
    readme_path.write_text(readme_content, encoding='utf-8')
    logger.debug(f"Created README.md in {folder_path}")


def _get_collection_name(company: str, platform: str, doc_type: str) -> str:
    """Generate collection name"""
    if platform:
        platform_slug = platform.lower().replace(' ', '_').replace('-', '_')
        if 'neura' in platform_slug:
            # Neura360 products
            return f"{platform_slug}_{doc_type}"
        elif company:
            company_slug = company.lower().replace(' ', '_').replace('-', '_')
            return f"{company_slug}_{platform_slug}_{doc_type}"
        else:
            return f"the_ai_company_{platform_slug}_{doc_type}"
    elif company:
        company_slug = company.lower().replace(' ', '_').replace('-', '_')
        return f"{company_slug}_{doc_type}"
    else:
        return f"general_{doc_type}"


def _get_doc_type_description(doc_type: str) -> str:
    """Get description for document type"""
    descriptions = {
        'case_studies': 'Success stories, client testimonials, project results',
        'services': 'Service descriptions, offerings, solutions',
        'company_profiles': 'Company information, about us, overviews',
        'industry_insights': 'Industry trends, market analysis, insights',
        'faqs': 'Frequently asked questions and answers',
        'platforms': 'Platform documentation, architecture, API docs, technical specs'
    }
    return descriptions.get(doc_type, 'Documentation')


def create_folder_structure(base_folder: Path, company: str = None):
    """Create folder structure for a company"""
    if company == 'The AI Company':
        # Create main company folder
        company_folder = base_folder / 'The AI Company'
        company_folder.mkdir(parents=True, exist_ok=True)
        create_readme(company_folder, company=company)
        
        # Create platform folders
        for platform in AI_COMPANY_PLATFORMS:
            platform_folder = company_folder / platform
            platform_folder.mkdir(parents=True, exist_ok=True)
            create_readme(platform_folder, company=company, platform=platform)
            
            # Create document type subfolders
            for doc_type in DOCUMENT_TYPES:
                doc_folder = platform_folder / doc_type
                doc_folder.mkdir(parents=True, exist_ok=True)
                create_readme(doc_folder, company=company, platform=platform, doc_type=doc_type)
            
            # Special handling for Neura360 - create sub-product folders
            if platform == 'Neura360':
                neura360_folder = platform_folder
                for product in NEURA360_PRODUCTS:
                    product_folder = neura360_folder / product
                    product_folder.mkdir(parents=True, exist_ok=True)
                    create_readme(product_folder, company=company, platform=product)
                    
                    # Create document type subfolders for each product
                    for doc_type in DOCUMENT_TYPES:
                        doc_folder = product_folder / doc_type
                        doc_folder.mkdir(parents=True, exist_ok=True)
                        create_readme(doc_folder, company=company, platform=product, doc_type=doc_type)
    
    elif company == 'Onlyne Reputation':
        # Create main company folder
        company_folder = base_folder / 'Onlyne Reputation'
        company_folder.mkdir(parents=True, exist_ok=True)
        create_readme(company_folder, company=company)
        
        # Create document type folders (no platform subfolders for now)
        for doc_type in DOCUMENT_TYPES:
            doc_folder = company_folder / doc_type
            doc_folder.mkdir(parents=True, exist_ok=True)
            create_readme(doc_folder, company=company, doc_type=doc_type)
    
    else:
        # Create general structure
        for doc_type in DOCUMENT_TYPES:
            doc_folder = base_folder / doc_type
            doc_folder.mkdir(parents=True, exist_ok=True)
            create_readme(doc_folder, doc_type=doc_type)


def main():
    parser = argparse.ArgumentParser(description='Create knowledge base folder structure')
    parser.add_argument('--base-folder', required=True, help='Base folder path where structure will be created')
    parser.add_argument('--company', choices=['The AI Company', 'Onlyne Reputation'], 
                       help='Create structure for specific company (default: both)')
    parser.add_argument('--document-types', help='Comma-separated list of document types to create (default: all)')
    
    args = parser.parse_args()
    
    base_folder = Path(args.base_folder)
    
    # Parse document types if provided
    doc_types = args.document_types.split(',') if args.document_types else DOCUMENT_TYPES
    doc_types = [dt.strip() for dt in doc_types]
    
    # Create base folder if it doesn't exist
    base_folder.mkdir(parents=True, exist_ok=True)
    logger.info(f"Creating folder structure in: {base_folder}")
    
    # Create structure for specified company or both
    if args.company:
        create_folder_structure(base_folder, args.company)
        logger.info(f"✓ Created folder structure for {args.company}")
    else:
        create_folder_structure(base_folder, 'The AI Company')
        logger.info("✓ Created folder structure for The AI Company")
        create_folder_structure(base_folder, 'Onlyne Reputation')
        logger.info("✓ Created folder structure for Onlyne Reputation")
    
    # Create main README
    main_readme = base_folder / 'README.md'
    main_readme_content = """# Knowledge Base Folder Structure

This folder contains organized documentation for The AI Company and Onlyne Reputation platforms.

## Structure

### The AI Company
- **GenAI Platform**: GenAI Agentic Platform documentation
- **Revenue Growth Platform**: Revenue Growth Platform documentation  
- **VANI**: Project VANI (Virtual Agent Network Interface) documentation
- **Neura360**: Neura360 Platform with sub-products:
  - Neura Signal
  - Neura Spark
  - Neura Risk
  - Neura Narrative
  - Neura Trend
  - Neura Agents

### Onlyne Reputation
- General documentation organized by document type

## Document Types

Each platform/product folder contains subfolders for:
- **case_studies**: Success stories and client testimonials
- **services**: Service descriptions and offerings
- **company_profiles**: Company information and overviews
- **industry_insights**: Industry trends and market analysis
- **faqs**: Frequently asked questions
- **platforms**: Platform documentation, architecture, API docs

## Usage

1. Place documents in the appropriate folder based on platform and document type
2. Use the upload script to process files:
   ```bash
   python scripts/upload_knowledge_base.py --folder "path/to/folder"
   ```

## Collection Naming

Documents are automatically mapped to RAG collections using the format:
`{company_slug}_{platform_slug}_{document_type}`

Examples:
- `the_ai_company_genai_platform_case_studies`
- `the_ai_company_vani_platforms`
- `neura360_signal_services`
- `onlyne_reputation_faqs`
"""
    main_readme.write_text(main_readme_content, encoding='utf-8')
    
    logger.info("\n" + "="*60)
    logger.info("Folder structure created successfully!")
    logger.info("="*60)
    logger.info(f"Base folder: {base_folder}")
    logger.info("\nYou can now place documents in the appropriate folders.")


if __name__ == '__main__':
    main()

