/**
 * AFLHR — "The Observatory" Design System
 * A scientific verification instrument aesthetic.
 */

export const colors = {
  // Backgrounds
  bg: '#06060b',
  bgSurface: '#0c0c14',
  bgElevated: '#12121c',
  bgHover: '#1a1a28',

  // Borders
  border: '#1e1e2e',
  borderLight: '#2a2a3d',

  // Primary — Amber/Gold (truth, branding)
  primary: '#c9a227',
  primaryLight: '#e4c44e',
  primaryDim: 'rgba(201, 162, 39, 0.15)',
  primaryGlow: 'rgba(201, 162, 39, 0.3)',

  // Verified — Jade Green
  verified: '#00d47b',
  verifiedDim: 'rgba(0, 212, 123, 0.12)',
  verifiedGlow: 'rgba(0, 212, 123, 0.4)',

  // Hallucination — Rose Red
  hallucination: '#ff3366',
  hallucinationDim: 'rgba(255, 51, 102, 0.12)',
  hallucinationGlow: 'rgba(255, 51, 102, 0.4)',

  // Text
  text: '#e8e8f0',
  textSecondary: '#9494a8',
  textMuted: '#5a5a6e',

  // Accent colors for pipeline stages
  retrieve: '#3b9eff',
  generate: '#a855f7',
  verify: '#f59e0b',
  verdict: '#00d47b',
}

export const fonts = {
  display: "'Syne', sans-serif",
  mono: "'IBM Plex Mono', monospace",
  body: "'DM Sans', sans-serif",
}

export const shadows = {
  card: '0 2px 20px rgba(0, 0, 0, 0.4)',
  glow: (color) => `0 0 30px ${color}`,
  inset: 'inset 0 1px 0 rgba(255,255,255,0.03)',
}

export const radius = {
  sm: 6,
  md: 10,
  lg: 16,
  xl: 24,
  full: '50%',
}
