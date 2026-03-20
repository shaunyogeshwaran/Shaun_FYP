import { useTheme } from '../ThemeContext'

/**
 * Ambient background effects — gradient orbs + floating particles.
 * Adapts to dark/light theme. Pure CSS animations for performance.
 */
export default function BackgroundEffects() {
  const { isDark } = useTheme()

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
      {Array.from({ length: 20 }, (_, i) => (
        <div
          key={i}
          className={isDark ? 'particle' : 'particle-light'}
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 8}s`,
            animationDuration: `${6 + Math.random() * 8}s`,
            width: `${1.5 + Math.random() * 2}px`,
            height: `${1.5 + Math.random() * 2}px`,
            opacity: isDark ? 0.2 + Math.random() * 0.35 : 0.15 + Math.random() * 0.2,
          }}
        />
      ))}
    </div>
  )
}
