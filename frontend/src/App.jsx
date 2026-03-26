import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './ThemeContext'
import Header from './components/Header'
import BackgroundEffects from './components/BackgroundEffects'
import VerifyPage from './pages/VerifyPage'
import ExplorePage from './pages/ExplorePage'
import AboutPage from './pages/AboutPage'
import './styles/global.css'

const API = ''

export default function App() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const check = () =>
      fetch(`${API}/api/health`)
        .then(r => r.json())
        .then(setHealth)
        .catch(() => setHealth(null))

    check()
    const interval = setInterval(check, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <ThemeProvider>
      <BackgroundEffects />
      <BrowserRouter>
        <Header health={health} />
        <Routes>
          <Route path="/" element={<VerifyPage />} />
          <Route path="/explore" element={<ExplorePage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}
