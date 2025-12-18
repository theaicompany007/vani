---
name: VANI Google Cloud Deployment
overview: Comprehensive deployment plan for VANI Flask application on Google Cloud Platform with multiple deployment options (Cloud Run, Compute Engine VM, App Engine) including production-grade setup with custom domain, SSL, load balancing, and CI/CD integration.
todos: []
---

# VANI Google Cloud Deployment Plan

## Overview

Deploy VANI (Flask-based outreach command center) on Google Cloud Platform with production-grade infrastructure including HTTPS, custom domain, monitoring, and automated deployments.

## Deployment Architecture Options

### Option 1: Cloud Run (Recommended for Production)

**Pros:**

- Serverless, auto-scaling
- HTTPS by default
- Pay-per-use pricing
- Easy CI/CD integration
- Built-in load balancing
- No server management

**Cons:**

- Cold starts possible
- 60-minute request timeout
- Background tasks need separate service

**Best for:** Production deployments with variable traffic

### Option 2: Compute Engine VM (Full Control)

**Pros:**

- Full control over environment
- Persistent storage
- No cold starts
- Background tasks run continuously
- Custom configurations

**Cons:**

- Server management required
- Manual scaling
- Need load balancer for HTTPS
- Higher base cost

**Best for:** High-traffic, always-on requirements, complex background tasks

### Option 3: App Engine (Legacy)

**Pros:**

- Managed platform
- Auto-scaling
- Integrated services

**Cons:**

- Less flexible than Cloud Run
- Older platform
- Limited customization

**Best for:** Simple deployments (not recommended for VANI)

## Recommended: Hybrid Approach

- **Cloud Run**: Main Flask application (web requests, API endpoints)
- **Cloud Scheduler + Cloud Functions**: Background polling tasks
- **Cloud SQL**: If migrating from Supabase (optional)
- **Cloud Load Balancer**: Custom domain + SSL (if using VM)

## Implementation Plan

### Phase 1: Cloud Run Deployment (Primary)

#### 1.1 Prepare Application for Cloud Run

**Files to Create/Modify:**

1. **`Dockerfile`** - Containerize Flask app
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 0 app:app
   ```

2. **`app.py`** or modify `run.py` - Cloud Run entry point

            - Remove ngrok dependency
            - Use environment variable for port: `os.getenv('PORT', 5000)`
            - Ensure Flask app is accessible as `app` object

3. **`.dockerignore`** - Exclude unnecessary files
   ```
   venv/
   __pycache__/
   *.pyc
   .git/
   .env.local
   logs/
   *.log
   ```

4. **`cloudbuild.yaml`** - CI/CD configuration
   ```yaml
   steps:
     - name: 'gcr.io/cloud-builders/docker'
       args: ['build', '-t', 'gcr.io/$PROJECT_ID/vani:latest', '.']
     - name: 'gcr.io/cloud-builders/docker'
       args: ['push', 'gcr.io/$PROJECT_ID/vani:latest']
     - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
       entrypoint: gcloud
       args:
         - 'run'
         - 'deploy'
         - 'vani'
         - '--image'
         - 'gcr.io/$PROJECT_ID/vani:latest'
         - '--region'
         - 'us-central1'
         - '--platform'
         - 'managed'
   ```


#### 1.2 Environment Configuration

**Cloud Run Environment Variables:**

- All variables from `.env.local` should be set in Cloud Run
- Use Secret Manager for sensitive values (API keys)
- Configure via: Cloud Console or `gcloud run services update`

**Required Variables:**

```
SUPABASE_URL
SUPABASE_KEY
SUPABASE_SERVICE_KEY
RESEND_API_KEY
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
OPENAI_API_KEY
RAG_API_KEY (optional)
GEMINI_API_KEY (optional)
WEBHOOK_BASE_URL (Cloud Run service URL)
FLASK_ENV=production
```

#### 1.3 Deploy to Cloud Run

**Manual Deployment:**

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/vani

# Deploy to Cloud Run
gcloud run deploy vani \
  --image gcr.io/PROJECT_ID/vani \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FLASK_ENV=production \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 1
```

**Get Service URL:**

```bash
gcloud run services describe vani --region us-central1 --format 'value(status.url)'
```

#### 1.4 Custom Domain Setup

1. **Map Custom Domain:**
   ```bash
   gcloud run domain-mappings create \
     --service vani \
     --domain yourdomain.com \
     --region us-central1
   ```

2. **Update DNS:**

            - Add CNAME record pointing to Cloud Run domain
            - Wait for SSL certificate provisioning (automatic)

3. **Update WEBHOOK_BASE_URL:**

            - Set to custom domain: `https://yourdomain.com`

### Phase 2: Background Tasks (Cloud Scheduler + Cloud Functions)

Since Cloud Run has request timeout limits, move background polling to Cloud Functions:

#### 2.1 Create Cloud Function for Polling

**File: `cloud_functions/dashboard_polling/main.py`**

```python
import requests
import os

def dashboard_polling(request):
    """Triggered by Cloud Scheduler"""
    service_url = os.getenv('VANI_SERVICE_URL')
    response = requests.post(f'{service_url}/api/dashboard/stats')
    return {'status': 'success', 'response': response.json()}
```

#### 2.2 Deploy Cloud Function

```bash
gcloud functions deploy dashboard_polling \
  --runtime python311 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point dashboard_polling \
  --set-env-vars VANI_SERVICE_URL=https://vani-xxx.run.app
```

#### 2.3 Create Cloud Scheduler Jobs

```bash
# Poll at 10 AM, 12 PM, 2 PM, 5 PM daily
gcloud scheduler jobs create http dashboard-poll-10am \
  --schedule="0 10 * * *" \
  --uri="https://REGION-PROJECT.cloudfunctions.net/dashboard_polling" \
  --http-method=POST \
  --time-zone="America/New_York"
```

### Phase 3: Compute Engine VM (Alternative/Supplemental)

If Cloud Run doesn't meet requirements, use VM deployment:

#### 3.1 Create VM Instance

```bash
gcloud compute instances create vani-vm \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --tags=http-server,https-server
```

#### 3.2 Setup Load Balancer

1. **Create Backend Service:**
   ```bash
   gcloud compute backend-services create vani-backend \
     --protocol HTTP \
     --health-checks vani-health-check \
     --global
   ```

2. **Create URL Map:**
   ```bash
   gcloud compute url-maps create vani-url-map \
     --default-service vani-backend
   ```

3. **Create HTTPS Proxy:**
   ```bash
   gcloud compute target-https-proxies create vani-https-proxy \
     --url-map vani-url-map \
     --ssl-certificates vani-ssl-cert
   ```

4. **Create Forwarding Rule:**
   ```bash
   gcloud compute forwarding-rules create vani-https-rule \
     --global \
     --target-https-proxy vani-https-proxy \
     --ports 443
   ```


#### 3.3 Deploy Application on VM

Follow existing `GOOGLE_VM_DEPLOYMENT.md` guide but:

- Remove ngrok dependency
- Use load balancer IP for webhooks
- Configure systemd services
- Setup log rotation

### Phase 4: Database & Storage

#### 4.1 Supabase (Current - Keep)

- No changes needed
- Ensure Cloud Run/VM can access Supabase
- Whitelist Cloud Run IP ranges if needed

#### 4.2 Optional: Migrate to Cloud SQL

- Create Cloud SQL PostgreSQL instance
- Export data from Supabase
- Import to Cloud SQL
- Update connection strings

### Phase 5: Monitoring & Logging

#### 5.1 Cloud Logging

- Automatic for Cloud Run
- Configure log retention
- Set up log-based metrics

#### 5.2 Cloud Monitoring

- Create uptime checks
- Set up alerts for errors
- Monitor response times
- Track API usage

#### 5.3 Error Reporting

```bash
gcloud services enable clouderrorreporting.googleapis.com
```

### Phase 6: Security

#### 6.1 Secret Manager

```bash
# Store API keys in Secret Manager
echo -n "your-api-key" | gcloud secrets create supabase-key --data-file=-

# Access in Cloud Run
gcloud run services update vani \
  --update-secrets SUPABASE_KEY=supabase-key:latest
```

#### 6.2 IAM Roles

- Create service account for Cloud Run
- Grant minimal required permissions
- Use service account for deployments

#### 6.3 VPC (Optional)

- Create VPC for VM deployment
- Configure firewall rules
- Private IP for internal services

### Phase 7: CI/CD Pipeline

#### 7.1 GitHub Actions Workflow

**File: `.github/workflows/deploy.yml`**

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: google-github-actions/setup-gcloud@v1
      - run: gcloud builds submit --tag gcr.io/$PROJECT_ID/vani
      - run: gcloud run deploy vani --image gcr.io/$PROJECT_ID/vani
```

#### 7.2 Cloud Build Triggers

- Connect GitHub repository
- Auto-deploy on push to main
- Run tests before deployment

## Migration Checklist

### Pre-Deployment

- [ ] Review and update `run.py` to work without ngrok
- [ ] Create Dockerfile
- [ ] Test Docker image locally
- [ ] Prepare environment variables list
- [ ] Set up GCP project and billing
- [ ] Enable required APIs (Cloud Run, Cloud Build, etc.)

### Deployment

- [ ] Build and push Docker image
- [ ] Deploy to Cloud Run
- [ ] Configure environment variables
- [ ] Test service URL
- [ ] Map custom domain (if applicable)
- [ ] Update webhook URLs in external services
- [ ] Deploy background task functions
- [ ] Create Cloud Scheduler jobs
- [ ] Test all endpoints

### Post-Deployment

- [ ] Set up monitoring and alerts
- [ ] Configure log retention
- [ ] Test webhook endpoints
- [ ] Verify all integrations work
- [ ] Update documentation
- [ ] Set up CI/CD pipeline
- [ ] Create backup procedures

## Cost Estimation

### Cloud Run (Estimated Monthly)

- Requests: ~$0.40 per million
- CPU/Memory: ~$10-50/month (depending on traffic)
- **Total: ~$15-60/month** (low to medium traffic)

### Compute Engine VM (Estimated Monthly)

- e2-medium instance: ~$30/month
- Load balancer: ~$18/month
- **Total: ~$48/month** (base cost)

### Additional Services

- Cloud Scheduler: Free tier (3 jobs)
- Cloud Functions: Free tier (2M invocations)
- Cloud Logging: Free tier (50GB)
- **Total: ~$0-10/month** (within free tier)

## Files to Create

1. `Dockerfile` - Container definition
2. `.dockerignore` - Docker build exclusions
3. `cloudbuild.yaml` - Cloud Build configuration
4. `cloud_functions/dashboard_polling/main.py` - Background polling function
5. `cloud_functions/dashboard_polling/requirements.txt` - Function dependencies
6. `.github/workflows/deploy.yml` - GitHub Actions workflow
7. `deploy-cloud-run.sh` - Deployment script
8. `scripts/setup_gcp_secrets.sh` - Secret Manager setup script

## Next Steps

1. Choose deployment option (Cloud Run recommended)
2. Create Dockerfile and test locally
3. Set up GCP project and enable APIs
4. Deploy to Cloud Run
5. Configure custom domain
6. Set up background tasks
7. Configure monitoring
8. Set up CI/CD

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)