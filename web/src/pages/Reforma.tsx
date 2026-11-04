import { AlertTriangle, ArrowRight, LoaderCircle, X } from 'lucide-react'
import { lazy, Suspense, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { GradeChip } from '../components/Grade'
import { Card, Eyebrow } from '../components/Layout'
import { REFORM_THRESHOLDS, canMerge, loadReform, type IndexFile, type ReformFile, type ReformUnit } from '../lib/data'
import { GRADES, VRSTA, eur, num } from '../lib/format'
import { simulatorHref, unitHref } from '../lib/router'

const ReformMap = lazy(() =>
  import('../components/ReformMap')
    .then((m) => ({ default: m.ReformMap }))
    .catch(() => ({ default: () => <MapBox>Karta se nije učitala. Osvježi stranicu.</MapBox> })),
)

function MapBox({ children }: { children: ReactNode }) {
  return (
    <div className="grid h-full w-full place-items-center rounded-2xl border border-hairline bg-surface px-6 text-center text-sm text-muted">
      {children}
    </div>
  )
}

const keyOf = (u: ReformUnit) => u.clanice.join('-')
const short = (naziv: string) => naziv.replace(/^(Općina|Grad) /, '')
const mil = (x: number) => `${num(x / 1e6, 1)} mil. €`

// where each threshold comes from in Croatian rules (docs/research/08 §7.3); there is no official minimum size
const THRESHOLD_SOURCE: Record<number, string> = {
  2500: 'Razred iz Vladine odluke o poticajima za spajanje (NN 88/2022); do 2.500 stanovnika općinsko vijeće ima 9 članova.',
  5000: 'Zadnji razred s dodatkom u Vladinoj odluci o poticajima (NN 88/2022); zakonski minimum u Sloveniji i Estoniji.',
  10000: 'Zakonski uvjet za status grada (Zakon o lokalnoj i područnoj samoupravi, čl. 5.).',
}

function readUrl(): { prag: number; s: string } {
  const q = new URLSearchParams(window.location.hash.split('?')[1] ?? '')
  const prag = Number(q.get('prag'))
  return { prag: (REFORM_THRESHOLDS as readonly number[]).includes(prag) ? prag : 5000, s: q.get('s') ?? '' }
}

/** The unit at the new threshold that holds most of an old group's population. */
function successor(key: string, units: ReformUnit[], bySifra: Map<string, { stanovnici: number }>): ReformUnit | undefined {
  const old = new Set(key.split('-'))
  let best: ReformUnit | undefined
  let most = 0
  for (const u of units) {
    const n = u.clanice.reduce((a, s) => a + (old.has(s) ? (bySifra.get(s)?.stanovnici ?? 0) + 1 : 0), 0)
    if (n > most) [best, most] = [u, n]
  }
  return best
}

export function Reforma({ index }: { index: IndexFile }) {
  const year = String(index.zadnja_godina)
  const [{ prag, s: selected }, setState] = useState(readUrl)
  const [files, setFiles] = useState<Record<number, ReformFile>>({})
  const [failed, setFailed] = useState<number[]>([])
  const [note, setNote] = useState('')
  const bySifra = useMemo(() => new Map(index.jedinice.map((u) => [u.sifra, u])), [index])
  // the threshold on screen: it lags `prag` while the next file loads, so the map, the summary
  // and the list stay (dimmed) instead of being replaced by a loading box
  const [shown, setShown] = useState<number | null>(null)
  if (files[prag] && shown !== prag) {
    setShown(prag)
    // the open group may not exist at the new threshold: open the one most of its people end up in
    const units = files[prag].jedinice
    let msg = ''
    if (selected && !units.some((u) => keyOf(u) === selected)) {
      const next = successor(selected, units, bySifra)
      const was = shown != null ? files[shown]?.jedinice.find((u) => keyOf(u) === selected) : undefined
      setState({ prag, s: next ? keyOf(next) : '' })
      if (was && next)
        msg =
          was.clanice.length > 1
            ? `Spojena jedinica ${was.naziv} ne postoji na pragu od ${num(prag)} stanovnika. Prikazana je jedinica u kojoj je većina njezinih stanovnika.`
            : `${was.naziv} se na pragu od ${num(prag)} stanovnika spaja sa susjedima. Prikazana je spojena jedinica.`
    }
    if (msg !== note) setNote(msg)
  }
  const file = shown != null ? files[shown] : undefined
  const stale = file != null && shown !== prag
  const loadFailed = failed.includes(prag) && !files[prag]

  useEffect(() => {
    if (files[prag] || failed.includes(prag)) return
    let live = true
    loadReform(prag)
      .then((f) => live && setFiles((m) => ({ ...m, [prag]: f })))
      .catch(() => live && setFailed((x) => [...x, prag]))
    return () => {
      live = false
    }
  }, [prag, files, failed])

  // once the first threshold is in, fetch the other two (about 130 KB each), so the slider is instant
  const anyLoaded = Object.keys(files).length > 0
  useEffect(() => {
    if (!anyLoaded) return
    let live = true
    for (const p of REFORM_THRESHOLDS)
      loadReform(p)
        .then((f) => live && setFiles((m) => (m[p] ? m : { ...m, [p]: f })))
        .catch(() => {}) // a failure shows up if that threshold is picked: the load effect retries it
    return () => {
      live = false
    }
  }, [anyLoaded])

  // in-app links to another threshold or group change the hash while this page stays mounted
  useEffect(() => {
    const on = () => {
      if (window.location.hash.startsWith('#/reforma')) setState(readUrl())
    }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])

  useEffect(() => {
    const href = `#/reforma?prag=${prag}${selected ? `&s=${selected}` : ''}`
    if (window.location.hash !== href) window.history.replaceState(null, '', href)
  }, [prag, selected])

  const setPrag = (p: number) => {
    setFailed((x) => x.filter((q) => q !== p))   // a retry: the load effect runs again for p
    setState((st) => ({ prag: p, s: st.s }))
  }
  // where focus goes when the group card closes: back to what opened it
  const openedBy = useRef<'list' | 'map'>('list')
  const groupList = useRef<HTMLSelectElement>(null)
  const mapArea = useRef<HTMLDivElement>(null)
  const select = (s: string, by: 'list' | 'map' = 'list') => {
    openedBy.current = by
    setNote('')
    setState((st) => ({ ...st, s }))
  }
  const close = () => {
    const by = openedBy.current
    select('')
    if (by === 'map') mapArea.current?.querySelector<HTMLElement>('.maplibregl-canvas')?.focus({ preventScroll: true })
    else groupList.current?.focus()
  }

  const before = useMemo(() => {
    const c: Record<number, number> = {}
    for (const u of index.jedinice) if (canMerge(u) && u.ocjena[year]) c[u.ocjena[year]!] = (c[u.ocjena[year]!] ?? 0) + 1
    return c
  }, [index, year])
  const after = useMemo(() => {
    const c: Record<number, number> = {}
    for (const u of file?.jedinice ?? []) if (u.ocjena) c[u.ocjena] = (c[u.ocjena] ?? 0) + 1
    return c
  }, [file])
  const merged = useMemo(() => (file?.jedinice ?? []).filter((u) => u.clanice.length > 1), [file])
  // merged units by county name, for the list next to the map
  const byCounty = useMemo(() => {
    const m = new Map<string, ReformUnit[]>()
    for (const u of merged) {
      const z = bySifra.get(u.clanice[0])?.zupanija ?? ''
      m.set(z, [...(m.get(z) ?? []), u])
    }
    return [...m.entries()].sort(([a], [b]) => a.localeCompare(b, 'hr'))
  }, [merged, bySifra])
  const savingsAbove10k = merged.filter((u) => u.usteda?.iznad_10000).reduce((a, u) => a + (u.usteda?.realno_do ?? 0), 0)
  const unit = file?.jedinice.find((u) => keyOf(u) === selected)
  const i = REFORM_THRESHOLDS.indexOf(prag as (typeof REFORM_THRESHOLDS)[number])

  return (
    <main className="mx-auto grid max-w-[1440px] gap-8 px-6 pt-8 lg:grid-cols-[minmax(0,460px)_1fr] lg:px-10">
      <div className="flex min-w-0 flex-col gap-6">
        <div>
          <Eyebrow>Karta reforme · scenarij, ne prijedlog granica</Eyebrow>
          <h1 className="mt-3 font-serif text-[2.4rem] leading-[1.05] font-semibold tracking-tight text-balance">
            Kako bi izgledala karta s manje jedinica?
          </h1>
          <p className="mt-4 leading-relaxed text-ink-2">
            Unutar svake županije najmanja općina ili grad ispod praga spaja se s najmanjim susjedom, sve dok sve jedinice ne
            dosegnu prag. Spojene jedinice ocjenjuju se istom metodom kao postojeće.
          </p>
        </div>

        <div>
          <div className="flex items-baseline justify-between">
            <label htmlFor="prag" className="text-xs font-semibold tracking-[0.08em] text-muted uppercase">
              Prag stanovnika
            </label>
            <span className="tabular flex items-center gap-1.5 text-sm font-semibold">
              {stale && !loadFailed && <LoaderCircle className="h-3.5 w-3.5 animate-spin text-muted" aria-hidden />}
              {num(prag)}
            </span>
          </div>
          <input
            id="prag"
            type="range"
            min={0}
            max={REFORM_THRESHOLDS.length - 1}
            step={1}
            value={i}
            onChange={(e) => setPrag(REFORM_THRESHOLDS[Number(e.target.value)])}
            aria-valuetext={`${num(prag)} stanovnika`}
            className="mt-3 w-full accent-ink"
          />
          <div className="mt-1 grid grid-cols-3 text-xs text-muted">
            {REFORM_THRESHOLDS.map((p, k) => (
              <button
                key={p}
                type="button"
                onClick={() => setPrag(p)}
                className={`tabular ${k === 0 ? 'text-left' : k === 2 ? 'text-right' : 'text-center'} ${p === prag ? 'font-semibold text-ink' : ''}`}
              >
                {num(p)}
              </button>
            ))}
          </div>
          <p className="mt-2 text-xs text-muted">
            {THRESHOLD_SOURCE[prag]} Službeni hrvatski minimum veličine jedinice ne postoji.
          </p>
        </div>

        <p className="sr-only" role="status">
          {stale && !loadFailed ? `Učitavam podatke za prag od ${num(prag)} stanovnika…` : ''}
        </p>
        {loadFailed && (
          <p className="text-sm text-ink-2">
            Podaci za prag od {num(prag)} stanovnika nisu se učitali.{' '}
            <button type="button" onClick={() => setPrag(prag)} className="underline decoration-axis underline-offset-4 hover:decoration-ink">
              Pokušaj ponovno
            </button>
            {file && ` Prikazan je prag od ${num(shown)}.`}
          </p>
        )}

        {file && (
          <Card className={`transition-opacity duration-200 ${stale ? 'opacity-55' : ''}`}>
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <span className="tabular font-serif text-4xl font-semibold">{num(file.n_prije)}</span>
              <ArrowRight className="h-5 w-5 self-center text-muted" aria-label="poslije" />
              <span className="tabular font-serif text-4xl font-semibold">{num(file.n_poslije)}</span>
              <span className="text-sm text-ink-2">općina i gradova</span>
            </div>
            <p className="mt-1 text-xs text-muted">Bez Grada Zagreba, koji je ujedno županija.</p>
            <dl className="mt-4 grid grid-cols-[1fr_auto] gap-x-4 gap-y-2 border-t border-hairline pt-4 text-sm">
              <dt className="text-ink-2">Spojenih jedinica</dt>
              <dd className="tabular text-right">{num(file.n_spojenih_skupina)}</dd>
              <dt className="text-ink-2">Stanovnika u spojenim jedinicama</dt>
              <dd className="tabular text-right">{num(file.stanovnika_u_spojenima)}</dd>
              <dt className="text-ink-2">
                Ušteda na općoj upravi
                <div className="text-xs text-muted">
                  samo od veličine; jaz koji postoji i bez spajanja {mil(file.jaz_bez_spajanja_zbroj)}
                </div>
              </dt>
              <dd className="tabular text-right">0 – {mil(file.usteda_realno_do_zbroj)} godišnje</dd>
              <dt className="text-ink-2">
                Poticaj države po NN 88/2022
                <div className="text-xs text-muted">pet godina; prijenos iz proračuna, ne ušteda</div>
              </dt>
              <dd className="tabular text-right">{mil(file.poticaj_godisnje_zbroj)} godišnje</dd>
              {file.izravnanje_isplata_spojene_promjena != null && file.izravnanje_isplata_ostale_promjena != null && (
                <>
                  <dt className="text-ink-2">
                    Fiskalno izravnanje, spojene jedinice
                    <div className="text-xs text-muted">promjena godišnje isplate</div>
                  </dt>
                  <dd className="tabular text-right">
                    {file.izravnanje_isplata_spojene_promjena < 0 ? '−' : '+'}
                    {mil(Math.abs(file.izravnanje_isplata_spojene_promjena))}
                  </dd>
                  <dt className="text-ink-2">
                    Fiskalno izravnanje, ostale jedinice
                    <div className="text-xs text-muted">iznos u proračunu je fiksan; državni proračun bez promjene</div>
                  </dt>
                  <dd className="tabular text-right">
                    {file.izravnanje_isplata_ostale_promjena < 0 ? '−' : '+'}
                    {mil(Math.abs(file.izravnanje_isplata_ostale_promjena))}
                  </dd>
                </>
              )}
            </dl>
            <p className="mt-3 text-xs leading-relaxed text-muted">
              Nacionalni plan oporavka kao smjer navodi 20 % stvarno spojenih jedinica, oko 111; ovaj scenarij uklanja{' '}
              {num(file.n_prije - file.n_poslije)}. Do 2026. nije spojena nijedna jedinica, a od planiranih poticaja za spajanje
              isplaćeno je oko 17 %.
            </p>
            {savingsAbove10k > 0 && (
              <p className="mt-3 flex gap-2 text-xs text-muted">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
                Od toga {mil(savingsAbove10k)} otpada na spojene jedinice iznad 10.000 stanovnika, gdje se dodatna ušteda od
                veličine ne očekuje.
              </p>
            )}
            <div className="mt-4 border-t border-hairline pt-4">
              <div className="grid grid-cols-[1fr_auto_auto] gap-x-4 gap-y-1 text-sm">
                <span className="text-xs text-muted">Ocjena</span>
                <span className="text-right text-xs text-muted">prije</span>
                <span className="text-right text-xs text-muted">poslije</span>
                {GRADES.map((g) => (
                  <div key={g.value} className="contents">
                    <span className="flex items-center gap-2">
                      <span className="h-3.5 w-6 rounded" style={{ background: g.color, boxShadow: 'inset 0 0 0 1px rgb(0 0 0 / 0.12)' }} aria-hidden />
                      <span className="tabular font-semibold">{g.value}</span>
                      <span className="text-ink-2">{g.word}</span>
                    </span>
                    <span className="tabular text-right">{before[g.value] ?? 0}</span>
                    <span className="tabular text-right font-semibold">{after[g.value] ?? 0}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {file && (
          <div>
            {/* keyboard and screen-reader alternative to clicking a merged unit on the map */}
            <label htmlFor="skupina" className="text-xs font-semibold tracking-[0.08em] text-muted uppercase">
              Spojene jedinice ({num(merged.length)})
            </label>
            <select
              id="skupina"
              ref={groupList}
              value={unit && unit.clanice.length > 1 ? selected : ''}
              onChange={(e) => select(e.target.value)}
              className="mt-2 w-full rounded-xl border border-axis bg-card px-3 py-2.5 text-sm"
            >
              <option value="">Odaberi spojenu jedinicu…</option>
              {byCounty.map(([zupanija, us]) => (
                <optgroup key={zupanija} label={zupanija}>
                  {us.map((u) => (
                    <option key={keyOf(u)} value={keyOf(u)}>
                      {u.naziv} ({num(u.stanovnici)} stanovnika)
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
        )}

        {note && (
          <p className="text-sm text-ink-2" role="status">
            {note}
          </p>
        )}

        {unit && <Selected u={unit} bySifra={bySifra} year={year} onClose={close} />}

        <p className="text-xs leading-relaxed text-muted">
          Scenarij za raspravu, ne prijedlog granica. Pravilo je namjerno jednostavno, pa ponekad stvara velike jedinice: mala
          općina kojoj je jedini susjed velik grad spaja se s njim. Susjedi su jedinice koje dijele granicu ili su povezane
          vezom preko mora; spaja se samo unutar županije. Ušteda i izravnanje računaju se kao u{' '}
          <a href="#/simulator" className="underline underline-offset-2">
            simulatoru spajanja
          </a>
          .
        </p>
      </div>

      <div ref={mapArea} className="h-[60vh] min-h-[420px] lg:sticky lg:top-24 lg:h-[min(80vh,860px)] lg:min-h-[520px]">
        {/* stays mounted across threshold changes: the view is kept and the new groups fade in */}
        {file && shown != null ? (
          <Suspense fallback={<MapBox>Učitavam kartu…</MapBox>}>
            <ReformMap
              units={file.jedinice}
              prag={shown}
              selected={selected}
              onSelect={(s) => select(s, 'map')}
              notice={
                stale
                  ? loadFailed
                    ? { text: `Podaci za prag ${num(prag)} nisu se učitali`, loading: false }
                    : { text: `Učitavam prag ${num(prag)}…`, loading: true }
                  : undefined
              }
            />
          </Suspense>
        ) : (
          <MapBox>{loadFailed ? 'Podaci Karte reforme nisu se učitali. Osvježi stranicu.' : 'Učitavam…'}</MapBox>
        )}
      </div>
    </main>
  )
}

function Selected({
  u,
  bySifra,
  year,
  onClose,
}: {
  u: ReformUnit
  bySifra: Map<string, IndexFile['jedinice'][number]>
  year: string
  onClose: () => void
}) {
  const members = u.clanice.map((s) => bySifra.get(s)).filter((m): m is NonNullable<typeof m> => !!m)
  members.sort((a, b) => b.stanovnici - a.stanovnici)
  const e = u.izravnanje
  return (
    <Card>
      <div className="flex items-start justify-between gap-4">
        <Eyebrow>
          {u.clanice.length > 1 ? `Spojena jedinica · ${u.clanice.length} članice` : 'Bez spajanja'} · {VRSTA[u.vrsta]} ·{' '}
          {num(u.stanovnici)} stanovnika
        </Eyebrow>
        <button type="button" onClick={onClose} className="-mt-1 -mr-2 grid h-8 w-8 shrink-0 place-items-center rounded-lg text-muted hover:bg-hairline/60" aria-label="Zatvori">
          <X className="h-4 w-4" />
        </button>
      </div>
      <h2 className="mt-2 font-serif text-2xl leading-tight font-semibold text-balance">
        {u.clanice.length > 1 ? members.map((m) => short(m.naziv)).join(' + ') : u.naziv}
      </h2>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <GradeChip g={u.ocjena} size="lg" />
        <span className="tabular text-sm text-ink-2">{num(u.bodovi, 1)} / 100 bodova</span>
      </div>
      {u.rang != null && (
        <p className="mt-2 text-sm text-ink-2">
          <span className="tabular font-semibold text-ink">
            {u.rang}. od {u.n_skupine}
          </span>{' '}
          u usporednoj skupini {u.skupina}
        </p>
      )}
      {u.clanice.length > 1 && (
        <>
          <ul className="mt-4 divide-y divide-hairline border-t border-hairline">
            {members.map((m) => (
              <li key={m.sifra} className="flex items-center gap-3 py-2 text-sm">
                {/* the population under the name, so the name is not cut off on narrow screens */}
                <div className="min-w-0 flex-1">
                  <a href={unitHref(m.slug)} className="block truncate underline decoration-axis underline-offset-4 hover:decoration-ink">
                    {m.naziv}
                  </a>
                  <div className="tabular text-xs text-muted">{num(m.stanovnici)} stanovnika</div>
                </div>
                <GradeChip g={u.ocjene_prije[m.sifra] ?? m.ocjena[year]} />
              </li>
            ))}
          </ul>
          <dl className="mt-3 grid grid-cols-[1fr_auto] gap-x-4 gap-y-2 border-t border-hairline pt-3 text-sm">
            {u.usteda && (
              <>
                <dt className="text-ink-2">Ušteda na općoj upravi</dt>
                <dd className="tabular text-right">0 – {eur(u.usteda.realno_do)}</dd>
              </>
            )}
            {e && (
              <>
                <dt className="text-ink-2">Fiskalno izravnanje (isplata)</dt>
                <dd className="tabular text-right">
                  {e.isplata_promjena == null || Math.abs(e.isplata_promjena) < 1
                    ? 'bez promjene'
                    : `${e.isplata_promjena < 0 ? '−' : '+'}${eur(Math.abs(e.isplata_promjena))}`}
                </dd>
              </>
            )}
          </dl>
          {u.usteda?.iznad_10000 && (
            <p className="mt-2 text-xs text-muted">Iznad 10.000 stanovnika dodatna ušteda od veličine se ne očekuje.</p>
          )}
          {u.clanice.length <= 4 && (
            <a href={simulatorHref(u.clanice)} className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium underline decoration-axis underline-offset-4 hover:decoration-ink">
              Otvori u simulatoru spajanja <ArrowRight className="h-4 w-4" aria-hidden />
            </a>
          )}
        </>
      )}
      {u.clanice.length === 1 && members[0] && (
        <a href={unitHref(members[0].slug)} className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium underline decoration-axis underline-offset-4 hover:decoration-ink">
          Pregled jedinice <ArrowRight className="h-4 w-4" aria-hidden />
        </a>
      )}
    </Card>
  )
}
