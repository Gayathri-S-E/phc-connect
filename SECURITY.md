# SECURITY.md — Security Engineering Standards & Defense Protocol
## Smart Health & Supply Chain Resilience Platform

> **Security Posture:** Zero-Trust, Defense-in-Depth, Principle of Least Privilege  
> **Target Standards:** OWASP Top 10 API Security, HIPAA / National Health Data Privacy Guidelines

---

### 1. Identity & Credential Protection

#### 1.1 Password Storage
- Passwords are encrypted using **Argon2id** (memory cost = 65536 KiB, iterations = 3, parallelism = 4) or **Bcrypt** (work factor ≥ 12).
- Plaintext passwords never touch database logs or error diagnostics.

#### 1.2 JWT Token Lifecycle & Rotation
- **Access Tokens**: Short-lived (15 minutes). Contains `sub` (User UUID), `org_id`, `fac_id`, and `token_type: access`. Never contains sensitive medical data.
- **Refresh Tokens**: Cryptographically random 256-bit strings (stored as a one-way SHA-256 hash in `user_sessions`). Valid for 7 days.
- **Token Rotation**: Every refresh request burns the used refresh token and issues a new pair. If a revoked or already-used refresh token is presented, all sessions for that user are immediately invalidated (Replay Attack Defense).

---

### 2. Multi-Tenancy, IDOR Prevention & Resource Scoping

#### 2.1 The Insecure Direct Object Reference (IDOR) Threat
An attacker possessing a valid JWT must not be able to query another patient's medical records or another facility's private stock by merely incrementing or guessing a UUID.

#### 2.2 Scoped Authorization Rules
Every query in the repository must inject organizational or facility scope filters:

```python
# CORRECT: Scoped query preventing horizontal privilege escalation
async def get_patient_by_id(
    self, 
    patient_id: UUID, 
    actor_facility_id: UUID, 
    is_global_admin: bool
) -> Patient | None:
    stmt = select(Patient).where(Patient.id == patient_id)
    if not is_global_admin:
        stmt = stmt.where(Patient.primary_facility_id == actor_facility_id)
    result = await self._session.execute(stmt)
    return result.scalar_one_or_none()
```

---

### 3. Privileged Operations & Step-Up Security

- **Super Admin Isolation**: Super Admin operations (assigning system roles, creating organizations, modifying audit policies) require recent authentication (within last 10 minutes) or TOTP/MFA code confirmation.
- **Audit Immutability**: The `audit_logs` table has no `UPDATE` or `DELETE` endpoints exposed in FastAPI. In production PostgreSQL, database grants restrict application users to `INSERT` and `SELECT` only on the audit table.
- **Segregation of Duties (SoD)**: The user creating a purchase order cannot be the user who approves that order.

---

### 4. Input Sanitization & Transport Security

- **Strict Schema Filtering**: Pydantic models use `extra="forbid"` to eliminate mass-assignment vulnerabilities.
- **SQL Injection Prevention**: 100% of queries use SQLAlchemy 2.0 parameterized expressions (`select()`, `where()`). Raw string concatenation in SQL is prohibited.
- **HTTP Security Headers**: Middleware injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security: max-age=31536000`, and strict CORS policies.
