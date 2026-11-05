import { useEffect, useId, useRef, useState } from 'react'
import { CheckCircle2, XCircle } from 'lucide-react'
import type { Fact, SourceFile } from '../lib/data'
import { eur, normalizeGradeLabels, num, pct } from '../lib/format'

// Quantities each indicator needs, and what each quantity is built from (PLAN §3.1).
const DEPS: Record<string, string[]> = { OS: ['PO'], PO: ['KP'], SD: ['glavnica'], ZO: ['FI'] }
const QUANTITY_NAMES: Record<string, string> = {
  KP: 'Kapitalne pomoći (KP)',
  PO: 'Tekući prihodi (PO)',
  OS: 'Operativni saldo (OS)',
  glavnica: 'Otplata glavnice',
  ND: 'Neto dug (ND)',
  SD: 'Servis duga (SD)',
  ZO: 'Zakonska osnovica (ZO)',
  FI: 'Fiskalno izravnanje (FI)',
  DO: 'Dospjele obveze (DO)',
}

function needed(src: SourceFile, key: string): string[] {
  const out: string[] = []
  const add = (q: string) => {
    if (out.includes(q)) return
    out.push(q)
    for (const d of DEPS[q] ?? []) add(d)
  }
  for (const q of src.pokazatelji[key]?.velicine ?? []) add(q)
  return out
}

// A null indicator: I3 when there is net debt and no operating surplus (infinite years); the others
// when their denominator is 0 (no current revenue, no legal base, no operating spending).
const indicatorValue = (key: string, v: number | null) =>
  v == null ? (key === 'I3' ? 'nema operativnog viška' : 'nema podataka (nazivnik je 0)') : key === 'I3' ? `${num(v, 1)} god.` : pct(v)

/** Years in which indicator k reads quantity q: year t for ND and DO, the window for the rest,
 *  and for I4 the legal base of the year before each window year. */
function usedYears(src: SourceFile, k: string, q: string): number[] {
  const win = src.prozor.godine
  if (q === 'ND' || q === 'DO') return [src.godina]
  if (k === 'I4' && (q === 'ZO' || q === 'FI')) return win.map((y) => y - 1)
  return win
}

const usedMap = (src: SourceFile, k: string) => Object.fromEntries(needed(src, k).map((q) => [q, usedYears(src, k, q)]))

/** The amounts indicator k reads, newest year first: an account feeds a quantity in that quantity's
 *  years (account 3 also feeds I5 directly, in year t). */
function inputsFor(src: SourceFile, k: string) {
  const used = usedMap(src, k)
  return src.ulazi
    .filter((u) =>
      (src.konta[u.konto]?.za ?? []).some((z) => (used[z] ?? []).includes(u.godina) || (z === k && u.godina === src.godina)),
    )
    .sort((a, b) => b.godina - a.godina || (a.redak ?? 0) - (b.redak ?? 0))
}

const span = (ys: number[]) => {
  const lo = Math.min(...ys)
  const hi = Math.max(...ys)
  return lo === hi ? `${hi}.` : `${lo}.–${hi}.`
}
const kontoName = (k: string) => (k === 'dio611' ? 'dio 611' : k)
const MAX_ACCOUNTS = 4

/** Where indicator k's amounts sit in the MF files, in one line: the Bilanca cells and the PR-RAS
 *  rows (the newest year's row for each account), e.g. "Bilanca 2025., ćelije LU324, MA324". */
function cellsFor(src: SourceFile, k: string): string {
  const ins = inputsFor(src, k)
  const out: string[] = []
  const bil = ins.filter((u) => src.konta[u.konto]?.izvor === 'Bilanca' && u.stupac && u.redak)
  if (bil.length) {
    const cells = [...new Set(bil.map((u) => `${u.stupac}${u.redak}`))]
    out.push(`Bilanca ${span(bil.map((u) => u.godina))}, ${cells.length > 1 ? 'ćelije' : 'ćelija'} ${cells.join(', ')}`)
  }
  const pr = ins.filter((u) => src.konta[u.konto]?.izvor === 'PR-RAS')
  if (pr.length) {
    const rows = new Map<string, number | null>()
    for (const u of pr) if (!rows.has(u.konto)) rows.set(u.konto, u.redak) // newest year first
    // main accounts (6, 3, 54) before their sub-accounts (6332, …)
    const listed = [...rows]
      .sort((a, b) => a[0].length - b[0].length).slice(0, MAX_ACCOUNTS).map(([c, r]) => `${kontoName(c)}${r ? ` (redak ${r})` : ''}`)
    const more = rows.size - listed.length
    out.push(
      `PR-RAS ${span(pr.map((u) => u.godina))}, ${rows.size > 1 ? 'konta' : 'konto'} ${listed.join(', ')}${more > 0 ? ` i još ${more}` : ''}`,
    )
  }
  if (ins.some((u) => src.konta[u.konto]?.izvor === 'Odluka MF-a')) out.push('odluke MF-a o fiskalnom izravnanju')
  return out.join('; ')
}

/** Formula, auxiliary quantities and input table behind one indicator (jedinice/<slug>/izvor.json). */
export function SourcePanel({ src, k }: { src: SourceFile; k: string }) {
  const p = src.pokazatelji[k]
  const qs = needed(src, k)
  const used = usedMap(src, k)
  const years = [...new Set(Object.values(used).flat())].sort((a, b) => b - a).map(String)
  const inputs = inputsFor(src, k)
  const windowed = k !== 'I5'
  const doq = src.velicine.DO
  return (
    <div className="mt-3 rounded-xl border border-hairline bg-page p-4 text-sm">
      <p>
        <span className="font-semibold">{p.naziv}</span> = {p.formula}
        <span className="tabular ml-2 font-semibold">= {indicatorValue(k, p.vrijednost)}</span>
      </p>
      {windowed && (
        <p className="mt-1 text-xs text-muted">
          w su ponderi godina: {src.prozor.godine.map((y, i) => `${y}. ×${src.prozor.ponderi[i]}`).join(', ')}.
        </p>
      )}
      <div className="mt-3 overflow-x-auto">
        <table className="w-full min-w-[520px] text-xs">
          <thead>
            <tr className="border-b border-hairline text-left text-muted">
              <th scope="col" className="py-1.5 pr-3 font-medium">Veličina</th>
              {years.map((y) => (
                <th key={y} scope="col" className="tabular py-1.5 pl-3 text-right font-medium">
                  {y}.
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {qs.map((q) => (
              <tr key={q} className="border-b border-hairline align-top">
                <th scope="row" className="py-1.5 pr-3 text-left font-normal">
                  <div className="font-medium text-ink">{QUANTITY_NAMES[q] ?? q}</div>
                  <div className="text-muted">{src.velicine[q]?.formula}</div>
                </th>
                {years.map((y) => (
                  <td key={y} className="tabular py-1.5 pl-3 text-right whitespace-nowrap">
                    {used[q].includes(Number(y)) && src.velicine[q]?.godine[y] != null ? eur(src.velicine[q].godine[y]) : ''}
                    {q === 'glavnica' && src.velicine.glavnica.refinanciranje?.[y] ? ' *' : ''}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {qs.includes('glavnica') && years.some((y) => src.velicine.glavnica.refinanciranje?.[y]) && (
        <p className="mt-2 text-xs text-ink-2">
          * Refinanciranje: otplata glavnice veća je od {pct(src.velicine.glavnica.prag_refinanciranja ?? null, 0)} tekućih
          prihoda i plaćena je novim kreditom (84), pa se broji samo 54 − 84.
        </p>
      )}
      {k === 'I5' && doq && (doq.pravilo1_iskljuceno ?? 0) > 0 && (
        <p className="mt-2 text-xs text-ink-2">
          Iskazano u Bilanci {eur(doq.iskazano)}. Od toga se ne broji {eur(doq.pravilo1_iskljuceno)}: kredit je u Bilanci
          iskazan u cijelosti kao dospio, a redovno se otplaćuje ili se još povlači.
        </p>
      )}
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[520px] text-xs">
          <caption className="mb-1.5 text-left text-xs font-semibold tracking-[0.06em] text-muted uppercase">Ulazni iznosi</caption>
          <thead>
            <tr className="border-b border-hairline text-left text-muted">
              <th scope="col" className="py-1.5 pr-3 font-medium">Konto</th>
              <th scope="col" className="py-1.5 pr-3 font-medium">Naziv</th>
              <th scope="col" className="py-1.5 pr-3 font-medium">Godina</th>
              <th scope="col" className="py-1.5 pr-3 text-right font-medium">Iznos</th>
              <th scope="col" className="py-1.5 font-medium">Mjesto u datoteci</th>
            </tr>
          </thead>
          <tbody>
            {inputs.map((u, i) => {
              const c = src.konta[u.konto]
              return (
                <tr key={i} className="border-b border-hairline align-top">
                  <td className="tabular py-1.5 pr-3 font-medium">{u.konto === 'dio611' ? 'dio 611' : u.konto}</td>
                  <td className="max-w-[260px] py-1.5 pr-3 text-ink-2">{c?.naziv}</td>
                  <td className="tabular py-1.5 pr-3">{u.godina}.</td>
                  <td className="tabular py-1.5 pr-3 text-right whitespace-nowrap">{eur(u.iznos, 2)}</td>
                  <td className="tabular py-1.5 whitespace-nowrap text-ink-2">
                    {c?.izvor === 'Bilanca'
                      ? `Bilanca${u.stupac && u.redak ? `, ćelija ${u.stupac}${u.redak}` : ''}`
                      : c?.izvor === 'Odluka MF-a'
                        ? `${u.datoteka ?? 'Odluka MF-a'}, list „${u.list ?? ''}”, ćelija ${u.stupac ?? ''}${u.redak ?? ''}` +
                          (u.udio != null && u.proracun != null ? ` (udio ${num(u.udio, 6)} × ${eur(u.proracun)})` : '')
                        : `PR-RAS${u.redak ? `, redak ${u.redak}` : ''}`}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      <ul className="mt-3 space-y-0.5 text-xs text-muted">
        {Object.entries(src.izvori).map(([name, f]) =>
          f.datoteka ? (
            <li key={name}>
              {name}: {f.datoteka}, list „{f.list}”
            </li>
          ) : null,
        )}
        <li>Konta s iznosom 0 nisu navedena. Izvor: Ministarstvo financija, izvještaji razine 22.</li>
      </ul>
    </div>
  )
}

// Indicator facts in the fact pack, by the label pipeline/facts.py gives them. The longer names are
// those of the packs before 5.11.; the longer ones come first so a prefix match takes them.
const FACT_COMPONENT: Record<string, string> = {
  'slobodni saldo nakon otplate glavnice': 'I2',
  'godine otplate neto duga': 'I3',
  'dospjele neplaćene obveze': 'I5',
  'operativni saldo': 'I1',
  'slobodni saldo': 'I2',
  'godine otplate duga': 'I3',
  'servis duga': 'I4',
  'dospjele obveze': 'I5',
}
// "Pokazatelj: …" and "Najslabiji pokazatelj" since 5.11.; "Sastavnica: …" and "Najslabija sastavnica" before
const INDICATOR = /^(?:Pokazatelj|Sastavnica): /
const WEAKEST = new Set(['Najslabiji pokazatelj', 'Najslabija sastavnica'])
// Same number spellings as pipeline/verify.py (NUMBER), so the text is split where the check reads it.
const NUMBER = /(?<![\d,.])-?\d+(?:[.,  ]\d+)*/g
const value = (token: string) => Math.abs(Number(token.replace(/[.  ]/g, '').replace(',', '.')))
/** What follows a number ("%", "€", "boda", "god."), so "2 %" is not taken for the grade "2". */
const UNIT = /^\s*(%|€|bod|god)/
const unitAfter = (s: string, end: number) => UNIT.exec(s.slice(end, end + 8))?.[1] ?? ''
const TIP_W = 288 // px, the fact popover under a number

/** The fact a number comes from: the first fact in pack order (grade and points come before the
 *  components) that has the number with a word next to it as in the text ("najviše 2", "2 (pod");
 *  then one that writes it the same way and with the same unit after it; then the same spelling
 *  with any unit; then the same value. */
function factFor(token: string, unit: string, facts: Fact[], near: string[] = []): { fact: Fact; component?: string } | null {
  const tokens = (f: Fact) =>
    [f.value, f.label].flatMap((s) => [...s.matchAll(NUMBER)].map((m) => ({ t: m[0], unit: unitAfter(s, (m.index ?? 0) + m[0].length) })))
  const v = value(token)
  const has = (f: Fact) => near.some((n) => f.value.toLowerCase().includes(n) || f.label.toLowerCase().includes(n))
  const best =
    facts.find((f) => has(f) && tokens(f).some((x) => x.t === token)) ??
    facts.find((f) => tokens(f).some((x) => x.t === token && x.unit === unit)) ??
    facts.find((f) => tokens(f).some((x) => x.t === token)) ??
    facts.find((f) => tokens(f).some((x) => value(x.t) === v))
  if (!best) return null
  const component = INDICATOR.test(best.label)
    ? FACT_COMPONENT[best.label.replace(INDICATOR, '')]
    : WEAKEST.has(best.label)
      ? Object.entries(FACT_COMPONENT).find(([n]) => best.value.startsWith(n))?.[1]
      : undefined
  return { fact: best, component }
}

/** Where a fact that is not a component comes from, by its label in pipeline/facts.py. */
function originOf(label: string, token: string): string | null {
  if (label.startsWith('Ocjena') && /^20\d\d$/.test(token)) return 'Godina izvještaja Ministarstva financija'
  if (label === 'Jedinica') return 'DZS, Popis stanovništva 2021.'
  if (label.startsWith('Ocjena') || label === 'Bodovi' || label === 'Jake strane')
    return 'Izračun iz pet pokazatelja; podaci su iz PR-RAS-a i Bilance Ministarstva financija'
  if (label === 'Usporedna skupina') return 'Vrsta jedinice i broj stanovnika (Popis 2021.)'
  if (label === 'Mjesto u skupini') return 'Poredak po bodovima unutar usporedne skupine'
  if (label === 'Upozorenja') return 'Prag upozorenja iz metodologije'
  if (label === 'Pravilo' || label === 'Napomena o podacima' || label === 'Usporedba') return 'Pravilo iz metodologije'
  if (label === 'Kontekst: broj stanovnika') return 'DZS: Popis 2021. i stanovništvo po godinama (PxWeb)'
  if (label === 'Kontekst: neto dohodak po stanovniku') return 'Porezna uprava, dohodak stanovništva'
  return null
}

/** The number is the peer group's median: its fact has it after "medijan" ("…; medijan skupine 81,9 boda")
 *  and the text names the median in the same clause before it (`before` is the text up to the number).
 *  Both are needed, because a unit's own value can equal the median: Viškovo 2025 has 88,4 boda and a
 *  median of 88,4, and only the second "88,4" of its text is the median. */
function isMedian(f: Fact, token: string, before: string) {
  const re = new RegExp(`(?<![\\d,.])${token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\d,])`, 'g')
  const inFact = [...f.value.matchAll(re)].some((m) => f.value.slice(0, m.index).toLowerCase().includes('medijan'))
  const clause = before.split(/[;.!?]\s|,\s/).pop() ?? ''
  return inFact && clause.toLowerCase().includes('medijan')
}

/** Source line of a matched number: for a median, the peer group; for a component, the MF cells
 *  (once izvor.json is loaded); otherwise where the fact comes from. */
const sourceLine = (n: { fact: Fact; component?: string; median?: boolean }, token: string, src: SourceFile | null) =>
  n.median
    ? 'Medijan usporedne skupine, isti izračun za svaku jedinicu skupine'
    : n.component && src
      ? cellsFor(src, n.component)
      : originOf(n.fact.label, token)

interface NumberPart {
  token: string
  /** position in the displayed text, for the snippet in the check list */
  at: number
  fact: Fact | null
  /** the component whose MF cells the number opens; never set for a median (those are not the unit's cells) */
  component?: string
  median: boolean
  /** the number check (pipeline/verify.py) did not find it in the fact pack */
  unknown: boolean
}

/** The displayed text split into plain strings and numbers, each with the fact it comes from. */
function splitNumbers(text: string, facts: Fact[], unknown: string[]) {
  const parts: (string | NumberPart)[] = []
  let last = 0
  for (const m of text.matchAll(NUMBER)) {
    const i = m.index ?? 0
    if (i > last) parts.push(text.slice(last, i))
    const end = i + m[0].length
    // the number with the word before it and with the word after it, as they could appear in a fact
    const near = [
      (/\S*\s?\S*$/.exec(text.slice(Math.max(0, i - 30), i))?.[0] ?? '') + m[0],
      m[0] + (/^\S*\s?\S*/.exec(text.slice(end, end + 30))?.[0] ?? ''),
    ]
      .map((n) => n.toLowerCase())
      .filter((n) => n.trim() !== m[0])
    const hit = factFor(m[0], unitAfter(text, end), facts, near)
    const bad = unknown.includes(m[0]) || !hit
    const median = !!hit && !bad && isMedian(hit.fact, m[0], text.slice(0, i))
    parts.push({
      token: m[0],
      at: i,
      fact: hit && !bad ? hit.fact : null,
      component: hit && !bad && !median ? hit.component : undefined,
      median,
      unknown: bad,
    })
    last = i + m[0].length
  }
  parts.push(text.slice(last))
  return parts
}

/** A few words around a number, so the list shows which "2" of the text it is. */
function snippet(text: string, at: number, len: number) {
  const from = Math.max(0, at - 28)
  const to = Math.min(text.length, at + len + 24)
  let before = text.slice(from, at)
  let after = text.slice(at + len, to)
  if (from > 0) before = '…' + before.replace(/^\S*\s/, '')
  if (to < text.length) after = after.replace(/\s\S*$/, '') + '…'
  return { before, after }
}

/** The explanation with every number marked: it shows the fact it comes from, and a number that
 *  belongs to a component opens that component's sources (PLAN §5, visible number check).
 *  Every number is a button, so the fact is reachable by mouse (hover), keyboard (focus) and touch (tap).
 *  With `listId`, the full check is rendered under the text as a list: every number, whether the
 *  check found it, its fact and its source; `listOpen` shows it. */
export function CheckedText({
  text,
  facts,
  onOpen,
  src = null,
  unknown = [],
  listId,
  listOpen = false,
  className = '',
}: {
  text: string
  facts: Fact[]
  onOpen: (component: string) => void
  src?: SourceFile | null
  unknown?: string[]
  listId?: string
  listOpen?: boolean
  className?: string
}) {
  const wrap = useRef<HTMLDivElement>(null)
  const tipId = useId()
  // the number whose fact is shown; `pinned` when opened by a tap or click, so it outlasts hover
  const [tip, setTip] = useState<{ i: number; left: number; top: number; width: number; pinned: boolean } | null>(null)
  const displayText = normalizeGradeLabels(text)
  const parts = splitNumbers(displayText, facts, unknown)
  const numbers = parts.filter((p): p is NumberPart => typeof p !== 'string')

  // a pinned fact closes on a tap anywhere else (touch browsers do not always move focus)
  const pinned = !!tip?.pinned
  useEffect(() => {
    if (!pinned) return
    const away = (e: PointerEvent) => {
      if (!(e.target instanceof Element && e.target.closest('[data-fact]'))) setTip(null)
    }
    document.addEventListener('pointerdown', away)
    return () => document.removeEventListener('pointerdown', away)
  }, [pinned])

  const show = (i: number, el: HTMLElement, pin: boolean) => {
    const box = wrap.current?.getBoundingClientRect()
    if (!box) return
    const r = el.getBoundingClientRect()
    const width = Math.min(TIP_W, box.width)
    const left = Math.max(0, Math.min(r.left - box.left + r.width / 2 - width / 2, box.width - width))
    setTip({ i, left, top: r.bottom - box.top + 6, width, pinned: pin })
  }
  const hide = (i: number) => setTip((t) => (t && t.i === i ? null : t))
  const shown = tip ? parts[tip.i] : undefined
  const cur = shown && typeof shown !== 'string' ? shown : undefined
  const curSource = cur?.fact ? sourceLine({ ...cur, fact: cur.fact }, cur.token, src) : null

  return (
    <>
      <div ref={wrap} className="relative">
        <p className={className}>
          {parts.map((p, i) => {
            if (typeof p === 'string') return <span key={i}>{p}</span>
            return (
              <button
                key={i}
                type="button"
                data-fact
                aria-describedby={tip?.i === i ? tipId : undefined}
                onMouseEnter={(e) => !tip?.pinned && show(i, e.currentTarget, false)}
                onMouseLeave={() => setTip((t) => (t && !t.pinned ? null : t))}
                onFocus={(e) => show(i, e.currentTarget, false)}
                onBlur={() => hide(i)}
                onKeyDown={(e) => e.key === 'Escape' && hide(i)}
                onClick={(e) => {
                  if (p.component) {
                    setTip(null)
                    onOpen(p.component)
                  } else if (tip?.i === i && tip.pinned) setTip(null)
                  else show(i, e.currentTarget, true)
                }}
                className={`rounded-sm underline decoration-dotted underline-offset-4 ${
                  p.component ? 'cursor-pointer decoration-axis hover:decoration-ink' : 'cursor-help decoration-hairline hover:decoration-axis'
                }`}
              >
                {p.token}
              </button>
            )
          })}
        </p>
        {tip && cur && (
          <div
            id={tipId}
            role="tooltip"
            className="pointer-events-none absolute z-20 rounded-xl border border-hairline bg-card p-3 font-sans text-sm leading-snug shadow-lg"
            style={{ left: tip.left, top: tip.top, width: tip.width }}
          >
            {cur.fact ? (
              <>
                <div className="text-xs text-muted">Izračunata činjenica</div>
                <div className="mt-0.5 font-medium">{cur.fact.label}</div>
                <div className="text-ink-2">{normalizeGradeLabels(cur.fact.value)}</div>
                {curSource && <div className="mt-1.5 border-t border-hairline pt-1.5 text-xs text-ink-2">Izvor: {curSource}</div>}
              </>
            ) : (
              <div>Broja nema među izračunatim činjenicama.</div>
            )}
            {cur.component && <div className="mt-1.5 text-xs text-muted">Klik otvara konta i retke u datotekama Ministarstva financija.</div>}
          </div>
        )}
      </div>
      {listId && (
        <div id={listId} hidden={!listOpen} className="mt-4 rounded-xl border border-hairline bg-page p-4">
          <p className="text-sm font-medium">
            Provjera brojki: {numbers.filter((n) => !n.unknown).length} od {numbers.length} nađeno među izračunatim činjenicama
          </p>
          <ol className="mt-3 divide-y divide-hairline text-sm">
            {numbers.map((n, i) => {
              const s = snippet(displayText, n.at, n.token.length)
              const line = n.fact ? sourceLine({ ...n, fact: n.fact }, n.token, src) : null
              return (
                <li key={i} className="grid grid-cols-[1.25rem_minmax(0,1fr)] gap-x-2 py-2.5 sm:grid-cols-[1.25rem_minmax(0,14rem)_minmax(0,1fr)] sm:gap-x-4">
                  {n.unknown ? (
                    <XCircle className="mt-0.5 h-4 w-4 text-warn" aria-label="Nije nađeno" />
                  ) : (
                    <CheckCircle2 className="mt-0.5 h-4 w-4 text-grade-5" aria-label="Provjereno" />
                  )}
                  <div className="text-ink-2">
                    {s.before}
                    <strong className="tabular font-semibold text-ink">{n.token}</strong>
                    {s.after}
                  </div>
                  <div className="col-start-2 mt-1 sm:col-start-3 sm:mt-0">
                    {n.fact ? (
                      <>
                        <div className="font-medium">{n.fact.label}</div>
                        <div className="text-xs text-ink-2">{normalizeGradeLabels(n.fact.value)}</div>
                        {line && <div className="mt-0.5 text-xs text-muted">Izvor: {line}</div>}
                        {n.component && (
                          <button
                            type="button"
                            onClick={() => onOpen(n.component!)}
                            className="mt-0.5 text-xs text-muted underline decoration-axis underline-offset-4 hover:text-ink hover:decoration-ink"
                          >
                            Prikaži izračun
                          </button>
                        )}
                      </>
                    ) : (
                      <div className="text-warn">Broja nema među izračunatim činjenicama.</div>
                    )}
                  </div>
                </li>
              )
            })}
          </ol>
        </div>
      )}
    </>
  )
}
