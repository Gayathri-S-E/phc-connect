# Smart Health & Supply Chain Resilience

## Production-Grade Healthcare & Pharmaceutical Supply Chain Management Platform

[![Architecture: Domain-Driven Design](https://img.shields.io/badge/Architecture-Domain--Driven%20Design-blue.svg)](file:///f:/github/phc%20connect/ARCHITECTURE.md)
[![Database: PostgreSQL 15+](https://img.shields.io/badge/Database-PostgreSQL%2015+-green.svg)](file:///f:/github/phc%20connect/DATABASE.md)
[![Backend: FastAPI + SQLAlchemy 2.0](https://img.shields.io/badge/Backend-FastAPI%20%7C%20SQLAlchemy%202.0-teal.svg)](file:///f:/github/phc%20connect/API.md)
[![Authorization: Database-Driven RBAC](https://img.shields.io/badge/Authorization-Database--Driven%20RBAC-red.svg)](file:///f:/github/phc%20connect/RBAC.md)

---

### Project Overview

**Smart Health & Supply Chain Resilience** is an enterprise-grade platform connecting primary healthcare delivery (PHCs, Community Health Centers, and District Hospitals) with end-to-end pharmaceutical supply chain logistics, inventory optimization, and intelligent shortage resilience.

The system guarantees:
- **Zero Hardcoding**: 100% database-driven permissions, roles, workflows, navigation, and thresholds.
- **Strict Domain Boundaries**: Modular architecture partitioned by business domains (Identity, Healthcare, Pharmacy, Supply Chain, Logistics, Intelligence, and Governance).
- **Concurrency & Resilience**: Row-level locking on inventory balances, FEFO batch allocation, and immutable audit trails.

---

### Architectural Documentation Suite

| Document | Purpose | Key Content |
| :--- | :--- | :--- |
| [**ANTIGRAVITY.md**](file:///f:/github/phc%20connect/ANTIGRAVITY.md) | **Architectural Constitution** | Core philosophy, strict anti-patterns, DDD rules, database-driven rules. |
| [**AI_START.md**](file:///f:/github/phc%20connect/AI_START.md) | **AI Agent Handbook** | Mandatory onboarding and pre-flight verification checklist for AI agents. |
| [**RBAC.md**](file:///f:/github/phc%20connect/RBAC.md) | **Role & Permission Matrix** | Approved 15 roles, atomic permissions, multi-tenancy & geographic scoping rules. |
| [**DATABASE.md**](file:///f:/github/phc%20connect/DATABASE.md) | **Data Architecture & Schema** | PostgreSQL schema, UUID PKs, foreign keys, constraints, and indexes. |
| [**ARCHITECTURE.md**](file:///f:/github/phc%20connect/ARCHITECTURE.md) | **System Blueprint** | Clean layered architecture, concurrency control, SoD, and error handling. |
| [**API.md**](file:///f:/github/phc%20connect/API.md) | **RESTful API Inventory** | Comprehensive endpoint catalog with HTTP verbs, permissions, and scopes. |
| [**SECURITY.md**](file:///f:/github/phc%20connect/SECURITY.md) | **Security Standards** | JWT rotation, Argon2id, IDOR defense, and OWASP Top 10 controls. |
| [**DEPLOYMENT.md**](file:///f:/github/phc%20connect/DEPLOYMENT.md) | **Deployment Guide** | Docker, docker-compose, environment variables, and Alembic migrations. |

---

### High-Level Architecture

```text
backend/
├── app/
│   ├── main.py                     # FastAPI app factory, middleware & router inclusion
│   ├── core/                       # Cross-cutting infrastructure
│   │   ├── config.py               # Pydantic Settings from environment
│   │   ├── database.py             # Async SQLAlchemy 2.0 engine & session maker
│   │   ├── security.py             # Password hashing (Argon2id/Bcrypt) & JWT lifecycle
│   │   ├── permissions.py          # Database-driven permission evaluator
│   │   ├── exceptions.py           # RFC 7807 problem details exception handlers
│   │   └── logging.py              # Structured JSON logging & correlation IDs
│   │
│   ├── api/
│   │   ├── deps.py                 # FastAPI dependencies (auth, permissions, db session)
│   │   └── v1/                     # RESTful v1 router modular endpoints
│   │       ├── auth.py             # Authentication & session rotation
│   │       ├── users.py            # User provisioning & profile management
│   │       ├── roles.py            # Dynamic role & permission assignment
│   │       ├── facilities.py       # PHCs, CHCs, warehouses, health centers
│   │       ├── patients.py         # Patient registration, records, clinical history
│   │       ├── appointments.py     # Appointment booking and triage
│   │       ├── consultations.py    # Doctor notes, vitals, diagnoses
│   │       ├── prescriptions.py    # Prescription drafting & pharmacy dispensing
│   │       ├── labs.py             # Diagnostic lab orders & validated results
│   │       ├── medications.py      # Formulary & cold-chain specifications
│   │       ├── inventory.py        # Stock levels, movements, FEFO batches
│   │       ├── procurement.py      # Purchase requests and supplier purchase orders
│   │       ├── suppliers.py        # Supplier registry and performance
│   │       ├── shipments.py        # Logistics tracking and transit milestones
│   │       ├── shortages.py        # Shortage reporting and escalation engine
│   │       ├── alerts.py           # Real-time operational & clinical alerts
│   │       ├── ai.py               # Demand forecasting & risk analysis
│   │       ├── dashboards.py       # Real-time role-scoped metrics
│   │       └── health.py           # Health checks (/health, /health/ready)
│   │
│   ├── models/                     # SQLAlchemy 2.0 ORM Declarative Models
│   ├── schemas/                    # Pydantic v2 DTOs (Request / Response validation)
│   ├── services/                   # Core business logic and transaction boundaries
│   └── repositories/               # Async database query abstractions
│
├── alembic/                        # Reversible database migrations
├── scripts/                        # Database seeding & administrative scripts
├── tests/                          # Automated unit, integration, and security tests
├── Dockerfile                      # Production multi-stage Docker build
├── docker-compose.yml              # Local PostgreSQL + Backend orchestration
├── requirements.txt                # Production Python dependencies
└── .env.example                    # Environment variable template
```

---

### Quick Start (Local Development)

#### 1. Clone & Configure Environment
```bash
cp .env.example .env
```

#### 2. Run with Docker Compose
```bash
docker-compose up --build
```

#### 3. Access API Documentation
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)
