// AI Disclosure: Development of this component was assisted by AI tools
// for code structuring, debugging, and refactoring. The document card
// design is the author's own work.
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../ThemeContext'
import { fonts } from '../styles/theme'

export default function DocumentCard({ doc, index, delay = 0 }) {
  const [open, setOpen] = useState(false)
  const { colors } = useTheme()

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.1, duration: 0.3 }}
      style={{
        border: `1px solid ${open ? colors.borderLight : colors.glassBorder}`,
        borderRadius: 10,
        background: open ? colors.bgElevated : colors.bgSurface,
        backdropFilter: colors.blur,
        WebkitBackdropFilter: colors.blur,
        marginBottom: 8,
        transition: 'all 0.2s ease',
        overflow: 'hidden',
      }}
    >
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '10px 14px', background: 'none', border: 'none', cursor: 'pointer', color: colors.textSecondary,
        }}
      >
        <span style={{ fontFamily: fonts.mono, fontSize: 11, fontWeight: 500, letterSpacing: '0.05em' }}>
          PASSAGE {index + 1}
        </span>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }} style={{ fontSize: 10, color: colors.textMuted }}>
          ▼
        </motion.span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div style={{
              padding: '0 14px 14px', fontFamily: fonts.body, fontSize: 13,
              color: colors.textSecondary, lineHeight: 1.7,
              borderTop: `1px solid ${colors.border}`, paddingTop: 12,
            }}>
              {doc}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
