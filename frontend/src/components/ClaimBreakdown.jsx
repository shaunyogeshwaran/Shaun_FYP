// AI Disclosure: Development of this component was assisted by AI tools
// for code structuring, debugging, and refactoring. The claim breakdown
// visualization design is the author's own work.
import { motion } from 'framer-motion'
import { useTheme } from '../ThemeContext'
import { fonts } from '../styles/theme'

export default function ClaimBreakdown({ claims, threshold }) {
  const { colors } = useTheme()

  if (!claims || claims.length === 0) return null

  const minScore = Math.min(...claims.map(c => c.score))

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{
        fontFamily: fonts.display, fontSize: 10, fontWeight: 700, color: colors.textMuted,
        textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 8,
      }}>
        Per-Claim Breakdown ({claims.length} claim{claims.length !== 1 ? 's' : ''})
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {claims.map((c, i) => {
          const isWeakest = c.score === minScore && claims.length > 1
          const passesThreshold = c.score >= (threshold || 0)
          const barColor = passesThreshold ? colors.verified : colors.hallucination

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8 + i * 0.1 }}
              style={{
                padding: '8px 12px', borderRadius: 8, background: colors.bgElevated,
                border: `1px solid ${isWeakest ? `${colors.hallucination}40` : colors.border}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ fontFamily: fonts.body, fontSize: 11, color: colors.textSecondary, flex: 1, lineHeight: 1.4, marginRight: 12 }}>
                  {c.claim}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                  {isWeakest && (
                    <span style={{
                      fontFamily: fonts.mono, fontSize: 8, padding: '2px 6px', borderRadius: 4,
                      background: colors.hallucinationDim, color: colors.hallucination,
                      border: `1px solid ${colors.hallucinationGlow}`,
                      textTransform: 'uppercase', letterSpacing: '0.05em',
                    }}>
                      weakest
                    </span>
                  )}
                  <span style={{ fontFamily: fonts.mono, fontSize: 12, fontWeight: 600, color: barColor, minWidth: 44, textAlign: 'right' }}>
                    {(c.score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div style={{ height: 3, borderRadius: 2, background: colors.border, overflow: 'hidden' }}>
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${c.score * 100}%` }}
                  transition={{ duration: 0.6, delay: 0.9 + i * 0.1 }}
                  style={{ height: '100%', borderRadius: 2, background: barColor }}
                />
              </div>
            </motion.div>
          )
        })}
      </div>

      {claims.length > 1 && (
        <div style={{ marginTop: 8, fontFamily: fonts.mono, fontSize: 10, color: colors.textMuted, textAlign: 'center' }}>
          Final score = min({claims.map(c => `${(c.score * 100).toFixed(1)}%`).join(', ')}) = {(minScore * 100).toFixed(1)}%
        </div>
      )}
    </div>
  )
}
