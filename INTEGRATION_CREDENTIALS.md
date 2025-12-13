# Integration Credentials Required

## Overview
This document lists all required API keys, tokens, and URLs for integrating with external services.

## 1. RAG Service (rag.kcube-consulting.com)

### Required Environment Variables

```bash
# RAG Service Configuration
RAG_SERVICE_URL=https://rag.kcube-consulting.com
RAG_API_KEY=27e887d021a49654a0a703688cb139cdf652dfec795009a5afb8e9556c49b181
RAG_ONLY=true  # Optional: Set to true to use only RAG service (no direct ChromaDB)
RAG_TRUSTED_ORIGIN=http://localhost:5000,https://yourdomain.com  # Optional: Allowed origins for browser requests
```

### How to Get
- **RAG_SERVICE_URL**: Already configured at `rag.kcube-consulting.com`
- **RAG_API_KEY**: Get from RAG service administrator or check existing `.env.local` file
- **RAG_ONLY**: Set to `true` to use RAG service exclusively
- **RAG_TRUSTED_ORIGIN**: Comma-separated list of allowed origins (for CORS)

### API Endpoints Used
- `POST /rag/query` - Query RAG service for knowledge base content
- `GET /rag/collections` - List available collections

### Collections Expected
- `case_studies` - Customer case studies and success stories
- `services` - Service descriptions and solutions
- `company_profiles` - Company information
- `industry_insights` - Industry-specific insights and pain points

---

## 2. Google Gemini / Notebook LM

### Required Environment Variables

```bash
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro  # or gemini-pro-vision, gemini-1.5-pro, etc.
GEMINI_NOTebook_LM_ENABLED=true  # Optional: Enable Notebook LM integration

# Notebook LM Specific (if using Notebook LM API directly)
NOTEBOOK_LM_API_KEY=your_notebook_lm_api_key_here  # If Notebook LM has separate API
NOTEBOOK_LM_PROJECT_ID=your_notebook_project_id  # If using Notebook LM project ID
```

### How to Get Gemini API Key

1. **Go to Google AI Studio**: https://makersuite.google.com/app/apikey
2. **Sign in** with your Google account
3. **Create API Key** or use existing key
4. **Copy the API key** and add to `.env.local`

### How to Access Notebook LM Content

**Option 1: Direct Gemini API (Recommended)**
- Use Gemini API to query Notebook LM content
- Requires: `GEMINI_API_KEY`
- Notebook LM content is accessible through Gemini API if you have access

**Option 2: Notebook LM API (If Available)**
- If Notebook LM has a separate API endpoint
- Requires: `NOTEBOOK_LM_API_KEY` and `NOTEBOOK_LM_PROJECT_ID`
- Check Notebook LM documentation for API access

### Customer Content Available
- Royal Enfield
- IndiGo Airlines
- ITQ Technologies
- EaseMyTrip
- Other customer data in your Notebook LM

### API Usage
- Query customer-specific case studies
- Get company profiles and business information
- Retrieve industry-specific insights
- Access real-time customer context

---

## 3. OpenAI (Already Configured)

### Required Environment Variables

```bash
# OpenAI Configuration (Already exists)
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXX
OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-4-turbo, etc.
OPENAI_PROJECT=your_openai_project_id  # Optional
```

### Status
✅ Already configured in the system

---

## 4. Supabase (Already Configured)

### Required Environment Variables

```bash
# Supabase Configuration (Already exists)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
```

### Status
✅ Already configured in the system

---

## Environment File Setup

### Add to `.env.local`

```bash
# ============================================
# RAG Service Configuration
# ============================================
RAG_SERVICE_URL=https://rag.kcube-consulting.com
RAG_API_KEY=27e887d021a49654a0a703688cb139cdf652dfec795009a5afb8e9556c49b181
RAG_ONLY=true
RAG_TRUSTED_ORIGIN=http://localhost:5000

# ============================================
# Google Gemini / Notebook LM Configuration
# ============================================
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-pro
GEMINI_NOTEBOOK_LM_ENABLED=true

# Optional: If Notebook LM has separate API
# NOTEBOOK_LM_API_KEY=your_notebook_lm_api_key
# NOTEBOOK_LM_PROJECT_ID=your_notebook_project_id

# ============================================
# Existing Configuration (Keep these)
# ============================================
OPENAI_API_KEY=your_existing_openai_key
SUPABASE_URL=your_existing_supabase_url
SUPABASE_SERVICE_KEY=your_existing_service_key
# ... other existing variables
```

---

## Verification Steps

### 1. Test RAG Service Connection

```python
import requests
import os

RAG_SERVICE_URL = os.getenv('RAG_SERVICE_URL')
RAG_API_KEY = os.getenv('RAG_API_KEY')

response = requests.post(
    f"{RAG_SERVICE_URL}/rag/query",
    headers={
        'Authorization': f'Bearer {RAG_API_KEY}',
        'x-api-key': RAG_API_KEY,
        'Content-Type': 'application/json'
    },
    json={
        'query': 'test query',
        'collections': ['case_studies'],
        'top_k': 5
    }
)
print(response.status_code)  # Should be 200
```

### 2. Test Gemini API Connection

```python
import google.generativeai as genai
import os

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Test query")
print(response.text)  # Should return generated content
```

### 3. Test Notebook LM Access

```python
# Query Notebook LM content through Gemini
# This depends on how Notebook LM content is accessed
# May require specific project ID or notebook ID
```

---

## Security Notes

1. **Never commit `.env.local`** to version control
2. **Use `.env.local`** for local development (takes priority over `.env`)
3. **Rotate API keys** periodically
4. **Use service role keys** only server-side, never expose to frontend
5. **Restrict RAG_TRUSTED_ORIGIN** to your actual domains

---

## Troubleshooting

### RAG Service Issues
- **401 Unauthorized**: Check `RAG_API_KEY` is correct
- **Connection Error**: Verify `RAG_SERVICE_URL` is accessible
- **Empty Results**: Check collections exist and have data

### Gemini API Issues
- **API Key Invalid**: Verify key at https://makersuite.google.com/app/apikey
- **Rate Limits**: Check quota in Google Cloud Console
- **Model Not Found**: Verify `GEMINI_MODEL` name is correct

### Notebook LM Access
- **Content Not Found**: Verify you have access to the Notebook LM project
- **API Errors**: Check if Notebook LM requires separate authentication

---

## Next Steps

1. Add credentials to `.env.local`
2. Test each service connection
3. Run ingestion script to sync Notebook LM content to RAG
4. Verify AI target identification works with all services













