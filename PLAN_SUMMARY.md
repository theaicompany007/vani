# AI-Powered Multi-Industry Target System - Plan Summary

## Required Credentials

### 1. RAG Service (rag.kcube-consulting.com)
```bash
RAG_SERVICE_URL=https://rag.kcube-consulting.com
RAG_API_KEY=27e887d021a49654a0a703688cb139cdf652dfec795009a5afb8e9556c49b181
RAG_ONLY=true
RAG_TRUSTED_ORIGIN=http://localhost:5000
```
**Status:** ✅ Already configured

### 2. Google Gemini / Notebook LM
```bash
GEMINI_API_KEY=your_gemini_api_key_here  # REQUIRED - Get from https://makersuite.google.com/app/apikey
GEMINI_MODEL=gemini-pro  # or gemini-1.5-pro
GEMINI_NOTEBOOK_LM_ENABLED=true
```
**How to Get:**
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create new API key or copy existing
4. Add to `.env.local`

**Notebook LM Content Available:**
- Royal Enfield
- IndiGo Airlines
- ITQ Technologies
- EaseMyTrip
- Other customer data

### 3. OpenAI (Already Configured)
```bash
OPENAI_API_KEY=your_existing_key  # ✅ Already configured
```

## Key Features to Implement

### 1. Industry-Based Access Control
- **Industry Admin Users** (`is_industry_admin = true`):
  - Only see targets from their assigned `industry_id`
  - Cannot access targets from other industries (403 error)
  - Cannot create targets outside their industry
  - Filter enforced server-side, cannot override
- **Super Users** (`is_super_user = true`):
  - See all targets
  - Can filter by industry
  - Can switch between industries
- **Target List API** (`GET /api/targets`):
  - Auto-filters by user's industry assignment
  - Industry admins: Filtered by `industry_id` or `active_industry_id`
  - Super users: Can use `industry` query parameter

### 2. Complete Target Management UI
- Add Target button and modal
- Edit Target functionality
- Delete Target with confirmation
- Link Contact button (uses existing API)
- Convert Contact to Target (from Contacts page)
- Status management (NEW, CONTACTED, RESPONDED, etc.)
- Search and filter targets
- Industry badges and filtering

### 3. AI Target Identification
- Multi-source knowledge: RAG + Gemini + OpenAI
- Industry-aware analysis
- Auto-populates Target Hit List
- Uses customer examples from Notebook LM

### 4. Industry-Adaptive System
- Global industry selector in header
- All views adapt to selected industry
- Content generation uses industry context

## Implementation Todos

1. ✅ Create RAG client (`app/integrations/rag_client.py`)
2. ✅ Create Gemini client (`app/integrations/gemini_client.py`)
3. ✅ Create RAG ingestion script
4. ✅ Create industry context service
5. ✅ Create target identification service (with RAG + Gemini)
6. ✅ Add industry switching API
7. ✅ Add AI target API endpoints
8. ✅ Add target management APIs (with industry restrictions)
9. ✅ **Add industry-based filtering to GET /api/targets**
10. ✅ **Add industry validation to prevent cross-industry access**
11. ✅ Add global industry selector UI
12. ✅ Add AI Target Finder UI
13. ✅ Complete Target Management UI
14. ✅ Add Convert Contact to Target
15. ✅ Make pitch generation industry-aware
16. ✅ Make message generation industry-aware
17. ✅ Update dashboard for industry

## Files to Create/Modify

### New Files:
- `app/integrations/rag_client.py`
- `app/integrations/gemini_client.py`
- `app/services/target_identification.py`
- `app/services/industry_context.py`
- `app/models/target_recommendation.py`
- `scripts/ingest_gemini_content_to_rag.py`
- `INTEGRATION_CREDENTIALS.md` ✅ (Created)

### Modify:
- `app/api/targets.py` - Add industry filtering, AI endpoints, CRUD operations
- `app/api/industries.py` - Add industry switching
- `app/api/pitch.py` - Industry-aware with RAG + Gemini
- `app/api/message_generator.py` - Industry-aware with RAG + Gemini
- `app/templates/command_center.html` - Complete UI updates

## Next Steps

1. Add `GEMINI_API_KEY` to `.env.local`
2. Test RAG service connection
3. Test Gemini API connection
4. Run ingestion script to sync Notebook LM content to RAG
5. Begin implementation following the plan








