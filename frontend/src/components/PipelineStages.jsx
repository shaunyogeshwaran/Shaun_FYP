import { motion } from 'framer-motion'
import { colors, fonts } from '../styles/theme'

const stages = [
  { key: 'retrieve', label: 'Retrieve', icon: '◈', color: colors.retrieve, desc: 'Finding evidence' },
  { key: 'generate', label: 'Generate', icon: '◉', color: colors.generate, desc: 'LLM response' },
  { key: 'verify', label: 'Verify', icon: '◎', color: colors.verify, desc: 'NLI check' },
  { key: 'verdict', label: 'Verdict', icon: '◆', color: colors.verdict, desc: 'Final decision' },
]

/**
 * Horizontal pipeline stage indicator with animated progress.
 * activeStage: null | 'retrieve' | 'generate' | 'verify' | 'verdict' | 'complete'
 */
export default function PipelineStages({ activeStage = null, loading = false }) {
  const activeIndex = activeStage === 'complete'
    ? stages.length
    : stages.findIndex(s => s.key === activeStage)

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 0,
      padding: '20px 0',
    }}>
      {stages.map((stage, i) => {
        const isActive = i === activeIndex
        const isComplete = i < activeIndex || activeStage === 'complete'
        const color = isComplete || isActive ? stage.color : colors.textMuted

        return (
          <div key={stage.key} style={{ display: 'flex', alignItems: 'center' }}>
            {/* Stage node */}
            <motion.div
              animate={isActive && loading ? {
                boxShadow: [
                  `0 0 0px ${stage.color}00`,
                  `0 0 20px ${stage.color}80`,
                  `0 0 0px ${stage.color}00`,
                ],
              } : {}}
              transition={{ duration: 1.5, repeat: Infinity }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
                position: 'relative',
              }}
            >
              <div style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                border: `2px solid ${color}`,
                background: isComplete ? `${stage.color}20` : isActive ? `${stage.color}10` : 'transparent',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 18,
                color: color,
                transition: 'all 0.4s ease',
                fontFamily: fonts.mono,
              }}>
                {isComplete ? '✓' : stage.icon}
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{
                  fontFamily: fonts.display,
                  fontSize: 11,
                  fontWeight: 700,
                  color: color,
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  transition: 'color 0.4s ease',
                }}>
                  {stage.label}
                </div>
              </div>
            </motion.div>

            {/* Connector line */}
            {i < stages.length - 1 && (
              <div style={{
                width: 60,
                height: 2,
                margin: '0 8px',
                marginBottom: 24,
                background: i < activeIndex || activeStage === 'complete'
                  ? `linear-gradient(90deg, ${stages[i].color}, ${stages[i + 1].color})`
                  : colors.border,
                borderRadius: 1,
                transition: 'background 0.4s ease',
                position: 'relative',
                overflow: 'hidden',
              }}>
                {isActive && loading && (
                  <motion.div
                    animate={{ x: ['-100%', '200%'] }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '40%',
                      height: '100%',
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
