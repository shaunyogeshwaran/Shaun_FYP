import { Link, useLocation } from 'react-router-dom'
import { useTheme } from '../ThemeContext'
import { fonts } from '../styles/theme'

const navItems = [
  { path: '/', label: 'Verify' },
  { path: '/explore', label: 'Explore' },
  { path: '/about', label: 'How It Works' },
]

export default function Header({ health }) {
  const location = useLocation()
  const { colors, isDark, toggle } = useTheme()

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      borderBottom: `1px solid ${colors.border}`,
      background: colors.glass,
      backdropFilter: colors.blur,
      WebkitBackdropFilter: colors.blur,
      transition: 'background 0.4s ease, border-color 0.4s ease',
    }}>
      {/* Gold accent line */}
      <div style={{
        height: 2,
        background: `linear-gradient(90deg, transparent, ${colors.primary}, transparent)`,
      }} />

      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 32px',
        maxWidth: 1400,
        margin: '0 auto',
        width: '100%',
      }}>
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 14, textDecoration: 'none' }}>
          <div style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            border: `1.5px solid ${colors.primary}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: colors.primaryDim,
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={colors.primary} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
          </div>
          <div>
            <h1 style={{
              fontFamily: fonts.display,
              fontSize: 18,
              fontWeight: 800,
              color: colors.text,
              letterSpacing: '-0.02em',
              lineHeight: 1,
            }}>
              AFLHR
            </h1>
            <p style={{
              fontFamily: fonts.mono,
              fontSize: 10,
              color: colors.textMuted,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              marginTop: 2,
            }}>
              Cw-CONLI Verification
            </p>
          </div>
        </Link>

        {/* Navigation */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          {navItems.map(item => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  fontFamily: fonts.body,
                  fontSize: 13,
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? colors.primary : colors.textSecondary,
                  padding: '8px 16px',
                  borderRadius: 8,
                  background: isActive ? colors.primaryDim : 'transparent',
                  transition: 'all 0.2s ease',
                  textDecoration: 'none',
                }}
              >
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* Right side: toggle + health */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* Theme toggle */}
          <button
            onClick={toggle}
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              border: `1px solid ${colors.border}`,
              background: colors.bgSurface,
              backdropFilter: colors.blur,
              WebkitBackdropFilter: colors.blur,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: colors.primary,
              fontSize: 16,
              transition: 'all 0.3s ease',
            }}
          >
            {isDark ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>

          {/* Health status */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '6px 14px',
            borderRadius: 20,
            border: `1px solid ${health ? 'rgba(0, 212, 123, 0.2)' : 'rgba(255, 51, 102, 0.2)'}`,
            background: health
              ? (isDark ? 'rgba(0, 212, 123, 0.06)' : 'rgba(5, 150, 105, 0.06)')
              : (isDark ? 'rgba(255, 51, 102, 0.06)' : 'rgba(220, 38, 38, 0.06)'),
          }}>
            <div style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: health ? colors.verified : colors.hallucination,
              boxShadow: `0 0 8px ${health ? colors.verifiedGlow : colors.hallucinationGlow}`,
              animation: health ? 'none' : 'pulse 2s infinite',
            }} />
            <span style={{
              fontFamily: fonts.mono,
              fontSize: 11,
              color: health ? colors.verified : colors.hallucination,
            }}>
              {health ? 'Engine Ready' : 'Connecting'}
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}
