import { Pause, Play } from 'lucide-react'
import { lazy, Suspense, useEffect, useMemo, useState, type ReactNode } from 'react'
import { GradeLegend } from '../components/Grade'
import { Eyebrow } from '../components/Layout'
import { Search } from '../components/Search'
import type { IndexFile } from '../lib/data'
import { num } from '../lib/format'
import { unitHref } from '../lib/router'

const YEARS = ['2019', '2020', '2021', '2022', '2023', '2024', '2025']

// MapLibre is about 1 MB, so the map is a separate chunk: the profile and methodology pages never load it.
const GradeMap = lazy(() =>
  import('../components/GradeMap')
    .then((m) => ({ default: m.GradeMap }))
    // offline or a stale deploy (chunk or its CSS missing): keep the page usable, the search still works
    .catch(() => ({ default: MapFailed })),
)

function MapFailed() {
  return <MapPlaceholder>Karta se nije učitala. Osvježi stranicu ili koristi pretragu.</MapPlaceholder>
}

function MapPlaceholder({ children }: { children: ReactNode }) {
  return (
    <div className="grid h-full w-full place-items-center rounded-2xl border border-hairline bg-surface px-6 text-center text-sm text-muted">
      {children}
    </div>
  )
}

export function Home({ index }: { index: IndexFile }) {
  const [year, setYear] = useState(String(index.zadnja_godina))
  const [playing, setPlaying] = useState(false)
  const jls = useMemo(() => index.jedinice.filter((u) => u.vrsta !== 'zupanija'), [index])

  useEffect(() => {
    if (!playing) return
    const t = setInterval(() => {
      setYear((y) => {
        const i = YEARS.indexOf(y)
        if (i === YEARS.length - 1) {
          setPlaying(false)
          return y
        }
        return YEARS[i + 1]
      })
    }, 1100)
    return () => clearInterval(t)
  }, [playing])

  const counts = useMemo(() => {
    const c: Record<number, number> = {}
    for (const u of jls) {
      const g = u.ocjena[year]
      if (g) c[g] = (c[g] ?? 0) + 1
    }
    return c
  }, [jls, year])

  const people = useMemo(() => {
    const p: Record<number, number> = {}
    for (const u of jls) {
      const g = u.ocjena[year]
      if (g) p[g] = (p[g] ?? 0) + u.stanovnici
    }
    return p
  }, [jls, year])
  const underPressure = (people[1] ?? 0) + (people[2] ?? 0)

  const examples = ['grad-zagreb', 'grad-split', 'opcina-sveta-marija', 'opcina-povljana']
    .map((s) => index.jedinice.find((u) => u.slug === s))
    .filter(Boolean)

  return (
    <main className="mx-auto grid max-w-[1440px] gap-8 px-6 pt-8 lg:grid-cols-[400px_1fr] lg:px-10">
      <div className="flex flex-col gap-7">
        <div>
          <Eyebrow>576 općina, gradova i županija · otvoreni podaci</Eyebrow>
          <h1 className="mt-3 font-serif text-[2.6rem] leading-[1.05] font-semibold tracking-tight text-balance">
            Kako stoje financije tvoje općine?
          </h1>
          <p className="mt-4 text-[1.05rem] leading-relaxed text-ink-2">
            Svaka jedinica dobiva ocjenu financijske stabilnosti od 1 do 5, izračunatu iz službenih izvještaja
            Ministarstva financija i uspoređenu sa sličnim jedinicama. Metoda i kod su otvoreni.
          </p>
          <p className="mt-3 border-l-2 border-axis pl-3 text-sm leading-relaxed text-muted">
            Ocjenjuje se financijska održivost proračuna, a ne kvaliteta upravljanja.
          </p>
        </div>

        <Search units={index.jedinice} year={year} />
        <div className="-mt-4 flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted">
          <span>Na primjer:</span>
          {examples.map((u) => (
            <a key={u!.slug} href={unitHref(u!.slug)} className="text-ink-2 underline decoration-axis underline-offset-4 hover:decoration-ink">
              {u!.naziv.replace(/^(Općina|Grad) /, '')}
            </a>
          ))}
        </div>

        <div className="rounded-2xl border border-hairline bg-card p-5">
          <div className="flex items-baseline justify-between">
            <Eyebrow>Ocjena za {year}.</Eyebrow>
            <span className="text-xs text-muted">broj jedinica</span>
          </div>
          <div className="mt-4">
            <GradeLegend counts={counts} />
          </div>
          <p className="mt-4 border-t border-hairline pt-4 text-sm leading-relaxed text-ink-2">
            U jedinicama s ocjenom 1 ili 2 živi{' '}
            <strong className="tabular font-semibold text-ink">{num(underPressure)}</strong> stanovnika.
          </p>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <Eyebrow>Godina</Eyebrow>
            <button
              type="button"
              onClick={() => {
                if (!playing && year === YEARS[YEARS.length - 1]) setYear(YEARS[0])
                setPlaying((p) => !p)
              }}
              className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-sm text-ink-2 hover:bg-hairline/60"
            >
              {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              {playing ? 'Zaustavi' : 'Pokreni 2019.–2025.'}
            </button>
          </div>
          <div className="mt-2 grid grid-cols-7 gap-1 rounded-xl bg-hairline/50 p-1" role="radiogroup" aria-label="Godina">
            {YEARS.map((y) => (
              <button
                key={y}
                type="button"
                role="radio"
                aria-checked={y === year}
                onClick={() => {
                  setPlaying(false)
                  setYear(y)
                }}
                className={`tabular rounded-lg py-1.5 text-sm transition ${y === year ? 'bg-card font-semibold shadow-sm' : 'text-ink-2 hover:text-ink'}`}
              >
                {y}
              </button>
            ))}
          </div>
        </div>

        <p className="text-xs leading-relaxed text-muted">
          Ocjena nije rang-lista: jedinice se uspoređuju sa sličnima po vrsti i veličini, a ocjena se računa iz pet
          pokazatelja (saldo, slobodni saldo, dug, servis duga, dospjele obveze). <a href="#/metodologija" className="underline underline-offset-2">Kako se računa?</a>
        </p>
      </div>

      {/* phones: shorter, so the page can still be scrolled past the map */}
      <div className="h-[60vh] min-h-[420px] lg:sticky lg:top-24 lg:h-[min(78vh,820px)] lg:min-h-[520px]">
        <Suspense fallback={<MapPlaceholder>Učitavam kartu…</MapPlaceholder>}>
          <GradeMap units={index.jedinice} year={year} />
        </Suspense>
      </div>
    </main>
  )
}
