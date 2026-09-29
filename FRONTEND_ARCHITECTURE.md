# FRONTEND_ARCHITECTURE.md — Frontend Architecture & Design Specification
## Smart Health & Supply Chain Resilience Platform (PHC Connect)

> **Design Principle:** One single connected healthcare platform serving 13 authorized user perspectives with shared components, role-aware routing, centralized API client, resilient error states, English + Tamil localization, and a unified context-aware AI assistant.

---

## 1. Directory Structure

```text
frontend/src/
├── assets/                  # Static assets and icons
├── components/
│   ├── common/              # Shared reusable design system components
│   │   ├── Badge.tsx        # Semantic status & priority indicators
│   │   ├── DataTable.tsx    # Paginated, searchable, sortable tables
│   │   ├── Header.tsx       # Top navigation bar with user profile, language switcher
│   │   ├── Layout.tsx       # App shell with responsive sidebar & drawer
│   │   ├── Modal.tsx        # Accessible dialogs & confirmation workflows
│   │   ├── Navigation.tsx   # Dynamic role navigation derived from permissions
│   │   ├── StateView.tsx    # Standardized Loading, Empty, and Error state displays
│   │   └── Toast.tsx        # Global toast alert notification system
│   └── ai/
│       └── UnifiedAiAssistant.tsx # Dockable, role-aware unified AI assistant
├── context/
│   ├── AuthContext.tsx      # Authentication state, login/logout, demo user switcher
│   └── LanguageContext.tsx  # English / Tamil localization provider
├── portals/                 # The 13 Dedicated Role Portals
│   ├── PatientPortal.tsx            # Role 01: Citizen / Patient
│   ├── DoctorPortal.tsx             # Role 02: Medical Officer
│   ├── NursePortal.tsx              # Role 03: Nurse / Healthcare Staff
│   ├── FacilityAdminPortal.tsx      # Role 04: PHC In-charge / Facility Manager
│   ├── PharmacistPortal.tsx         # Role 05: Pharmacist / Storekeeper
│   ├── DistrictHealthPortal.tsx     # Role 06: District Health Officer (DHO)
│   ├── DistrictSupplyPortal.tsx     # Role 07: District Supply Chain Officer (DSCO)
│   ├── DistrictEmergencyPortal.tsx  # Role 08: District Emergency Coordinator (DEC)
│   ├── StateHealthPortal.tsx        # Role 09: State Health Administrator
│   ├── StateSupplyPortal.tsx        # Role 10: State Supply Chain / Warehouse Manager
│   ├── PublicHealthAnalystPortal.tsx# Role 11: State Public Health Analyst
│   ├── NationalHealthPortal.tsx     # Role 12: National Health Authority
│   └── PlatformAdminPortal.tsx      # Role 13: National Platform Administrator / Super Admin
├── services/
│   ├── api.ts               # Centralized HTTP client with JWT interceptor & retry
│   └── types.ts             # TypeScript interfaces for models & API contracts
├── utils/
│   ├── formatters.ts        # Date, time, currency, and numerical formatters
│   └── i18n.ts              # English and Tamil localized string dictionaries
├── App.tsx                  # Root application router and route guards
├── index.css                # Global healthcare design system variables & glassmorphism
└── main.tsx                 # React DOM root entry point
```

---

## 2. Authentication & Session Architecture

### 2.1 Token Lifecycle
1. **Initial Login:** User provides credentials -> `POST /api/v1/auth/login` returns:
   - `access_token` (Short-lived JWT, HS256)
   - `refresh_token` (Longer-lived token)
   - User identity, assigned roles, and facility scope.
2. **Storage:**
   - `access_token` and `refresh_token` stored securely in `localStorage` for PWA offline-first resilience.
3. **Session Rehydration:**
   - On page refresh, `AuthContext` calls `GET /api/v1/auth/me` to refresh active permissions and scope.
   - Concurrently calls `GET /api/v1/navigation/me` to fetch authorized navigation items.
4. **Transparent Token Rotation (401 Interceptor):**
   - When any API call receives HTTP 401 Unauthorized:
   - Client automatically queues failed request.
   - Issues `POST /api/v1/auth/refresh` with `{ "refresh_token": "..." }`.
   - On success: updates tokens and retries queued requests transparently.
   - On failure (refresh expired/revoked): wipes tokens, sets user to null, and redirects to `/login` with flash alert "Session expired. Please log in again."

### 2.2 Instant Demo Switcher
In development and demo environments, `AuthContext` exposes an instant Role Switcher dropdown populated with all 13 canonical seeded demo accounts (default password `Demo@Health2026`). Switching accounts triggers seamless re-authentication and route update without requiring manual logout.

---

## 3. Dynamic Navigation & Role-Based Routing

### 3.1 Permission-Driven Navigation Contract
Navigation items are never hardcoded by role names in the frontend. Instead, the UI queries the authoritative server endpoint:
`GET /api/v1/navigation/me`
This endpoint evaluates the user's active database permissions and returns only the authorized menu items:
- Citizen users receive `/patient`, `/patient/appointments`, `/patient/records`, `/patient/assistant`.
- Medical Officers receive `/clinical/queue`, `/clinical/patients`, `/clinical/labs`.
- Nurses receive `/clinical/triage`, `/clinical/patients`, `/clinical/labs`.
- Pharmacists receive `/pharmacy/dispense`, `/pharmacy/inventory`, `/pharmacy/receipts`.
- Facility In-Charges receive `/facility`, `/facility/attendance`, `/facility/camps`.
- Governance officers receive `/district`, `/supply`, `/emergency`, `/state`, `/analytics`, `/national`, `/platform`.

### 3.2 Client Route Guards
A higher-order route guard `<ProtectedRoute>` wraps each portal:
- Verifies authentication status.
- Evaluates required permission for the target route.
- If unauthenticated -> redirects to `/login`.
- If authenticated but missing permission -> renders accessible `<StateView state="403" />` Forbidden view with explanation and "Return to Authorized Dashboard" button.

---

## 4. Centralized API Client (`services/api.ts`)

All network communication flows through a unified client `fetchWithAuth`:
- **Base URL:** Auto-detected from `VITE_API_URL` or fallback to `http://localhost:8000/api/v1`.
- **Headers:** Automatically attaches `Authorization: Bearer <token>` and `Content-Type: application/json`.
- **RFC 7807 Error Normalization:** Standardizes API errors into `{ status, title, detail, type, validationErrors }`.
- **Global Error Interception:**
  - `401`: Triggers token refresh flow.
  - `403`: Returns permission denied error.
  - `404`: Returns resource not found error.
  - `409`: Returns conflict / duplicate state error.
  - `422`: Formats field-level validation errors into interactive UI hints.
  - `500`: Returns server error with trace ID for support.
  - Network Offline: Detects lack of internet connectivity and displays offline alert.

---

## 5. UI State Machine (Every Feature)

Every interactive feature component implements the mandatory states:
1. **Loading State:** `<StateView state="loading" />` with accessible spinner, skeleton loaders, and aria-busy.
2. **Empty State:** `<StateView state="empty" />` with descriptive message and clear call-to-action button.
3. **Success State:** Non-intrusive toast notification and updated data table/card.
4. **Validation Error State:** Inline error text below input fields with red border and error icon.
5. **Forbidden (403) State:** Shield icon with clear explanation of required permission.
6. **Confirmation Modal:** High-impact actions (e.g. final diagnosis, stock write-off, incident declaration) require explicit modal confirmation before dispatching API request.

---

## 6. Unified AI Assistant Architecture

A single floating and collapsible AI drawer (`UnifiedAiAssistant.tsx`) is mounted into the master `Layout`:
- **Context Awareness:** Automatically inspects the authenticated user's role and facility scope.
- **Dynamic Endpoint Routing:**
  - `PATIENT` -> Calls `/api/v1/patient-portal/wellness-assistant/chat` (Wellness and lifestyle advice).
  - `DOCTOR` -> Calls `/api/v1/doctor-portal/clinical-assistant/advise` (Differential diagnosis and drug interaction check).
  - `NURSE` -> Calls `/api/v1/nurse-portal/triage-assistant/score` (Triage score recommendation).
  - `PHARMACIST` / `DSCO` -> Calls `/api/v1/ai/forecast` & `/api/v1/ai/risk-analysis` (Stockout risk and demand forecasting).
  - Governance roles (`DHO`, `DEC`, `STATE_ADMIN`, `STATE_SUPPLY`, `ANALYST`, `NHA`) -> Calls `/api/v1/governance/ai-assistant` with grounded rule-based summaries.
- **Language Support:** Prompts and responses support English and Tamil (`ta`).
- **Strict Guardrails:** Visual disclaimers emphasize that AI responses are decision-support only and do not replace authorized human clinical or executive sign-off.

---

## 7. Localization (English + Tamil)

- All UI text, status badges, error messages, and table headers are decoupled into `utils/i18n.ts`.
- `LanguageContext` provides `t(key)` helper and language toggle in the header.
- Switching language instantly updates all rendered components without reload.
- Status values stored in backend remain canonical English/database enums (e.g. `SCHEDULED`, `DISPENSED`, `APPROVED`), while the UI renders localized human-readable labels:
  - English: `Dispensed` | Tamil: `வழங்கப்பட்டது`
  - English: `Low Stock` | Tamil: `குறைந்த இருப்பு`
  - English: `Waiting Queue` | Tamil: `காத்திருப்பு வரிசை`

---

## 8. Mobile-First Responsive Design & Accessibility

- **Responsive Breakpoints:**
  - Mobile (`< 768px`): Collapsible hamburger menu, single-column stacked cards, bottom navigation sheet for quick actions.
  - Tablet (`768px – 1024px`): Two-column grid, compact sidebar.
  - Desktop (`> 1024px`): Full sidebar navigation, multi-column dashboard analytics, wide data tables.
- **Accessibility (WCAG 2.1 AA):**
  - High-contrast color palette with WCAG AAA compliant text contrast.
  - Status indicators never rely solely on color (paired with distinct icons and textual badges).
  - Fully keyboard navigatable (Tab, Enter, Escape for modals).
  - Semantic HTML (`<main>`, `<nav>`, `<aside>`, `<header>`, `<button>`, `<label>`).
