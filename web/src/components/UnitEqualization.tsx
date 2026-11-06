import type { UnitEqualization } from '../lib/data'
import { eur, num } from '../lib/format'
import { Card, Eyebrow, Fold } from './Layout'

// Self-contained on purpose: the card can be dropped from the profile without touching anything else.

const REFERENCE: Record<UnitEqualization['vrsta_reference'], string> = {
  opcina: 'za općine',
  grad: 'za gradove',
  zupanija: 'za županije',
}

/** 0,2 -> "20 %", 0,215 -> "21,5 %" */
const rate = (x: number | null | undefined) => {
  if (x == null) return '–'
  const p = x * 100
  return `${num(p, Math.abs(p - Math.round(p)) < 1e-9 ? 0 : 1)} %`
}

/** Rounded for the card: 0,1 mil. € from a million up, 10.000 € below it. */
const scale = (ref: number) => (ref >= 1e6 ? 'mil' : 'eur')
const money = (x: number, unit: 'mil' | 'eur', withUnit = true) =>
  unit === 'mil' ? `${num(x / 1e6, 1)}${withUnit ? ' mil. €' : ''}` : `${num(Math.round(x / 1e4) * 1e4)}${withUnit ? ' €' : ''}`

function Bar({ label, value, max, strong }: { label: string; value: number; max: number; strong?: boolean }) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-4 text-sm">
        <span className="text-ink-2">{label}</span>
        <span className="tabular font-medium whitespace-nowrap">{eur(value, 2)}</span>
      </div>
      <div className="mt-1.5 h-2.5 overflow-hidden rounded-full bg-page" aria-hidden>
        <div className={`h-full rounded-full ${strong ? 'bg-ink-2' : 'bg-axis'}`} style={{ width: `${Math.min(100, (value / max) * 100)}%` }} />
      </div>
    </div>
  )
}

/** "Fiskalno izravnanje" (pipeline/kontekst.py equalization): tax capacity per inhabitant against the
 * reference value of the unit's type, and the estimated yearly payout (share of all full amounts x the
 * budget line, as in the merger simulator). The full amount itself is not shown. */
export function UnitEqualizationCard({ e, zagreb }: { e: UnitEqualization; zagreb: boolean }) {
  const below = e.kapacitet_pc < e.referentna_pc
  const max = Math.max(e.kapacitet_pc, e.referentna_pc) * 1.05
  const ref = REFERENCE[e.vrsta_reference]
  const s = e.stopa
  const more = s?.ispod_maksimuma ? e.uz_najvise_stope : null
  const unit = scale(more?.procjena ?? 0)
  return (
    <Card>
      <Eyebrow>Fiskalno izravnanje</Eyebrow>
      <div className="mt-3 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="tabular font-serif text-2xl font-semibold">{eur(e.isplata)}</span>
        <span className="text-sm text-ink-2">{e.isplata > 0 ? 'godišnje, procjena isplate' : 'jedinica ne prima izravnanje'}</span>
      </div>
      <div className="mt-4 space-y-3">
        <Bar label="Porezni kapacitet po stanovniku" value={e.kapacitet_pc} max={max} strong />
        <Bar label={`Referentna vrijednost ${ref}`} value={e.referentna_pc} max={max} />
      </div>
      <p className="mt-3 text-sm leading-relaxed text-ink-2">
        {below
          ? `Kapacitet je ispod referentne vrijednosti ${ref}, pa jedinica prima izravnanje: država joj iz proračuna nadoknađuje dio razlike.`
          : `Kapacitet je iznad referentne vrijednosti ${ref}, pa jedinica izravnanje ne prima.`}
        {zagreb && ' Grad Zagreb ne ulazi u izračun referentnih vrijednosti, nego se mjeri s gradovima.'}
      </p>
      {s?.ispod_maksimuma && (
        <p className="mt-3 rounded-xl bg-page p-3 text-sm leading-relaxed text-ink-2">
          <strong className="font-semibold text-ink">Stope poreza na dohodak ispod najviših:</strong>{' '}
          <span className="tabular">
            {rate(s.niza)} i {rate(s.visa)} (dopušteno do {rate(s.niza_max)} i {rate(s.visa_max)}).
          </span>
          {more && more.procjena >= 5000 && (
            <>
              {' '}
              Uz najviše stope proračun bi imao oko {money(more.procjena, unit)} godišnje više
              {money(more.od, unit) !== money(more.do, unit) && (
                <span className="tabular whitespace-nowrap">
                  {' '}
                  ({money(more.od, unit, false)}–{money(more.do, unit)})
                </span>
              )}
              .
            </>
          )}{' '}
          Stope određuje vijeće, a izravnanje razliku ne nadoknađuje.
        </p>
      )}
      <Fold>
      <p className="text-xs leading-relaxed text-muted">
        Zakon o financiranju jedinica lokalne i područne (regionalne) samouprave, čl. 8. i 9. Isplata = iznos u državnom
        proračunu ({eur(e.iznos_proracuna)} za {e.proracun_godina}.; za {e.godina}. još nije utvrđen, pa se uzima isti) × udio
        jedinice u zbroju punih iznosa svih jedinica. Puni iznos je (referentna vrijednost − kapacitet) × broj stanovnika.
        Kapacitet i referentne vrijednosti iz tablice Ministarstva financija za{' '}
        {e.godina}.{s ? ` Stope: Porezna uprava, odluke jedinica za ${s.godina}.` : ''}
        {more &&
          ` Procjena iz poreza stanovnika ${more.godina_poreza}. (Porezna uprava), samo dohodak na koji se plaća lokalna stopa.`}
      </p>
      </Fold>
    </Card>
  )
}
