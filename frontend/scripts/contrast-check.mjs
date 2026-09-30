// WCAG 2.x contrast check for every text/background pair defined by the Med2Us design system.
// Run: node scripts/contrast-check.mjs   (exit 1 if any pair fails)
// kinds: body >= 4.5, large >= 3 (>= 18.66px bold / 24px), ui >= 3 (borders of controls, focus ring, icons)

const C = {
  white: '#ffffff', snow: '#f9f9f9', ink: '#14304a', inkDeep: '#0b1f33',
  coolSky: '#5aa9e6', coolSkyHover: '#4a9bd9', skyBlue: '#7fc8f8', gold: '#ffe45e', rose: '#ff6392', roseHover: '#f0457c',
  mutedFg: '#48647c', muted: '#edf3f8', accent: '#eaf4fd', secondary: '#e3f1fc', border: '#d5e3ee', input: '#6f8faa', ring: '#2b76b5',
  primaryText: '#1f5f96',
  successSoft: '#dcf0fd', successText: '#0f4f7e', successBorder: '#7fc8f8',
  warningSoft: '#fff8cf', warningText: '#6b5500', warningFg: '#3a2f00', warningBorder: '#f0d43a',
  dangerSoft: '#ffe8ef', dangerText: '#a8174a', dangerFg: '#3d0a1e', dangerBorder: '#ffb0c8',
  infoSoft: '#eef6fd', infoText: '#1f5f96', infoBorder: '#b7d8f2',
  aiSoft: '#f0f7fd', aiText: '#1d5a8c', aiBorder: '#a9d3f2',
  neutralSoft: '#edf3f8', neutralText: '#334d64',
};

const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
const lum = (hex) => { const n = parseInt(hex.slice(1), 16); return 0.2126 * lin(n >> 16) + 0.7152 * lin((n >> 8) & 255) + 0.0722 * lin(n & 255); };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };

// [label, foreground, background, kind]
const pairs = [
  // Base text
  ['body text on background (snow)', C.ink, C.snow, 'body'],
  ['body text on surface (white)', C.ink, C.white, 'body'],
  ['muted text on white', C.mutedFg, C.white, 'body'],
  ['muted text on snow', C.mutedFg, C.snow, 'body'],
  ['muted text on muted fill (table head)', C.mutedFg, C.muted, 'body'],
  ['text on hover/accent fill', C.ink, C.accent, 'body'],
  ['text on secondary fill', C.ink, C.secondary, 'body'],
  ['link / primary-text on white', C.primaryText, C.white, 'body'],
  ['link / primary-text on snow', C.primaryText, C.snow, 'body'],
  ['link / primary-text on primary-soft', C.primaryText, C.secondary, 'body'],
  // Buttons
  ['primary button: dark text on cool-sky', C.inkDeep, C.coolSky, 'body'],
  ['primary button hover: dark text on darker cool-sky', C.inkDeep, C.coolSkyHover, 'body'],
  ['destructive button: dark text on rose-kiss', C.dangerFg, C.rose, 'body'],
  ['destructive button hover', C.dangerFg, C.roseHover, 'body'],
  ['warning button: dark text on royal-gold', C.warningFg, C.gold, 'body'],
  ['success button: dark text on sky-blue', C.inkDeep, C.skyBlue, 'body'],
  ['(reference) white text on cool-sky - NOT USED', C.white, C.coolSky, 'info'],
  // Status badges / alerts
  ['success text on success-soft', C.successText, C.successSoft, 'body'],
  ['warning text on warning-soft', C.warningText, C.warningSoft, 'body'],
  ['danger text on danger-soft', C.dangerText, C.dangerSoft, 'body'],
  ['info text on info-soft', C.infoText, C.infoSoft, 'body'],
  ['ai text on ai-soft', C.aiText, C.aiSoft, 'body'],
  ['neutral text on neutral-soft', C.neutralText, C.neutralSoft, 'body'],
  ['danger text on white', C.dangerText, C.white, 'body'],
  ['warning text on white', C.warningText, C.white, 'body'],
  ['alert body (ink) on danger-soft', C.ink, C.dangerSoft, 'body'],
  ['alert body (ink) on warning-soft', C.ink, C.warningSoft, 'body'],
  ['alert body (ink) on success-soft', C.ink, C.successSoft, 'body'],
  // Tooltip (inverted)
  ['tooltip: snow on ink', C.snow, C.ink, 'body'],
  // UI components (>= 3:1)
  ['input border on white', C.input, C.white, 'ui'],
  ['input border on snow', C.input, C.snow, 'ui'],
  ['focus ring on white', C.ring, C.white, 'ui'],
  ['focus ring on snow', C.ring, C.snow, 'ui'],
  ['focus ring on cool-sky button', C.ring, C.coolSky, 'info'],
  ['selected tab underline (primary-text) on white', C.primaryText, C.white, 'ui'],
  ['checked checkbox border (ink) on cool-sky', C.ink, C.coolSky, 'ui'],
  ['status icon (success-text) on success-soft', C.successText, C.successSoft, 'ui'],
  // Logo
  ['logo: ink strokes on cool-sky', C.inkDeep, C.coolSky, 'ui'],
  ['logo: ink strokes on snow node', C.inkDeep, C.snow, 'ui'],
  ['logo: ink strokes on rose node', C.inkDeep, C.rose, 'ui'],
  ['logo: ink strokes on gold hub', C.inkDeep, C.gold, 'ui'],
];

const min = { body: 4.5, large: 3, ui: 3, info: 0 };
let failed = 0;
for (const [label, fg, bg, kind] of pairs) {
  const r = ratio(fg, bg);
  const ok = r >= min[kind];
  if (!ok) failed++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${r.toFixed(2).padStart(5)}:1  [${kind.padEnd(4)}]  ${label}  (${fg} on ${bg})`);
}
console.log(failed ? `\n${failed} pair(s) FAILED` : `\nAll ${pairs.filter((p) => p[3] !== 'info').length} checked pairs pass (info rows are reference only).`);
process.exit(failed ? 1 : 0);
