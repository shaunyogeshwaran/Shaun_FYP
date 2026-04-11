// AI Disclosure: Development of this component was assisted by AI tools
// for code structuring, debugging, and refactoring. The pipeline stage
// visualization design is the author's own work.
import { motion } from 'framer-motion'
import { useTheme } from '../ThemeContext'
import { fonts } from '../styles/theme'

export default function PipelineStages({ activeStage = null, loading = false }) {
  const { colors } = useTheme()

  const stages = [
    { key: 'retrieve', label: 'Retrieve', color: colors.retrieve },
    { key: 'generate', label: 'Generate', color: colors.generate },
    { key: 'verify', label: 'Verify', color: colors.verify },
    { key: 'verdict', label: 'Verdict', color: colors.verdict },
  ]

  const activeIndex = activeStage === 'complete'
    ? stages.length
    : stages.findIndex(s => s.key === activeStage)

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '16px 0 20px', gap: 0,
    }}>
      {stages.map((stage, i) => {
        const isActive = i === activeIndex
        const isComplete = i < activeIndex || activeStage === 'complete'
        const color = isComplete || isActive ? stage.color : colors.textMuted

        return (
          <div key={stage.key} style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              {/* Circle */}
              <motion.div
                animate={isActive && loading ? {
                  boxShadow: [`0 0 0px ${stage.color}00`, `0 0 24px ${stage.color}90`, `0 0 0px ${stage.color}00`],
                } : {
                  boxShadow: isComplete ? `0 0 12px ${stage.color}40` : 'none',
                }}
                transition={isActive && loading ? { duration: 1.5, repeat: Infinity } : { duration: 0.4 }}
                style={{
                  width: 40, height: 40, borderRadius: '50%',
                  border: `2px solid ${color}`,
                  background: isComplete ? `${stage.color}25` : 'transparent',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'border-color 0.4s ease, background 0.4s ease',
                }}
              >
                {isComplete ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={stage.color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  <div style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: isActive ? stage.color : colors.textMuted,
                    transition: 'background 0.4s ease',
                  }} />
                )}
              </motion.div>

              {/* Label */}
              <div style={{
                fontFamily: fonts.mono, fontSize: 10, fontWeight: 600, color,
                textTransform: 'uppercase', letterSpacing: '0.1em',
                transition: 'color 0.4s ease',
              }}>
                {stage.label}
              </div>
            </div>

            {/* Connector line */}
            {i < stages.length - 1 && (
              <div style={{
                width: 48, height: 2, margin: '0 10px', marginBottom: 20,
                background: colors.border, borderRadius: 1,
                position: 'relative', overflow: 'hidden',
              }}>
                {/* Filled portion */}
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: (i < activeIndex || activeStage === 'complete') ? '100%' : '0%' }}
                  transition={{ duration: 0.4 }}
                  style={{
                    height: '100%', borderRadius: 1,
                    background: `linear-gradient(90deg, ${stages[i].color}, ${stages[i + 1].color})`,
                  }}
                />
                {/* Shimmer when active */}
                {isActive && loading && (
                  <motion.div
                    animate={{ x: ['-100%', '200%'] }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    style={{
                      position: 'absolute', top: 0, left: 0, width: '40%', height: '100%',
                      background: `linear-gradient(90deg, transparent, ${stage.color}, transparent)`,
                    }}
                  />
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
