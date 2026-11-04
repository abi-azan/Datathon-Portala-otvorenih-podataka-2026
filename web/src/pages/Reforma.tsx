import { AlertTriangle, ArrowRight, X } from 'lucide-react'
import { lazy, Suspense, useEffect, useMemo, useState, type ReactNode } from 'react'
import { GradeChip } from '../components/Grade'
import { Card, Eyebrow } from '../components/Layout'
import { REFORM_THRESHOLDS, canMerge, loadReform, type IndexFile, type ReformFile, type ReformUnit } from '../lib/data'
import { GRADES, VRSTA, eur, num, pct } from '../lib/format'
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

function readUrl(): { prag: number; s: string } {
  const q = new URLSearchParams(window.location.hash.split('?')[1] ?? '')
  const prag = Number(q.get('prag'))
  return { prag: (REFORM_THRESHOLDS as readonly number[]).includes(prag) ? prag : 5000, s: q.get('s') ?? '' }
}

export function Reforma({ index }: { index: IndexFile }) {
  const year = String(index.zadnja_godina)
  const [{ prag, s: selected }, setState] = useState(readUrl)
  const [files, setFiles] = useState<Record<number, ReformFile>>({})
  const [failed, setFailed] = useState<number[]>([])
  const bySifra = useMemo(() => new Map(index.jedinice.map((u) => [u.sifra, u])), [index])
  const file = files[prag]

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
  const select = (s: string) => setState((st) => ({ ...st, s }))

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
            <span className="tabular text-sm font-semibold">{num(prag)}</span>
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
        </div>

        {failed.includes(prag) && !file && <p className="text-sm text-ink-2">Podaci Karte reforme nisu se učitali. Osvježi stranicu.</p>}

        {file && (
          <Card>
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
                <div className="text-xs text-muted">strukturni jaz (gornja granica) {mil(file.strukturni_jaz_zbroj)}</div>
              </dt>
              <dd className="tabular text-right">0 – {mil(file.usteda_realno_do_zbroj)} godišnje</dd>
              {file.izravnanje_promjena_zbroj != null && (
                <>
                  <dt className="text-ink-2">
                    Fiskalno izravnanje
                    <div className="text-xs text-muted">promjena punog iznosa prema zakonskoj formuli</div>
                  </dt>
                  <dd className="tabular text-right">{file.izravnanje_promjena_zbroj < 0 ? '−' : ''}{mil(Math.abs(file.izravnanje_promjena_zbroj))}</dd>
                </>
              )}
            </dl>
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

        {unit && <Selected u={unit} bySifra={bySifra} year={year} onClose={() => select('')} />}

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

      <div className="h-[60vh] min-h-[420px] lg:sticky lg:top-24 lg:h-[min(80vh,860px)] lg:min-h-[520px]">
        {file ? (
          <Suspense fallback={<MapBox>Učitavam kartu…</MapBox>}>
            <ReformMap units={file.jedinice} prag={prag} selected={selected} onSelect={select} />
          </Suspense>
        ) : (
          <MapBox>Učitavam…</MapBox>
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
          {num(u.stanovnici)} st.
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
          u skupini {u.skupina}
        </p>
      )}
      {u.clanice.length > 1 && (
        <>
          <ul className="mt-4 divide-y divide-hairline border-t border-hairline">
            {members.map((m) => (
              <li key={m.sifra} className="flex items-center gap-3 py-2 text-sm">
                <a href={unitHref(m.slug)} className="min-w-0 flex-1 truncate underline decoration-axis underline-offset-4 hover:decoration-ink">
                  {m.naziv}
                </a>
                <span className="tabular text-xs text-muted">{num(m.stanovnici)} st.</span>
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
                <dt className="text-ink-2">Fiskalno izravnanje (puni iznos)</dt>
                <dd className="tabular text-right">
                  {Math.abs(e.promjena) < 1 ? 'bez promjene' : `${e.promjena < 0 ? '−' : '+'}${eur(Math.abs(e.promjena))}`}
                  {e.promjena_udio != null && Math.abs(e.promjena) >= 1 && ` (${pct(e.promjena_udio)})`}
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
          Svjedodžba jedinice <ArrowRight className="h-4 w-4" aria-hidden />
        </a>
      )}
    </Card>
  )
}
