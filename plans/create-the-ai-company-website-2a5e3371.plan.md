<!-- 2a5e3371-858c-4aad-89df-fc1dbaa2cc27 63669049-ecf2-41f7-aefd-2667fb6bb7b4 -->
# Create Standalone The AI Company Website Project

## Overview

Build a completely independent Next.js project for "The AI Company" marketing website. The project will use Supabase for data storage, optionally integrate with RAG/Chroma services for Knowledge Base chat, and include Docker containerization with a Python management script similar to the OnlyneReputation app but completely independent.

## Project Structure

```
theaicompany-web/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Home page
│   ├── api/
│   │   ├── use-cases/
│   │   │   └── route.ts         # GET use cases API
│   │   ├── contacts/
│   │   │   └── route.ts         # POST contact form API
│   │   └── rag/
│   │       └── query/
│   │           └── route.ts     # RAG proxy for Knowledge Base (optional)
│   └── components/
│       ├── ServiceCard.tsx
│       ├── UseCaseCard.tsx
│       └── ChatModal.tsx
├── lib/
│   ├── supabase.ts              # Supabase client setup
│   └── types.ts                 # TypeScript interfaces
├── migrations/
│   └── init.sql                 # Supabase schema migration
├── docker/
│   ├── Dockerfile               # Production Docker image
│   └── docker-compose.yml      # Local development setup
├── scripts/
│   ├── seed-use-cases.ts       # Seed initial data
│   └── setup-supabase.mjs      # Supabase setup helper
├── run-theaicompany-web.py     # Main management script
├── package.json
├── tsconfig.json
├── next.config.ts
├── .env.example
└── README.md
```

## Implementation Steps

### 1. Initialize New Next.js Project

- Create new directory `theaicompany-web` (outside current workspace)
- Initialize Next.js 15 project with TypeScript
- Configure Tailwind CSS
- Set up project structure

### 2. Install Dependencies

- Core: `next`, `react`, `react-dom`, `typescript`
- Database: `@supabase/supabase-js`
- UI: `lucide-react` (icons), `tailwindcss`
- Optional: `better-sqlite3` (if needed for local dev)

### 3. Supabase Setup

- Create new Supabase project with `theaicompany007@gmail.com`
- Create database schema:
  - `use_cases` table (id, industry, account, use_case, stat, description, channel, created_at)
  - `website_contacts` table (id, name, email, phone, message, created_at)
- Create migration file `migrations/init.sql`
- Set up environment variables for Supabase connection
- Create `lib/supabase.ts` with client initialization

### 4. Create API Routes

- `app/api/use-cases/route.ts`:
  - GET: Fetch all use cases with optional search/filter
  - Support query params: `?search=term&industry=IndustryName`
- `app/api/contacts/route.ts`:
  - POST: Submit contact form, store in Supabase
  - Validate input, return success/error
- `app/api/rag/query/route.ts` (optional):
  - POST: Proxy to RAG service for Knowledge Base chat
  - Use `RAG_SERVICE_URL` and `RAG_API_KEY` from env
  - Forward queries to `https://rag.kcube-consulting.com/rag/query`

### 5. Create Main Page Component

- Convert provided React code to Next.js format
- Replace Firebase calls with API route calls (`/api/use-cases`)
- Implement search and filter functionality
- Connect contact form to `/api/contacts`
- Integrate ChatModal with RAG API (if enabled)

### 6. Create Supporting Components

- `ServiceCard.tsx`: Three pillar service cards
- `UseCaseCard.tsx`: Dynamic use case display cards
- `ChatModal.tsx`: AI Knowledge Base chat interface
  - Connect to `/api/rag/query` if RAG enabled
  - Fallback to static responses if RAG unavailable

### 7. Docker Configuration

- `docker/Dockerfile`:
  - Multi-stage build (dependencies → production)
  - Node.js 22.x base image
  - Copy project files, install deps, build Next.js
  - Expose port 3000
- `docker/docker-compose.yml`:
  - Next.js app service
  - ngrok service (optional, for local tunneling)
  - Environment variables configuration
  - Volume mounts for development

### 8. Python Management Script

- Create `run-theaicompany-web.py`:
  - Reuse utility functions from `run-onlynereputation-agentic-app.py`:
    - `print_success`, `print_warn`, `print_error`, `print_info`
    - `run_cmd` (command execution)
    - `check_port_in_use`, `wait_for_server`
  - New functions:
    - `check_dependencies()`: Verify Node.js, npm, Docker
    - `setup_supabase()`: Guide through Supabase setup
    - `seed_initial_data()`: Run seed script
    - `start_local_dev()`: Start Next.js dev server
    - `build_docker()`: Build Docker image
    - `start_docker()`: Run Docker container
    - `setup_ngrok()`: Configure ngrok tunnel
    - `deploy_to_vm()`: Deploy to Google Cloud VM
    - `check_status()`: Check service health

### 9. Environment Configuration

- Create `.env.example` with:
  - Supabase: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - RAG (optional): `RAG_SERVICE_URL`, `RAG_API_KEY`
  - App: `NEXT_PUBLIC_APP_URL`
  - ngrok: `NGROK_AUTH_TOKEN`, `NGROK_DOMAIN`

### 10. Seed Script

- Create `scripts/seed-use-cases.ts`:
  - Use provided `RAW_USE_CASE_DATA` array
  - Connect to Supabase using service role key
  - Insert use cases if table is empty
  - Handle duplicates gracefully

### 11. Deployment Scripts

- `deploy/docker-build.sh`: Build production Docker image
- `deploy/docker-run.sh`: Run container with ngrok
- `deploy/vm-setup.sh`: Setup script for Google Cloud VM
- `deploy/vm-deploy.sh`: Deploy to VM script

### 12. Documentation

- `README.md`: Setup instructions, environment variables, deployment guide
- Document RAG integration (optional)
- Document Docker deployment
- Document VM deployment process

## Key Features

### RAG Integration (Optional)

- Knowledge Base chat uses RAG service if `RAG_SERVICE_URL` is configured
- Falls back gracefully if RAG unavailable
- Proxy API route keeps `RAG_API_KEY` server-side only

### Supabase Integration

- Use cases stored in Supabase `use_cases` table
- Contact form submissions in `website_contacts` table
- Real-time updates via Supabase subscriptions (optional)

### Docker Deployment

- Production-ready Docker image
- Environment-based configuration
- ngrok integration for tunneling
- Health check endpoints

### Python Management Script

- Interactive menu system
- Local development mode
- Docker build/run commands
- VM deployment automation
- Status checking utilities

## File Structure Details

```
theaicompany-web/
├── app/
│   ├── layout.tsx               # Root layout (standalone, no auth)
│   ├── page.tsx                 # Main marketing page
│   ├── globals.css              # Global styles
│   ├── api/
│   │   ├── use-cases/route.ts
│   │   ├── contacts/route.ts
│   │   └── rag/query/route.ts
│   └── components/
│       ├── ServiceCard.tsx
│       ├── UseCaseCard.tsx
│       └── ChatModal.tsx
├── lib/
│   ├── supabase.ts              # Supabase client
│   └── types.ts                 # TypeScript types
├── migrations/
│   └── init.sql                 # Database schema
├── scripts/
│   ├── seed-use-cases.ts
│   └── setup-supabase.mjs
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── deploy/
│   ├── docker-build.sh
│   ├── docker-run.sh
│   ├── vm-setup.sh
│   └── vm-deploy.sh
├── run-theaicompany-web.py      # Main script
├── package.json
├── tsconfig.json
├── next.config.ts
├── .env.example
└── README.md
```

## Environment Variables

### Required

- `NEXT_PUBLIC_SUPABASE_URL`: Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key (server-side only)

### Optional

- `RAG_SERVICE_URL`: RAG service endpoint (default: `https://rag.kcube-consulting.com`)
- `RAG_API_KEY`: RAG service API key
- `NEXT_PUBLIC_APP_URL`: Public URL of the website
- `NGROK_AUTH_TOKEN`: ngrok authentication token
- `NGROK_DOMAIN`: ngrok domain (e.g., `growthrevenue-prod.grok.app`)

## Testing Checklist

- Project initializes correctly
- Supabase connection works
- Use cases API returns data
- Contact form submits successfully
- Search and filter work
- Chat modal works (with/without RAG)
- Docker build succeeds
- Docker container runs
- ngrok tunnel works
- Python script functions correctly
- VM deployment works

## Dependencies from Existing Script

Functions to reuse from `run-onlynereputation-agentic-app.py`:

- Color printing utilities (print_success, print_warn, etc.)
- Command execution (run_cmd)
- Port checking (check_port_in_use)
- Server waiting (wait_for_server)
- Process management utilities

### To-dos

- [ ] Install lucide-react and optionally better-sqlite3 packages
- [ ] Create new Supabase project and database tables (use_cases, website_contacts)
- [ ] Create API routes for use cases and contact form submissions
- [ ] Create standalone layout for /theaicompany route without Header/AuthGate
- [ ] Convert React component to Next.js page with API integration
- [ ] Extract ServiceCard, UseCaseCard, and ChatModal components
- [ ] Update AuthGate to allow /theaicompany path without authentication
- [ ] Create Docker and VM deployment configurations with ngrok setup