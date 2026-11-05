import { ArrowRight, Pause, Play } from 'lucide-react'
import { lazy, Suspense, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Eyebrow } from '../components/Layout'
import { Search } from '../components/Search'
import { UnitTable } from '../components/UnitTable'
import { loadDatasets, loadReform, type IndexFile } from '../lib/data'
import { num } from '../lib/format'
import { simulatorHref, unitHref } from '../lib/router'
import { CONTEXT_VIEWS, contextView, type ViewKey } from '../lib/views'

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
    }, 1300) // the map cross-fades in 650 ms (GradeMap), then each year holds as long again
    return () => clearInterval(t)
  }, [playing])

  const examples = ['grad-zagreb', 'grad-split', 'opcina-sveta-marija']
    .map((s) => index.jedinice.find((u) => u.slug === s))
    .filter(Boolean)
  const years = useMemo(
    () => [...new Set(index.jedinice.flatMap((u) => Object.keys(u.ocjena).filter((y) => u.ocjena[y] != null)))].sort(),
    [index],
  )

  const yearControls = (
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
      <div className="mt-2 grid grid-cols-7 gap-0.5 rounded-xl bg-hairline/50 p-1 sm:gap-1" role="radiogroup" aria-label="Godina">
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
            className={`tabular rounded-lg py-1.5 text-[13px] transition sm:text-sm ${y === year ? 'bg-card font-semibold shadow-sm' : 'text-ink-2 hover:text-ink'}`}
          >
            {y}
          </button>
        ))}
      </div>
    </div>
  )

  // Below lg the page is one column: intro, search, map, the examples, the view and the years (the
  // legend is on the map). From lg the left column holds everything but the map, in the same order.
  return (
    <main className="mx-auto flex max-w-[1440px] flex-col gap-7 px-6 pt-8 lg:grid lg:grid-cols-[400px_1fr] lg:gap-8 lg:px-10">
      <div className="contents lg:flex lg:flex-col lg:gap-7">
        <div className="order-1">
          <Eyebrow>Otvoreni podaci · otvoreni kod</Eyebrow>
          <h1 className="mt-3 font-serif text-[2.9rem] leading-[1.05] font-semibold tracking-tight">Fiskalna karta</h1>
          <p className="mt-2 font-serif text-[1.35rem] leading-snug text-balance text-ink">
            Financijska održivost proračuna svih {num(index.jedinice.length)} općina, gradova i županija
            {years.length > 0 && `, ${years[0]}.–${years[years.length - 1]}.`}
          </p>
          <p className="mt-4 text-[1.05rem] leading-relaxed text-ink-2">
            Svaka jedinica dobiva ocjenu od 1 do 5. Ocjena se računa iz službenih izvještaja Ministarstva financija, a uz
            nju se prikazuje i usporedba sa sličnim jedinicama.
          </p>
          <p className="mt-3 border-l-2 border-axis pl-3 text-sm leading-relaxed text-muted">
            Ocjenjuje se financijska održivost proračuna, a ne kvaliteta upravljanja.
          </p>
        </div>

        <div className="order-2 flex flex-col gap-3">
          <Search units={index.jedinice} year={year} />
          <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted">
            <span>Na primjer:</span>
            {examples.map((u) => (
              <a key={u!.slug} href={unitHref(u!.slug)} className="text-ink-2 underline decoration-axis underline-offset-4 hover:decoration-ink">
                {u!.naziv.replace(/^(Općina|Grad) /, '')}
              </a>
            ))}
          </div>
        </div>

        <Stories index={index} className="order-4" />

        <div className="order-5">
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

        <div className="order-6 flex flex-col gap-4 rounded-2xl border border-hairline bg-card p-5">
          {yearControls}
          {ctx && (
            <p className="border-t border-hairline pt-4 text-sm leading-relaxed text-ink-2">
              Ovaj pokazatelj ne ulazi u ocjenu, nego služi za usporedbu. Jedinice su podijeljene u pet jednako brojnih
              razreda prema vrijednosti u {year}. godini. Tamnija boja znači veću vrijednost, ne nužno bolji rezultat.
            </p>
          )}
        </div>

        <p className="order-7 text-xs leading-relaxed text-muted">
          Ocjena nije rang-lista: računa se iz pet pokazatelja prema stalnim pragovima (operativni saldo, slobodni saldo,
          godine otplate duga, servis duga, dospjele obveze). Mjesto među sličnim jedinicama prikazuje se odvojeno.{' '}
          <a href="#/metodologija" className="underline underline-offset-2">Kako se računa?</a>
        </p>
      </div>

      <div className="order-3 flex min-w-0 flex-col gap-3 lg:sticky lg:top-24 lg:col-start-2 lg:row-start-1 lg:self-start">
        <div className="flex items-center justify-end gap-4 lg:justify-between">
          <KeyFigures index={index} className="hidden lg:flex" />
          <div className="grid shrink-0 grid-cols-2 gap-1 rounded-xl bg-hairline/50 p-1" role="radiogroup" aria-label="Karta ili tablica">
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
        {/* phones: under the map, which comes right after the search */}
        <KeyFigures index={index} className="flex lg:hidden" />
      </div>
    </main>
  )
}

/** A strip of figures computed from the API files, never typed in: units, years, people in units
 *  under pressure in the latest year, and the sources the build reads through an API.
 *  `className` carries the display (flex) for the breakpoints where it shows. */
function KeyFigures({ index, className = '' }: { index: IndexFile; className?: string }) {
  const [apis, setApis] = useState<number | null>(null)
  useEffect(() => {
    loadDatasets()
      .then((s) => setApis(s.filter((d) => d.koristi_se && d.pristup.startsWith('API')).length))
      .catch(() => setApis(null))
  }, [])
  const f = useMemo(() => {
    const last = String(index.zadnja_godina)
    const years = [...new Set(index.jedinice.flatMap((u) => Object.keys(u.ocjena).filter((y) => u.ocjena[y] != null)))].sort()
    // municipalities and towns only: a county's people also live in its municipalities
    const pressed = index.jedinice
      .filter((u) => u.vrsta !== 'zupanija' && (u.ocjena[last] === 1 || u.ocjena[last] === 2))
      .reduce((a, u) => a + u.stanovnici, 0)
    return { units: index.jedinice.length, years, last, pressed }
  }, [index])
  const item = (value: string, label: ReactNode, key: string) => (
    <div key={key} className="flex flex-row-reverse items-baseline justify-end gap-1.5">
      <dt className="text-ink-2">{label}</dt>
      <dd className="tabular font-semibold text-ink">{value}</dd>
    </div>
  )
  return (
    <dl className={`flex-wrap gap-x-5 gap-y-1 text-sm ${className}`} aria-label="Brojke iz podataka">
      {item(num(f.units), 'općina, gradova i županija', 'u')}
      {f.years.length > 0 && item(num(f.years.length), `godina (${f.years[0]}.–${f.years[f.years.length - 1]}.)`, 'y')}
      {item(num(f.pressed), `stanovnika u jedinicama s ocjenom 1 ili 2 (${f.last}.)`, 'p')}
      {apis != null &&
        item(
          num(apis),
          <a href="#/metodologija?o=podaci" className="underline decoration-axis underline-offset-4 hover:decoration-ink">
            izvora preko API-ja
          </a>,
          'a',
        )}
    </dl>
  )
}

/** Three ways into the product, one per feature. Every number is read from the data, not typed in:
 *  Povljana's grade last year and this year, and the unit counts of the reform at 5.000 people. */
function Stories({ index, className = '' }: { index: IndexFile; className?: string }) {
  const [reform, setReform] = useState<{ prije: number; poslije: number } | null>(null)
  useEffect(() => {
    loadReform(5000)
      .then((r) => setReform({ prije: r.n_prije, poslije: r.n_poslije }))
      .catch(() => setReform(null))
  }, [])
  const last = String(index.zadnja_godina)
  const prev = String(index.zadnja_godina - 1)
  const bySlug = (slug: string) => index.jedinice.find((u) => u.slug === slug)
  const povljana = bySlug('opcina-povljana')
  const pag = bySlug('grad-pag')
  const rows: { href: string; lead: string; text: string }[] = []
  if (povljana) {
    const [a, b] = [povljana.ocjena[prev], povljana.ocjena[last]]
    rows.push({
      href: unitHref(povljana.slug),
      lead: 'Povljana',
      text: a && b && a !== b ? `ocjena s ${a} na ${b} u godinu dana` : `što stoji iza ocjene ${b ?? ''}`.trim(),
    })
  }
  if (povljana && pag) rows.push({ href: simulatorHref([pag.sifra, povljana.sifra]), lead: 'Pag i Povljana', text: 'što bi dalo spajanje' })
  rows.push({
    href: '#/reforma?prag=5000',
    lead: 'Karta reforme',
    text: reform ? `${num(reform.prije)} jedinica postaje ${num(reform.poslije)}` : 'kako bi izgledala karta s manje jedinica',
  })
  return (
    <nav className={className} aria-label="Za početak">
      <Eyebrow>Za početak</Eyebrow>
      <ul className="mt-2 space-y-1">
        {rows.map((r) => (
          <li key={r.href}>
            <a href={r.href} className="group flex items-baseline gap-2 py-0.5 text-[15px] text-ink-2 hover:text-ink">
              <ArrowRight
                className="h-4 w-4 shrink-0 translate-y-[3px] text-muted transition-transform group-hover:translate-x-0.5 group-hover:text-ink"
                aria-hidden
              />
              <span>
                <span className="font-medium text-ink">{r.lead}:</span> {r.text}
              </span>
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
