import { ExternalLink } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { Card, Eyebrow } from '../components/Layout'
import { loadDatasets, loadMethodology, type Dataset, type MethodologyDoc } from '../lib/data'
import { GRADES, num } from '../lib/format'

const REPO = 'https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026'
const SECTIONS = [
  ['pokazatelji', 'Pokazatelji'],
  ['pravila', 'Pravila i zastavice'],
  ['ai', 'AI objašnjenje'],
  ['simulator', 'Simulator i Karta reforme'],
  ['podaci', 'Podaci'],
  ['ogranicenja', 'Ograničenja'],
] as const

const threshold = (key: string, v: number) => (key === 'I3' ? `${num(v, 0)} god.` : `${num(v * 100, v * 100 < 1 ? 1 : 0)} %`)
const day = (iso?: string | null) => (iso ? new Date(iso).toLocaleDateString('hr-HR') : '–')
const link = 'underline decoration-axis underline-offset-4 hover:decoration-ink'

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24">
      <h2 className="mt-12 font-serif text-2xl font-semibold tracking-tight">{title}</h2>
      {children}
    </section>
  )
}

// The page reads metodologija.json, which publish.py builds from the code (pipeline/metodologija.py),
// so thresholds, weights, rules and the prompt shown here are the ones the computation uses.
export function Methodology() {
  const [doc, setDoc] = useState<MethodologyDoc | null>(null)
  const [sets, setSets] = useState<Dataset[] | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    Promise.all([loadMethodology(), loadDatasets()])
      .then(([d, s]) => {
        setDoc(d)
        setSets(s)
      })
      .catch(() => setFailed(true))
  }, [])

  const used = (sets ?? []).filter((s) => s.koristi_se)
  const ckan = used.find((s) => s.kljuc === 'ckan_package_search')

  return (
    <main className="mx-auto max-w-4xl px-6 pt-10">
      <Eyebrow>Metodologija i podaci</Eyebrow>
      <h1 className="mt-2 font-serif text-4xl font-semibold tracking-tight">Kako se računa ocjena</h1>
      <p className="mt-4 text-lg leading-relaxed text-ink-2">
        Ocjena mjeri financijsku stabilnost proračuna jedinice: koliko tekući prihodi pokrivaju rashode, koliko je dug
        opterećenje i plaća li jedinica račune na vrijeme. Ne mjeri kvalitetu usluga ni razvijenost. Sve na ovoj stranici
        čita se iz istog koda koji računa ocjene.
      </p>
      <nav aria-label="Sadržaj stranice" className="mt-6 flex flex-wrap gap-2">
        {SECTIONS.map(([id, label]) => (
          <a key={id} href={`#/metodologija`} onClick={(e) => {
            e.preventDefault()
            document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
          }} className="rounded-full border border-hairline px-3 py-1 text-sm hover:border-ink">
            {label}
          </a>
        ))}
      </nav>

      {failed && <p className="mt-8 text-ink-2">Podaci o metodologiji nisu se učitali. Osvježi stranicu.</p>}
      {!doc && !failed && <p className="mt-8 text-muted">Učitavam…</p>}

      {doc && (
        <>
          <Section id="pokazatelji" title="Pet pokazatelja">
            <p className="mt-3 leading-relaxed text-ink-2">
              Svaki pokazatelj pretvara se u 0–100 bodova linearnom interpolacijom između pragova (KDZ, Austrija; INEKO,
              Slovačka). Ukupni bodovi su ponderirani zbroj, a ocjena 5–1 slijedi iz bodova. {doc.prozor.opis}
            </p>
            <div className="mt-4 overflow-x-auto">
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
                        {p.pragovi.map((t) => `${threshold(p.oznaka, t.vrijednost)} → ${t.bodovi}`).join(' · ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-6 grid gap-6 md:grid-cols-2">
              <Card>
                <Eyebrow>Pomoćne veličine (konta PR-RAS i Bilance)</Eyebrow>
                <dl className="mt-3 space-y-2 text-sm">
                  {doc.velicine.map((v) => (
                    <div key={v.oznaka}>
                      <dt className="font-medium">{v.oznaka}</dt>
                      <dd className="text-ink-2">{v.formula}</dd>
                    </div>
                  ))}
                </dl>
              </Card>
              <Card>
                <Eyebrow>Ljestvica</Eyebrow>
                <ul className="mt-3 space-y-2">
                  {doc.ocjene.map((g, i) => {
                    const meta = GRADES.find((x) => x.value === g.ocjena)
                    return (
                      <li key={g.ocjena} className="flex items-center gap-3 text-sm">
                        <span className="h-4 w-7 rounded" style={{ background: meta?.color, boxShadow: 'inset 0 0 0 1px rgb(0 0 0 / 0.12)' }} aria-hidden />
                        <strong className="w-3">{g.ocjena}</strong>
                        <span className="flex-1">{g.rijec}</span>
                        <span className="tabular text-muted">
                          {g.od_bodova}–{i === 0 ? 100 : doc.ocjene[i - 1].od_bodova} bodova
                        </span>
                      </li>
                    )
                  })}
                </ul>
                <p className="mt-4 text-sm text-ink-2">
                  Ocjena se računa i u četiri scenarija pondera ({Object.keys(doc.scenariji).join(', ')}). Ako je ista u svima,
                  na svjedodžbi piše da je stabilna.
                </p>
              </Card>
            </div>
            <p className="mt-4 text-sm text-ink-2">{doc.skupine.opis} Razredi veličine: {doc.skupine.razredi.join(', ')}.</p>
          </Section>

          <Section id="pravila" title="Pravila i zastavice">
            <ul className="mt-3 space-y-3">
              {doc.pravila.map((r) => (
                <li key={r.oznaka} className="text-ink-2">
                  <strong className="font-semibold text-ink">{r.oznaka.charAt(0).toUpperCase() + r.oznaka.slice(1)}.</strong> {r.tekst}
                </li>
              ))}
            </ul>
            <p className="mt-5 text-sm text-muted">Crvene zastavice ne ulaze u bodove; upozoravaju na:</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink-2">
              {doc.zastavice.map((z) => (
                <li key={z.oznaka}>
                  {z.oznaka}: {z.tekst}
                </li>
              ))}
            </ul>
          </Section>

          <Section id="ai" title="AI objašnjenje i provjera brojki">
            <p className="mt-3 leading-relaxed text-ink-2">{doc.ai.opis}</p>
            <p className="mt-3 text-sm text-ink-2">
              Model: {doc.ai.model}.
              {doc.ai.batch &&
                ` AI tekst ima ${num(doc.ai.batch.ai)} od ${num(doc.ai.batch.jedinica)} jedinica; ostale imaju predložak s oznakom.`}{' '}
              Na svjedodžbi je svaka brojka u tekstu označena: pokazuje činjenicu iz koje dolazi, a brojka sastavnice vodi na
              konta i retke u datotekama Ministarstva financija.
            </p>
            <details className="mt-4 rounded-xl border border-hairline bg-card p-4">
              <summary className="cursor-pointer text-sm font-medium">Prompt modela (javno)</summary>
              <pre className="mt-3 overflow-x-auto text-xs leading-relaxed whitespace-pre-wrap text-ink-2">
                {`SUSTAV:\n${doc.ai.sustav}\n\n${doc.ai.pravila}\n\n${doc.ai.primjer}`}
              </pre>
              <p className="mt-2 font-mono text-xs break-all text-muted">sha256 prompta: {doc.ai.prompt_sha256}</p>
            </details>
            <p className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm">
              <a className={link} href={doc.ai.kod.prompt}>Prompt (explain.py)</a>
              <a className={link} href={doc.ai.kod.provjera}>Provjera (verify.py)</a>
              <a className={link} href={doc.ai.kod.cinjenice}>Paket činjenica (facts.py)</a>
              <a className={link} href={doc.ai.kod.biljeznica}>Kaggle bilježnica</a>
            </p>
          </Section>

          <Section id="simulator" title="Simulator spajanja i Karta reforme">
            <ul className="mt-3 space-y-3 text-ink-2">
              <li>
                <strong className="font-semibold text-ink">Spajanje.</strong> Tokovi i stanja članica zbrajaju se po godini, a
                ocjena se računa istom metodom. Pravilo 1 primjenjuje se po članici prije zbrajanja; spojena jedinica je grad
                ako je barem jedna članica grad.
              </li>
              <li>
                <strong className="font-semibold text-ink">Ušteda.</strong> {doc.simulator.usteda}
              </li>
              <li>
                <strong className="font-semibold text-ink">Izravnanje.</strong> {doc.simulator.izravnanje}
              </li>
              <li>
                <strong className="font-semibold text-ink">Karta reforme.</strong> {doc.simulator.reforma}
              </li>
            </ul>
          </Section>

          <Section id="podaci" title="Podaci">
            {ckan && (
              <p className="mt-3 inline-flex items-center gap-2 rounded-full bg-card px-3 py-1.5 text-sm shadow-sm ring-1 ring-hairline">
                Povučeno s data.gov.hr API-ja (CKAN) {day(ckan.zadnje_preuzimanje)}
              </p>
            )}
            <p className="mt-3 text-sm text-ink-2">
              Svaki skup se preuzima automatski; vrijeme, ETag i sha256 svakog preuzimanja su u{' '}
              <a className={link} href="./api/v1/izvori.json">zapisu izvora</a>.
            </p>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[720px] text-sm">
                <thead>
                  <tr className="border-b border-hairline text-left text-xs text-muted">
                    <th scope="col" className="py-2 pr-3 font-medium">Skup podataka</th>
                    <th scope="col" className="py-2 pr-3 font-medium">Izdavatelj</th>
                    <th scope="col" className="py-2 pr-3 font-medium">Pristup</th>
                    <th scope="col" className="py-2 pr-3 font-medium">Licenca</th>
                    <th scope="col" className="py-2 font-medium">Preuzeto</th>
                  </tr>
                </thead>
                <tbody>
                  {used.map((s) => (
                    <tr key={s.kljuc} className="border-b border-hairline align-top">
                      <td className="py-2.5 pr-3">
                        <a className={link} href={s.portal_url || s.url}>
                          {s.naziv}
                        </a>
                        <div className="mt-0.5 text-xs text-muted">{s.uloga}</div>
                      </td>
                      <td className="py-2.5 pr-3 text-ink-2">{s.izdavatelj}</td>
                      <td className="py-2.5 pr-3 text-ink-2">{s.pristup}</td>
                      <td className="py-2.5 pr-3 text-xs text-ink-2">
                        {s.licenca_url ? (
                          <a className={link} href={s.licenca_url}>
                            {s.licenca}
                          </a>
                        ) : (
                          s.licenca
                        )}
                      </td>
                      <td className="tabular py-2.5 text-xs whitespace-nowrap text-ink-2">{day(s.zadnje_preuzimanje)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-4 text-sm text-ink-2">
              Otvoreni izlaz:{' '}
              <a className={link} href="./api/v1/openapi.json">
                API (OpenAPI 3.1)
              </a>
              ,{' '}
              <a className={link} href="./api/v1/rezultati.csv">
                svi rezultati (CSV)
              </a>
              ,{' '}
              <a className={link} href="./api/v1/metodologija.json">
                metodologija (JSON)
              </a>
              . Kod je na{' '}
              <a className={`${link} inline-flex items-center gap-1`} href={REPO}>
                GitHubu <ExternalLink className="h-3.5 w-3.5" aria-hidden />
              </a>{' '}
              (EUPL-1.2), a podaci pod CC BY 4.0. U izradi koda korišten je Claude Code kao razvojni alat; u proizvodu se
              koristi samo model otvorenog koda (Gemma 4).
            </p>
          </Section>

          <Section id="ogranicenja" title="Ograničenja">
            <ul className="mt-3 list-disc space-y-2 pl-5 text-ink-2">
              {doc.ogranicenja.map((o) => (
                <li key={o}>{o}</li>
              ))}
            </ul>
          </Section>
        </>
      )}
    </main>
  )
}
