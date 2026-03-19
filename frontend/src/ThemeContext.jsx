import { createContext, useContext, useState, useEffect } from 'react'
import { dark, light } from './styles/theme'

const ThemeContext = createContext()

export function ThemeProvider({ children }) {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('aflhr-theme')
    return saved ? saved === 'dark' : true
  })

  const toggle = () => setIsDark(prev => !prev)
  const colors = isDark ? dark : light

  useEffect(() => {
    localStorage.setItem('aflhr-theme', isDark ? 'dark' : 'light')
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light')
  }, [isDark])

  return (
    <ThemeContext.Provider value={{ colors, isDark, toggle }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
