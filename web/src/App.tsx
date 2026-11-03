import { useEffect, useState } from 'react'
import { Footer, Header } from './components/Layout'
import { loadIndex, type IndexFile } from './lib/data'
import { useRoute } from './lib/router'
import { Home } from './pages/Home'
import { Methodology } from './pages/Methodology'
import { Profile } from './pages/Profile'

export default function App() {
  const route = useRoute()
  const [index, setIndex] = useState<IndexFile | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    loadIndex().then(setIndex).catch(() => setError(true))
  }, [])

  useEffect(() => {
    if (route.page !== 'unit') document.title = 'Fiskalna karta · financije općina, gradova i županija'
  }, [route])

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded focus:bg-card focus:px-3 focus:py-2">
        Preskoči na sadržaj
      </a>
      <Header current={route.page} />
      <div id="main" className="flex-1">
        {error && <p className="mx-auto max-w-3xl px-6 py-20 text-center">Podaci se nisu učitali. Pokušaj ponovno.</p>}
        {!index && !error && <p className="mx-auto max-w-3xl px-6 py-20 text-center text-muted">Učitavam…</p>}
        {index && route.page === 'home' && <Home index={index} />}
        {index && route.page === 'unit' && <Profile slug={route.slug} lastYear={index.zadnja_godina} />}
        {route.page === 'methodology' && <Methodology />}
      </div>
      <Footer generated={index?.generirano} />
    </div>
  )
}
