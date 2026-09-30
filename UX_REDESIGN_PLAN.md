# Med2Us UI/UX Redesign - Audit and Implementation Plan

## Phase 1-3: What exists (audit)

**Stack:** React 19, Vite, Tailwind v4 (theme tokens in `frontend/src/index.css`), react-router-dom 7. `components/ui/*` are
hand-written shadcn-style primitives (cva + clsx + tailwind-merge) with **no Radix primitives, no `components.json`, no `@/` alias**.

**Shell:** fixed 64px top header (brand, role switcher, language, sign-out) + 256px sidebar (menu from `GET /navigation/me`,
built on the backend from permissions) + content capped at `max-w-7xl` and centred + a floating AI button (bottom-right) that opens a
420x580 window over the page.

**Screens:** 13 role portals (`portals/*.tsx`, 600-1,240 lines each, 12.4k lines total) plus the landing page and 7 new screens
(capacity, stock-out warnings, redistribution, federated model, nearest facility, Google services). Shared pieces already used by
all portals: `PageHeader`, `Card*`, `Button`, `Input`, `Textarea`, `Badge`, `Alert`, `DataTable`, `StateView`.

**Information architecture (source of truth):** roles -> sections -> screens, defined by the backend navigation catalogue
(patient, clinical, facility, pharmacy, district, supply, emergency, state, analytics, national, platform, capacity, intelligence).
Terminology comes from `utils/i18n.ts` (English/Tamil/Hindi); this must be preserved.

## Phase 2: UX problems found

| # | Problem | Evidence | Root cause |
|---|---|---|---|
| 1 | **Competing navigation** | Sidebar lists `/patient/appointments`, `/patient/records`... and the portal *also* renders in-page sub-tabs (`activeTab`) for the same sections | Two systems describe one hierarchy |
| 2 | **Dead space on wide screens** | Content `max-w-7xl mx-auto` inside a full-width viewport; one column regardless of content | Layout ignores viewport, no context column |
| 3 | **Weak page context** | Header shows title + badges; no "state / what next"; role switcher in the top bar competes with page context | Context spread between header, sidebar and page |
| 4 | **AI is a floating window over content** | `UnifiedAiAssistant` fixed bottom-right, covers table rows/actions; unaware of the current page | Bolted-on overlay, not part of the layout |
| 5 | **Container nesting and pills** | 93 `Card`/`glass-card` usages; rounded-full pills for tabs, badges, statuses, buttons | One treatment used for every concept |
| 6 | **Status by colour only** in several tables | `Badge` variants without icon/label pairing | No status system |
| 7 | **Generic empty/loading states** | `StateView` centred blocks with little guidance | No "what it is / why / what next" pattern |
| 8 | **Inconsistent design tokens** | Two palettes in `index.css` (brand-* and Cool Sky/Rose Kiss), ad-hoc slate classes | Tokens not semantic |

## Phase 4: Redesign plan

**Design principles:** context-first (every screen answers where / what / state / next), calm clinical palette (no AI glow),
information-dense but scannable, shape used by meaning (tabs = underline, statuses = icon+label chips, actions = rectangular buttons).

### Architecture
```
AppShell
 ├─ SidebarNav        global destinations (from backend nav, grouped by section) - collapsible, icon rail on md
 ├─ TopBar            breadcrumb + role/scope context + language + account (NO duplicate navigation)
 ├─ SectionNav        only when a section has sub-views (replaces in-page portal tabs; URL-driven, deep-linkable)
 ├─ PageTemplate      PageHeader (breadcrumb, title, one-line purpose, state chips, primary/secondary actions)
 │                    + Content (+ optional ContextRail on >= xl) 
 └─ AiPanel           docked, context-aware side panel (xl: docked column, below: sheet); reads current route/selection
```

### Phases and ownership
| Phase | Work | Files |
|---|---|---|
| 5 | Design system: shadcn/ui foundation (Radix primitives, `components.json`, `@/` alias), semantic tokens (surface, border, text, primary, status: success/warning/danger/info, `ai`), type scale, radius/shadow/motion scales | `index.css`, `components/ui/*`, `lib/` |
| 6-7 | Shell + navigation: AppShell, SidebarNav, TopBar, SectionNav, breadcrumbs, mobile sheet nav | `components/layout/*`, `Layout.tsx` |
| 8-9 | Templates and components: PageTemplate, PageHeader v2, StatusBadge (icon+label), DataTable v2 (sticky header, sort, density, skeleton), FilterBar, EmptyState, MetricStrip, ContextRail, Stat/Key-value | `components/ui/*`, `components/common/*` |
| 10 | Every page: 13 portals and the 7 new screens move to templates; in-page tabs become URL-driven SectionNav | `portals/*`, `pages/*` |
| 11 | AI native: docked panel with page context chip, structured answers (headings, lists, sources, confirm-action card), AI marker on AI-generated content, no floating window on desktop | `components/ai/*` |
| 12-13 | Real states (loading skeleton, empty, error+retry, forbidden, stale data) and responsive behaviour per template; mobile: bottom-sheet AI, collapsible filters, card-list tables | all |
| 14 | Accessibility: focus order/visibility, landmarks, labels, contrast, reduced motion, dialog/sheet semantics | all |
| 15 | Remove obsolete CSS/classes (`glass-card`, unused palette, old Header/Navigation) | cleanup |

### Constraints (from the brief and the product)
- Function unchanged: same routes, API calls, permissions, terminology, i18n keys (extend, never rename).
- No fake data, statistics, charts or AI insights; empty states use real actions only.
- shadcn/ui only as the component base; no other UI kit.
- AI appears only where the backend supports it (Patient, Doctor, Nurse assistants; forecast explanations).

### Delivery waves
1. **Foundation (sequential):** phases 5-9 (system, shell, navigation, templates). Everything below depends on it.
2. **Pages (parallel, one agent per portal group, each owns its files):** 13 portals + new screens.
3. **AI panel + verification:** docked AI, a11y and responsive checks, build/type-check, cleanup.
Verification limits: type-check/build and scripted DOM checks only; visual review in a real browser is still needed from the user.
