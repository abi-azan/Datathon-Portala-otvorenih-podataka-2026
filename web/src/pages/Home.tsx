import { Pause, Play } from 'lucide-react'
import { lazy, Suspense, useEffect, useMemo, useState, type ReactNode } from 'react'
import { GradeLegend } from '../components/Grade'
import { Eyebrow } from '../components/Layout'
import { Search } from '../components/Search'
import { UnitTable } from '../components/UnitTable'
import type { IndexFile } from '../lib/data'
import { num } from '../lib/format'
import { unitHref } from '../lib/router'
import { CONTEXT_VIEWS, SEQUENTIAL, classOf, contextView, quintiles, type ViewKey } from '../lib/views'

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
  const [view, setView] = useState<ViewKey>('ocjena')
  const [mode, setMode] = useState<'karta' | 'tablica'>('karta')
  const ctx = contextView(view)
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

  // legend of a context view: the five quintile classes with their ranges and unit counts
  const classes = useMemo(() => {
    if (!ctx) return []
    const cuts = quintiles(jls, ctx, year)
    const vals = jls.map((u) => ctx.value(u, year))
    const finite = vals.filter((v): v is number => v != null && Number.isFinite(v))
    if (!finite.length) return []                  // no values for this year: no classes, no legend rows
    const lo = Math.min(...finite)
    const hi = Math.max(...finite)
    const edges = [lo, ...cuts, hi]
    return SEQUENTIAL.map((color, i) => ({
      color,
      from: edges[i],
      to: edges[i + 1],
      n: vals.filter((v) => classOf(v, cuts) === i + 1).length,
    }))
  }, [ctx, jls, year])

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
            Svaka općina, svaki grad i svaka županija dobivaju ocjenu financijske održivosti proračuna od 1 do 5,
            izračunatu iz službenih izvještaja Ministarstva financija i uspoređenu sa sličnim jedinicama. Metoda i kod su otvoreni.
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

        <div>
          <Eyebrow>Prikaz na karti</Eyebrow>
          <div className="mt-2 grid grid-cols-3 gap-1 rounded-xl bg-hairline/50 p-1" role="radiogroup" aria-label="Prikaz na karti">
            {[{ key: 'ocjena' as ViewKey, short: 'Ocjena' }, ...CONTEXT_VIEWS].map((v) => (
              <button
                key={v.key}
                type="button"
                role="radio"
                aria-checked={v.key === view}
                onClick={() => setView(v.key)}
                className={`rounded-lg px-2 py-1.5 text-sm transition ${v.key === view ? 'bg-card font-semibold shadow-sm' : 'text-ink-2 hover:text-ink'}`}
              >
                {v.short}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-hairline bg-card p-5">
          <div className="flex items-baseline justify-between gap-3">
            <Eyebrow>{ctx ? `${ctx.label}, ${year}.` : `Ocjena za ${year}.`}</Eyebrow>
            <span className="shrink-0 text-xs text-muted">broj jedinica</span>
          </div>
          {!ctx ? (
            <>
              <div className="mt-4">
                <GradeLegend counts={counts} />
              </div>
              <p className="mt-4 border-t border-hairline pt-4 text-sm leading-relaxed text-ink-2">
                U jedinicama s ocjenom 1 ili 2 živi{' '}
                <strong className="tabular font-semibold text-ink">{num(underPressure)}</strong> stanovnika.
              </p>
            </>
          ) : (
            <>
              <ul className="mt-4 space-y-1.5" aria-label={`Legenda: ${ctx.label}`}>
                {classes.map((c, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm">
                    <span className="h-4 w-7 shrink-0 rounded" style={{ background: c.color }} aria-hidden />
                    <span className="tabular flex-1 text-ink-2">
                      {ctx.range(c.from, c.to)}
                    </span>
                    <span className="tabular text-muted">{c.n}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-4 border-t border-hairline pt-4 text-sm leading-relaxed text-ink-2">
                Ovi pokazatelji služe za usporedbu i ne ulaze u ocjenu. Jedinice su podijeljene u pet razreda prema
                vrijednosti pokazatelja u {year}. godini. Tamnija boja znači veću vrijednost, ne nužno bolji rezultat.
              </p>
            </>
          )}
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

      <div className="flex min-w-0 flex-col gap-3 lg:sticky lg:top-24 lg:self-start">
        <div className="flex justify-end">
          <div className="grid grid-cols-2 gap-1 rounded-xl bg-hairline/50 p-1" role="radiogroup" aria-label="Karta ili tablica">
            {(['karta', 'tablica'] as const).map((m) => (
              <button
                key={m}
                type="button"
                role="radio"
                aria-checked={m === mode}
                onClick={() => setMode(m)}
                className={`rounded-lg px-3 py-1 text-sm transition ${m === mode ? 'bg-card font-semibold shadow-sm' : 'text-ink-2 hover:text-ink'}`}
              >
                {m === 'karta' ? 'Karta' : 'Tablica'}
              </button>
            ))}
          </div>
        </div>
        {/* phones: shorter, so the page can still be scrolled past the map */}
        <div className="h-[60vh] min-h-[420px] lg:h-[min(74vh,780px)] lg:min-h-[500px]">
          {mode === 'karta' ? (
            <Suspense fallback={<MapPlaceholder>Učitavam kartu…</MapPlaceholder>}>
              <GradeMap units={index.jedinice} year={year} colorBy={view} />
            </Suspense>
          ) : (
            <UnitTable units={index.jedinice} year={year} ctx={ctx} />
          )}
        </div>
      </div>
    </main>
  )
}
