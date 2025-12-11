"""Test script for Contacts and Companies functionality"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.__init__ import create_app
from app.supabase_client import get_supabase_client
from app.services.contact_service import (
    find_or_create_company, find_duplicates, upsert_contacts,
    normalize_email, normalize_phone, resolve_best_domain
)

def test_company_creation():
    """Test company creation and lookup"""
    print("\n=== Testing Company Creation ===")
    app = create_app()
    
    with app.app_context():
        supabase = get_supabase_client(app)
        
        # Test 1: Create new company
        print("\n1. Creating new company 'Test Company Inc'...")
        company_id = find_or_create_company(supabase, "Test Company Inc", "testcompany.com")
        if company_id:
            print(f"   ✓ Company created with ID: {company_id}")
        else:
            print("   ✗ Failed to create company")
            return False
        
        # Test 2: Find existing company by domain
        print("\n2. Finding company by domain 'testcompany.com'...")
        company_id2 = find_or_create_company(supabase, None, "testcompany.com")
        if company_id2 == company_id:
            print(f"   ✓ Found existing company: {company_id2}")
        else:
            print(f"   ✗ Company ID mismatch: {company_id2} != {company_id}")
            return False
        
        # Test 3: Find existing company by name
        print("\n3. Finding company by name 'Test Company Inc'...")
        company_id3 = find_or_create_company(supabase, "Test Company Inc", None)
        if company_id3 == company_id:
            print(f"   ✓ Found existing company: {company_id3}")
        else:
            print(f"   ✗ Company ID mismatch: {company_id3} != {company_id}")
            return False
        
        print("\n✓ All company tests passed!")
        return True


def test_contact_normalization():
    """Test contact data normalization"""
    print("\n=== Testing Contact Normalization ===")
    
    # Test email normalization
    test_emails = [
        ("  Test@Example.COM  ", "test@example.com"),
        ("", ""),
        (None, "")
    ]
    
    for input_email, expected in test_emails:
        result = normalize_email(input_email)
        if result == expected:
            print(f"   ✓ Email normalization: '{input_email}' -> '{result}'")
        else:
            print(f"   ✗ Email normalization failed: '{input_email}' -> '{result}' (expected '{expected}')")
            return False
    
    # Test phone normalization
    test_phones = [
        ("+1 (555) 123-4567", "15551234567"),
        ("555-1234", "5551234"),
        ("", ""),
        (None, "")
    ]
    
    for input_phone, expected in test_phones:
        result = normalize_phone(input_phone)
        if result == expected:
            print(f"   ✓ Phone normalization: '{input_phone}' -> '{result}'")
        else:
            print(f"   ✗ Phone normalization failed: '{input_phone}' -> '{result}' (expected '{expected}')")
            return False
    
    # Test domain extraction
    test_domains = [
        ("test@example.com", "example.com"),
        ("user@company.co.uk", "company.co.uk"),
        ("", None),
        (None, None)
    ]
    
    for input_email, expected in test_domains:
        result = resolve_best_domain(None, input_email)
        if result == expected:
            print(f"   ✓ Domain extraction: '{input_email}' -> '{result}'")
        else:
            print(f"   ✗ Domain extraction failed: '{input_email}' -> '{result}' (expected '{expected}')")
            return False
    
    print("\n✓ All normalization tests passed!")
    return True


def test_contact_duplicates():
    """Test duplicate detection"""
    print("\n=== Testing Duplicate Detection ===")
    app = create_app()
    
    with app.app_context():
        supabase = get_supabase_client(app)
        
        # Create test contacts
        test_contacts = [
            {
                'name': 'John Doe',
                'email': 'john@test.com',
                'phone': '5551234567',
                'company': 'Test Company'
            },
            {
                'name': 'Jane Smith',
                'email': 'jane@test.com',
                'phone': '5559876543',
                'company': 'Test Company'
            }
        ]
        
        # Insert test contacts
        print("\n1. Creating test contacts...")
        for contact in test_contacts:
            domain = resolve_best_domain(None, contact['email'])
            company_id = find_or_create_company(supabase, contact['company'], domain)
            contact['company_id'] = company_id
            contact['email'] = normalize_email(contact['email'])
            contact['phone'] = normalize_phone(contact['phone'])
            
            try:
                supabase.table('contacts').insert(contact).execute()
                print(f"   ✓ Created contact: {contact['name']}")
            except Exception as e:
                print(f"   ⚠ Contact may already exist: {contact['name']} ({e})")
        
        # Test duplicate detection
        print("\n2. Testing duplicate detection...")
        new_rows = [
            {'name': 'John Doe Updated', 'email': 'john@test.com', 'phone': '5551111111'},
            {'name': 'New Person', 'email': 'new@test.com', 'phone': '5552222222'}
        ]
        
        duplicates, uniques = find_duplicates(supabase, new_rows)
        
        if len(duplicates) == 1 and duplicates[0]['match_type'] == 'email':
            print(f"   ✓ Found 1 duplicate by email")
        else:
            print(f"   ✗ Duplicate detection failed: found {len(duplicates)} duplicates")
            return False
        
        if len(uniques) == 1:
            print(f"   ✓ Found 1 unique contact")
        else:
            print(f"   ✗ Unique detection failed: found {len(uniques)} uniques")
            return False
        
        print("\n✓ All duplicate detection tests passed!")
        return True


def test_bulk_import():
    """Test bulk contact import"""
    print("\n=== Testing Bulk Import ===")
    app = create_app()
    
    with app.app_context():
        supabase = get_supabase_client(app)
        
        test_rows = [
            {
                'name': 'Bulk Test 1',
                'email': 'bulk1@test.com',
                'company': 'Bulk Company',
                'role': 'Manager'
            },
            {
                'name': 'Bulk Test 2',
                'email': 'bulk2@test.com',
                'company': 'Bulk Company',
                'phone': '5553333333'
            }
        ]
        
        print("\n1. Testing bulk upsert...")
        result = upsert_contacts(supabase, test_rows, {'updateExisting': False})
        
        if result.get('imported', 0) >= 2:
            print(f"   ✓ Successfully imported {result['imported']} contacts")
        else:
            print(f"   ✗ Import failed: imported {result.get('imported', 0)} contacts")
            if result.get('errors'):
                print(f"   Errors: {result['errors']}")
            return False
        
        if result.get('errors') and len(result['errors']) > 0:
            print(f"   ⚠ Import completed with {len(result['errors'])} errors")
        else:
            print("   ✓ No errors during import")
        
        print("\n✓ All bulk import tests passed!")
        return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Contacts & Companies Functionality Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Normalization", test_contact_normalization()))
    results.append(("Company Creation", test_company_creation()))
    results.append(("Duplicate Detection", test_contact_duplicates()))
    results.append(("Bulk Import", test_bulk_import()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"Total: {len(results)} tests | Passed: {passed} | Failed: {failed}")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {failed} test(s) failed. Please review the output above.")
        return 1


if __name__ == '__main__':
    exit(main())

