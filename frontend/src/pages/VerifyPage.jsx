import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTheme } from '../ThemeContext'
import { fonts } from '../styles/theme'
import CircularGauge from '../components/CircularGauge'
import PipelineStages from '../components/PipelineStages'
import ThresholdPanel from '../components/ThresholdPanel'
import VerdictStamp from '../components/VerdictStamp'
import DocumentCard from '../components/DocumentCard'
import ClaimBreakdown from '../components/ClaimBreakdown'

const API = ''

const SUGGESTED_QUERIES = [
  'When was the University of Westminster founded?',
  'What are AI hallucinations?',
  'What is the climate of Sri Lanka?',
]

function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

/** Glassmorphism card wrapper */
function GlassCard({ children, style = {}, accentColor, borderColor, ...rest }) {
  const { colors } = useTheme()
  return (
    <motion.div
      {...rest}
      style={{
        background: colors.bgSurface,
        backdropFilter: colors.blur,
        WebkitBackdropFilter: colors.blur,
        borderRadius: 16,
        border: `1px solid ${borderColor || colors.glassBorder}`,
        padding: 24,
        position: 'relative',
        transition: 'background 0.4s ease, border-color 0.4s ease',
        ...style,
      }}
    >
      {accentColor && (
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: 2,
          background: `linear-gradient(90deg, ${accentColor}, transparent)`,
          borderRadius: '16px 16px 0 0',
        }} />
      )}
      {children}
    </motion.div>
  )
}

export default function VerifyPage() {
  const { colors } = useTheme()
  const [query, setQuery] = useState('')
  const [pivot, setPivot] = useState(0.75)
  const [strict, setStrict] = useState(0.95)
  const [lenient, setLenient] = useState(0.70)
  const [offline, setOffline] = useState(false)
  const [v2Mode, setV2Mode] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [pipelineStage, setPipelineStage] = useState(null)
  const inputRef = useRef(null)

  useEffect(() => { inputRef.current?.focus() }, [])

  // Pipeline stage color for the border glow
  const stageColor = pipelineStage === 'retrieve' ? colors.retrieve
    : pipelineStage === 'generate' ? colors.generate
    : pipelineStage === 'verify' ? colors.verify
    : pipelineStage === 'verdict' ? colors.verdict
    : null

  const handleVerify = async () => {
    if (!query.trim() || loading) return
    setLoading(true); setError(null); setResult(null)

    setPipelineStage('retrieve')
    await sleep(400)
    setPipelineStage('generate')
    await sleep(400)
    setPipelineStage('verify')

    try {
      const res = await fetch(`${API}/api/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          pivot,
          strict_threshold: strict,
          lenient_threshold: lenient,
          offline_mode: offline,
          v2_mode: v2Mode,
        }),
      })
      if (!res.ok) throw new Error(`API error: ${res.status}`)
      const data = await res.json()
      setPipelineStage('verdict')
      await sleep(300)
      setPipelineStage('complete')
      setResult(data)
    } catch (e) {
      setError(e.message)
      setPipelineStage(null)
    } finally {
      setLoading(false)
    }
  }

  const isVerified = result?.verdict?.status === 'VERIFIED'
  const verdictColor = isVerified ? colors.verified : colors.hallucination

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 32px 60px', position: 'relative' }}>

      {/* Query input */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'stretch', position: 'relative' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleVerify()}
              placeholder="Enter a claim to verify..."
              style={{
                width: '100%', padding: '16px 20px 16px 48px', borderRadius: 12,
                border: `1.5px solid ${stageColor || (loading ? colors.primary : colors.border)}`,
                background: colors.bgSurface,
                backdropFilter: colors.blur, WebkitBackdropFilter: colors.blur,
                color: colors.text, fontFamily: fonts.body, fontSize: 15, outline: 'none',
                transition: 'border-color 0.4s ease, box-shadow 0.4s ease',
                boxShadow: stageColor
                  ? `0 0 20px ${stageColor}30, inset 0 0 20px ${stageColor}08`
                  : 'none',
              }}
              onFocus={e => { if (!loading) e.target.style.borderColor = colors.primary }}
              onBlur={e => { if (!loading) e.target.style.borderColor = colors.border }}
            />
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
              stroke={stageColor || colors.textMuted} strokeWidth="2"
              style={{
                position: 'absolute', left: 18, top: '50%', transform: 'translateY(-50%)',
                transition: 'stroke 0.4s ease',
              }}>
              <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
            </svg>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.95 }}
            onClick={handleVerify}
            disabled={loading || !query.trim()}
            style={{
              padding: '16px 36px', borderRadius: 12, border: `1.5px solid ${colors.primary}`,
              background: loading ? colors.bgElevated : `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
              color: loading ? colors.textMuted : '#0a0a0a',
              fontFamily: fonts.display, fontWeight: 700, fontSize: 14, letterSpacing: '0.05em',
              cursor: loading ? 'wait' : (!query.trim() ? 'not-allowed' : 'pointer'),
              opacity: !query.trim() ? 0.4 : 1, textTransform: 'uppercase',
              transition: 'all 0.3s ease', whiteSpace: 'nowrap',
              position: 'relative', overflow: 'hidden',
            }}
          >
            {/* Button shimmer during loading */}
            {loading && (
              <motion.div
                animate={{ x: ['-100%', '200%'] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                style={{
                  position: 'absolute', top: 0, left: 0, width: '40%', height: '100%',
                  background: `linear-gradient(90deg, transparent, ${colors.primaryLight}40, transparent)`,
                }}
              />
            )}
            {loading ? 'Analyzing...' : 'Verify'}
          </motion.button>
        </div>
        {error && (
          <motion.p initial={{ opacity: 0, y: -5 }} animate={{ opacity: 1, y: 0 }}
            style={{
              color: colors.hallucination, fontFamily: fonts.mono, fontSize: 12, marginTop: 10,
              padding: '8px 14px', background: colors.hallucinationDim, borderRadius: 8,
              border: `1px solid ${colors.hallucinationGlow}`,
            }}
          >
            {error}
          </motion.p>
        )}
      </div>

      {/* Controls */}
      <div style={{ marginBottom: 20 }}>
        <ThresholdPanel
          pivot={pivot} setPivot={setPivot}
          strict={strict} setStrict={setStrict}
          lenient={lenient} setLenient={setLenient}
          offline={offline} setOffline={setOffline}
          v2Mode={v2Mode} setV2Mode={setV2Mode}
        />
      </div>

      {/* Pipeline stages */}
      {(loading || result) && <PipelineStages activeStage={pipelineStage} loading={loading} />}

      {/* Results */}
      <AnimatePresence mode="wait">
        {result && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.4 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.3fr 1.1fr', gap: 16, marginBottom: 24 }}>

              {/* Evidence */}
              <GlassCard initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }} accentColor={colors.retrieve}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 8,
                    background: `${colors.retrieve}15`, border: `1px solid ${colors.retrieve}30`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={colors.retrieve} strokeWidth="2">
                      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
                    </svg>
                  </div>
                  <div>
                    <h2 style={{ fontFamily: fonts.display, fontSize: 14, fontWeight: 700, color: colors.retrieve }}>Evidence</h2>
                    <span style={{ fontFamily: fonts.mono, fontSize: 10, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.08em' }}>RAG Retrieval</span>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 20 }}>
                  <CircularGauge
                    value={result.retrieval.retrieval_score}
                    color={result.retrieval.retrieval_score >= pivot ? colors.verified : colors.hallucination}
                    label="Confidence" size={130} delay={200}
                  />
                </div>

                <div style={{
                  fontSize: 11, fontFamily: fonts.mono, padding: '8px 12px', borderRadius: 8,
                  marginBottom: 16, textAlign: 'center',
                  background: result.retrieval.retrieval_score >= pivot ? colors.verifiedDim : colors.hallucinationDim,
                  color: result.retrieval.retrieval_score >= pivot ? colors.verified : colors.hallucination,
                  border: `1px solid ${result.retrieval.retrieval_score >= pivot ? colors.verifiedGlow : colors.hallucinationGlow}`,
                }}>
                  {result.retrieval.retrieval_score >= pivot ? 'LENIENT' : 'STRICT'} MODE
                  <span style={{ opacity: 0.6, marginLeft: 6 }}>(score {result.retrieval.retrieval_score >= pivot ? '>=' : '<'} {pivot})</span>
                </div>

                <div style={{ marginTop: 12 }}>
                  <div style={{ fontFamily: fonts.display, fontSize: 10, fontWeight: 700, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 8 }}>
                    Retrieved Passages
                  </div>
                  {result.retrieval.documents.map((doc, i) => <DocumentCard key={i} doc={doc} index={i} delay={i + 2} />)}
                </div>
              </GlassCard>

              {/* Generation */}
              <GlassCard initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} accentColor={colors.generate} style={{ display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 8,
                    background: `${colors.generate}15`, border: `1px solid ${colors.generate}30`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={colors.generate} strokeWidth="2">
                      <path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" />
                    </svg>
                  </div>
                  <div>
                    <h2 style={{ fontFamily: fonts.display, fontSize: 14, fontWeight: 700, color: colors.generate }}>Generation</h2>
                    <span style={{ fontFamily: fonts.mono, fontSize: 10, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.08em' }}>LLM Response</span>
                  </div>
                </div>

                {offline && (
                  <div style={{
                    fontSize: 11, fontFamily: fonts.mono, padding: '8px 12px', borderRadius: 8, marginBottom: 16,
                    background: `${colors.verify}12`, color: colors.verify, border: `1px solid ${colors.verify}25`,
                    display: 'flex', alignItems: 'center', gap: 6,
                  }}>
                    <span style={{ fontSize: 14 }}>⚡</span> Offline — Mock response
                  </div>
                )}

                <div style={{
                  flex: 1, background: colors.bgElevated, backdropFilter: colors.blur, WebkitBackdropFilter: colors.blur,
                  borderRadius: 10, padding: 18, border: `1px solid ${colors.border}`,
                }}>
                  <p style={{ fontFamily: fonts.body, fontSize: 14, lineHeight: 1.8, color: colors.text, margin: 0 }}>
                    {result.generation}
                  </p>
                </div>

                <div style={{ marginTop: 16, display: 'flex', gap: 16, fontFamily: fonts.mono, fontSize: 10, color: colors.textMuted }}>
                  <span>MODEL: Llama-3.1-8B</span><span>PROVIDER: Groq</span><span>TEMP: 0.1</span>
                </div>
              </GlassCard>

              {/* Verification */}
              <GlassCard
                initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}
                accentColor={verdictColor}
                borderColor={`${verdictColor}30`}
                style={{ boxShadow: `0 0 40px ${verdictColor}08` }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 8,
                    background: `${colors.verify}15`, border: `1px solid ${colors.verify}30`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={colors.verify} strokeWidth="2">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    </svg>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
                    <div>
                      <h2 style={{ fontFamily: fonts.display, fontSize: 14, fontWeight: 700, color: colors.verify }}>Verification</h2>
                      <span style={{ fontFamily: fonts.mono, fontSize: 10, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.08em' }}>NLI Analysis</span>
                    </div>
                    {result.version === 'v2' && (
                      <span style={{
                        marginLeft: 'auto', fontFamily: fonts.mono, fontSize: 9, padding: '2px 8px', borderRadius: 4,
                        background: `${colors.primary}18`, color: colors.primary, border: `1px solid ${colors.primary}30`,
                        letterSpacing: '0.05em',
                      }}>
                        v2
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
                  <CircularGauge value={result.nli_score} color={verdictColor} label="Entailment" size={130} delay={400} />
                </div>

                {/* Threshold bar */}
                <div style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontFamily: fonts.mono, fontSize: 10, color: colors.textMuted }}>
                    <span>THRESHOLD ({result.verdict.mode})</span>
                    <span style={{ color: colors.textSecondary }}>{(result.verdict.threshold * 100).toFixed(1)}%</span>
                  </div>
                  <div style={{ height: 6, borderRadius: 3, background: colors.bgElevated, position: 'relative', overflow: 'hidden' }}>
                    <motion.div initial={{ width: 0 }} animate={{ width: `${result.verdict.threshold * 100}%` }} transition={{ duration: 0.8, delay: 0.5 }}
                      style={{ height: '100%', borderRadius: 3, background: colors.textMuted }} />
                    <motion.div initial={{ left: 0 }} animate={{ left: `${result.nli_score * 100}%` }} transition={{ duration: 0.8, delay: 0.6 }}
                      style={{ position: 'absolute', top: -3, width: 3, height: 12, borderRadius: 2, background: verdictColor, transform: 'translateX(-50%)', boxShadow: `0 0 8px ${verdictColor}80` }} />
                  </div>
                </div>

                <div style={{
                  fontFamily: fonts.body, fontSize: 12, color: colors.textSecondary, lineHeight: 1.6,
                  marginBottom: 20, padding: '10px 14px', background: colors.bgElevated, borderRadius: 8, border: `1px solid ${colors.border}`,
                }}>
                  {result.verdict.reasoning}
                </div>

                {/* Per-claim breakdown (v2 only) */}
                {result.per_claim && result.per_claim.length > 1 && (
                  <ClaimBreakdown claims={result.per_claim} threshold={result.verdict.threshold} />
                )}

                {/* NLI method indicator */}
                {result.nli_method && result.nli_method !== 'whole' && (
                  <div style={{ marginBottom: 12, fontFamily: fonts.mono, fontSize: 10, color: colors.textMuted, textAlign: 'center' }}>
                    Method: {result.nli_method} ({result.n_claims} claim{result.n_claims !== 1 ? 's' : ''})
                  </div>
                )}

                {/* Verdict Stamp */}
                <div style={{ textAlign: 'center' }}><VerdictStamp status={result.verdict.status} /></div>

                <div style={{
                  marginTop: 16, fontFamily: fonts.mono, fontSize: 10, color: colors.textSecondary,
                  padding: '10px 14px', background: colors.bgElevated, borderRadius: 8, textAlign: 'center', border: `1px solid ${colors.border}`,
                }}>
                  NLI {(result.nli_score * 100).toFixed(1)}% {result.verdict.passed ? '>=' : '<'} Threshold {(result.verdict.threshold * 100).toFixed(1)}%
                </div>
              </GlassCard>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state */}
      {!result && !loading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          style={{ textAlign: 'center', padding: '60px 0 80px' }}
        >
          {/* Animated shield icon */}
          <motion.div
            animate={{ boxShadow: [`0 0 30px ${colors.primaryGlow}`, `0 0 60px ${colors.primaryGlow}`, `0 0 30px ${colors.primaryGlow}`] }}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            style={{
              width: 88, height: 88, borderRadius: 22,
              border: `1.5px solid ${colors.primary}40`,
              background: `linear-gradient(135deg, ${colors.primaryDim}, transparent)`,
              backdropFilter: colors.blur, WebkitBackdropFilter: colors.blur,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 28px',
            }}
          >
            <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke={colors.primary} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
          </motion.div>

          <h2 style={{
            fontFamily: fonts.display, fontSize: 24, fontWeight: 800, color: colors.text,
            marginBottom: 6, letterSpacing: '-0.02em',
          }}>
            Verify a claim
          </h2>
          <p style={{
            fontFamily: fonts.mono, fontSize: 11, color: colors.textMuted,
            letterSpacing: '0.06em', textTransform: 'uppercase',
            maxWidth: 480, margin: '0 auto 32px',
          }}>
            Retrieve evidence &rarr; Generate response &rarr; NLI verification &rarr; Adaptive verdict
          </p>

          <div style={{
            fontFamily: fonts.mono, fontSize: 10, color: colors.textMuted,
            letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 14,
          }}>
            Try a query
          </div>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
            {SUGGESTED_QUERIES.map((q, i) => (
              <motion.button
                key={q}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                whileHover={{ scale: 1.03, borderColor: colors.primary, background: colors.primaryDim }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setQuery(q)}
                style={{
                  padding: '10px 18px', borderRadius: 10,
                  border: `1px solid ${colors.border}`,
                  background: colors.bgSurface,
                  backdropFilter: colors.blur, WebkitBackdropFilter: colors.blur,
                  color: colors.textSecondary, fontFamily: fonts.body, fontSize: 12,
                  cursor: 'pointer', transition: 'all 0.2s ease',
                }}
              >
                {q}
              </motion.button>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}
