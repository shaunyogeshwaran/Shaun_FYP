import { useState } from 'react'
import { motion } from 'framer-motion'
import { useTheme } from '../ThemeContext'
import { fonts } from '../styles/theme'

const API = ''

const BATCH_QUERIES = [
  { query: 'When was the University of Westminster founded?', category: 'Westminster' },
  { query: 'How many campuses does the University of Westminster have?', category: 'Westminster' },
  { query: 'What happened at the Royal Polytechnic Institution in 1896?', category: 'Westminster' },
  { query: 'What are AI hallucinations?', category: 'AI' },
  { query: 'What types of AI hallucinations exist?', category: 'AI' },
  { query: 'What is the climate of Sri Lanka?', category: 'Distractor' },
  { query: 'Who is the president of the United States?', category: 'Off-topic' },
]

export default function ExplorePage() {
  const { colors } = useTheme()
  const [results, setResults] = useState([])
  const [running, setRunning] = useState(false)
  const [currentIdx, setCurrentIdx] = useState(-1)
  const [v2Mode, setV2Mode] = useState(false)

  const runBatch = async () => {
    setRunning(true); setResults([])
    for (let i = 0; i < BATCH_QUERIES.length; i++) {
      setCurrentIdx(i)
      try {
        const res = await fetch(`${API}/api/verify`, {
<<<<<<< Updated upstream
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: BATCH_QUERIES[i].query, pivot: 0.75, strict_threshold: 0.95, lenient_threshold: 0.70, offline_mode: true }),
=======
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: BATCH_QUERIES[i].query,
            pivot: 0.75,
            strict_threshold: 0.95,
            lenient_threshold: 0.70,
            offline_mode: true,
            v2_mode: v2Mode,
          }),
>>>>>>> Stashed changes
        })
        if (!res.ok) throw new Error(`${res.status}`)
        const data = await res.json()
        setResults(prev => [...prev, { ...BATCH_QUERIES[i], result: data, error: null }])
      } catch (e) {
        setResults(prev => [...prev, { ...BATCH_QUERIES[i], result: null, error: e.message }])
      }
    }
    setCurrentIdx(-1); setRunning(false)
  }

  const verified = results.filter(r => r.result?.verdict?.status === 'VERIFIED').length
  const hallucinated = results.filter(r => r.result?.verdict?.status === 'HALLUCINATION').length
  const withResults = results.filter(r => r.result)
  const avgRetrieval = withResults.length > 0 ? withResults.reduce((s, r) => s + r.result.retrieval.retrieval_score, 0) / withResults.length : 0
  const avgNli = withResults.length > 0 ? withResults.reduce((s, r) => s + r.result.nli_score, 0) / withResults.length : 0

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 32px 60px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontFamily: fonts.display, fontSize: 28, fontWeight: 800, color: colors.text, letterSpacing: '-0.02em' }}>
            Batch <span style={{ color: colors.primary }}>Explorer</span>
          </h1>
          <p style={{ fontFamily: fonts.body, fontSize: 14, color: colors.textMuted, marginTop: 6 }}>
            Run multiple queries through the pipeline and compare results side-by-side.
          </p>
        </div>
<<<<<<< Updated upstream
        <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} onClick={runBatch} disabled={running}
          style={{
            padding: '12px 32px', borderRadius: 10, border: `1px solid ${colors.primary}`,
            background: running ? colors.bgElevated : `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
            color: running ? colors.textMuted : (colors.bg === '#06060b' ? '#0a0a0a' : '#fff'),
            fontFamily: fonts.display, fontWeight: 700, fontSize: 13, cursor: running ? 'wait' : 'pointer',
            textTransform: 'uppercase', letterSpacing: '0.05em',
          }}
        >
          {running ? `Running ${currentIdx + 1}/${BATCH_QUERIES.length}...` : 'Run All Queries'}
        </motion.button>
=======

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            cursor: 'pointer',
            fontFamily: fonts.mono,
            fontSize: 11,
            color: v2Mode ? colors.primary : colors.textMuted,
            padding: '10px 16px',
            borderRadius: 10,
            border: `1px solid ${v2Mode ? colors.primary + '40' : colors.border}`,
            background: v2Mode ? `${colors.primary}10` : colors.bgSurface,
            transition: 'all 0.2s',
          }}>
            <input
              type="checkbox"
              checked={v2Mode}
              onChange={e => setV2Mode(e.target.checked)}
            />
            v2
          </label>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={runBatch}
            disabled={running}
            style={{
              padding: '12px 32px',
              borderRadius: 10,
              border: `1px solid ${colors.primary}`,
              background: running ? colors.bgElevated : `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
              color: running ? colors.textMuted : '#0a0a0a',
              fontFamily: fonts.display,
              fontWeight: 700,
              fontSize: 13,
              cursor: running ? 'wait' : 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            {running ? `Running ${currentIdx + 1}/${BATCH_QUERIES.length}...` : 'Run All Queries'}
          </motion.button>
        </div>
>>>>>>> Stashed changes
      </div>

      {/* Stats */}
      {results.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 28 }}>
          {[
            { label: 'Total', value: results.length, color: colors.primary },
            { label: 'Verified', value: verified, color: colors.verified },
            { label: 'Hallucinated', value: hallucinated, color: colors.hallucination },
            { label: 'Avg Retrieval', value: `${(avgRetrieval * 100).toFixed(1)}%`, color: colors.retrieve },
            { label: 'Avg NLI', value: `${(avgNli * 100).toFixed(1)}%`, color: colors.verify },
          ].map(stat => (
            <div key={stat.label} style={{
              background: colors.bgSurface, backdropFilter: colors.blur, WebkitBackdropFilter: colors.blur,
              border: `1px solid ${colors.glassBorder}`, borderRadius: 12, padding: '16px 20px', textAlign: 'center',
              transition: 'background 0.4s ease',
            }}>
              <div style={{ fontFamily: fonts.mono, fontSize: 24, fontWeight: 600, color: stat.color }}>{stat.value}</div>
              <div style={{ fontFamily: fonts.display, fontSize: 10, fontWeight: 600, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: 4 }}>{stat.label}</div>
            </div>
          ))}
        </motion.div>
      )}

      {/* Table */}
      {results.length > 0 && (
        <div style={{
          background: colors.bgSurface, backdropFilter: colors.blur, WebkitBackdropFilter: colors.blur,
          border: `1px solid ${colors.glassBorder}`, borderRadius: 16, overflow: 'hidden', transition: 'background 0.4s ease',
        }}>
          <div style={{
            display: 'grid', gridTemplateColumns: '2fr 0.8fr 0.8fr 0.8fr 0.8fr',
            padding: '12px 20px', borderBottom: `1px solid ${colors.border}`, background: colors.bgElevated,
          }}>
            {['Query', 'Category', 'Retrieval', 'NLI Score', 'Verdict'].map(h => (
              <div key={h} style={{ fontFamily: fonts.display, fontSize: 10, fontWeight: 700, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.12em' }}>{h}</div>
            ))}
          </div>
          {results.map((r, i) => {
            const iv = r.result?.verdict?.status === 'VERIFIED'
            const vc = r.error ? colors.textMuted : (iv ? colors.verified : colors.hallucination)
            return (
              <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                style={{
                  display: 'grid', gridTemplateColumns: '2fr 0.8fr 0.8fr 0.8fr 0.8fr',
                  padding: '14px 20px', borderBottom: i < results.length - 1 ? `1px solid ${colors.border}` : 'none',
                  alignItems: 'center', transition: 'background 0.15s', cursor: 'default',
                }}
                onMouseEnter={e => e.currentTarget.style.background = colors.bgHover}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <div style={{ fontFamily: fonts.body, fontSize: 13, color: colors.text, paddingRight: 16 }}>{r.query}</div>
                <div><span style={{ fontFamily: fonts.mono, fontSize: 10, padding: '3px 8px', borderRadius: 4, background: colors.bgElevated, border: `1px solid ${colors.border}`, color: colors.textSecondary }}>{r.category}</span></div>
                <div style={{ fontFamily: fonts.mono, fontSize: 12, color: r.result ? colors.retrieve : colors.textMuted }}>{r.result ? `${(r.result.retrieval.retrieval_score * 100).toFixed(1)}%` : '—'}</div>
                <div style={{ fontFamily: fonts.mono, fontSize: 12, color: r.result ? colors.verify : colors.textMuted }}>{r.result ? `${(r.result.nli_score * 100).toFixed(1)}%` : '—'}</div>
                <div style={{ fontFamily: fonts.mono, fontSize: 11, fontWeight: 600, color: vc, display: 'flex', alignItems: 'center', gap: 6 }}>
                  {r.error ? 'Error' : (<><span style={{ width: 8, height: 8, borderRadius: '50%', background: vc, display: 'inline-block', boxShadow: `0 0 6px ${vc}60` }} />{r.result?.verdict?.status}</>)}
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      {/* Empty state */}
      {results.length === 0 && !running && (
        <div style={{ textAlign: 'center', padding: '80px 0' }}>
          <div style={{
            width: 80, height: 80, borderRadius: 20, border: `1px solid ${colors.border}`,
            background: colors.bgSurface, backdropFilter: colors.blur, WebkitBackdropFilter: colors.blur,
            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px',
          }}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke={colors.textMuted} strokeWidth="1.5">
              <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
            </svg>
          </div>
          <h2 style={{ fontFamily: fonts.display, fontSize: 20, fontWeight: 700, color: colors.textSecondary, marginBottom: 8 }}>Batch Verification Explorer</h2>
          <p style={{ fontFamily: fonts.body, fontSize: 14, color: colors.textMuted, maxWidth: 500, margin: '0 auto', lineHeight: 1.6 }}>
            Run {BATCH_QUERIES.length} pre-configured queries across different knowledge domains to see how the Cw-CONLI pipeline handles varying retrieval quality and topic relevance.
          </p>
        </div>
      )}

      {running && results.length < BATCH_QUERIES.length && (
        <div style={{ textAlign: 'center', padding: '20px 0', fontFamily: fonts.mono, fontSize: 12, color: colors.textMuted, animation: 'pulse 1.5s infinite' }}>
          Processing: {BATCH_QUERIES[currentIdx]?.query || '...'}
        </div>
      )}
    </div>
  )
}
