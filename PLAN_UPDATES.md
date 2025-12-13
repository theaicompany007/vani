# Plan Updates: Use Case Protection for Contacts & Companies

## Summary
Added use case protection and industry-based filtering for Contacts and Companies tabs to the plan.

## Changes Made to Plan

### 1. Use Case Protection
- **Contacts Tab**: Requires `contact_management` use case permission
- **Companies Tab**: Requires `company_management` use case permission
- All contact endpoints: Add `@require_use_case('contact_management')`
- All company endpoints: Add `@require_use_case('company_management')`
- UI: Hide tabs if user doesn't have permission

### 2. Industry-Based Filtering for Contacts
- **GET `/api/contacts`**:
  - Industry admins: Only see contacts from their assigned industry
  - Super users: See all contacts, can filter by industry
  - Filter by contact's `industry` field or linked company's industry
- **POST/PUT `/api/contacts`**:
  - Auto-assign industry from user's `active_industry_id` (if industry admin)
  - Industry admins cannot create/update contacts outside their industry

### 3. Industry-Based Filtering for Companies
- **GET `/api/companies`**:
  - Industry admins: Only see companies from their assigned industry
  - Super users: See all companies, can filter by industry
  - Filter by company's `industry` field
- **POST/PUT `/api/companies`**:
  - Auto-assign industry from user's `active_industry_id` (if industry admin)
  - Industry admins cannot create/update companies outside their industry

### 4. UI Updates
- Hide Contacts tab if user doesn't have `contact_management` permission
- Hide Companies tab if user doesn't have `company_management` permission
- Show industry badges on contact/company cards
- Show industry filter dropdown (super users only)
- Show "Showing contacts/companies for: [Industry Name]" notice (industry admins)

### 5. Migration Required
- Create `app/migrations/013_add_contact_company_use_cases.sql`
- Add `contact_management` and `company_management` use cases to `use_cases` table if they don't exist

## New Todos Added

1. `add_use_case_protection_contacts` - Add use case decorators and UI protection for Contacts
2. `add_use_case_protection_companies` - Add use case decorators and UI protection for Companies
3. `add_industry_filtering_contacts` - Add industry-based filtering to contacts API
4. `add_industry_filtering_companies` - Add industry-based filtering to companies API
5. `create_use_cases_migration` - Create migration for new use cases

## Implementation Details

### Use Cases to Create
```sql
-- Add to use_cases table if not exists
INSERT INTO use_cases (code, name, description) 
VALUES 
  ('contact_management', 'Contact Management', 'Manage contacts and contact data'),
  ('company_management', 'Company Management', 'Manage companies and company data')
ON CONFLICT (code) DO NOTHING;
```

### API Changes
- `app/api/contacts.py`: Add `@require_use_case('contact_management')` to all endpoints
- `app/api/companies.py`: Add `@require_use_case('company_management')` to all endpoints
- Add industry filtering logic similar to targets API

### UI Changes
- Check user permissions on page load
- Hide/show tabs based on permissions
- Add industry filtering UI similar to targets tab
- Show industry badges and notices












