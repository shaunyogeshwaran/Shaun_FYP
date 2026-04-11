// AI Disclosure: Development of this component was assisted by AI tools
// for code structuring, debugging, and refactoring. The verdict display
// design is the author's own work.
import { motion } from 'framer-motion'
import { useTheme } from '../ThemeContext'
import { fonts } from '../styles/theme'

export default function VerdictStamp({ status, show = true }) {
  const { colors } = useTheme()
  const isVerified = status === 'VERIFIED'
  const color = isVerified ? colors.verified : colors.hallucination
  const glow = isVerified ? colors.verifiedGlow : colors.hallucinationGlow

  if (!show) return null

  return (
    <motion.div
      initial={{ opacity: 0, scale: 2.5, rotate: -15 }}
      animate={{ opacity: 1, scale: 1, rotate: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20, delay: 0.3 }}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
        padding: '18px 16px', borderRadius: 12,
        border: `2px solid ${color}`,
        background: isVerified ? colors.verifiedDim : colors.hallucinationDim,
        boxShadow: `0 0 40px ${glow}, inset 0 0 30px ${glow}`,
        position: 'relative',
      }}
    >
      {/* Shimmer — clipped independently */}
      <div style={{
        position: 'absolute', inset: 0, borderRadius: 12, overflow: 'hidden',
        pointerEvents: 'none',
      }}>
        <motion.div
          animate={{ x: ['-100%', '200%'] }}
          transition={{ duration: 2, delay: 0.8, ease: 'easeInOut' }}
          style={{
            position: 'absolute', top: 0, left: 0, width: '40%', height: '100%',
            background: `linear-gradient(90deg, transparent, ${color}30, transparent)`,
          }}
        />
      </div>

      {/* Icon */}
      <div style={{
        width: 32, height: 32, borderRadius: '50%',
        border: `2px solid ${color}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 16, color, fontWeight: 800,
      }}>
        {isVerified ? '✓' : '✗'}
      </div>

      {/* Status text — auto-scales */}
      <div style={{
        fontFamily: fonts.display, fontWeight: 800, color,
        letterSpacing: '0.12em', textTransform: 'uppercase', lineHeight: 1,
        textAlign: 'center', fontSize: 15,
        position: 'relative',
      }}>
        {status}
      </div>

      {/* Divider */}
      <div style={{
        width: '60%', height: 1,
        background: `linear-gradient(90deg, transparent, ${color}60, transparent)`,
      }} />

      {/* Subtitle */}
      <div style={{
        fontFamily: fonts.mono, fontSize: 9, color: `${color}bb`,
        letterSpacing: '0.1em', textTransform: 'uppercase', textAlign: 'center',
        lineHeight: 1.4, position: 'relative',
      }}>
        {isVerified ? 'Factually supported' : 'Unsupported claims'}
      </div>
    </motion.div>
  )
}
