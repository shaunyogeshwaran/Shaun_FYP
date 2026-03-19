import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../ThemeContext'
import { fonts } from '../styles/theme'

function Slider({ label, value, onChange, min = 0, max = 1, step = 0.01, tooltip, color }) {
  const { colors } = useTheme()
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <label title={tooltip} style={{ fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary, cursor: 'help' }}>
          {label}
        </label>
        <span style={{ fontFamily: fonts.mono, fontSize: 13, fontWeight: 600, color: color || colors.primary }}>
          {value.toFixed(2)}
        </span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={e => onChange(parseFloat(e.target.value))} />
    </div>
  )
}

export default function ThresholdPanel({
  pivot, setPivot,
  strict, setStrict,
  lenient, setLenient,
  offline, setOffline,
  v2Mode = false, setV2Mode = () => {},
}) {
  const [open, setOpen] = useState(true)
  const { colors } = useTheme()

  return (
    <div style={{
      border: `1px solid ${colors.glassBorder}`,
      borderRadius: 12,
      background: colors.bgSurface,
      backdropFilter: colors.blur,
      WebkitBackdropFilter: colors.blur,
      overflow: 'hidden',
      transition: 'background 0.4s ease, border-color 0.4s ease',
    }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 20px', background: 'none', border: 'none', cursor: 'pointer', color: colors.text,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={colors.primary} strokeWidth="2" strokeLinecap="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83" />
          </svg>
          <span style={{
            fontFamily: fonts.display, fontSize: 12, fontWeight: 700,
            textTransform: 'uppercase', letterSpacing: '0.1em', color: colors.textSecondary,
          }}>
            Control Panel
          </span>
        </div>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }} style={{ color: colors.textMuted, fontSize: 12 }}>
          ▼
        </motion.span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '0 20px 20px', borderTop: `1px solid ${colors.border}`, paddingTop: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 24 }}>
                <Slider label="Pivot Point" value={pivot} onChange={setPivot} tooltip="Retrieval scores below this -> STRICT verification mode" color={colors.primary} step={0.05} />
                <Slider label="Strict Threshold" value={strict} onChange={setStrict} tooltip="Applied when retrieval confidence is LOW (below pivot)" color={colors.hallucination} step={0.01} />
                <Slider label="Lenient Threshold" value={lenient} onChange={setLenient} tooltip="Applied when retrieval confidence is HIGH (above pivot)" color={colors.verified} step={0.01} />
              </div>

              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                marginTop: 12, paddingTop: 12, borderTop: `1px solid ${colors.border}`,
              }}>
                <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
                  <label style={{
                    display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer',
                    fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary,
                  }}>
                    <input type="checkbox" checked={offline} onChange={e => setOffline(e.target.checked)} />
                    Offline Mode
                    <span style={{ color: colors.textMuted, fontSize: 11 }}>— mock LLM, real RAG + NLI</span>
                  </label>
                  <label style={{
                    display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer',
                    fontFamily: fonts.body, fontSize: 12,
                    color: v2Mode ? colors.primary : colors.textSecondary,
                    transition: 'color 0.2s',
                  }}>
                    <input type="checkbox" checked={v2Mode} onChange={e => setV2Mode(e.target.checked)} />
                    v2 Mode
                    <span style={{ color: colors.textMuted, fontSize: 11 }}>— windowed NLI + claim decomposition + BGE embeddings</span>
                  </label>
                </div>

                <div style={{ fontFamily: fonts.mono, fontSize: 10, color: colors.textMuted, display: 'flex', gap: 16 }}>
                  <span>P={pivot.toFixed(2)}</span>
                  <span>T<sub>s</sub>={strict.toFixed(2)}</span>
                  <span>T<sub>l</sub>={lenient.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
