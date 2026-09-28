# DEPLOYMENT.md — Production Deployment & Infrastructure Guide
## Smart Health & Supply Chain Resilience Platform

> **Target Environment:** Containerized Linux (Docker / Kubernetes / Cloud Run)  
> **Process Manager:** Uvicorn with Gunicorn ASGI workers  
> **Database:** Managed PostgreSQL 15+ (AWS RDS, GCP Cloud SQL, or High-Availability Cluster)

---

### 1. Environment Configuration (`.env`)

Never commit `.env` to version control. Use `.env.example` as the canonical template:

```ini
# Environment & Server
ENVIRONMENT=production
DEBUG=false
APP_NAME="Smart Health & Supply Chain Resilience"
PORT=8000
HOST=0.0.0.0
WORKERS=4

# Database Connection (Asyncpg)
DATABASE_URL=postgresql+asyncpg://app_user:strong_password@postgres:5432/smarthealth_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_TIMEOUT_SECONDS=30

# JWT & Authentication Security
JWT_SECRET=generate_with_openssl_rand_hex_64
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS & Trusted Hosts
ALLOWED_ORIGINS=["https://health.gov.in","https://phc-connect.internal"]
ALLOWED_HOSTS=["health.gov.in","api.phc-connect.internal"]

# Logging & Observability
LOG_LEVEL=INFO
ENABLE_JSON_LOGS=true
```

---

### 2. Docker Architecture

#### Multi-Stage Dockerfile (`backend/Dockerfile`)
```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production runtime
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl && rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .

# Run as non-root user
RUN useradd -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
```

---

### 3. Orchestration with Docker Compose (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: smarthealth_postgres
    restart: always
    environment:
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: local_dev_secret_password
      POSTGRES_DB: smarthealth_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app_user -d smarthealth_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: smarthealth_backend
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    command: >
      sh -c "alembic upgrade head &&
             python scripts/seed_initial_data.py &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

volumes:
  pgdata:
```

---

### 4. Migration Execution & Zero-Downtime Releases

1. **Pre-Deployment**: Run migrations (`alembic upgrade head`) before shifting traffic. All schema migrations must be additive and backwards-compatible.
2. **Readiness Verification**: Kubernetes / load balancers query `GET /health/ready`. Traffic is routed only after database connectivity is verified.
3. **Graceful Shutdown**: On `SIGTERM`, FastAPI finishes inflight requests and gracefully closes PostgreSQL connection pools.
