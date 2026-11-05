import { ChevronDown, ExternalLink } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { IndicatorsExplained } from '../components/IndicatorsExplained'
import { Eyebrow } from '../components/Layout'
import { loadDatasets, loadMethodology, type Dataset, type MethodologyDoc } from '../lib/data'
import { num } from '../lib/format'

const REPO = 'https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026'
const SECTIONS = [
  ['pokazatelji', 'Pokazatelji'],
  ['pravila', 'Pravila i upozorenja'],
  ['ai', 'AI objašnjenje'],
  ['simulator', 'Simulator i Karta reforme'],
  ['kontekst', 'Kontekst u pregledu jedinice'],
  ['podaci', 'Podaci'],
  ['ogranicenja', 'Ograničenja'],
] as const

// "pravilo 1/2" are identifiers in metodologija.json (the MCP server looks them up); on screen they get names
const RULE_NAMES: Record<string, string> = {
  'pravilo 1': 'Kredit iskazan kao dospio (pravilo 1)',
  'pravilo 2': 'Ograničenje ocjene zbog dospjelih obveza (pravilo 2)',
}
const day = (iso?: string | null) => (iso ? new Date(iso).toLocaleDateString('hr-HR') : '–')
const link = 'underline decoration-axis underline-offset-4 hover:decoration-ink'

/** One part of the page, folded except the first, so the page reads as a list of seven headings.
 *  The id stays on the element, so the section links and #/metodologija?o=<id> still find it. */
function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <details id={id} open={id === SECTIONS[0][0]} className="group scroll-mt-24 border-b border-hairline">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 rounded py-5 [&::-webkit-details-marker]:hidden">
        <h2 className="font-serif text-2xl font-semibold tracking-tight">{title}</h2>
        <ChevronDown className="h-5 w-5 shrink-0 text-muted transition-transform group-open:rotate-180" aria-hidden />
      </summary>
      <div className="pb-10">{children}</div>
    </details>
  )
}

/** Open a section and bring it into view. */
function openSection(id: string, smooth = true) {
  const el = document.getElementById(id)
  if (!(el instanceof HTMLDetailsElement)) return
  el.open = true
  el.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'start' })
}
const setAll = (open: boolean) =>
  SECTIONS.forEach(([id]) => {
    const el = document.getElementById(id)
    if (el instanceof HTMLDetailsElement) el.open = open
  })

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

  // #/metodologija?o=podaci opens that section once the page has its content
  useEffect(() => {
    if (!doc) return
    const o = new URLSearchParams(window.location.hash.split('?')[1] ?? '').get('o')
    if (o && SECTIONS.some(([id]) => id === o)) requestAnimationFrame(() => openSection(o, false))
  }, [doc])

  const used = (sets ?? []).filter((s) => s.koristi_se)
  const ckan = used.find((s) => s.kljuc === 'ckan_package_search')
  const dzsApi = used.find((s) => s.kljuc === 'dzs_pxweb_sp31_2')

  return (
    <main className="mx-auto max-w-4xl px-6 pt-10">
      <Eyebrow>Metodologija i podaci</Eyebrow>
      <h1 className="mt-2 font-serif text-4xl font-semibold tracking-tight">Kako se računa ocjena</h1>
      <p className="mt-4 text-lg leading-relaxed text-ink-2">
        Ocjena mjeri financijsku održivost proračuna jedinice: koliko tekući prihodi pokrivaju rashode, koliko je dug
        opterećenje i plaća li jedinica račune na vrijeme. Ne mjeri kvalitetu usluga ni razvijenost. Sve na ovoj stranici
        čita se iz istog koda koji računa ocjene.
      </p>
      <nav aria-label="Sadržaj stranice" className="mt-6 flex flex-wrap items-center gap-2">
        {SECTIONS.map(([id, label]) => (
          <a
            key={id}
            href={`#/metodologija?o=${id}`}
            onClick={(e) => {
              e.preventDefault()
              openSection(id)
            }}
            className="rounded-full border border-hairline px-3 py-1 text-sm hover:border-ink"
          >
            {label}
          </a>
        ))}
        <span className="ml-1 flex gap-3 text-sm text-muted">
          <button type="button" onClick={() => setAll(true)} className="underline decoration-axis underline-offset-4 hover:text-ink">
            Otvori sve
          </button>
          <button type="button" onClick={() => setAll(false)} className="underline decoration-axis underline-offset-4 hover:text-ink">
            Zatvori sve
          </button>
        </span>
      </nav>

      {failed && <p className="mt-8 text-ink-2">Podaci o metodologiji nisu se učitali. Osvježi stranicu.</p>}
      {!doc && !failed && <p className="mt-8 text-muted">Učitavam…</p>}

      {doc && (
        <div className="mt-8 border-t border-hairline">
          <Section id="pokazatelji" title="Pet pokazatelja">
            <IndicatorsExplained doc={doc} />
          </Section>

          <Section id="pravila" title="Pravila i upozorenja">
            <ul className="mt-3 space-y-3">
              {doc.pravila.map((r) => (
                <li key={r.oznaka} className="text-ink-2">
                  <strong className="font-semibold text-ink">{RULE_NAMES[r.oznaka] ?? r.oznaka.charAt(0).toUpperCase() + r.oznaka.slice(1)}.</strong> {r.tekst}
                </li>
              ))}
            </ul>
            <p className="mt-5 text-sm text-muted">Upozorenja (Z1–Z4) ne mijenjaju bodove. Prikazuju se za:</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink-2">
              {doc.zastavice.map((z) => (
                <li key={z.oznaka}>
                  {z.oznaka}: {z.tekst}
                </li>
              ))}
            </ul>
            {doc.kriterij_10 &&
              doc.kriterij_10.split(/\n\s*\n/).map((para, i) => (
                <p key={i} className={`${i ? 'mt-2' : 'mt-5'} text-sm leading-relaxed text-ink-2`}>
                  {para}
                </p>
              ))}
          </Section>

          <Section id="ai" title="AI objašnjenje i provjera brojki">
            <p className="mt-3 leading-relaxed text-ink-2">{doc.ai.opis}</p>
            <p className="mt-3 text-sm text-ink-2">
              Model: {doc.ai.model}.
              {doc.ai.batch?.prikazano_ai != null &&
                (doc.ai.batch.prikazano_ai < doc.ai.batch.jedinica
                  ? ` AI tekst je objavljen za ${num(doc.ai.batch.prikazano_ai)} od ${num(doc.ai.batch.jedinica)} jedinica; ostale imaju predložak s oznakom.`
                  : ` AI tekst je objavljen za svih ${num(doc.ai.batch.jedinica)} jedinica.`)}
              {doc.ai.prompt_jednak_batchu === false && ' Prompt se od generiranja promijenio; prikazan je trenutni.'}{' '}
              Na pregledu jedinice je svaka brojka u tekstu označena: pokazuje činjenicu iz koje dolazi, a brojka pokazatelja vodi
              na konta i retke u datotekama Ministarstva financija.
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
              <a className={link} href={doc.ai.kod.cinjenice}>Činjenice (facts.py)</a>
              <a className={link} href={doc.ai.kod.biljeznica}>Kaggle bilježnica</a>
            </p>
          </Section>

          <Section id="simulator" title="Simulator spajanja i Karta reforme">
            <ul className="mt-3 space-y-3 text-ink-2">
              <li>
                <strong className="font-semibold text-ink">Spajanje.</strong> Prihodi, rashodi, dug i novac na računu članica
                zbrajaju se za svaku godinu, a ocjena se računa istom metodom. Pravilo o kreditu iskazanom kao dospio primjenjuje
                se na svaku članicu prije zbrajanja; spojena jedinica je grad ako je barem jedna članica grad.
              </li>
              <li>
                <strong className="font-semibold text-ink">Ušteda.</strong> {doc.simulator.usteda}
              </li>
              <li>
                <strong className="font-semibold text-ink">Izravnanje.</strong> {doc.simulator.izravnanje}
              </li>
              {doc.simulator.poticaj && (
                <li>
                  <strong className="font-semibold text-ink">Poticaj.</strong> {doc.simulator.poticaj}
                </li>
              )}
              <li>
                <strong className="font-semibold text-ink">Karta reforme.</strong> {doc.simulator.reforma}
              </li>
              {doc.simulator.demografija && (
                <li>
                  <strong className="font-semibold text-ink">Stanovništvo.</strong> {doc.simulator.demografija}
                </li>
              )}

            </ul>
          </Section>

          {(doc.stanovnistvo_gospodarstvo || doc.izravnanje_jedinice) && (
            <Section id="kontekst" title="Kontekst u pregledu jedinice">
              <p className="mt-3 text-ink-2">
                Dvije kartice u pregledu jedinice ne ulaze u ocjenu. Daju kontekst uz brojke proračuna. Kad jedinica jako
                odstupa od svoje skupine u broju stanovnika ili dohotku, AI objašnjenje to spominje u zadnjoj rečenici.
              </p>
              {dzsApi && (
                <p className="mt-3 inline-flex items-center gap-2 rounded-full bg-card px-3 py-1.5 text-sm shadow-sm ring-1 ring-hairline">
                  Preuzeto s PxWeb API-ja DZS-a {day(dzsApi.zadnje_preuzimanje)}
                </p>
              )}
              <ul className="mt-3 space-y-3 text-ink-2">
                {doc.stanovnistvo_gospodarstvo && (
                  <li>
                    <strong className="font-semibold text-ink">Stanovništvo i gospodarstvo.</strong> {doc.stanovnistvo_gospodarstvo}
                  </li>
                )}
                {doc.izravnanje_jedinice && (
                  <li>
                    <strong className="font-semibold text-ink">Fiskalno izravnanje.</strong> {doc.izravnanje_jedinice}
                  </li>
                )}
              </ul>
            </Section>
          )}

          <Section id="podaci" title="Podaci">
            {ckan && (
              <p className="mt-3 inline-flex items-center gap-2 rounded-full bg-card px-3 py-1.5 text-sm shadow-sm ring-1 ring-hairline">
                Preuzeto s data.gov.hr API-ja (CKAN) {day(ckan.zadnje_preuzimanje)}
              </p>
            )}
            {doc.revizija && <p className="mt-3 text-sm text-ink-2">{doc.revizija}</p>}
            <p className="mt-3 text-sm text-ink-2">
              Podaci Ministarstva financija, Porezne uprave, DZS-a i Portala otvorenih podataka preuzimaju se automatski pri
              svakoj obradi podataka;
              izvješća revizije i podaci za šifrarnik (DGU, indeks razvijenosti) osvježavaju se ručno. Vrijeme, ETag i sha256
              svakog preuzimanja su u <a className={link} href="./api/v1/izvori.json">zapisu izvora</a>.
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
              Preuzimanje podataka i koda:{' '}
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
              </a>{' '}
              i{' '}
              <a className={link} href="./api/v1/dcat.jsonld">
                katalog skupova u DCAT-AP-u
              </a>
              , koji portal otvorenih podataka može preuzeti. Kod je na{' '}
              <a className={`${link} inline-flex items-center gap-1`} href={REPO}>
                GitHubu <ExternalLink className="h-3.5 w-3.5" aria-hidden />
              </a>{' '}
              (EUPL-1.2), a podaci pod CC BY 4.0. U izradi koda korišten je Claude Code kao razvojni alat. Aplikacija koristi
              samo otvoreni model Gemma 4 (Apache-2.0).
            </p>
          </Section>

          <Section id="ogranicenja" title="Ograničenja">
            <ul className="mt-3 list-disc space-y-2 pl-5 text-ink-2">
              {doc.ogranicenja.map((o) => (
                <li key={o}>{o}</li>
              ))}
            </ul>
          </Section>
        </div>
      )}
    </main>
  )
}
