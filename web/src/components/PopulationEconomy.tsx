import { Radio } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { ContextIndicator, PopulationEconomy } from '../lib/data'
import { liveSeries } from '../lib/dzs'
import { eur, num, pct } from '../lib/format'
import { Card, Eyebrow } from './Layout'
import { StatRow } from './StatRow'

const MINUS = '−'
/** +6,2 % / −8,2 with a real minus sign */
const signed = (s: string, x: number) => (x > 0 ? `+${s}` : x < 0 ? `${MINUS}${s.replace(/^[-−]/, '')}` : s)
const sPct = (x: number | null | undefined, digits = 1) => (x == null ? '–' : signed(pct(Math.abs(x), digits), x))
const sNum = (x: number | null | undefined, digits = 1) => (x == null ? '–' : signed(num(Math.abs(x), digits), x))
const day = (iso: string | null | undefined) => (iso ? new Date(iso).toLocaleDateString('hr-HR') : null)

/** Croatian plural of "zgrada" after a number: 1 zgrada, 2 zgrade, 5 zgrada. */
const buildings = (n: number) => {
  const d = n % 10,
    h = n % 100
  return d >= 2 && d <= 4 && (h < 12 || h > 14) ? 'zgrade' : 'zgrada'
}

/** Value text under the DZS symbol rule: "-" (none) reads "nema", "z" (confidential) "podatak nije javan". */
function shown(i: ContextIndicator, format: (x: number) => string) {
  if (i.oznaka === 'z' || (i.vrijednost == null && i.oznaka !== '-')) return i.oznaka === 'z' ? 'podatak nije javan' : '–'
  if (i.oznaka === '-') return 'nema'
  return format(i.vrijednost as number)
}

function Sparkline({ points, label }: { points: [string, number][]; label: string }) {
  if (points.length < 2) return null
  const w = 112,
    h = 32,
    pad = 3
  const vs = points.map((p) => p[1])
  const lo = Math.min(...vs),
    hi = Math.max(...vs)
  const x = (i: number) => pad + (i * (w - 2 * pad)) / (points.length - 1)
  const y = (v: number) => (hi === lo ? h / 2 : h - pad - ((v - lo) * (h - 2 * pad)) / (hi - lo))
  const d = points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p[1]).toFixed(1)}`).join(' ')
  const last = points.length - 1
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} role="img" aria-label={label} className="shrink-0 text-ink-2">
      <path d={d} fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={x(0)} cy={y(points[0][1])} r={2.25} fill="var(--color-card)" stroke="currentColor" strokeWidth={1.5} />
      <circle cx={x(last)} cy={y(points[last][1])} r={2.75} fill="currentColor" />
    </svg>
  )
}

/** "Stanovništvo i gospodarstvo": context that does not enter the score (pipeline/kontekst.py).
 * Per-capita figures use Popis 2021; the population estimates only give the trend, and the
 * browser asks DZS for them live (lib/dzs.ts), keeping the static copy when that fails. */
export function PopulationEconomyCard({ data }: { data: PopulationEconomy }) {
  const [live, setLive] = useState<Record<string, number | null> | null>(null)
  useEffect(() => {
    if (!data.uzivo) return
    let alive = true
    liveSeries(data.uzivo).then((s) => alive && s && setLive(s.values))
    return () => {
      alive = false
    }
  }, [data.uzivo])

  const p = data.pokazatelji
  const first = p.promjena_stanovnistva.od_godine ?? 2021
  const fromStatic = Object.entries(data.procjene).filter((e): e is [string, number] => e[1] != null)
  const fromLive = live ? Object.entries(live).filter((e): e is [string, number] => e[1] != null && Number(e[0]) >= first) : []
  const isLive = fromLive.length >= 2 && fromLive.some(([y]) => Number(y) === first)
  const series = (isLive ? fromLive : fromStatic).sort((a, b) => Number(a[0]) - Number(b[0]))
  const [y0, v0] = series[0] ?? [String(first), null]
  const [y1, v1] = series[series.length - 1] ?? [String(p.promjena_stanovnistva.godina), null]
  const change = v0 && v1 != null ? v1 / v0 - 1 : null
  const med = (x: number | null, f: (v: number) => string) => (x == null ? undefined : f(x))

  const dzs = data.izvori.filter((s) => s.tablica)
  const updated = (t: string) => day(dzs.find((s) => s.tablica === t)?.azurirano)
  const pu = data.izvori.find((s) => !s.tablica)
  const nights = p.nocenja_po_stanovniku
  const permits = p.dozvole_na_1000

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <Eyebrow>Stanovništvo i gospodarstvo</Eyebrow>
        {isLive && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-page px-2.5 py-1 text-xs whitespace-nowrap text-ink-2">
            <Radio className="h-3.5 w-3.5 shrink-0" aria-hidden /> uživo s API-ja DZS-a
          </span>
        )}
      </div>
      <p className="mt-1 text-xs text-muted">Ne ulazi u ocjenu.</p>

      <div className="mt-4 flex items-center justify-between gap-4">
        <div>
          <div className="text-sm text-ink-2">Broj stanovnika</div>
          <div className="mt-0.5 flex flex-wrap items-baseline gap-x-2">
            <span className="tabular font-serif text-2xl font-semibold">{sPct(change)}</span>
            <span className="text-sm text-ink-2">od {y0}.</span>
          </div>
          <div className="tabular mt-0.5 text-sm text-ink-2">
            {num(v1)} u {y1}.
          </div>
          {p.promjena_stanovnistva.medijan != null && (
            <div className="tabular text-xs text-muted">
              medijan <span className="hidden sm:inline">usporedne skupine </span>
              <span className="whitespace-nowrap">{sPct(p.promjena_stanovnistva.medijan)}</span>
            </div>
          )}
        </div>
        <Sparkline
          points={series}
          label={`Broj stanovnika od ${y0}. do ${y1}.: ${series.map(([y, v]) => `${y}. ${num(v)}`).join(', ')}`}
        />
      </div>

      <dl className="mt-4 space-y-3 border-t border-hairline pt-3 text-sm">
        <StatRow
          label={`Prirodni prirast na 1.000 stanovnika (${p.prirodni_prirast.godina}.)`}
          hint={p.prirodni_prirast.broj != null ? `Rođeni minus umrli: ${sNum(p.prirodni_prirast.broj, 0)}.` : undefined}
          value={shown(p.prirodni_prirast, (x) => sNum(x))}
          median={med(p.prirodni_prirast.medijan, (x) => sNum(x))}
        />
        <StatRow
          label={`Neto migracija na 1.000 stanovnika (${p.neto_migracija.godina}.)`}
          hint={p.neto_migracija.broj != null ? `Doseljeni minus odseljeni: ${sNum(p.neto_migracija.broj, 0)}.` : undefined}
          value={shown(p.neto_migracija, (x) => sNum(x))}
          median={med(p.neto_migracija.medijan, (x) => sNum(x))}
        />
        <StatRow
          label={`Noćenja turista po stanovniku (${nights.godina}.)`}
          hint={
            nights.oznaka === 'z'
              ? 'DZS ga ne objavljuje radi zaštite povjerljivosti.'
              : nights.oznaka === '-'
                ? 'Nema komercijalnog smještaja.'
                : nights.broj != null
                  ? `${num(nights.broj)} noćenja u komercijalnom smještaju.`
                  : undefined
          }
          value={shown(nights, (x) => num(x, x < 10 ? 1 : 0))}
          median={med(nights.medijan, (x) => num(x, x < 10 ? 1 : 0))}
        />
        <StatRow
          label={`Građevinske dozvole na 1.000 stanovnika (${permits.godina}.)`}
          hint={
            permits.oznaka === '-'
              ? 'Nije izdana nijedna dozvola za novu zgradu.'
              : permits.broj != null
                ? `${num(permits.broj)} ${buildings(permits.broj)} s izdanom dozvolom.`
                : undefined
          }
          value={shown(permits, (x) => num(x, 1))}
          median={med(permits.medijan, (x) => num(x, 1))}
        />
        <StatRow
          label={`Neto dohodak po stanovniku (${p.neto_dohodak_pc.godina}.)`}
          hint="Dohodak stanovnika po prebivalištu, nakon poreza i doprinosa."
          value={eur(p.neto_dohodak_pc.vrijednost)}
          median={med(p.neto_dohodak_pc.medijan, (x) => eur(x))}
        />
        <StatRow
          label="Udio mirovina u dohotku"
          value={pct(p.udio_mirovina.vrijednost)}
          median={med(p.udio_mirovina.medijan, (x) => pct(x))}
        />
      </dl>

      <p className="mt-4 text-xs leading-relaxed text-muted">
        Izvor: Državni zavod za statistiku, PxWeb (stanovništvo{updated('SP31_2') && `, ažurirano ${updated('SP31_2')}`}; turizam u
        komercijalnom smještaju{updated('BS_TU19') && `, ${updated('BS_TU19')}`}; građevinske dozvole
        {updated('PX14') && `, ${updated('PX14')}`}) i Porezna uprava (neto dohodak stanovništva{pu?.azurirano && `, ${day(pu.azurirano)}`}).
        Iznosi po stanovniku računaju se s Popisom 2021.
        {data.skupina ? ` Medijan je za usporednu skupinu „${data.skupina}”.` : ' Grad Zagreb nema usporedne skupine.'}
      </p>
    </Card>
  )
}
