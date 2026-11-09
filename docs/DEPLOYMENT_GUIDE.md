# Production Deployment & Hosting Guide

> [!IMPORTANT]
> **Deployment Status Transparency:**
> This repository contains production-ready Docker containers, Nginx reverse proxy configurations, environment templates, and multi-cloud architectural recipes. In accordance with strict software engineering standards, **the application is currently configured and verified locally in containerized environments; live cloud hosting has not been provisioned or claimed until external cloud deployments are formally executed by the platform administrator.**

---

## 1. Hosting Architecture Comparison & Recommendations

| Subsystem | Tier 1: Cloud-Native Enterprise (AWS) | Tier 2: Managed PaaS (Railway / Render) | Tier 3: Budget / Open-Source Self-Hosted |
| :--- | :--- | :--- | :--- |
| **Frontend** | AWS S3 + CloudFront CDN | Vercel / Netlify | Nginx container on VPS (Hetzner / DigitalOcean) |
| **FastAPI Backend** | AWS App Runner / ECS Fargate | Railway Service / Render Web Service | Docker on VPS via Docker Compose |
| **Relational Database** | AWS Aurora Serverless PostgreSQL 16 | Railway Managed PostgreSQL | PostgreSQL 16 Docker container with named volume |
| **Vector Database** | Pinecone / Qdrant Cloud / Chroma on ECS | ChromaDB on Persistent Volume | ChromaDB on persistent local NVMe volume |
| **Media & File Storage**| AWS S3 Bucket with CloudFront CDN | Cloudflare R2 / AWS S3 | Local Docker volume (`./storage`) with Nginx static serve |
| **Background / Workers**| Celery on AWS SQS + ECS Workers | Railway Background Worker | FastAPI Async Background Tasks / Celery + Redis |
| **Estimated Cost** | **$45 - $120 / month** | **$15 - $35 / month** | **$10 - $20 / month** (Single VPS) |

### Recommended Default Strategy:
- **For Rapid MVP / Education Demo:** Deploy Frontend to **Vercel** and Backend + PostgreSQL to **Railway** ($5-$15/mo).
- **For High-Concurrency Institutional Rollout:** Deploy via **AWS ECS Fargate** with **Aurora PostgreSQL** and **S3 + CloudFront CDN**.

---

## 2. Production Configuration & Environment Hardening

Ensure the following environment variables are securely populated in production (see `.env.production.example`):

```bash
# General Environment
ENVIRONMENT=production
DEBUG=false
PROJECT_NAME="AI-Powered Multimodal Student Tutor"
VERSION=1.0.0

# Server Bindings
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
WORKERS_COUNT=4

# Cryptographic Keys (Generate with `openssl rand -hex 32`)
JWT_SECRET_KEY=94f872c0d8329ab813d9f2e...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Production Database Pool
DATABASE_URL=postgresql://tutor_admin:StrongPassword123@postgres:5432/ai_tutor_db

# CORS & Security
CORS_ORIGINS=["https://tutor.yourdomain.edu","https://app.yourdomain.edu"]
ENABLE_RATE_LIMITER=true
RATE_LIMIT_PER_MINUTE=120

# Error Monitoring (Sentry)
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0

# File Logging & Rotation
ENABLE_FILE_LOGGING=true
LOG_FILE_PATH=/app/storage/logs/tutor.log
```

---

## 3. Step-by-Step Deployment Procedures

### 3.1 Option A: Local & Staging Deployment with Docker Compose

1. **Clone and Navigate:**
   ```bash
   git clone <repo_url>
   cd "AI tutor"
   ```

2. **Configure Environment:**
   ```bash
   cp .env.production.example .env
   # Edit .env with your production secrets
   ```

3. **Build and Launch Multi-Container Stack:**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

4. **Verify Health:**
   ```bash
   curl -f http://localhost/api/v1/health
   # Expected response: {"status": "healthy", "database": "connected", "vector_store": "ready"}
   ```

5. **Stop Stack:**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

---

### 3.2 Option B: Deployment to Railway / Render (PaaS)

1. **Deploy PostgreSQL:**
   - In Railway / Render Dashboard, click **New +** $\rightarrow$ **Database** $\rightarrow$ **PostgreSQL 16**.
   - Copy the provided `DATABASE_URL`.

2. **Deploy FastAPI Backend:**
   - Click **New +** $\rightarrow$ **GitHub Repo** $\rightarrow$ select your repository.
   - Set Root Directory to `backend`.
   - Add Environment Variables (`DATABASE_URL`, `JWT_SECRET_KEY`, `ENVIRONMENT=production`, etc.).
   - Attach a **Persistent Disk** mounted to `/app/storage` (for ChromaDB and audio caches).
   - Start Command: `gunicorn -c gunicorn_conf.py app.main:app`.

3. **Deploy Frontend:**
   - Click **New +** $\rightarrow$ **Static Site** $\rightarrow$ select your repository.
   - Set Root Directory to `frontend`.
   - Build Command: `npm install && npm run build`.
   - Output Directory: `dist`.
   - Set `VITE_API_URL` to your live backend domain (e.g., `https://backend-production.up.railway.app`).

---

### 3.3 Option C: Enterprise AWS Cloud Deployment

1. **Database:** Provision **AWS RDS PostgreSQL 16** with Multi-AZ redundancy within a private VPC subnet.
2. **Backend Container:**
   - Build backend Docker image and push to **AWS Elastic Container Registry (ECR)**:
     ```bash
     aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com
     docker build -t ai-tutor-backend ./backend
     docker tag ai-tutor-backend:latest <account_id>.dkr.ecr.us-east-1.amazonaws.com/ai-tutor-backend:latest
     docker push <account_id>.dkr.ecr.us-east-1.amazonaws.com/ai-tutor-backend:latest
     ```
   - Launch an **AWS App Runner** or **ECS Fargate Service** using the pushed image.
   - Inject secrets via **AWS Secrets Manager**.
3. **Frontend CDN:**
   - Build Vite SPA: `cd frontend && npm run build`.
   - Sync `dist/` to an S3 bucket configured for static web hosting:
     ```bash
     aws s3 sync dist/ s3://ai-tutor-frontend-production --delete
     ```
   - Configure **CloudFront CDN Distribution** pointing to the S3 bucket with an SSL certificate issued via **AWS Certificate Manager (ACM)**.
4. **Monitoring & Logging:**
   - Stream container stdout/stderr to **AWS CloudWatch Logs**.
   - Configure Sentry DSN in backend environment for real-time exception alerts.
