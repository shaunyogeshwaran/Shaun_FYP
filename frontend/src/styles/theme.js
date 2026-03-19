/**
 * AFLHR — "The Observatory" Design System
 * Dark + Light themes with glassmorphism support.
 */

export const dark = {
  // Backgrounds
  bg: '#06060b',
  bgSurface: 'rgba(12, 12, 20, 0.75)',
  bgElevated: 'rgba(18, 18, 28, 0.8)',
  bgHover: '#1a1a28',
  bgSolid: '#0c0c14',

  // Borders
  border: 'rgba(30, 30, 46, 0.6)',
  borderLight: 'rgba(42, 42, 61, 0.6)',

  // Primary — Amber/Gold
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

  // Pipeline stage accents
  retrieve: '#3b9eff',
  generate: '#a855f7',
  verify: '#f59e0b',
  verdict: '#00d47b',

  // Glass
  glass: 'rgba(12, 12, 20, 0.55)',
  glassBorder: 'rgba(255, 255, 255, 0.06)',
  blur: 'blur(20px)',
}

export const light = {
  // Backgrounds
  bg: '#f0efe8',
  bgSurface: 'rgba(255, 255, 255, 0.55)',
  bgElevated: 'rgba(255, 255, 255, 0.7)',
  bgHover: 'rgba(0, 0, 0, 0.03)',
  bgSolid: '#ffffff',

  // Borders
  border: 'rgba(0, 0, 0, 0.08)',
  borderLight: 'rgba(0, 0, 0, 0.12)',

  // Primary — Deeper Gold for contrast
  primary: '#9a7b15',
  primaryLight: '#c9a227',
  primaryDim: 'rgba(154, 123, 21, 0.1)',
  primaryGlow: 'rgba(154, 123, 21, 0.2)',

  // Verified
  verified: '#059669',
  verifiedDim: 'rgba(5, 150, 105, 0.1)',
  verifiedGlow: 'rgba(5, 150, 105, 0.25)',

  // Hallucination
  hallucination: '#dc2626',
  hallucinationDim: 'rgba(220, 38, 38, 0.08)',
  hallucinationGlow: 'rgba(220, 38, 38, 0.25)',

  // Text
  text: '#1a1a2e',
  textSecondary: '#4a4a62',
  textMuted: '#8888a0',

  // Pipeline stage accents
  retrieve: '#2563eb',
  generate: '#7c3aed',
  verify: '#d97706',
  verdict: '#059669',

  // Glass
  glass: 'rgba(255, 255, 255, 0.45)',
  glassBorder: 'rgba(0, 0, 0, 0.06)',
  blur: 'blur(20px)',
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
