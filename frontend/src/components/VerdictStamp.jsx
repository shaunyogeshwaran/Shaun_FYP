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
        display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 6,
        padding: '16px 32px', borderRadius: 12,
        border: `2px solid ${color}`,
        background: isVerified ? colors.verifiedDim : colors.hallucinationDim,
        boxShadow: `0 0 40px ${glow}`,
        position: 'relative', overflow: 'hidden',
      }}
    >
      <motion.div
        animate={{ x: ['-100%', '200%'] }}
        transition={{ duration: 2, delay: 0.8, ease: 'easeInOut' }}
        style={{
          position: 'absolute', top: 0, left: 0, width: '40%', height: '100%',
          background: `linear-gradient(90deg, transparent, ${color}30, transparent)`,
          pointerEvents: 'none',
        }}
      />
      <div style={{
        fontFamily: fonts.display, fontSize: 28, fontWeight: 800, color,
        letterSpacing: '0.08em', textTransform: 'uppercase', lineHeight: 1,
      }}>
        {isVerified ? '✓' : '✗'} {status}
      </div>
      <div style={{
        fontFamily: fonts.mono, fontSize: 10, color: `${color}aa`,
        letterSpacing: '0.15em', textTransform: 'uppercase',
      }}>
        {isVerified ? 'Response is factually supported' : 'Response contains unsupported claims'}
      </div>
    </motion.div>
  )
}
