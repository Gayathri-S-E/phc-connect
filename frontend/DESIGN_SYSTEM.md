# Med2Us design system

Source of truth: `src/index.css` (tokens) and `src/components/ui/*` (components). Contrast is verified by
`node scripts/contrast-check.mjs` (fails below 4.5:1 for body text, 3:1 for large text and UI).

## Palette (mandatory, the only hues in the product)

| Name | Hex | Role |
|---|---|---|
| cool-sky | `#5aa9e6` | primary fills, info, focus accents, logo field |
| sky-blue | `#7fc8f8` | secondary / success treatment, tints |
| bright-snow | `#f9f9f9` | page background |
| royal-gold | `#ffe45e` | warning / attention |
| rose-kiss | `#ff6392` | danger / critical |
| white | `#ffffff` | surfaces (cards, inputs, popovers) |

Neutrals are shades and tints of cool-sky's hue (205 deg). There is no slate/grey/green/purple.

## Semantic tokens (Tailwind utilities: `bg-primary`, `text-foreground`, ...)

| Token | Hex | Use |
|---|---|---|
| background | `#f9f9f9` | app background |
| card / popover | `#ffffff` | surfaces |
| foreground | `#14304a` | body text (13.5:1 on white) |
| muted-foreground | `#48647c` | secondary text (6.2:1) |
| muted / neutral-soft | `#edf3f8` | table head, quiet fills |
| accent | `#eaf4fd` | hover fill |
| secondary / primary-soft | `#e3f1fc` | subtle fills |
| border | `#d5e3ee` | panel borders (decorative) |
| input | `#6f8faa` | control borders (3.4:1) |
| ring | `#2b76b5` | focus ring (4.8:1) |
| primary | `#5aa9e6` | primary button, selected fills. Text on it: `primary-foreground` `#0b1f33` (6.6:1). White fails (2.5:1). |
| primary-hover | `#4a9bd9` | |
| primary-text | `#1f5f96` | links and text/icons on light (6.7:1) |
| destructive / danger | `#ff6392` (hover `#f0457c`) | critical fill; text on it `#3d0a1e` |
| danger-text / soft / border | `#a8174a` / `#ffe8ef` / `#ffb0c8` | critical text, background, border |
| warning | `#ffe45e` | attention fill; text on it `#3a2f00` |
| warning-text / soft / border | `#6b5500` / `#fff8cf` / `#f0d43a` | |
| success | `#7fc8f8` | always with a check icon + label |
| success-text / soft / border | `#0f4f7e` / `#dcf0fd` / `#7fc8f8` | |
| info-text / soft / border | `#1f5f96` / `#eef6fd` / `#b7d8f2` | |
| ai-text / soft / border | `#1d5a8c` / `#f0f7fd` / `#a9d3f2` | AI content, always with the sparkle icon |
| neutral-text | `#334d64` | |
| chart-1..5 | cool-sky, rose-kiss, royal-gold, sky-blue, ink | |

Status is always icon + label + colour (see `StatusBadge`, `Alert`). Never colour alone.

## Type, space, shape, motion

- Fonts: Inter, Noto Sans Tamil, Noto Sans Devanagari (Hindi), JetBrains Mono.
- Scale: `text-page-title` 24/32 semibold, `text-section-title` 17/24, `text-body` 15/24 (default body), `text-small` 13/20,
  `text-caption` 12/16, `font-mono` for ids/codes. Default `text-xs/sm/base` still exist.
- Spacing: Tailwind 4px rhythm (`--spacing: 0.25rem`).
- Radius by meaning: controls (button, input, tab, badge) `rounded-md` 6px; panels (card, table, alert) `rounded-lg` 8px;
  overlays (dialog, sheet, popover) `rounded-xl` 12px. `rounded-2xl/3xl` are capped at 12px. Pills (`rounded-full`) only
  for tiny counters/avatars - never buttons or tabs.
- Shadows: `shadow-xs..2xl` are barely-there; structure comes from 1px borders.
- Motion: 150-200 ms, `cubic-bezier(0.2,0,0,1)`; `animate-fade-in`, `animate-scale-in`, `animate-slide-left`; all animation
  collapses under `prefers-reduced-motion`.
- Focus: global 2px `--ring` outline with 2px offset on every `:focus-visible`.

## shadcn/ui setup

`components.json` (new-york, css variables, `@/` aliases). Radix via the unified `radix-ui` package, `tw-animate-css` for
open/close animations. Components live in `src/components/ui/`; `cn()` is in `src/lib/utils.ts`.

Components: button, badge, status-badge, card, input, textarea, label, select, checkbox, switch, tabs (underline),
dialog (Radix, legacy composition API kept), sheet, dropdown-menu, tooltip, popover, separator, skeleton, table, alert,
scroll-area, breadcrumb, collapsible, empty-state, metric (+MetricGrid), key-value (KeyValueList), page-header (legacy props).
Brand: `components/brand/MedLogo.tsx` (`<MedLogo variant="mark|full" size={32} />`), `public/favicon.svg`.

## Legacy aliases

The default Tailwind palette is disabled. Old class names (`slate-*`, `sky-*`, `emerald-*`, `indigo-*`, `amber-*`, `rose-*`,
`red-*` ...) still resolve, but to palette-derived shades, so un-migrated screens already render in-palette. Migrate to
semantic tokens and do not add new uses. Caution: `text-slate-400/500` and `text-sky-400` on white do NOT meet AA; use
`text-muted-foreground` / `text-primary-text`.
