/**
 * AFLHR — "The Observatory" Design System
 * Dark + Light themes with glassmorphism support.
 * Dark theme tuned for projector visibility (boosted contrast).
 */

export const dark = {
  // Backgrounds — slightly lifted for projector contrast
  bg: '#0a0a12',
  bgSurface: 'rgba(16, 16, 28, 0.85)',
  bgElevated: 'rgba(22, 22, 36, 0.9)',
  bgHover: '#1e1e30',
  bgSolid: '#0e0e18',

  // Borders — more visible on projector
  border: 'rgba(50, 50, 72, 0.7)',
  borderLight: 'rgba(65, 65, 88, 0.7)',

  // Primary — Amber/Gold (boosted)
  primary: '#dbb430',
  primaryLight: '#f0d060',
  primaryDim: 'rgba(219, 180, 48, 0.18)',
  primaryGlow: 'rgba(219, 180, 48, 0.35)',

  // Verified — Jade Green (boosted)
  verified: '#00e888',
  verifiedDim: 'rgba(0, 232, 136, 0.15)',
  verifiedGlow: 'rgba(0, 232, 136, 0.5)',

  // Hallucination — Rose Red (boosted)
  hallucination: '#ff4477',
  hallucinationDim: 'rgba(255, 68, 119, 0.15)',
  hallucinationGlow: 'rgba(255, 68, 119, 0.5)',

  // Text — brighter for projector readability
  text: '#f0f0f8',
  textSecondary: '#b0b0c4',
  textMuted: '#7a7a92',

  // Pipeline stage accents (boosted)
  retrieve: '#4dacff',
  generate: '#b870ff',
  verify: '#ffb020',
  verdict: '#00e888',

  // Glass — slightly more opaque for projector
  glass: 'rgba(14, 14, 24, 0.7)',
  glassBorder: 'rgba(255, 255, 255, 0.08)',
  blur: 'blur(20px)',
}

export const light = {
  // Backgrounds — more opaque for projector readability
  bg: '#eae9e0',
  bgSurface: 'rgba(255, 255, 255, 0.82)',
  bgElevated: 'rgba(255, 255, 255, 0.92)',
  bgHover: 'rgba(0, 0, 0, 0.05)',
  bgSolid: '#ffffff',

  // Borders — much stronger for projector
  border: 'rgba(0, 0, 0, 0.18)',
  borderLight: 'rgba(0, 0, 0, 0.22)',

  // Primary — Bold gold
  primary: '#7a6010',
  primaryLight: '#9a7b15',
  primaryDim: 'rgba(122, 96, 16, 0.12)',
  primaryGlow: 'rgba(122, 96, 16, 0.25)',

  // Verified — Darker green for contrast
  verified: '#047857',
  verifiedDim: 'rgba(4, 120, 87, 0.12)',
  verifiedGlow: 'rgba(4, 120, 87, 0.3)',

  // Hallucination — Bold red
  hallucination: '#b91c1c',
  hallucinationDim: 'rgba(185, 28, 28, 0.1)',
  hallucinationGlow: 'rgba(185, 28, 28, 0.3)',

  // Text — darker for projector
  text: '#0f0f1e',
  textSecondary: '#3a3a52',
  textMuted: '#6a6a80',

  // Pipeline stage accents — deeper for light bg
  retrieve: '#1d4ed8',
  generate: '#6d28d9',
  verify: '#b45309',
  verdict: '#047857',

  // Glass — more opaque
  glass: 'rgba(255, 255, 255, 0.72)',
  glassBorder: 'rgba(0, 0, 0, 0.12)',
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
