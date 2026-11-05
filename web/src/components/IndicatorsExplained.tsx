import { ArrowRight, ChevronDown } from 'lucide-react'
import { useEffect, useState } from 'react'
import { loadUnit, type MethodologyDoc, type YearResult } from '../lib/data'
import { GRADES, num } from '../lib/format'
import { unitHref } from '../lib/router'
import { GradeChip } from './Grade'
import { Eyebrow } from './Layout'

// The worked example: a city everyone knows, with strong and weak indicators, so the weighting shows.
// Its numbers are read from the API at run time, never typed in.
const EXAMPLE = { slug: 'grad-split', name: 'Grad Split' }

/** What each indicator asks, in plain words. Thresholds, weights and formulas come from metodologija.json. */
const PLAIN: Record<string, { question: string; text: string }> = {
  I1: {
    question: 'Pokrivaju li tekući prihodi rashode poslovanja?',
    text: 'Razlika tekućih prihoda i rashoda poslovanja, kao udio tekućih prihoda. Višak znači da redovni rad ne troši više nego što donosi.',
  },
  I2: {
    question: 'Ostaje li novca nakon otplate kredita?',
    text: 'Operativni saldo umanjen za otplatu glavnice kredita, kao udio tekućih prihoda. To je novac koji ostaje za ulaganja.',
  },
  I3: {
    question: 'Za koliko bi se godina dug mogao otplatiti?',
    text: 'Neto dug (krediti umanjeni za novac na računu) podijeljen s prosječnim operativnim viškom. Bez neto duga pokazatelj daje 100 bodova, a uz dug bez operativnog viška 0.',
  },
  I4: {
    question: 'Koliko prihoda odlazi na otplatu kredita i kamata?',
    text: 'Kamate i otplata glavnice u godini, kao udio zakonske osnovice: prihoda prethodne godine od kojih zakon računa granicu zaduživanja.',
  },
  I5: {
    question: 'Plaća li jedinica račune na vrijeme?',
    text: 'Neplaćene obveze kojima je prošao rok, na kraju godine, kao udio rashoda poslovanja. Od 30 % ocjena je najviše 2, bez obzira na ostale pokazatelje.',
  },
}

const SET_NAMES: Record<string, string> = { osnovni: 'Osnovni', jednaki: 'Jednaki', kdz: 'KDZ', ineko: 'INEKO' }

/** A threshold value as the methodology writes it: years for I3, a percentage otherwise. */
function valueLabel(key: string, v: number) {
  if (key === 'I3') return `${num(v, 0)} god.`
  const p = v * 100
  return `${num(p, Math.abs(p - Math.round(p)) < 1e-9 ? 0 : 1)} %`
}

/** The example unit's value of an indicator, with one decimal. */
function exampleValue(key: string, v: number | null) {
  if (key === 'I3') return v == null ? 'dug bez operativnog viška' : v === 0 ? 'nema neto duga' : `${num(v, 1)} god.`
  return v == null ? '–' : `${num(v * 100, 1)} %`
}

/** The 0-100 points scale of one indicator: the bar in the grade colours, the threshold values above
 *  it and their points below, so "which value gives how many points" reads without a formula. */
function Scale({ k, pragovi }: { k: string; pragovi: { vrijednost: number; bodovi: number }[] }) {
  const stops = [...pragovi].sort((a, b) => a.bodovi - b.bodovi)
  const bands = GRADES.slice()
    .reverse()
    .map((g, i) => `${g.color} ${i * 20}% ${(i + 1) * 20}%`)
    .join(', ')
  const place = (p: number) =>
    p <= 0 ? { left: '0%' } : p >= 100 ? { right: '0%' } : { left: `${p}%`, transform: 'translateX(-50%)' }
  return (
    <div className="mt-4 grid grid-cols-[4.5rem_1fr] items-center gap-x-3 gap-y-1 text-[11px] sm:text-xs">
      <span className="text-muted">vrijednost</span>
      <div className="relative h-4">
        {stops.map((s) => (
          <span key={s.bodovi} className="tabular absolute top-0 whitespace-nowrap text-ink-2" style={place(s.bodovi)}>
            {valueLabel(k, s.vrijednost)}
          </span>
        ))}
      </div>
      <span aria-hidden />
      <div className="relative">
        <div className="h-2.5 rounded-full" style={{ background: `linear-gradient(90deg, ${bands})` }} aria-hidden />
        {stops.map((s) => (
          <span
            key={s.bodovi}
            className="absolute -top-0.5 h-3.5 w-px bg-ink"
            style={{ left: `calc(${s.bodovi}% - ${s.bodovi >= 100 ? 1 : 0}px)` }}
            aria-hidden
          />
        ))}
      </div>
      <span className="text-muted">bodovi</span>
      <div className="relative h-4">
        {stops.map((s) => (
          <span key={s.bodovi} className="tabular absolute top-0 text-muted" style={place(s.bodovi)}>
            {s.bodovi}
          </span>
        ))}
      </div>
      <span className="sr-only">
        {stops.map((s) => `${valueLabel(k, s.vrijednost)} daje ${s.bodovi} bodova`).join('; ')}; između pragova bodovi rastu
        ravnomjerno.
      </span>
    </div>
  )
}

/** The "Pet pokazatelja" section of the methodology page: how a grade is made in four steps, a worked
 *  example, each indicator in plain words with its scale, then the scale of grades, the four weight
 *  sets and, folded, the formulas and accounts. Everything numeric comes from metodologija.json. */
export function IndicatorsExplained({ doc }: { doc: MethodologyDoc }) {
  const [example, setExample] = useState<YearResult | null>(null)
  useEffect(() => {
    loadUnit(EXAMPLE.slug)
      .then((u) => setExample(u.godine[String(doc.godina)] ?? null))
      .catch(() => setExample(null))
  }, [doc.godina])

  const weights = doc.pokazatelji.map((p) => p.ponder)
  const cuts = doc.ocjene.filter((g) => g.od_bodova > 0)
  const scoreKey = (oznaka: string) => `S${oznaka.slice(1)}` as keyof YearResult
  const valueKey = (oznaka: string) => oznaka as keyof YearResult
  const ex = example && example.bodovi != null && !example.ogranicenje_do ? example : null

  const steps = [
    { title: 'Pet pokazatelja', text: 'iz godišnjih izvještaja koje jedinice predaju Ministarstvu financija (PR-RAS i Bilanca)' },
    { title: 'Bodovi 0–100', text: 'za svaki pokazatelj, prema stalnim pragovima, isti za sve jedinice' },
    {
      title: 'Ponderirani zbroj',
      text: `${doc.pokazatelji.map((p) => `${p.naziv.toLowerCase()} ${p.ponder} %`).join(', ')}`,
    },
    { title: 'Ocjena 1–5', text: cuts.map((g) => `od ${g.od_bodova} bodova ${g.ocjena}`).join(', ') },
  ]

  return (
    <div>
      <p className="mt-3 leading-relaxed text-ink-2">
        Ocjena nastaje u četiri koraka. Pragovi su preuzeti iz dvaju postojećih sustava ocjenjivanja općinskih financija,
        austrijskog KDZ-a i slovačkog INEKO-a.
      </p>
      <ol className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {steps.map((s, i) => (
          <li key={s.title} className="rounded-xl border border-hairline bg-card p-4">
            <div className="flex items-center gap-2">
              <span className="tabular grid h-6 w-6 shrink-0 place-items-center rounded-full bg-ink text-xs font-semibold text-white">
                {i + 1}
              </span>
              <span className="font-semibold">{s.title}</span>
            </div>
            <p className="mt-2 text-sm leading-snug text-ink-2">{s.text}</p>
          </li>
        ))}
      </ol>

      {/* worked example */}
      {ex && (
        <div className="mt-6 rounded-2xl border border-hairline bg-card p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <Eyebrow>
              Primjer: {EXAMPLE.name}, {doc.godina}.
            </Eyebrow>
            <a href={unitHref(EXAMPLE.slug)} className="inline-flex items-center gap-1 text-sm underline decoration-axis underline-offset-4 hover:decoration-ink">
              Pregled jedinice <ArrowRight className="h-3.5 w-3.5" aria-hidden />
            </a>
          </div>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="border-b border-hairline text-left text-xs text-muted">
                  <th scope="col" className="py-2 pr-3 font-medium">Pokazatelj</th>
                  <th scope="col" className="py-2 pr-3 font-medium">Vrijednost</th>
                  <th scope="col" className="py-2 pr-3 text-right font-medium">Bodovi</th>
                  <th scope="col" className="py-2 pr-3 text-right font-medium">Ponder</th>
                  <th scope="col" className="py-2 text-right font-medium">Doprinos</th>
                </tr>
              </thead>
              <tbody>
                {doc.pokazatelji.map((p) => {
                  const s = ex[scoreKey(p.oznaka)] as number | null
                  return (
                    <tr key={p.oznaka} className="border-b border-hairline">
                      <th scope="row" className="py-2 pr-3 text-left font-medium">{p.naziv}</th>
                      <td className="tabular py-2 pr-3 text-ink-2">{exampleValue(p.oznaka, ex[valueKey(p.oznaka)] as number | null)}</td>
                      <td className="tabular py-2 pr-3 text-right">{num(s, 1)}</td>
                      <td className="tabular py-2 pr-3 text-right text-ink-2">{p.ponder} %</td>
                      <td className="tabular py-2 text-right font-medium">{s == null ? '–' : num((s * p.ponder) / 100, 1)}</td>
                    </tr>
                  )
                })}
              </tbody>
              <tfoot>
                <tr>
                  <th scope="row" colSpan={4} className="pt-3 pr-3 text-right text-sm font-medium">
                    Zbroj
                  </th>
                  <td className="tabular pt-3 text-right text-base font-semibold">{num(ex.bodovi, 1)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
          <p className="mt-3 flex flex-wrap items-center gap-2 text-sm text-ink-2">
            {num(ex.bodovi, 1)} bodova daje ocjenu <GradeChip g={ex.ocjena} />
          </p>
          <p className="mt-2 text-xs text-muted">Doprinos = bodovi × ponder. Zbroj doprinosa su ukupni bodovi jedinice.</p>
        </div>
      )}

      {/* the five indicators */}
      <h3 className="mt-8 font-serif text-xl font-semibold">Pokazatelji jedan po jedan</h3>
      <p className="mt-1 text-sm text-ink-2">{doc.prozor.opis.replace('I1-I4', 'I1–I4')}</p>
      <ul className="mt-4 space-y-4">
        {doc.pokazatelji.map((p) => {
          const plain = PLAIN[p.oznaka]
          const sorted = [...p.pragovi].sort((a, b) => a.bodovi - b.bodovi)
          const higherBetter = sorted[sorted.length - 1].vrijednost > sorted[0].vrijednost
          return (
            <li key={p.oznaka} className="rounded-2xl border border-hairline bg-card p-5">
              <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                <h4 className="text-lg font-semibold">
                  <span className="mr-2 font-mono text-sm text-muted">{p.oznaka}</span>
                  {p.naziv}
                </h4>
                <span className="text-sm text-ink-2">
                  ponder <strong className="tabular font-semibold text-ink">{p.ponder} %</strong>
                </span>
              </div>
              {plain && <p className="mt-1 font-serif text-[1.05rem] text-ink">{plain.question}</p>}
              {plain && <p className="mt-1.5 text-sm leading-relaxed text-ink-2">{plain.text}</p>}
              <p className="mt-2 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full bg-page px-2.5 py-1 font-medium text-ink-2 ring-1 ring-hairline">
                  {higherBetter ? 'više je bolje' : 'manje je bolje'}
                </span>
                <span className="rounded-full bg-page px-2.5 py-1 text-ink-2 ring-1 ring-hairline">
                  {p.oznaka === 'I5' ? 'stanje na kraju godine' : `prosjek zadnje ${doc.prozor.ponderi.length} godine`}
                </span>
              </p>
              <Scale k={p.oznaka} pragovi={p.pragovi} />
              <details className="group/f mt-3">
                <summary className="flex cursor-pointer list-none items-center gap-1 text-xs text-muted hover:text-ink [&::-webkit-details-marker]:hidden">
                  Formula
                  <ChevronDown className="h-3.5 w-3.5 transition-transform group-open/f:rotate-180" aria-hidden />
                </summary>
                <p className="mt-1.5 font-mono text-xs text-ink-2">{p.formula}</p>
              </details>
            </li>
          )
        })}
      </ul>
      <p className="mt-3 text-xs text-muted">Između dvaju pragova bodovi rastu ravnomjerno (linearna interpolacija).</p>

      {/* grades, weight sets, peer groups */}
      <div className="mt-8 grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border border-hairline bg-card p-5">
          <Eyebrow>Od bodova do ocjene</Eyebrow>
          <ul className="mt-3 space-y-2">
            {doc.ocjene.map((g, i) => {
              const meta = GRADES.find((x) => x.value === g.ocjena)
              return (
                <li key={g.ocjena} className="flex items-center gap-3 text-sm">
                  <span className="h-4 w-7 rounded" style={{ background: meta?.color, boxShadow: 'inset 0 0 0 1px rgb(0 0 0 / 0.12)' }} aria-hidden />
                  <strong className="w-3">{g.ocjena}</strong>
                  <span className="flex-1">{meta?.word ?? g.rijec}</span>
                  <span className="tabular text-muted">
                    {g.od_bodova}–{i === 0 ? 100 : doc.ocjene[i - 1].od_bodova} bodova
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
        <div className="rounded-2xl border border-hairline bg-card p-5">
          <Eyebrow>Četiri skupa pondera</Eyebrow>
          <p className="mt-2 text-sm text-ink-2">
            Ocjena se računa i uz tri druga skupa pondera. Ako je ista uz sva četiri, na pregledu jedinice piše da ne ovisi o
            ponderima.
          </p>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-hairline text-muted">
                  <th scope="col" className="py-1.5 pr-2 text-left font-medium">Skup</th>
                  {doc.pokazatelji.map((p) => (
                    <th key={p.oznaka} scope="col" className="py-1.5 pl-2 text-right font-medium" title={p.naziv}>
                      {p.oznaka}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(doc.scenariji).map(([name, w]) => (
                  <tr key={name} className="border-b border-hairline">
                    <th scope="row" className="py-1.5 pr-2 text-left font-medium">{SET_NAMES[name] ?? name}</th>
                    {doc.pokazatelji.map((p) => (
                      <td key={p.oznaka} className="tabular py-1.5 pl-2 text-right text-ink-2">
                        {num(w[p.oznaka] ?? 0, Number.isInteger(w[p.oznaka]) ? 0 : 1)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-muted">
            Ponderi u postocima; osnovni skup ({weights.join(' / ')}) daje ocjenu na karti.
          </p>
        </div>
      </div>
      <p className="mt-4 text-sm text-ink-2">
        {doc.skupine.opis} Razredi veličine (broj stanovnika):{' '}
        {doc.skupine.razredi.map((r) => r.replace(/(?<=\d)-(?=\d)/g, '–')).join(', ')}.
      </p>

      {/* formulas and accounts, folded */}
      <details className="group/k mt-6 rounded-2xl border border-hairline bg-card">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 [&::-webkit-details-marker]:hidden">
          <span className="font-medium">Formule, pragovi i konta</span>
          <ChevronDown className="h-4 w-4 shrink-0 text-muted transition-transform group-open/k:rotate-180" aria-hidden />
        </summary>
        <div className="px-5 pb-5">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-hairline text-left text-xs text-muted">
                  <th scope="col" className="py-2 pr-3 font-medium">Pokazatelj</th>
                  <th scope="col" className="py-2 pr-3 font-medium">Formula</th>
                  <th scope="col" className="py-2 pr-3 text-right font-medium">Ponder</th>
                  <th scope="col" className="py-2 font-medium">Pragovi (vrijednost → bodovi)</th>
                </tr>
              </thead>
              <tbody>
                {doc.pokazatelji.map((p) => (
                  <tr key={p.oznaka} className="border-b border-hairline align-top">
                    <th scope="row" className="py-2.5 pr-3 text-left font-medium">
                      {p.oznaka} · {p.naziv}
                    </th>
                    <td className="py-2.5 pr-3 font-mono text-xs text-ink-2">{p.formula}</td>
                    <td className="tabular py-2.5 pr-3 text-right">{p.ponder}</td>
                    <td className="tabular py-2.5 text-xs text-ink-2">
                      {p.pragovi.map((t) => `${valueLabel(p.oznaka, t.vrijednost)} → ${t.bodovi}`).join(' · ')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h4 className="mt-5 text-xs font-semibold tracking-wide text-muted uppercase">Pomoćne veličine (konta PR-RAS-a i Bilance)</h4>
          <dl className="mt-2 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
            {doc.velicine.map((v) => {
              // "6 − KP (tekući prihodi)" -> name "tekući prihodi", formula "6 − KP"
              const m = /^(.*?)\s*\(([^()]+)\)$/.exec(v.formula)
              const [name, formula] = m && !/\d/.test(m[2]) ? [m[2], m[1]] : [null, v.formula]
              return (
                <div key={v.oznaka}>
                  <dt className="font-medium">
                    {v.oznaka}
                    {name && <span className="font-normal text-ink-2"> · {name}</span>}
                  </dt>
                  <dd className="text-xs text-ink-2">{formula}</dd>
                </div>
              )
            })}
          </dl>
        </div>
      </details>
    </div>
  )
}
