import { AlertTriangle, ArrowRight, Info, RotateCcw, Scale, X } from 'lucide-react'
import { lazy, Suspense, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { GradeChip } from '../components/Grade'
import { Card, Eyebrow } from '../components/Layout'
import { Search } from '../components/Search'
import {
  loadGroups,
  loadSimulator,
  loadUnit,
  type GroupMedians,
  type IndexFile,
  type MergeSummary,
  type SimulatorFile,
  type UnitDetail,
  type UnitIndex,
} from '../lib/data'
import { COMPONENTS, FLAGS, QUALITY, VRSTA, eur, num, pct } from '../lib/format'
import { parseSelection, simulatorHref, unitHref } from '../lib/router'

// Same lazy chunk as the home page: MapLibre is about 1 MB.
const GradeMap = lazy(() =>
  import('../components/GradeMap')
    .then((m) => ({ default: m.GradeMap }))
    .catch(() => ({ default: () => <MapBox>Karta se nije učitala. Jedinice možeš odabrati pretragom.</MapBox> })),
)

function MapBox({ children }: { children: ReactNode }) {
  return (
    <div className="grid h-full w-full place-items-center rounded-2xl border border-hairline bg-surface px-6 text-center text-sm text-muted">
      {children}
    </div>
  )
}

const MAX = 4
const ZAGREB = '01333'
const EXAMPLES = [
  { label: 'Povljana + Pag', j: ['03166', '05738'] },
  { label: 'Donji Lapac, Perušić, Plitvička Jezera i Udbina', j: ['00841', '03239', '04553', '04677'] },
]

const keyOf = (sifre: string[]) => [...sifre].sort().join('-')
const short = (naziv: string) => naziv.replace(/^(Općina|Grad) /, '')
const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

/** One line per component for the merged unit, in the words of the profile page (pipeline/facts.py). */
function describe(key: string, v: number | null, r: MergeSummary['zadnja']): string {
  if (key === 'I1' && v != null) return `${v >= 0 ? 'operativni višak' : 'operativni manjak'} iznosi ${pct(Math.abs(v))} tekućih prihoda`
  if (key === 'I2' && v != null)
    return v >= 0
      ? `nakon otplate glavnice kredita ostaje ${pct(v)} tekućih prihoda`
      : `nakon otplate glavnice kredita nedostaje ${pct(-v)} tekućih prihoda`
  if (key === 'I3') {
    if ((r.ND ?? 0) <= 0) return 'jedinica nema neto duga (novac na računu pokriva kredite)'
    if (v == null) return 'jedinica ima neto dug, a nema operativnog viška iz kojeg bi ga otplaćivala'
    return `neto dug mogao bi se otplatiti iz operativnog viška za ${num(v, 1)} god.`
  }
  if (key === 'I4' && v != null) return `otplata kredita i kamata iznosi ${pct(v)} zakonske osnovice`
  if (key === 'I5') {
    if ((r.DO ?? 0) <= 0) return 'na kraju godine nema dospjelih neplaćenih obveza'
    return `dospjele neplaćene obveze na kraju godine iznose ${eur(r.DO)}, što je ${pct(v)} rashoda poslovanja`
  }
  return 'nema podataka'
}

function median(key: string, v: number | null | undefined): string {
  if (v == null) return ''
  if (key === 'I3') return `medijan skupine ${num(v, 1)} god.`
  return `medijan skupine ${pct(v)}`
}

export function Simulator({ index }: { index: IndexFile }) {
  const year = String(index.zadnja_godina)
  const bySifra = useMemo(() => new Map(index.jedinice.map((u) => [u.sifra, u])), [index])
  const jls = useMemo(() => index.jedinice.filter((u) => u.vrsta !== 'zupanija'), [index])
  const eligible = useCallback((u: UnitIndex) => u.vrsta !== 'zupanija' && u.sifra !== ZAGREB, [])

  /** A selection from the URL: known, allowed units of the first unit's county, at most MAX. */
  const clean = useCallback(
    (sifre: string[]) => {
      const units = sifre.map((s) => bySifra.get(s)).filter((u): u is UnitIndex => !!u && eligible(u))
      return units.filter((u) => u.zup_id === units[0].zup_id).slice(0, MAX).map((u) => u.sifra)
    },
    [bySifra, eligible],
  )

  const [sel, setSel] = useState<string[]>(() => clean(parseSelection(window.location.hash)))
  const [status, setStatus] = useState('')
  const [file, setFile] = useState<{ zup: number; data: SimulatorFile | null; failed: boolean } | null>(null)
  const [details, setDetails] = useState<Record<string, UnitDetail>>({})
  const [groups, setGroups] = useState<GroupMedians | null>(null)

  // links to another selection (examples, the profile page) change the hash
  useEffect(() => {
    const on = () => {
      if (window.location.hash.startsWith('#/simulator')) setSel(clean(parseSelection(window.location.hash)))
    }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [clean])

  // the selection lives in the URL, so it can be shared; replaceState does not fire hashchange
  useEffect(() => {
    const href = simulatorHref(sel)
    if (window.location.hash !== href) window.history.replaceState(null, '', href)
  }, [sel])

  const first = sel.length ? bySifra.get(sel[0]) : undefined
  const zup = first?.zup_id ?? null

  useEffect(() => {
    if (zup == null) return
    let live = true // until the file for this county arrives, `file` is for another one (see `current`)
    loadSimulator(zup)
      .then((data) => live && setFile({ zup, data, failed: false }))
      .catch(() => live && setFile({ zup, data: null, failed: true }))
    return () => {
      live = false
    }
  }, [zup])

  useEffect(() => {
    for (const s of sel) {
      const u = bySifra.get(s)
      if (u && !details[s]) loadUnit(u.slug).then((d) => setDetails((m) => ({ ...m, [s]: d }))).catch(() => {})
    }
  }, [sel, bySifra, details])

  useEffect(() => {
    loadGroups().then(setGroups).catch(() => {})
  }, [])

  const current = file && file.zup === zup ? file : null
  const skupine = current?.data?.skupine

  /** Why a unit cannot be the next pick; undefined if it can (or is already picked). */
  const reason = useCallback(
    (u: UnitIndex): string | undefined => {
      if (sel.includes(u.sifra)) return undefined
      if (!eligible(u)) return 'Županije i Grad Zagreb ne spajaju se u simulatoru'
      if (!first) return undefined
      if (u.zup_id !== first.zup_id) return `Druga županija: spajaju se samo jedinice iste županije (${first.zupanija})`
      if (sel.length >= MAX) return `Najviše ${MAX} jedinice`
      if (!skupine) return current?.failed ? 'Podaci simulatora nisu se učitali' : 'Učitavam podatke županije…'
      if (skupine[keyOf([...sel, u.sifra])]) return undefined
      const touches = sel.some((s) => skupine[keyOf([s, u.sifra])])
      return touches ? 'S odabranima ne čini povezanu cjelinu' : 'Ne graniči s odabranim jedinicama'
    },
    [sel, first, skupine, current, eligible],
  )

  const toggle = useCallback(
    (sifra: string) => {
      const u = bySifra.get(sifra)
      if (!u) return
      if (sel.includes(sifra)) {
        setSel(sel.filter((s) => s !== sifra))
        setStatus(`Uklonjeno iz odabira: ${u.naziv}.`)
        return
      }
      const r = reason(u)
      if (r) {
        setStatus(`${u.naziv} se ne može dodati. ${r}.`)
        return
      }
      setSel([...sel, sifra])
      setStatus(`Dodano u odabir: ${u.naziv}.`)
    },
    [bySifra, sel, reason],
  )

  const dimmed = useMemo(() => jls.filter((u) => reason(u)).map((u) => u.sifra), [jls, reason])
  const focus = useMemo(() => (zup == null ? [] : jls.filter((u) => u.zup_id === zup).map((u) => u.sifra)), [jls, zup])
  const hint = useCallback(
    (sifra: string) => {
      const u = bySifra.get(sifra)
      if (!u) return undefined
      if (sel.includes(sifra)) return 'Klikni za uklanjanje iz odabira'
      const r = reason(u)
      return r ? `Ne može se odabrati: ${r.charAt(0).toLowerCase()}${r.slice(1)}` : undefined
    },
    [bySifra, sel, reason],
  )

  const result = sel.length >= 2 && skupine ? skupine[keyOf(sel)] : undefined
  const broken = sel.length >= 2 && !!skupine && !result
  const members = sel.map((s) => bySifra.get(s)!).sort((a, b) => b.stanovnici - a.stanovnici)

  const reset = () => {
    setSel([])
    setStatus('Odabir je poništen.')
  }

  return (
    <main className="mx-auto grid max-w-[1440px] gap-8 px-6 pt-8 lg:grid-cols-[minmax(0,560px)_1fr] lg:px-10">
      <div className="flex min-w-0 flex-col gap-6">
        <div>
          <Eyebrow>Simulator spajanja · scenarij za raspravu</Eyebrow>
          <h1 className="mt-3 font-serif text-[2.4rem] leading-[1.05] font-semibold tracking-tight text-balance">
            Što ako se susjedne jedinice spoje?
          </h1>
          <p className="mt-4 leading-relaxed text-ink-2">
            Odaberi 2 do {MAX} susjedne općine ili grada iste županije. Prihodi, rashodi, dug i stanovnici se zbrajaju, a
            ocjena se računa istom metodom kao za postojeće jedinice.
          </p>
          <p className="mt-3 border-l-2 border-axis pl-3 text-sm leading-relaxed text-muted">
            Scenarij za raspravu, ne prijedlog granica.
          </p>
        </div>

        <div>
          <Search
            units={jls}
            year={year}
            onPick={(u) => toggle(u.sifra)}
            disabledReason={reason}
            label="Dodaj općinu ili grad u spajanje"
            placeholder={sel.length ? 'Dodaj susjednu općinu ili grad…' : 'Odaberi prvu općinu ili grad…'}
          />
          <p className="mt-2 text-xs text-muted">Jedinice možeš birati i klikom na karti.</p>
        </div>

        {sel.length === 0 && (
          <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted">
            <span>Probaj:</span>
            {EXAMPLES.map((e) => (
              <a key={e.label} href={simulatorHref(e.j)} className="text-ink-2 underline decoration-axis underline-offset-4 hover:decoration-ink">
                {e.label}
              </a>
            ))}
          </div>
        )}

        <p className="sr-only" aria-live="polite">
          {status}
        </p>

        {sel.length > 0 && (
          <Card className="!p-5">
            <div className="flex items-center justify-between gap-4">
              <Eyebrow>
                Odabrano {sel.length} od najviše {MAX} · {first?.zupanija}
              </Eyebrow>
              <button
                type="button"
                onClick={reset}
                className="flex shrink-0 items-center gap-1.5 rounded-lg px-2 py-1 text-sm whitespace-nowrap text-ink-2 hover:bg-hairline/60"
              >
                <RotateCcw className="h-4 w-4" aria-hidden /> Počni ispočetka
              </button>
            </div>
            <ul className="mt-3 divide-y divide-hairline">
              {members.map((u) => (
                <li key={u.sifra} className="flex items-center gap-3 py-2.5">
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium">{u.naziv}</div>
                    <div className="text-xs text-muted">
                      {VRSTA[u.vrsta]} · {num(u.stanovnici)} stanovnika
                    </div>
                  </div>
                  <GradeChip g={u.ocjena[year]} />
                  <button
                    type="button"
                    onClick={() => toggle(u.sifra)}
                    className="grid h-8 w-8 shrink-0 place-items-center rounded-lg text-muted hover:bg-hairline/60 hover:text-ink"
                    aria-label={`Ukloni ${u.naziv}`}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
            {status && <p className="mt-2 text-sm text-ink-2" aria-hidden>{status}</p>}
            {sel.length === 1 && <p className="mt-2 text-sm text-muted">Dodaj susjednu jedinicu: na karti su istaknute one koje se mogu odabrati.</p>}
            {broken && (
              <p className="mt-2 flex gap-2 text-sm text-ink-2">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                Odabrane jedinice ne čine povezanu cjelinu. Dodaj jedinicu koja ih povezuje ili ukloni jednu.
              </p>
            )}
            {current?.failed && <p className="mt-2 text-sm text-ink-2">Podaci simulatora za ovu županiju nisu se učitali. Osvježi stranicu.</p>}
          </Card>
        )}

        {result && <Result r={result} members={members} details={details} groups={groups} year={year} />}
      </div>

      <div className="h-[55vh] min-h-[380px] lg:sticky lg:top-24 lg:h-[min(80vh,860px)] lg:min-h-[520px]">
        <Suspense fallback={<MapBox>Učitavam kartu…</MapBox>}>
          <GradeMap
            units={index.jedinice}
            year={year}
            selectable
            selected={sel}
            onSelect={toggle}
            dimmed={dimmed}
            hint={hint}
            focus={focus}
          />
        </Suspense>
      </div>
    </main>
  )
}

function Result({
  r,
  members,
  details,
  groups,
  year,
}: {
  r: MergeSummary
  members: UnitIndex[]
  details: Record<string, UnitDetail>
  groups: GroupMedians | null
  year: string
}) {
  const z = r.zadnja
  const med = groups?.[r.skupina]?.[String(r.godina)]
  const rows = members.map((u) => {
    const d = details[u.sifra]?.godine[year]
    return {
      u,
      DO: d?.DO ?? null,
      I5: d?.I5 ?? null,
      uprava: u.uprava_pc != null ? u.uprava_pc * u.stanovnici : null,
    }
  })
  const worst = rows.reduce<(typeof rows)[number] | null>((w, x) => (x.I5 != null && (!w || (w.I5 ?? 0) < x.I5) ? x : w), null)
  const diluted = (z.DO ?? 0) > 0 && worst?.I5 != null && z.I5 != null && worst.I5 - z.I5 >= 0.02
  const u = r.usteda
  const notes = [
    ...z.zastavice.map((f) => ({ kind: 'flag' as const, text: FLAGS[f] ?? f })),
    ...(z.ogranicenje_do
      ? [{ kind: 'flag' as const, text: 'Ocjena je ograničena na najviše 2 jer dospjele obveze dosežu 30 % rashoda poslovanja.' }]
      : []),
    ...z.kvaliteta.map((q) => ({ kind: 'data' as const, text: QUALITY[q] ?? q })),
  ]

  return (
    <div className="flex flex-col gap-6">
      {/* the merged unit */}
      <Card>
        <Eyebrow>
          Spojena jedinica · {VRSTA[r.vrsta]} · {num(r.stanovnici)} stanovnika
        </Eyebrow>
        <h2 className="mt-2 font-serif text-2xl leading-tight font-semibold text-balance">
          {members.map((m) => short(m.naziv)).join(' + ')}
        </h2>
        <div className="mt-4 flex flex-wrap items-end justify-between gap-4">
          <GradeChip g={z.ocjena} size="lg" />
          <div className="text-right">
            <div className="tabular font-serif text-4xl leading-none font-semibold">{num(z.bodovi, 1)}</div>
            <div className="mt-1 text-xs text-muted">od 100 bodova</div>
          </div>
        </div>
        <p className="mt-4 text-sm text-ink-2">
          <span className="tabular font-semibold text-ink">
            {z.rang}. od {z.n_skupine}
          </span>{' '}
          u skupini {r.skupina} (rang među postojećim jedinicama skupine, bez samih članica), {r.godina}.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-hairline pt-4 text-sm">
          <span className="text-muted">Prije:</span>
          {members.map((m) => (
            <span key={m.sifra} className="inline-flex items-center gap-1.5">
              <span className="text-ink-2">{short(m.naziv)}</span>
              <GradeChip g={m.ocjena[year]} />
            </span>
          ))}
          <ArrowRight className="h-4 w-4 text-muted" aria-label="poslije" />
          <GradeChip g={z.ocjena} />
        </div>
      </Card>

      {/* before and after, absolute amounts */}
      <Card>
        <Eyebrow>Prije i poslije, {year}.</Eyebrow>
        <div className="mt-3 -mx-2 overflow-x-auto">
          <table className="w-full min-w-[480px] text-sm">
            <thead>
              <tr className="border-b border-hairline text-left text-xs text-muted">
                <th scope="col" className="px-2 py-2 font-medium">Jedinica</th>
                <th scope="col" className="px-2 py-2 font-medium">Ocjena</th>
                <th scope="col" className="px-2 py-2 text-right font-medium">Stanovnici</th>
                <th scope="col" className="px-2 py-2 text-right font-medium">Dospjele obveze</th>
                <th scope="col" className="px-2 py-2 text-right font-medium">Opća uprava</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((x) => (
                <tr key={x.u.sifra} className="border-b border-hairline align-top">
                  <th scope="row" className="px-2 py-2.5 text-left font-normal">
                    <a href={unitHref(x.u.slug)} className="underline decoration-axis underline-offset-4 hover:decoration-ink">
                      {short(x.u.naziv)}
                    </a>
                  </th>
                  <td className="px-2 py-2.5">
                    <span className="tabular font-semibold">{x.u.ocjena[year] ?? '–'}</span>
                  </td>
                  <td className="tabular px-2 py-2.5 text-right">{num(x.u.stanovnici)}</td>
                  <td className="tabular px-2 py-2.5 text-right">
                    {eur(x.DO)}
                    <div className="text-xs text-muted">{pct(x.I5)} rashoda</div>
                  </td>
                  <td className="tabular px-2 py-2.5 text-right">
                    {eur(x.uprava)}
                    <div className="text-xs text-muted">{num(x.u.uprava_pc)} € po st.</div>
                  </td>
                </tr>
              ))}
              <tr className="align-top font-semibold">
                <th scope="row" className="px-2 py-2.5 text-left">Spojena</th>
                <td className="px-2 py-2.5">
                  <span className="tabular">{z.ocjena}</span>
                </td>
                <td className="tabular px-2 py-2.5 text-right">{num(r.stanovnici)}</td>
                <td className="tabular px-2 py-2.5 text-right">
                  {eur(z.DO)}
                  <div className="text-xs font-normal text-muted">{pct(z.I5)} rashoda</div>
                </td>
                <td className="tabular px-2 py-2.5 text-right">
                  {eur(u?.uprava_zbroj)}
                  <div className="text-xs font-normal text-muted">{num(z.uprava_pc)} € po st.</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-muted">
          Dospjele obveze su neplaćene obveze kojima je prošao rok, kao udio u rashodima poslovanja. Opća uprava je funkcija 01
          bez transfera (017 i 018).
        </p>
        {diluted && worst && (
          <div className="mt-4 flex gap-2.5 rounded-xl bg-page p-3 text-sm">
            <Scale className="mt-0.5 h-4 w-4 shrink-0 text-ink-2" aria-hidden />
            <p>
              <strong className="font-semibold">Dug ne nestaje spajanjem, nego se raspoređuje na veći proračun.</strong>{' '}
              Dospjele obveze ostaju {eur(z.DO)}, a njihov udio u rashodima pada s {pct(worst.I5)} ({short(worst.u.naziv)}) na{' '}
              {pct(z.I5)}.
            </p>
          </div>
        )}
      </Card>

      {/* savings on general administration (PLAN §4.3) */}
      {u && (
        <Card>
          <Eyebrow>Ušteda na općoj upravi</Eyebrow>
          <div className="mt-3 font-serif text-3xl font-semibold">
            <span className="tabular">0 – {eur(u.realno_do)}</span> <span className="text-base font-normal text-muted">godišnje</span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-ink-2">
            Procijenjeni potencijal uštede na općoj upravi: 0 – {eur(u.realno_do)} godišnje. Gornja granica temelji se na
            usporedbi sa sličnim jedinicama; u praksi se ostvari tek dio, osobito kod dobrovoljnih spajanja.
          </p>
          <dl className="mt-4 grid grid-cols-[1fr_auto] gap-x-4 gap-y-2 border-t border-hairline pt-4 text-sm">
            <dt className="text-ink-2">Opća uprava članica zajedno</dt>
            <dd className="tabular text-right">{eur(u.uprava_zbroj)}</dd>
            <dt className="text-ink-2">
              Očekivano za skupinu {r.skupina}
              <div className="text-xs text-muted">
                medijan {num(u.medijan_pc, 2)} € po stanovniku × {num(r.stanovnici)}
              </div>
            </dt>
            <dd className="tabular text-right">{eur(u.ocekivano)}</dd>
            <dt className="text-ink-2">Strukturni jaz (gornja granica)</dt>
            <dd className="tabular text-right">{eur(u.strukturni_jaz)}</dd>
            <dt className="text-ink-2">
              Realističan raspon
              <div className="text-xs text-muted">do 10 % troška uprave, najviše do jaza</div>
            </dt>
            <dd className="tabular text-right font-semibold">0 – {eur(u.realno_do)}</dd>
          </dl>
          {u.strukturni_jaz === 0 && (
            <p className="mt-3 text-sm text-ink-2">
              Spojena jedinica na upravu troši manje od medijana sličnih jedinica, pa se ušteda od veličine ne očekuje.
            </p>
          )}
          {u.iznad_10000 && (
            <p className="mt-3 flex gap-2 text-sm text-ink-2">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
              Spojena jedinica ima više od 10.000 stanovnika. Iznad te veličine dodatna ušteda se ne očekuje; alternativa je
              funkcionalno spajanje ili zajedničke službe.
            </p>
          )}
          <p className="mt-3 text-xs text-muted">
            Troškovi prijelaza (usklađivanje službi, sustava i propisa) nisu uključeni. Studije reformi u Danskoj, Njemačkoj i
            Nizozemskoj pokazuju da se u praksi ostvari tek dio potencijala ili ništa.
          </p>
        </Card>
      )}

      <Equalization r={r} members={members} />

      {/* components */}
      <Card>
        <Eyebrow>Pet sastavnica ocjene spojene jedinice</Eyebrow>
        <ul className="mt-4 space-y-4">
          {COMPONENTS.map((c) => {
            const score = z[c.score as keyof typeof z] as number | null
            const v = z[c.key as keyof typeof z] as number | null
            const m = median(c.key, med?.[c.key])
            return (
              <li key={c.key}>
                <div className="flex items-baseline justify-between gap-4">
                  <span className="font-medium">{c.name}</span>
                  <span className="tabular shrink-0 text-sm font-semibold">{num(score, 0)}</span>
                </div>
                <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-page" role="img" aria-label={`${c.name}: ${num(score, 0)} od 100 bodova`}>
                  <div className="h-full rounded-full bg-ink-2" style={{ width: `${score ?? 0}%` }} />
                </div>
                <p className="mt-1 text-sm text-ink-2">
                  {capitalize(describe(c.key, v, z))}
                  {m && `; ${m}`}
                </p>
              </li>
            )
          })}
        </ul>
      </Card>

      {/* warnings */}
      <Card>
        <Eyebrow>Upozorenja i napomene</Eyebrow>
        {notes.length === 0 ? (
          <p className="mt-3 text-sm text-ink-2">Spojena jedinica nema upozorenja za {r.godina}.</p>
        ) : (
          <ul className="mt-3 space-y-2.5">
            {notes.map((n, i) => (
              <li key={i} className="flex gap-2.5 text-sm">
                {n.kind === 'data' ? (
                  <Info className="mt-0.5 h-4 w-4 shrink-0 text-ink-2" aria-label="Napomena o podacima" />
                ) : (
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-ink-2" aria-label="Upozorenje" />
                )}
                <span>{n.text}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <div className="rounded-2xl border border-hairline bg-page p-5 text-sm leading-relaxed text-ink-2">
        <p>
          <strong className="font-semibold text-ink">Scenarij za raspravu, ne prijedlog granica.</strong> Spajanje ima i
          nefinancijsku cijenu: manje vijećnika po stanovniku i veću udaljenost od uprave. Tokovi i stanja su zbrojeni
          za {r.godina}., a ocjena je izračunata istom metodom kao za postojeće jedinice.{' '}
          <a href="#/metodologija" className="underline underline-offset-2">
            Kako se računa
          </a>
        </p>
        <p className="mt-2">
          Svjedodžbe članica:{' '}
          {members.map((m, i) => (
            <span key={m.sifra}>
              {i > 0 && ' · '}
              <a href={unitHref(m.slug)} className="underline decoration-axis underline-offset-4 hover:decoration-ink">
                {short(m.naziv)}
              </a>
            </span>
          ))}
        </p>
      </div>
    </div>
  )
}

/** Fiscal equalization under the statutory formula (pipeline/merge.py equalization, N5b). */
function Equalization({ r, members }: { r: MergeSummary; members: UnitIndex[] }) {
  const e = r.izravnanje
  const own = (sifra: string) => e?.puni_po_clanici[r.clanice.indexOf(sifra)]
  const why = !e
    ? ''
    : e.oznake.includes('clanica_iznad_referentne')
      ? ' Smanjuje se jer je porezni kapacitet barem jedne članice iznad referentne vrijednosti, pa podiže kapacitet spojene jedinice.'
      : r.vrsta === 'grad' && members.some((m) => m.vrsta === 'opcina')
        ? ' Smanjuje se jer spojena jedinica postaje grad: za gradove vrijedi niža referentna vrijednost, a porez se računa po stopama grada.'
        : ' Smanjuje se jer se porezni kapacitet spojene jedinice računa po njezinim stopama.'
  return (
    <Card>
      <Eyebrow>Fiskalno izravnanje</Eyebrow>
      {!e ? (
        <p className="mt-3 text-sm leading-relaxed text-ink-2">
          Spajanje može smanjiti fiskalno izravnanje: kad jedna članica ima porezni kapacitet iznad referentne vrijednosti,
          kapacitet spojene jedinice raste. Procjena za ovu skupinu nije dostupna.
        </p>
      ) : e.oznake.includes('bez_prava_na_izravnanje') ? (
        <p className="mt-3 text-sm leading-relaxed text-ink-2">
          Nijedna članica nema pravo na fiskalno izravnanje, jer im je porezni kapacitet iznad referentne vrijednosti, pa
          spajanje tu ništa ne mijenja.
        </p>
      ) : (
        <>
          <div className="mt-3 flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span className="tabular font-serif text-2xl font-semibold">{eur(e.puni_clanice)}</span>
            <ArrowRight className="h-4 w-4 self-center text-muted" aria-label="nakon spajanja" />
            <span className="tabular font-serif text-2xl font-semibold">{eur(e.puni_spojena)}</span>
            <span className="tabular text-sm text-ink-2">
              {Math.abs(e.promjena) < 1 ? 'bez promjene' : `${e.promjena < 0 ? '−' : '+'}${eur(Math.abs(e.promjena))}`}
              {e.promjena_udio != null && Math.abs(e.promjena) >= 1 && ` (${pct(e.promjena_udio)})`}
            </span>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-ink-2">
            Puni godišnji iznos prema zakonskoj formuli, za članice zajedno i za spojenu jedinicu.
            {Math.abs(e.promjena) < 1
              ? ' Sve članice su ispod referentne vrijednosti, pa se zbroj ne mijenja.'
              : e.promjena < 0 && why}
          </p>
          <dl className="mt-3 grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 border-t border-hairline pt-3 text-sm">
            {members.map((m) => (
              <div key={m.sifra} className="contents">
                <dt className="text-ink-2">{short(m.naziv)}</dt>
                <dd className="tabular text-right">{eur(own(m.sifra))}</dd>
              </div>
            ))}
          </dl>
        </>
      )}
      <p className="mt-3 text-xs text-muted">
        Zakon o financiranju jedinica lokalne i područne (regionalne) samouprave, čl. 8. i 9.; kapacitet i referentne
        vrijednosti iz tablice Ministarstva financija{e ? ` za ${e.godina}.` : '.'} Formula na toj tablici daje iste pune
        iznose kao Ministarstvo za svih 576 jedinica. Isplata je udio u iznosu iz državnog proračuna (2026. oko 63 % punog
        iznosa), a promjena udjela ostalih jedinica nije uključena.
      </p>
    </Card>
  )
}
