import { motion } from 'framer-motion'
import { useTheme } from '../ThemeContext'
import { fonts } from '../styles/theme'

const fadeUp = { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } }

export default function AboutPage() {
  const { colors } = useTheme()

  const stages = [
    {
      step: '01', title: 'Retrieve Evidence', color: colors.retrieve,
      icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" /></svg>,
      desc: 'The user\'s query is encoded into a 384-dimensional vector using the all-MiniLM-L6-v2 sentence transformer. FAISS performs cosine similarity search against the indexed knowledge base, returning the top-2 most relevant passages.',
      detail: 'The retrieval confidence score (0-1) measures how semantically similar the best match is to the query. This score becomes the key input for the adaptive threshold.',
      model: 'all-MiniLM-L6-v2', output: 'Retrieval score + top-k documents',
    },
    {
      step: '02', title: 'Generate Response', color: colors.generate,
      icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5z" /><path d="M2 17l10 5 10-5" /><path d="M2 12l10 5 10-5" /></svg>,
      desc: 'The retrieved context is combined with the query and sent to Llama-3.1-8B-Instant via the Groq API. The LLM generates a grounded response using only the provided evidence.',
      detail: 'Temperature is set to 0.1 for deterministic, factual responses. An offline mode is available that returns a mock response while still running the full RAG + NLI pipeline.',
      model: 'Llama-3.1-8B-Instant (Groq)', output: 'Generated text response',
    },
    {
      step: '03', title: 'Verify via NLI', color: colors.verify,
      icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>,
      desc: 'RoBERTa-large-MNLI performs Natural Language Inference: the retrieved context is the premise, and the generated response is the hypothesis. The model outputs entailment, neutral, and contradiction probabilities.',
      detail: 'The entailment probability (softmax index 2) is extracted as the NLI score. Higher scores indicate the response is well-supported by the evidence.',
      model: 'RoBERTa-large-MNLI', output: 'Entailment score (0-1)',
    },
    {
      step: '04', title: 'Adaptive Verdict', color: colors.verdict,
      icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>,
      desc: 'Here is where Cw-CONLI differs from standard approaches. Instead of a fixed threshold, the system computes a dynamic threshold based on retrieval confidence:',
      detail: 'When retrieval is strong (above the pivot), a lenient threshold is used — the system trusts the evidence. When retrieval is weak (below the pivot), a strict threshold is applied — the system demands stronger NLI entailment before accepting the response.',
      model: 'Tiered / Sqrt / Sigmoid variants', output: 'VERIFIED or HALLUCINATION',
    },
  ]

  const variants = [
    { name: 'Tiered', formula: 'T = rs < pivot ? T_strict : T_lenient', desc: 'Binary step function. Simple and interpretable — a hard switch at the pivot point. Discontinuous but predictable.', pros: 'Easy to tune, very fast', cons: 'Discontinuity at pivot' },
    { name: 'Square Root', formula: 'T = T_s - (T_s - T_l) × √rs', desc: 'Concave curve that drops the threshold quickly for moderate retrieval scores, then flattens. Smooth and continuous.', pros: 'Smooth transition, 2 params', cons: 'Sensitive to low retrieval' },
    { name: 'Sigmoid', formula: 'T = T_l + (T_s - T_l) / (1 + e^(k(rs-p)))', desc: 'S-shaped logistic transition centered at the pivot. The steepness parameter k controls how sharp the transition is.', pros: 'Most flexible, tunable', cons: 'Larger hyperparameter space' },
  ]

  const techStack = [
    { label: 'Embeddings', value: 'all-MiniLM-L6-v2 (384-dim)', color: colors.retrieve },
    { label: 'Vector Index', value: 'FAISS IndexFlatIP (CPU)', color: colors.retrieve },
    { label: 'NLI Verifier', value: 'RoBERTa-large-MNLI', color: colors.verify },
    { label: 'LLM Generator', value: 'Llama-3.1-8B-Instant (Groq)', color: colors.generate },
    { label: 'Backend', value: 'FastAPI + Python 3.11', color: colors.textSecondary },
    { label: 'Frontend', value: 'React 18 + Vite', color: colors.textSecondary },
    { label: 'Evaluation', value: 'HaluEval (20K samples, QA + Summarization)', color: colors.primary },
    { label: 'Compute', value: 'Apple M4, 24GB RAM, CPU-only', color: colors.primary },
  ]

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '40px 32px 80px' }}>
      {/* Title */}
      <motion.div {...fadeUp} transition={{ delay: 0 }}>
        <h1 style={{ fontFamily: fonts.display, fontSize: 36, fontWeight: 800, color: colors.text, letterSpacing: '-0.03em', marginBottom: 8 }}>
          How <span style={{ color: colors.primary }}>Cw-CONLI</span> Works
        </h1>
        <p style={{ fontFamily: fonts.body, fontSize: 16, color: colors.textMuted, lineHeight: 1.7, maxWidth: 640, marginBottom: 48 }}>
          Confidence-Weighted Cross-document Natural Language Inference — an adaptive verification framework that adjusts its scrutiny based on evidence quality.
        </p>
      </motion.div>

      {/* Pipeline steps */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {stages.map((stage, i) => (
          <motion.div key={stage.step} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}
            style={{
              display: 'grid', gridTemplateColumns: '80px 1fr', gap: 24, padding: 28,
              background: colors.bgSurface, backdropFilter: colors.blur, WebkitBackdropFilter: colors.blur,
              border: `1px solid ${colors.glassBorder}`, borderRadius: 16, position: 'relative', overflow: 'hidden',
              transition: 'background 0.4s ease',
            }}>
            <div style={{ position: 'absolute', top: 0, left: 0, width: 3, height: '100%', background: stage.color }} />
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 56, height: 56, borderRadius: 14, border: `1.5px solid ${stage.color}40`, background: `${stage.color}10`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: stage.color }}>{stage.icon}</div>
              <span style={{ fontFamily: fonts.mono, fontSize: 11, fontWeight: 600, color: stage.color, opacity: 0.6 }}>{stage.step}</span>
            </div>
            <div>
              <h3 style={{ fontFamily: fonts.display, fontSize: 18, fontWeight: 700, color: stage.color, marginBottom: 10 }}>{stage.title}</h3>
              <p style={{ fontFamily: fonts.body, fontSize: 14, color: colors.textSecondary, lineHeight: 1.7, marginBottom: 10 }}>{stage.desc}</p>
              <p style={{ fontFamily: fonts.body, fontSize: 13, color: colors.textMuted, lineHeight: 1.7, marginBottom: 16 }}>{stage.detail}</p>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <span style={{ fontFamily: fonts.mono, fontSize: 10, padding: '5px 10px', borderRadius: 6, background: `${stage.color}10`, border: `1px solid ${stage.color}25`, color: stage.color }}>MODEL: {stage.model}</span>
                <span style={{ fontFamily: fonts.mono, fontSize: 10, padding: '5px 10px', borderRadius: 6, background: colors.bgElevated, border: `1px solid ${colors.border}`, color: colors.textMuted }}>OUTPUT: {stage.output}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Threshold variants */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }} style={{ marginTop: 48 }}>
        <h2 style={{ fontFamily: fonts.display, fontSize: 24, fontWeight: 800, color: colors.text, letterSpacing: '-0.02em', marginBottom: 8 }}>
          Threshold <span style={{ color: colors.primary }}>Variants</span>
        </h2>
        <p style={{ fontFamily: fonts.body, fontSize: 14, color: colors.textMuted, marginBottom: 24, lineHeight: 1.7 }}>
          Cw-CONLI implements three functions to map retrieval confidence to a verification threshold:
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {variants.map((v, i) => (
            <motion.div key={v.name} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 + i * 0.1 }}
              style={{
                background: colors.bgSurface, backdropFilter: colors.blur, WebkitBackdropFilter: colors.blur,
                border: `1px solid ${colors.glassBorder}`, borderRadius: 14, padding: 24, transition: 'background 0.4s ease',
              }}>
              <h4 style={{ fontFamily: fonts.display, fontSize: 16, fontWeight: 700, color: colors.primary, marginBottom: 6 }}>{v.name}</h4>
              <code style={{ fontFamily: fonts.mono, fontSize: 11, color: colors.verify, display: 'block', padding: '8px 12px', background: colors.bgElevated, borderRadius: 6, marginBottom: 14, border: `1px solid ${colors.border}` }}>{v.formula}</code>
              <p style={{ fontFamily: fonts.body, fontSize: 13, color: colors.textSecondary, lineHeight: 1.6, marginBottom: 14 }}>{v.desc}</p>
              <div style={{ display: 'flex', gap: 8, fontSize: 10, fontFamily: fonts.mono }}>
                <span style={{ padding: '4px 8px', borderRadius: 4, background: colors.verifiedDim, color: colors.verified, border: `1px solid ${colors.verifiedGlow}` }}>+ {v.pros}</span>
                <span style={{ padding: '4px 8px', borderRadius: 4, background: colors.hallucinationDim, color: colors.hallucination, border: `1px solid ${colors.hallucinationGlow}` }}>- {v.cons}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Tech stack */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}
        style={{
          marginTop: 48, background: colors.bgSurface, backdropFilter: colors.blur, WebkitBackdropFilter: colors.blur,
          border: `1px solid ${colors.glassBorder}`, borderRadius: 16, padding: 32, transition: 'background 0.4s ease',
        }}>
        <h2 style={{ fontFamily: fonts.display, fontSize: 20, fontWeight: 800, color: colors.text, marginBottom: 20 }}>
          Technical <span style={{ color: colors.primary }}>Stack</span>
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
          {techStack.map(item => (
            <div key={item.label} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 16px',
              borderRadius: 8, background: colors.bgElevated, border: `1px solid ${colors.border}`,
            }}>
              <span style={{ fontFamily: fonts.display, fontSize: 12, fontWeight: 600, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{item.label}</span>
              <span style={{ fontFamily: fonts.mono, fontSize: 11, color: item.color }}>{item.value}</span>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Footer */}
      <div style={{ marginTop: 48, textAlign: 'center', fontFamily: fonts.mono, fontSize: 11, color: colors.textMuted, lineHeight: 1.8 }}>
        <p>AFLHR — Confidence-Weighted CONLI for Hallucination Detection</p>
        <p>BSc Computer Science Final Year Project</p>
        <p style={{ color: colors.primary }}>Shaun Yogeshwaran · University of Westminster / IIT</p>
      </div>
    </div>
  )
}
