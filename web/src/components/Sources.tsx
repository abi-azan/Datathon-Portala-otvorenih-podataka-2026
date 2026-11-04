import { useEffect, useId, useRef, useState } from 'react'
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

/** Formula, auxiliary quantities and input table behind one indicator (jedinice/<slug>/izvor.json). */
export function SourcePanel({ src, k }: { src: SourceFile; k: string }) {
  const p = src.pokazatelji[k]
  const qs = needed(src, k)
  const used = Object.fromEntries(qs.map((q) => [q, usedYears(src, k, q)]))
  const years = [...new Set(Object.values(used).flat())].sort((a, b) => b - a).map(String)
  // only amounts the formula reads: an account feeds a quantity in that quantity's years
  // (account 3 also feeds I5 directly, in year t)
  const inputs = src.ulazi
    .filter((u) =>
      (src.konta[u.konto]?.za ?? []).some((z) => (used[z] ?? []).includes(u.godina) || (z === k && u.godina === src.godina)),
    )
    .sort((a, b) => b.godina - a.godina || (a.redak ?? 0) - (b.redak ?? 0))
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
          Iskazano u Bilanci {eur(doq.iskazano)}; pravilo 1 isključuje {eur(doq.pravilo1_iskljuceno)} kredita koji je iskazan
          kao cijeli dospio, a redovno se otplaćuje ili se još povlači.
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

// Component facts in the fact pack, by the label pipeline/facts.py gives them.
const FACT_COMPONENT: Record<string, string> = {
  'operativni saldo': 'I1',
  'slobodni saldo nakon otplate glavnice': 'I2',
  'godine otplate neto duga': 'I3',
  'servis duga': 'I4',
  'dospjele neplaćene obveze': 'I5',
}
// Same number spellings as pipeline/verify.py (NUMBER), so the text is split where the check reads it.
const NUMBER = /(?<![\d,.])-?\d+(?:[.,\u00a0\u202f]\d+)*/g
const value = (token: string) => Math.abs(Number(token.replace(/[.\u00a0\u202f]/g, '').replace(',', '.')))
/** What follows a number ("%", "€", "boda", "god."), so "2 %" is not taken for the grade "2". */
const UNIT = /^\s*(%|€|bod|god)/
const unitAfter = (s: string, end: number) => UNIT.exec(s.slice(end, end + 8))?.[1] ?? ''
const TIP_W = 288 // px, the fact popover under a number

/** The fact a number comes from: the first fact in pack order (grade and points come before the
 *  components) that writes it the same way and with the same unit after it; then the same spelling
 *  with any unit; then the same value. */
function factFor(token: string, unit: string, facts: Fact[]): { fact: Fact; component?: string } | null {
  const tokens = (f: Fact) =>
    [f.value, f.label].flatMap((s) => [...s.matchAll(NUMBER)].map((m) => ({ t: m[0], unit: unitAfter(s, (m.index ?? 0) + m[0].length) })))
  const v = value(token)
  const best =
    facts.find((f) => tokens(f).some((x) => x.t === token && x.unit === unit)) ??
    facts.find((f) => tokens(f).some((x) => x.t === token)) ??
    facts.find((f) => tokens(f).some((x) => value(x.t) === v))
  if (!best) return null
  const component = best.label.startsWith('Sastavnica: ')
    ? FACT_COMPONENT[best.label.slice('Sastavnica: '.length)]
    : best.label === 'Najslabija sastavnica'
      ? Object.entries(FACT_COMPONENT).find(([n]) => best.value.startsWith(n))?.[1]
      : undefined
  return { fact: best, component }
}

/** The explanation with every number marked: it shows the fact it comes from, and a number that
 *  belongs to a component opens that component's sources (PLAN §5, visible number check).
 *  Every number is a button, so the fact is reachable by mouse (hover), keyboard (focus) and touch (tap). */
export function CheckedText({
  text,
  facts,
  onOpen,
  className = '',
}: {
  text: string
  facts: Fact[]
  onOpen: (component: string) => void
  className?: string
}) {
  const wrap = useRef<HTMLDivElement>(null)
  const tipId = useId()
  // the number whose fact is shown; `pinned` when opened by a tap or click, so it outlasts hover
  const [tip, setTip] = useState<{ i: number; left: number; top: number; width: number; pinned: boolean } | null>(null)
  const displayText = normalizeGradeLabels(text)
  const parts: (string | { token: string; fact: Fact | null; component?: string })[] = []
  let last = 0
  for (const m of displayText.matchAll(NUMBER)) {
    const i = m.index ?? 0
    if (i > last) parts.push(displayText.slice(last, i))
    const hit = factFor(m[0], unitAfter(displayText, i + m[0].length), facts)
    parts.push({ token: m[0], fact: hit?.fact ?? null, component: hit?.component })
    last = i + m[0].length
  }
  parts.push(displayText.slice(last))

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

  return (
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
              <div className="text-xs text-muted">Iz paketa činjenica</div>
              <div className="mt-0.5 font-medium">{cur.fact.label}</div>
              <div className="text-ink-2">{normalizeGradeLabels(cur.fact.value)}</div>
            </>
          ) : (
            <div>Broj nije u paketu činjenica.</div>
          )}
          {cur.component && <div className="mt-1.5 text-xs text-muted">Klik otvara konta i retke u datotekama Ministarstva financija.</div>}
        </div>
      )}
    </div>
  )
}
