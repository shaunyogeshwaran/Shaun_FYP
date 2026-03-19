import { useEffect, useState } from 'react'
import { colors, fonts } from '../styles/theme'

/**
 * Animated circular SVG gauge — the signature visual element.
 * Shows a score as a filled arc with a glowing endpoint.
 */
export default function CircularGauge({
  value = 0,
  size = 140,
  strokeWidth = 8,
  color = colors.primary,
  label = '',
  showValue = true,
  delay = 0,
}) {
  const [animatedValue, setAnimatedValue] = useState(0)

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedValue(value)
    }, delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (animatedValue * circumference)
  const pct = (animatedValue * 100).toFixed(1)

  return (
    <div style={{ textAlign: 'center', position: 'relative' }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{ transform: 'rotate(-90deg)', filter: `drop-shadow(0 0 8px ${color}40)` }}
      >
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={colors.border}
          strokeWidth={strokeWidth}
        />
        {/* Fill */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        />
      </svg>
      {showValue && (
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <span style={{
            fontFamily: fonts.mono,
            fontSize: size * 0.18,
            fontWeight: 600,
            color: color,
            letterSpacing: '-0.02em',
          }}>
            {pct}%
          </span>
          {label && (
            <span style={{
              fontFamily: fonts.body,
              fontSize: size * 0.085,
              color: colors.textMuted,
              marginTop: 2,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
            }}>
              {label}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
