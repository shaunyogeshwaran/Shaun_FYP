import { useState, useEffect } from 'react'

const API = 'http://localhost:8000'

function ScoreBar({ value, label, color = '#3b82f6', showPercent = true }) {
  const pct = (value * 100).toFixed(1)
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 13, color: '#94a3b8' }}>
        <span>{label}</span>
        <span style={{ color, fontWeight: 600 }}>{showPercent ? `${pct}%` : value.toFixed(4)}</span>
      </div>
      <div style={{ height: 8, borderRadius: 4, background: '#1e293b' }}>
        <div style={{ height: '100%', borderRadius: 4, background: color, width: `${Math.min(pct, 100)}%`, transition: 'width 0.6s ease' }} />
      </div>
    </div>
  )
}

function Slider({ label, value, onChange, min = 0, max = 1, step = 0.05, tooltip }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <label style={{ fontSize: 13, color: '#cbd5e1' }} title={tooltip}>{label}</label>
        <span style={{ fontSize: 13, color: '#3b82f6', fontWeight: 600 }}>{value.toFixed(2)}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step}
        value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{ width: '100%', accentColor: '#3b82f6' }}
      />
    </div>
  )
}

function VerdictBadge({ status }) {
  const isVerified = status === 'VERIFIED'
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 8,
      padding: '10px 20px', borderRadius: 8,
      background: isVerified ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
      border: `1px solid ${isVerified ? '#22c55e' : '#ef4444'}`,
      color: isVerified ? '#22c55e' : '#ef4444',
      fontWeight: 700, fontSize: 18,
    }}>
      {isVerified ? '✓' : '✗'} {status}
    </div>
  )
}

function DocumentCard({ doc, index }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ border: '1px solid #334155', borderRadius: 8, padding: 12, marginBottom: 8, background: '#0f172a' }}>
      <div
        onClick={() => setOpen(!open)}
        style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
      >
        <span style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8' }}>Document {index + 1}</span>
        <span style={{ color: '#64748b', fontSize: 12 }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && <p style={{ fontSize: 13, color: '#cbd5e1', marginTop: 8, lineHeight: 1.6 }}>{doc}</p>}
    </div>
  )
}

export default function App() {
  const [query, setQuery] = useState('')
  const [pivot, setPivot] = useState(0.75)
  const [strict, setStrict] = useState(0.95)
  const [lenient, setLenient] = useState(0.70)
  const [offline, setOffline] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [health, setHealth] = useState(null)

  useEffect(() => {
    fetch(`${API}/api/health`).then(r => r.json()).then(setHealth).catch(() => setHealth(null))
  }, [])

  const handleVerify = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API}/api/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query, pivot, strict_threshold: strict, lenient_threshold: lenient, offline_mode: offline,
        }),
      })
      if (!res.ok) throw new Error(`API error: ${res.status}`)
      setResult(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const verdictColor = result?.verdict?.status === 'VERIFIED' ? '#22c55e' : '#ef4444'

  return (
    <div style={{ minHeight: '100vh', background: '#020617', color: '#e2e8f0', fontFamily: "'Inter', system-ui, sans-serif" }}>
      {/* Header */}
      <header style={{ borderBottom: '1px solid #1e293b', padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>🔍</div>
          <div>
            <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#f1f5f9' }}>AFLHR Lite</h1>
            <p style={{ margin: 0, fontSize: 12, color: '#64748b' }}>Confidence-Weighted Hallucination Verification</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: health ? '#22c55e' : '#ef4444' }} />
          <span style={{ fontSize: 12, color: '#64748b' }}>{health ? 'Engine Ready' : 'Connecting...'}</span>
        </div>
      </header>

      <div style={{ display: 'flex', minHeight: 'calc(100vh - 69px)' }}>
        {/* Sidebar */}
        <aside style={{ width: 280, borderRight: '1px solid #1e293b', padding: 20, flexShrink: 0 }}>
          <h3 style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: 1, color: '#64748b', marginBottom: 16, fontWeight: 600 }}>Threshold Settings</h3>
          <Slider label="Pivot Point" value={pivot} onChange={setPivot} tooltip="Retrieval scores below this → STRICT mode" />
          <Slider label="Strict Threshold" value={strict} onChange={setStrict} tooltip="Applied when retrieval confidence is LOW" />
          <Slider label="Lenient Threshold" value={lenient} onChange={setLenient} tooltip="Applied when retrieval confidence is HIGH" />

          <div style={{ marginTop: 20, padding: '12px 0', borderTop: '1px solid #1e293b' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, color: '#cbd5e1' }}>
              <input type="checkbox" checked={offline} onChange={e => setOffline(e.target.checked)} style={{ accentColor: '#3b82f6' }} />
              Offline Mode
            </label>
            <p style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>Uses mock LLM response (RAG + NLI still run)</p>
          </div>

          <div style={{ marginTop: 20, padding: '12px 0', borderTop: '1px solid #1e293b' }}>
            <h3 style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: 1, color: '#64748b', marginBottom: 12, fontWeight: 600 }}>How It Works</h3>
            <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.8 }}>
              <div style={{ marginBottom: 4 }}>1. <strong style={{ color: '#3b82f6' }}>Retrieve</strong> — find relevant evidence</div>
              <div style={{ marginBottom: 4 }}>2. <strong style={{ color: '#8b5cf6' }}>Generate</strong> — LLM creates response</div>
              <div style={{ marginBottom: 4 }}>3. <strong style={{ color: '#f59e0b' }}>Verify</strong> — NLI checks entailment</div>
              <div>4. <strong style={{ color: '#22c55e' }}>Verdict</strong> — adaptive threshold decides</div>
            </div>
          </div>

          <div style={{ marginTop: 20, padding: '12px 0', borderTop: '1px solid #1e293b' }}>
            <h3 style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: 1, color: '#64748b', marginBottom: 8, fontWeight: 600 }}>Knowledge Base</h3>
            <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.8 }}>
              <div>• University of Westminster</div>
              <div>• AI Hallucinations</div>
              <div>• Climate of Sri Lanka <span style={{ color: '#64748b' }}>(distractor)</span></div>
            </div>
          </div>
        </aside>

        {/* Main */}
        <main style={{ flex: 1, padding: 24, maxWidth: 1100 }}>
          {/* Query Input */}
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', gap: 12 }}>
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleVerify()}
                placeholder="Ask a question... e.g., When was the University of Westminster founded?"
                style={{
                  flex: 1, padding: '12px 16px', borderRadius: 8,
                  border: '1px solid #334155', background: '#0f172a',
                  color: '#e2e8f0', fontSize: 15, outline: 'none',
                }}
              />
              <button
                onClick={handleVerify}
                disabled={loading || !query.trim()}
                style={{
                  padding: '12px 28px', borderRadius: 8, border: 'none',
                  background: loading ? '#334155' : 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  color: '#fff', fontWeight: 600, fontSize: 15, cursor: loading ? 'wait' : 'pointer',
                  opacity: !query.trim() ? 0.5 : 1,
                }}
              >
                {loading ? 'Verifying...' : 'Verify'}
              </button>
            </div>
            {error && <p style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>Error: {error}</p>}
          </div>

          {/* Results */}
          {result && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
              {/* Evidence Column */}
              <div style={{ background: '#0f172a', borderRadius: 12, border: '1px solid #1e293b', padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                  <span style={{ fontSize: 20 }}>📚</span>
                  <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#3b82f6' }}>Evidence (RAG)</h2>
                </div>

                <ScoreBar
                  value={result.retrieval.retrieval_score}
                  label="Retrieval Confidence"
                  color={result.retrieval.retrieval_score >= pivot ? '#22c55e' : '#ef4444'}
                />

                <div style={{
                  fontSize: 12, padding: '6px 10px', borderRadius: 6, marginBottom: 16,
                  background: result.retrieval.retrieval_score >= pivot ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                  color: result.retrieval.retrieval_score >= pivot ? '#22c55e' : '#ef4444',
                  border: `1px solid ${result.retrieval.retrieval_score >= pivot ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`,
                }}>
                  Score {result.retrieval.retrieval_score >= pivot ? '≥' : '<'} pivot ({pivot}) → {result.retrieval.retrieval_score >= pivot ? 'LENIENT' : 'STRICT'} mode
                </div>

                <h3 style={{ fontSize: 13, color: '#64748b', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Retrieved Documents</h3>
                {result.retrieval.documents.map((doc, i) => (
                  <DocumentCard key={i} doc={doc} index={i} />
                ))}
              </div>

              {/* Generation Column */}
              <div style={{ background: '#0f172a', borderRadius: 12, border: '1px solid #1e293b', padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                  <span style={{ fontSize: 20 }}>🤖</span>
                  <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#8b5cf6' }}>Generation (LLM)</h2>
                </div>

                {offline && (
                  <div style={{ fontSize: 12, padding: '6px 10px', borderRadius: 6, marginBottom: 12, background: 'rgba(245,158,11,0.1)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.2)' }}>
                    Offline Mode — Mock response used
                  </div>
                )}

                <div style={{ background: '#1e293b', borderRadius: 8, padding: 16 }}>
                  <p style={{ fontSize: 14, lineHeight: 1.7, color: '#e2e8f0', margin: 0 }}>{result.generation}</p>
                </div>

                <div style={{ marginTop: 16, fontSize: 12, color: '#64748b' }}>
                  <div>Model: Llama-3.1-8B-Instant</div>
                  <div>Provider: Groq</div>
                </div>
              </div>

              {/* Verification Column */}
              <div style={{ background: '#0f172a', borderRadius: 12, border: '1px solid #1e293b', padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                  <span style={{ fontSize: 20 }}>🛡️</span>
                  <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#f59e0b' }}>Verification (NLI)</h2>
                </div>

                <ScoreBar
                  value={result.nli_score}
                  label="Entailment Score"
                  color="#f59e0b"
                />

                <ScoreBar
                  value={result.verdict.threshold}
                  label={`Threshold (${result.verdict.mode})`}
                  color="#64748b"
                />

                <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16, lineHeight: 1.6 }}>
                  {result.verdict.reasoning}
                </div>

                <div style={{ marginBottom: 16 }}>
                  <VerdictBadge status={result.verdict.status} />
                </div>

                <div style={{
                  fontSize: 12, color: '#94a3b8', padding: '8px 12px',
                  background: '#1e293b', borderRadius: 6, lineHeight: 1.6,
                }}>
                  NLI Score ({(result.nli_score * 100).toFixed(1)}%) {result.verdict.passed ? '≥' : '<'} Threshold ({(result.verdict.threshold * 100).toFixed(1)}%)
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!result && !loading && (
            <div style={{ textAlign: 'center', padding: '80px 0', color: '#475569' }}>
              <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.5 }}>🔍</div>
              <h2 style={{ fontSize: 20, fontWeight: 600, color: '#64748b', marginBottom: 8 }}>Enter a query to begin</h2>
              <p style={{ fontSize: 14 }}>The system will retrieve evidence, generate a response, and verify it for hallucinations.</p>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 20, flexWrap: 'wrap' }}>
                {[
                  'When was the University of Westminster founded?',
                  'What are AI hallucinations?',
                  'What is the climate of Sri Lanka?',
                ].map(q => (
                  <button
                    key={q}
                    onClick={() => { setQuery(q); }}
                    style={{
                      padding: '8px 14px', borderRadius: 6, border: '1px solid #334155',
                      background: 'transparent', color: '#94a3b8', fontSize: 12, cursor: 'pointer',
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
