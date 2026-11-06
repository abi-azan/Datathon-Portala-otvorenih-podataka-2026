import { ExternalLink, Radio } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { Dataset } from '../lib/data'
import { num } from '../lib/format'
import { CATALOGUE_URL, liveCatalogue, livePxTable, liveWfsCount, wfsHitsUrl, type ApiCheck } from '../lib/portal'

const day = (iso?: string | null) => (iso ? new Date(iso).toLocaleDateString('hr-HR') : null)
const link = 'underline decoration-axis underline-offset-4 hover:decoration-ink'

interface Row {
  key: string
  name: string
  api: string
  what: string
  /** the address the browser asks, also the "otvori poziv" link */
  call: string
  ask: () => Promise<ApiCheck | null>
  /** the answer in words */
  say: (value: number) => string
  /** when the build last read this API */
  fetched?: string | null
}

/** The public APIs the build reads, each asked once more from the reader's browser when the panel comes
 *  into view (lib/portal.ts), so the page shows that they answer today and what they say. The counts in
 *  the first sentence come from skupovi.json. A service that does not answer is said so, with the day
 *  of the build's last download. */
export function ApiPanel({ sets }: { sets: Dataset[] }) {
  const by = (kljuc: string) => sets.find((s) => s.kljuc === kljuc)
  const api = sets.filter((s) => s.pristup.startsWith('API'))
  const files = sets.filter((s) => s.pristup.startsWith('datoteka'))
  const px = sets.filter((s) => s.pristup === 'API (PxWeb)')
  const ckan = by('ckan_package_search')
  const pxMain = by('dzs_pxweb_sp31_2')
  const borders = by('dzs_wfs_granice')

  const rows: Row[] = []
  if (ckan)
    rows.push({
      key: 'ckan',
      name: 'Portal otvorenih podataka',
      api: 'CKAN API · package_search, package_show',
      what: 'Katalog svih skupova na Portalu, iz kojeg nastaje kartica „Otvoreni podaci jedinice”. Preko istog API-ja pri svakoj obradi nalazimo najnovije tablice Porezne uprave.',
      call: CATALOGUE_URL,
      ask: liveCatalogue,
      say: (v) => `${num(v)} skupova u katalogu`,
      fetched: ckan.zadnje_preuzimanje,
    })
  if (pxMain)
    rows.push({
      key: 'pxweb',
      name: 'Državni zavod za statistiku',
      api: `PxWeb API · ${px.length} tablica`,
      what: 'Po općinama i gradovima: procjena stanovništva, doseljeni i odseljeni, rođeni, umrli, noćenja turista i građevinske dozvole. Broj stanovnika pregled jedinice traži i uživo.',
      call: pxMain.url,
      ask: () => livePxTable(pxMain.url),
      say: (v) => `procjena stanovništva do ${v}. godine`,
      fetched: pxMain.zadnje_preuzimanje,
    })
  if (borders)
    rows.push({
      key: 'wfs',
      name: 'Državni zavod za statistiku i NIPP',
      api: 'INSPIRE WFS (OGC) · 2 sloja',
      what: 'Granice i službena površina općina i gradova te stanovništvo iz Popisa 2021. Iz granica nastaju karta, susjedi i otoci.',
      call: wfsHitsUrl(borders.url),
      ask: () => liveWfsCount(borders.url),
      say: (v) => `${num(v)} općina i gradova u sloju granica`,
      fetched: borders.zadnje_preuzimanje,
    })

  // undefined: not asked or no answer yet; null: asked, no answer
  const [answers, setAnswers] = useState<Record<string, ApiCheck | null | undefined>>({})
  const box = useRef<HTMLDivElement>(null)
  const asked = useRef(false)
  const calls = rows.map((r) => r.call).join('|')
  useEffect(() => {
    const el = box.current
    if (!el || !rows.length) return
    let alive = true
    const ask = () => {
      if (asked.current) return
      asked.current = true
      for (const r of rows) r.ask().then((a) => alive && setAnswers((s) => ({ ...s, [r.key]: a })))
    }
    // the panel sits in a folded section: ask when it is opened and seen, not when the page loads
    const io =
      typeof IntersectionObserver === 'undefined'
        ? null
        : new IntersectionObserver((entries) => entries.some((e) => e.isIntersecting) && ask())
    if (io) io.observe(el)
    else ask()
    return () => {
      alive = false
      io?.disconnect()
    }
    // rows are rebuilt on every render; their addresses say when they really changed
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [calls])

  if (!rows.length) return null
  return (
    <div ref={box} className="mt-4 rounded-xl border border-hairline bg-card p-4 sm:p-5">
      <h3 className="font-semibold">Podaci preko API-ja</h3>
      <p className="mt-1 text-sm text-ink-2">
        Od {num(api.length + files.length)} izvora podataka {num(api.length)} čitamo izravno preko API-ja tijela javnog sektora.
        To su tri servisa, a tvoj preglednik ih upravo pita odgovaraju li.
      </p>
      <ul className="mt-3 divide-y divide-hairline">
        {rows.map((r) => {
          const a = answers[r.key]
          return (
            <li key={r.key} className="grid gap-x-5 gap-y-1.5 py-3 sm:grid-cols-[1fr_auto]">
              <div>
                <div className="font-medium">{r.name}</div>
                <div className="text-xs text-muted">{r.api}</div>
              </div>
              <div className="sm:text-right">
                <span
                  aria-live="polite"
                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs ${a ? 'bg-page text-ink' : 'text-muted'}`}
                >
                  {a && <Radio className="h-3.5 w-3.5 shrink-0" aria-hidden />}
                  {a ? `uživo: ${r.say(a.value)}` : a === null ? 'trenutno ne odgovara' : 'pitam…'}
                </span>
              </div>
              <p className="text-sm text-ink-2 sm:col-span-2">
                {r.what}{' '}
                <span className="whitespace-nowrap text-muted">
                  {day(r.fetched) && `Zadnja obrada: ${day(r.fetched)} `}
                  <a className={`inline-flex items-center gap-1 ${link}`} href={r.call} target="_blank" rel="noreferrer">
                    otvori poziv <ExternalLink className="h-3 w-3" aria-hidden />
                  </a>
                </span>
              </p>
            </li>
          )
        })}
      </ul>
      <p className="border-t border-hairline pt-3 text-sm text-ink-2">
        Preostali izvori ({num(files.length)}) su datoteke. Financijske izvještaje jedinica Ministarstvo financija objavljuje samo
        kao Excel tablice na svojim stranicama, bez API-ja, a izvješća Državnog ureda za reviziju su PDF. Tablice Porezne
        uprave preuzimamo s Portala.
      </p>
    </div>
  )
}
