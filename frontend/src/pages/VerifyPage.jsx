import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { colors, fonts } from '../styles/theme'
import CircularGauge from '../components/CircularGauge'
import PipelineStages from '../components/PipelineStages'
import ThresholdPanel from '../components/ThresholdPanel'
import VerdictStamp from '../components/VerdictStamp'
import DocumentCard from '../components/DocumentCard'

const API = ''  // proxied via vite

const SUGGESTED_QUERIES = [
  'When was the University of Westminster founded?',
  'What are AI hallucinations?',
  'What is the climate of Sri Lanka?',
]

export default function VerifyPage() {
  const [query, setQuery] = useState('')
  const [pivot, setPivot] = useState(0.75)
  const [strict, setStrict] = useState(0.95)
  const [lenient, setLenient] = useState(0.70)
  const [offline, setOffline] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [pipelineStage, setPipelineStage] = useState(null)
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const handleVerify = async () => {
    if (!query.trim() || loading) return
    setLoading(true)
    setError(null)
    setResult(null)

    // Animate pipeline stages
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
    <div style={{
      maxWidth: 1200,
      margin: '0 auto',
      padding: '24px 32px 60px',
    }}>
      {/* Query Section */}
      <div style={{ marginBottom: 20 }}>
        <div style={{
          display: 'flex',
          gap: 12,
          alignItems: 'stretch',
        }}>
          <div style={{
            flex: 1,
            position: 'relative',
          }}>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleVerify()}
              placeholder="Enter a claim to verify..."
              style={{
                width: '100%',
                padding: '16px 20px',
                paddingLeft: 48,
                borderRadius: 12,
                border: `1px solid ${loading ? colors.primary : colors.border}`,
                background: colors.bgSurface,
                color: colors.text,
                fontFamily: fonts.body,
                fontSize: 15,
                outline: 'none',
                transition: 'border-color 0.3s ease',
                boxShadow: loading ? `0 0 20px ${colors.primaryDim}` : 'none',
              }}
              onFocus={e => e.target.style.borderColor = colors.primary}
              onBlur={e => { if (!loading) e.target.style.borderColor = colors.border }}
            />
            <svg
              width="18" height="18" viewBox="0 0 24 24"
              fill="none" stroke={colors.textMuted} strokeWidth="2"
              style={{ position: 'absolute', left: 18, top: '50%', transform: 'translateY(-50%)' }}
            >
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleVerify}
            disabled={loading || !query.trim()}
            style={{
              padding: '16px 36px',
              borderRadius: 12,
              border: `1px solid ${colors.primary}`,
              background: loading
                ? colors.bgElevated
                : `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
              color: loading ? colors.textMuted : '#0a0a0a',
              fontFamily: fonts.display,
              fontWeight: 700,
              fontSize: 14,
              letterSpacing: '0.05em',
              cursor: loading ? 'wait' : (!query.trim() ? 'not-allowed' : 'pointer'),
              opacity: !query.trim() ? 0.4 : 1,
              textTransform: 'uppercase',
              transition: 'all 0.3s ease',
              whiteSpace: 'nowrap',
            }}
          >
            {loading ? 'Analyzing...' : 'Verify'}
          </motion.button>
        </div>

        {error && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              color: colors.hallucination,
              fontFamily: fonts.mono,
              fontSize: 12,
              marginTop: 10,
              padding: '8px 14px',
              background: colors.hallucinationDim,
              borderRadius: 8,
              border: `1px solid rgba(255, 51, 102, 0.2)`,
            }}
          >
            {error}
          </motion.p>
        )}
      </div>

      {/* Threshold Controls */}
      <div style={{ marginBottom: 20 }}>
        <ThresholdPanel
          pivot={pivot} setPivot={setPivot}
          strict={strict} setStrict={setStrict}
          lenient={lenient} setLenient={setLenient}
          offline={offline} setOffline={setOffline}
        />
      </div>

      {/* Pipeline Stages */}
      {(loading || result) && (
        <PipelineStages
          activeStage={pipelineStage}
          loading={loading}
        />
      )}

      {/* Results */}
      <AnimatePresence mode="wait">
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4, staggerChildren: 0.1 }}
          >
            {/* Three column results */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1.2fr 1fr',
              gap: 16,
              marginBottom: 24,
            }}>
              {/* Evidence Column */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                style={{
                  background: colors.bgSurface,
                  borderRadius: 16,
                  border: `1px solid ${colors.border}`,
                  padding: 24,
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                {/* Top accent */}
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 2,
                  background: `linear-gradient(90deg, ${colors.retrieve}, transparent)`,
                }} />

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  marginBottom: 20,
                }}>
                  <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: 8,
                    background: `${colors.retrieve}15`,
                    border: `1px solid ${colors.retrieve}30`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={colors.retrieve} strokeWidth="2">
                      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
                    </svg>
                  </div>
                  <div>
                    <h2 style={{
                      fontFamily: fonts.display,
                      fontSize: 14,
                      fontWeight: 700,
                      color: colors.retrieve,
                      letterSpacing: '-0.01em',
                    }}>
                      Evidence
                    </h2>
                    <span style={{
                      fontFamily: fonts.mono,
                      fontSize: 10,
                      color: colors.textMuted,
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                    }}>
                      RAG Retrieval
                    </span>
                  </div>
                </div>

                {/* Gauge */}
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 20 }}>
                  <CircularGauge
                    value={result.retrieval.retrieval_score}
                    color={result.retrieval.retrieval_score >= pivot ? colors.verified : colors.hallucination}
                    label="Confidence"
                    size={130}
                    delay={200}
                  />
                </div>

                {/* Mode indicator */}
                <div style={{
                  fontSize: 11,
                  fontFamily: fonts.mono,
                  padding: '8px 12px',
                  borderRadius: 8,
                  marginBottom: 16,
                  textAlign: 'center',
                  background: result.retrieval.retrieval_score >= pivot
                    ? colors.verifiedDim
                    : colors.hallucinationDim,
                  color: result.retrieval.retrieval_score >= pivot
                    ? colors.verified
                    : colors.hallucination,
                  border: `1px solid ${result.retrieval.retrieval_score >= pivot
                    ? 'rgba(0, 212, 123, 0.2)'
                    : 'rgba(255, 51, 102, 0.2)'}`,
                }}>
                  {result.retrieval.retrieval_score >= pivot ? 'LENIENT' : 'STRICT'} MODE
                  <span style={{ opacity: 0.6, marginLeft: 6 }}>
                    (score {result.retrieval.retrieval_score >= pivot ? '≥' : '<'} {pivot})
                  </span>
                </div>

                {/* Documents */}
                <div style={{ marginTop: 12 }}>
                  <div style={{
                    fontFamily: fonts.display,
                    fontSize: 10,
                    fontWeight: 700,
                    color: colors.textMuted,
                    textTransform: 'uppercase',
                    letterSpacing: '0.12em',
                    marginBottom: 8,
                  }}>
                    Retrieved Passages
                  </div>
                  {result.retrieval.documents.map((doc, i) => (
                    <DocumentCard key={i} doc={doc} index={i} delay={i + 2} />
                  ))}
                </div>
              </motion.div>

              {/* Generation Column */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                style={{
                  background: colors.bgSurface,
                  borderRadius: 16,
                  border: `1px solid ${colors.border}`,
                  padding: 24,
                  position: 'relative',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                {/* Top accent */}
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 2,
                  background: `linear-gradient(90deg, ${colors.generate}, transparent)`,
                }} />

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  marginBottom: 20,
                }}>
                  <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: 8,
                    background: `${colors.generate}15`,
                    border: `1px solid ${colors.generate}30`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={colors.generate} strokeWidth="2">
                      <path d="M12 2L2 7l10 5 10-5-10-5z" />
                      <path d="M2 17l10 5 10-5" />
                      <path d="M2 12l10 5 10-5" />
                    </svg>
                  </div>
                  <div>
                    <h2 style={{
                      fontFamily: fonts.display,
                      fontSize: 14,
                      fontWeight: 700,
                      color: colors.generate,
                      letterSpacing: '-0.01em',
                    }}>
                      Generation
                    </h2>
                    <span style={{
                      fontFamily: fonts.mono,
                      fontSize: 10,
                      color: colors.textMuted,
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                    }}>
                      LLM Response
                    </span>
                  </div>
                </div>

                {offline && (
                  <div style={{
                    fontSize: 11,
                    fontFamily: fonts.mono,
                    padding: '8px 12px',
                    borderRadius: 8,
                    marginBottom: 16,
                    background: 'rgba(245, 158, 11, 0.08)',
                    color: colors.verify,
                    border: '1px solid rgba(245, 158, 11, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}>
                    <span style={{ fontSize: 14 }}>⚡</span>
                    Offline — Mock response
                  </div>
                )}

                {/* Response text */}
                <div style={{
                  flex: 1,
                  background: colors.bgElevated,
                  borderRadius: 10,
                  padding: 18,
                  border: `1px solid ${colors.border}`,
                }}>
                  <p style={{
                    fontFamily: fonts.body,
                    fontSize: 14,
                    lineHeight: 1.8,
                    color: colors.text,
                    margin: 0,
                  }}>
                    {result.generation}
                  </p>
                </div>

                {/* Model info */}
                <div style={{
                  marginTop: 16,
                  display: 'flex',
                  gap: 16,
                  fontFamily: fonts.mono,
                  fontSize: 10,
                  color: colors.textMuted,
                }}>
                  <span>MODEL: Llama-3.1-8B</span>
                  <span>PROVIDER: Groq</span>
                  <span>TEMP: 0.1</span>
                </div>
              </motion.div>

              {/* Verification Column */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                style={{
                  background: colors.bgSurface,
                  borderRadius: 16,
                  border: `1px solid ${verdictColor}30`,
                  padding: 24,
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: `0 0 40px ${verdictColor}08`,
                }}
              >
                {/* Top accent */}
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 2,
                  background: `linear-gradient(90deg, ${colors.verify}, ${verdictColor})`,
                }} />

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  marginBottom: 20,
                }}>
                  <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: 8,
                    background: `${colors.verify}15`,
                    border: `1px solid ${colors.verify}30`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={colors.verify} strokeWidth="2">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    </svg>
                  </div>
                  <div>
                    <h2 style={{
                      fontFamily: fonts.display,
                      fontSize: 14,
                      fontWeight: 700,
                      color: colors.verify,
                      letterSpacing: '-0.01em',
                    }}>
                      Verification
                    </h2>
                    <span style={{
                      fontFamily: fonts.mono,
                      fontSize: 10,
                      color: colors.textMuted,
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                    }}>
                      NLI Analysis
                    </span>
                  </div>
                </div>

                {/* NLI Gauge */}
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
                  <CircularGauge
                    value={result.nli_score}
                    color={verdictColor}
                    label="Entailment"
                    size={130}
                    delay={400}
                  />
                </div>

                {/* Threshold bar */}
                <div style={{ marginBottom: 16 }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: 6,
                    fontFamily: fonts.mono,
                    fontSize: 10,
                    color: colors.textMuted,
                  }}>
                    <span>THRESHOLD ({result.verdict.mode})</span>
                    <span style={{ color: colors.textSecondary }}>
                      {(result.verdict.threshold * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div style={{
                    height: 6,
                    borderRadius: 3,
                    background: colors.bgElevated,
                    position: 'relative',
                    overflow: 'hidden',
                  }}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${result.verdict.threshold * 100}%` }}
                      transition={{ duration: 0.8, delay: 0.5 }}
                      style={{
                        height: '100%',
                        borderRadius: 3,
                        background: colors.textMuted,
                      }}
                    />
                    {/* Score marker */}
                    <motion.div
                      initial={{ left: 0 }}
                      animate={{ left: `${result.nli_score * 100}%` }}
                      transition={{ duration: 0.8, delay: 0.6 }}
                      style={{
                        position: 'absolute',
                        top: -3,
                        width: 3,
                        height: 12,
                        borderRadius: 2,
                        background: verdictColor,
                        transform: 'translateX(-50%)',
                        boxShadow: `0 0 8px ${verdictColor}80`,
                      }}
                    />
                  </div>
                </div>

                {/* Reasoning */}
                <div style={{
                  fontFamily: fonts.body,
                  fontSize: 12,
                  color: colors.textSecondary,
                  lineHeight: 1.6,
                  marginBottom: 20,
                  padding: '10px 14px',
                  background: colors.bgElevated,
                  borderRadius: 8,
                  border: `1px solid ${colors.border}`,
                }}>
                  {result.verdict.reasoning}
                </div>

                {/* Verdict Stamp */}
                <div style={{ textAlign: 'center' }}>
                  <VerdictStamp status={result.verdict.status} />
                </div>

                {/* Score comparison */}
                <div style={{
                  marginTop: 16,
                  fontFamily: fonts.mono,
                  fontSize: 10,
                  color: colors.textSecondary,
                  padding: '10px 14px',
                  background: colors.bgElevated,
                  borderRadius: 8,
                  textAlign: 'center',
                  border: `1px solid ${colors.border}`,
                }}>
                  NLI {(result.nli_score * 100).toFixed(1)}% {result.verdict.passed ? '≥' : '<'} Threshold {(result.verdict.threshold * 100).toFixed(1)}%
                </div>
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty State */}
      {!result && !loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          style={{
            textAlign: 'center',
            padding: '80px 0',
          }}
        >
          <div style={{
            width: 80,
            height: 80,
            borderRadius: 20,
            border: `1px solid ${colors.border}`,
            background: colors.bgSurface,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 24px',
          }}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke={colors.textMuted} strokeWidth="1.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
          </div>
          <h2 style={{
            fontFamily: fonts.display,
            fontSize: 22,
            fontWeight: 700,
            color: colors.textSecondary,
            marginBottom: 8,
          }}>
            Enter a claim to verify
          </h2>
          <p style={{
            fontFamily: fonts.body,
            fontSize: 14,
            color: colors.textMuted,
            maxWidth: 440,
            margin: '0 auto 28px',
            lineHeight: 1.6,
          }}>
            The pipeline will retrieve evidence, generate a response, and verify it using confidence-weighted NLI.
          </p>

          <div style={{
            display: 'flex',
            gap: 10,
            justifyContent: 'center',
            flexWrap: 'wrap',
          }}>
            {SUGGESTED_QUERIES.map(q => (
              <motion.button
                key={q}
                whileHover={{ scale: 1.03, borderColor: colors.primary }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setQuery(q)}
                style={{
                  padding: '10px 18px',
                  borderRadius: 10,
                  border: `1px solid ${colors.border}`,
                  background: colors.bgSurface,
                  color: colors.textSecondary,
                  fontFamily: fonts.body,
                  fontSize: 12,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
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

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
