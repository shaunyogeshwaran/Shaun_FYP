import { Link, useLocation } from 'react-router-dom'
import { colors, fonts } from '../styles/theme'

const navItems = [
  { path: '/', label: 'Verify' },
  { path: '/explore', label: 'Explore' },
  { path: '/about', label: 'How It Works' },
]

export default function Header({ health }) {
  const location = useLocation()

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 100,
      borderBottom: `1px solid ${colors.border}`,
      background: 'rgba(6, 6, 11, 0.85)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
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
            position: 'relative',
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

        {/* Health status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 14px',
          borderRadius: 20,
          border: `1px solid ${health ? 'rgba(0, 212, 123, 0.2)' : 'rgba(255, 51, 102, 0.2)'}`,
          background: health ? 'rgba(0, 212, 123, 0.06)' : 'rgba(255, 51, 102, 0.06)',
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
    </header>
  )
}
