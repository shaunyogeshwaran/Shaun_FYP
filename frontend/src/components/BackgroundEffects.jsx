// AI Disclosure: Development of this component was assisted by AI tools
// for code structuring, debugging, and refactoring. The visual effects
// design is the author's own work.
import { useMemo } from 'react'
import { useTheme } from '../ThemeContext'

/**
 * Ambient background effects — gradient orbs + floating particles.
 * Adapts to dark/light theme. Pure CSS animations for performance.
 */
export default function BackgroundEffects() {
  const { isDark } = useTheme()

  // Memoize particle positions so they don't jump on re-renders
  const particles = useMemo(() =>
    Array.from({ length: 20 }, () => ({
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      animationDelay: `${Math.random() * 8}s`,
      animationDuration: `${6 + Math.random() * 8}s`,
      width: `${1.5 + Math.random() * 2}px`,
      height: `${1.5 + Math.random() * 2}px`,
      opacityDark: 0.2 + Math.random() * 0.35,
      opacityLight: 0.15 + Math.random() * 0.2,
    })),
  [])

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 0,
      pointerEvents: 'none', overflow: 'hidden',
    }}>
      {/* Gradient orbs */}
      <div className={isDark ? 'orb orb-1' : 'orb orb-light-1'} />
      <div className={isDark ? 'orb orb-2' : 'orb orb-light-2'} />
      <div className={isDark ? 'orb orb-3' : 'orb orb-light-3'} />

      {/* Floating particles */}
      {particles.map((p, i) => (
        <div
          key={i}
          className={isDark ? 'particle' : 'particle-light'}
          style={{
            left: p.left,
            top: p.top,
            animationDelay: p.animationDelay,
            animationDuration: p.animationDuration,
            width: p.width,
            height: p.height,
            opacity: isDark ? p.opacityDark : p.opacityLight,
          }}
        />
      ))}
    </div>
  )
}
