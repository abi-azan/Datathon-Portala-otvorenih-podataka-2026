import { useEffect, useState } from 'react'
import { Footer, Header } from './components/Layout'
import { loadIndex, type IndexFile } from './lib/data'
import { useRoute } from './lib/router'
import { Home } from './pages/Home'
import { Methodology } from './pages/Methodology'
import { Profile } from './pages/Profile'
import { Reforma } from './pages/Reforma'
import { Simulator } from './pages/Simulator'

export default function App() {
  const route = useRoute()
  const [index, setIndex] = useState<IndexFile | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    loadIndex().then(setIndex).catch(() => setError(true))
  }, [])

  // On the home page, fetch the lazy map chunk alongside the index instead of after it.
  useEffect(() => {
    if (route.page === 'home' || route.page === 'simulator') import('./components/GradeMap').catch(() => {})
  }, [route.page])

  useEffect(() => {
    if (route.page === 'simulator') document.title = 'Simulator spajanja · Fiskalna karta'
    else if (route.page === 'reform') document.title = 'Karta reforme · Fiskalna karta'
    else if (route.page === 'methodology') document.title = 'Metodologija i podaci · Fiskalna karta'
    else if (route.page !== 'unit') document.title = 'Fiskalna karta · financije općina, gradova i županija'
  }, [route])

  return (
    <div className="flex min-h-screen flex-col">
      {/* not href="#main": the hash is the router, so the link would navigate home */}
      <button
        type="button"
        onClick={() => document.getElementById('main')?.focus()}
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded focus:bg-card focus:px-3 focus:py-2"
      >
        Preskoči na sadržaj
      </button>
      <Header current={route.page} />
      <div id="main" tabIndex={-1} className="flex-1 outline-none">
        {error && (
          <p className="mx-auto max-w-3xl px-6 py-20 text-center">
            Podaci se nisu učitali.{' '}
            <button type="button" onClick={() => window.location.reload()} className="underline">
              Pokušaj ponovno
            </button>
          </p>
        )}
        {!index && !error && <p className="mx-auto max-w-3xl px-6 py-20 text-center text-muted">Učitavam…</p>}
        {index && route.page === 'home' && <Home index={index} />}
        {index && route.page === 'unit' && <Profile key={route.slug} slug={route.slug} lastYear={index.zadnja_godina} />}
        {index && route.page === 'simulator' && <Simulator index={index} />}
        {index && route.page === 'reform' && <Reforma index={index} />}
        {route.page === 'methodology' && <Methodology />}
      </div>
      <Footer generated={index?.generirano} />
    </div>
  )
}
