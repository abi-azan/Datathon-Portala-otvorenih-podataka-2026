import { useMemo, useState } from 'react'
import type { UnitIndex, Vrsta } from '../lib/data'
import { VRSTA, num } from '../lib/format'
import { unitHref } from '../lib/router'
import type { ContextView } from '../lib/views'
import { GradeChip } from './Grade'

const short = (naziv: string) => naziv.replace(/^(Općina|Grad) /, '')
// Croatian plural: 2, 3, 4, 22... jedinice; 1, 5-20, 21... jedinica
const units2_4 = (n: number) => n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14)

/** Table alternative to the map (PLAN §6 UX, decision O5): alphabetical, filtered by county and
 * type, and ranked only inside the peer group, so it never reads as a national ranking. */
export function UnitTable({ units, year, ctx }: { units: UnitIndex[]; year: string; ctx: ContextView | undefined }) {
  const [zup, setZup] = useState('')
  const [vrsta, setVrsta] = useState<'' | Vrsta>('')

  const counties = useMemo(
    () => [...new Set(units.filter((u) => u.vrsta !== 'zupanija').map((u) => u.zupanija))].sort((a, b) => a.localeCompare(b, 'hr')),
    [units],
  )

  // rank in the peer group by points of the year, ties share the better rank (as in the build)
  const rank = useMemo(() => {
    const groups = new Map<string, number[]>()
    for (const u of units) {
      const b = u.bodovi[year]
      if (b != null) groups.set(u.skupina, [...(groups.get(u.skupina) ?? []), b])
    }
    const out = new Map<string, { r: number; n: number }>()
    for (const u of units) {
      const b = u.bodovi[year]
      const g = groups.get(u.skupina)
      if (b == null || !g || g.length < 2) continue
      out.set(u.sifra, { r: 1 + g.filter((x) => x > b).length, n: g.length })
    }
    return out
  }, [units, year])

  const rows = useMemo(
    () =>
      units
        .filter((u) => (!zup || u.zupanija === zup) && (!vrsta || u.vrsta === vrsta))
        .sort((a, b) => short(a.naziv).localeCompare(short(b.naziv), 'hr')),
    [units, zup, vrsta],
  )

  const select = 'rounded-lg border border-axis bg-card px-2.5 py-1.5 text-sm'
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-hairline bg-card">
      <div className="flex flex-wrap items-center gap-2 border-b border-hairline p-3">
        <label className="sr-only" htmlFor="tablica-zupanija">
          Županija
        </label>
        <select id="tablica-zupanija" value={zup} onChange={(e) => setZup(e.target.value)} className={select}>
          <option value="">Sve županije</option>
          {counties.map((z) => (
            <option key={z} value={z}>
              {z}
            </option>
          ))}
        </select>
        <label className="sr-only" htmlFor="tablica-vrsta">
          Vrsta jedinice
        </label>
        <select id="tablica-vrsta" value={vrsta} onChange={(e) => setVrsta(e.target.value as '' | Vrsta)} className={select}>
          <option value="">Sve vrste</option>
          <option value="opcina">Općine</option>
          <option value="grad">Gradovi</option>
          <option value="zupanija">Županije</option>
        </select>
        <span className="ml-auto text-xs text-muted" role="status">
          {num(rows.length)} {units2_4(rows.length) ? 'jedinice' : 'jedinica'}, abecedno
        </span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto">
        <table className="w-full text-sm">
          <caption className="sr-only">
            Ocjene za {year}. abecedno; mjesto se navodi samo unutar usporedne skupine
          </caption>
          <thead className="sticky top-0 bg-card">
            <tr className="border-b border-hairline text-left text-xs text-muted">
              <th scope="col" className="px-3 py-2 font-medium">
                Jedinica
              </th>
              <th scope="col" className="px-3 py-2 text-right font-medium">
                Stanovnici
              </th>
              <th scope="col" className="px-3 py-2 font-medium">
                Ocjena {year}.
              </th>
              <th scope="col" className="px-3 py-2 font-medium">
                Mjesto u skupini
              </th>
              {ctx && (
                <th scope="col" className="px-3 py-2 text-right font-medium">
                  {ctx.short}
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {rows.map((u) => {
              const rk = rank.get(u.sifra)
              return (
                <tr key={u.sifra} className="border-b border-hairline align-top last:border-0">
                  <th scope="row" className="px-3 py-2 text-left font-normal">
                    <a href={unitHref(u.slug)} className="font-medium underline decoration-axis underline-offset-4 hover:decoration-ink">
                      {u.naziv}
                    </a>
                    <div className="text-xs text-muted">
                      {VRSTA[u.vrsta]}
                      {u.vrsta !== 'zupanija' && ` · ${u.zupanija}`}
                    </div>
                  </th>
                  <td className="tabular px-3 py-2 text-right">{num(u.stanovnici)}</td>
                  <td className="px-3 py-2">
                    <GradeChip g={u.ocjena[year]} />
                  </td>
                  <td className="px-3 py-2">
                    <span className="tabular">{rk ? `${num(rk.r)}. od ${num(rk.n)}` : '–'}</span>
                    <div className="text-xs text-muted">{u.skupina}</div>
                  </td>
                  {ctx && <td className="tabular px-3 py-2 text-right whitespace-nowrap">{ctx.format(ctx.value(u, year))}</td>}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
