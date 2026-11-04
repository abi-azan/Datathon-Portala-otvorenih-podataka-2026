import type { Fact, SourceFile } from '../lib/data'
import { eur, num, pct } from '../lib/format'

// Quantities each indicator needs, and what each quantity is built from (PLAN §3.1).
const DEPS: Record<string, string[]> = { OS: ['PO'], PO: ['KP'], SD: ['glavnica'] }
const QUANTITY_NAMES: Record<string, string> = {
  KP: 'Kapitalne pomoći (KP)',
  PO: 'Tekući prihodi (PO)',
  OS: 'Operativni saldo (OS)',
  glavnica: 'Otplata glavnice',
  ND: 'Neto dug (ND)',
  SD: 'Servis duga (SD)',
  ZO: 'Zakonska osnovica (ZO)',
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

const indicatorValue = (key: string, v: number | null) =>
  v == null ? 'nema operativnog viška' : key === 'I3' ? `${num(v, 1)} god.` : pct(v)

/** Formula, auxiliary quantities and input table behind one indicator (jedinice/<slug>/izvor.json). */
export function SourcePanel({ src, k }: { src: SourceFile; k: string }) {
  const p = src.pokazatelji[k]
  const qs = needed(src, k)
  // the years this indicator reads: year t for I5, the window for the rest, and for I4 also the
  // year before the window (ZO of y − 1)
  const win = src.prozor.godine
  const years = (k === 'I5' ? [src.godina] : k === 'I4' ? [...win, Math.min(...win) - 1] : win).map(String)
  const inputs = src.ulazi
    .filter((u) => (src.konta[u.konto]?.za ?? []).some((z) => qs.includes(z) || z === k))
    .filter((u) => years.includes(String(u.godina)))
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
                    {src.velicine[q]?.godine[y] != null ? eur(src.velicine[q].godine[y]) : ''}
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
          * Refinanciranje: otplata glavnice veća je od 10 % tekućih prihoda i plaćena je novim kreditom (84), pa se broji
          samo 54 − 84.
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
                    {c?.izvor === 'Bilanca' ? `Bilanca, ${u.stupac}${u.redak}` : `PR-RAS, redak ${u.redak}`}
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
const NUMBER = /(?<![\d,.])-?\d+(?:[.,  ]\d+)*/g
const value = (token: string) => Math.abs(Number(token.replace(/[.  ]/g, '').replace(',', '.')))

/** The fact a number comes from: the first fact in pack order (grade and points come before the
 *  components) that writes it exactly the same way; failing that, one with the same value. */
function factFor(token: string, facts: Fact[]): { fact: Fact; component?: string } | null {
  const tokens = (f: Fact) => [...f.value.matchAll(NUMBER), ...f.label.matchAll(NUMBER)].map((m) => m[0])
  const v = value(token)
  const best = facts.find((f) => tokens(f).includes(token)) ?? facts.find((f) => tokens(f).some((t) => value(t) === v))
  if (!best) return null
  const component = best.label.startsWith('Sastavnica: ')
    ? FACT_COMPONENT[best.label.slice('Sastavnica: '.length)]
    : best.label === 'Najslabija sastavnica'
      ? Object.entries(FACT_COMPONENT).find(([n]) => best.value.startsWith(n))?.[1]
      : undefined
  return { fact: best, component }
}

/** The explanation with every number marked: it shows the fact it comes from, and a number that
 *  belongs to a component opens that component's sources (PLAN §5, visible number check). */
export function CheckedText({ text, facts, onOpen }: { text: string; facts: Fact[]; onOpen: (component: string) => void }) {
  const parts: (string | { token: string; fact: Fact | null; component?: string })[] = []
  let last = 0
  for (const m of text.matchAll(NUMBER)) {
    const i = m.index ?? 0
    if (i > last) parts.push(text.slice(last, i))
    const hit = factFor(m[0], facts)
    parts.push({ token: m[0], fact: hit?.fact ?? null, component: hit?.component })
    last = i + m[0].length
  }
  parts.push(text.slice(last))
  return (
    <>
      {parts.map((p, i) => {
        if (typeof p === 'string') return <span key={i}>{p}</span>
        const title = p.fact ? `Iz paketa činjenica: ${p.fact.label} – ${p.fact.value}` : 'Broj nije u paketu činjenica'
        if (p.component)
          return (
            <button
              key={i}
              type="button"
              onClick={() => onOpen(p.component!)}
              title={`${title}. Klikni za konta i izvorne datoteke.`}
              className="cursor-pointer underline decoration-axis decoration-dotted underline-offset-4 hover:decoration-ink"
            >
              {p.token}
            </button>
          )
        return (
          <span key={i} title={title} className="underline decoration-hairline decoration-dotted underline-offset-4">
            {p.token}
          </span>
        )
      })}
    </>
  )
}
