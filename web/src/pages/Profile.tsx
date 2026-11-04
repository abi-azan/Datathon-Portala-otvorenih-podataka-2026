import { AlertTriangle, ArrowLeft, ArrowRight, CheckCircle2, ExternalLink, Info, MapPin, ShieldCheck, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { GradeChip } from '../components/Grade'
import { Card, Eyebrow } from '../components/Layout'
import { TrendChart } from '../components/TrendChart'
import { CheckedText, SourcePanel } from '../components/Sources'
import { HttpError, loadGroups, loadSource, loadUnit, type GroupMedians, type SourceFile, type UnitDetail } from '../lib/data'
import { COMPONENTS, FLAGS, QUALITY, VRSTA, eur, num, pct } from '../lib/format'
import { simulatorHref, unitHref } from '../lib/router'

const YEARS = ['2019', '2020', '2021', '2022', '2023', '2024', '2025']

export function Profile({ slug, lastYear }: { slug: string; lastYear: number }) {
  const [unit, setUnit] = useState<UnitDetail | null>(null)
  const [groups, setGroups] = useState<GroupMedians | null>(null)
  const [error, setError] = useState<string | null>(null)
  // visible number check: which component's sources are open, and the source file once loaded
  const [openSrc, setOpenSrc] = useState<string | null>(null)
  const [src, setSrc] = useState<SourceFile | null>(null)
  const [srcFailed, setSrcFailed] = useState(false)
  const showSources = (k: string, scroll = false) => {
    setOpenSrc((cur) => (cur === k && !scroll ? null : k))
    if (!src)
      loadSource(slug)
        .then(setSrc)
        .catch(() => setSrcFailed(true))
    if (scroll) setTimeout(() => document.getElementById(`src-${k}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
  }

  // App renders <Profile key={slug}>, so state starts empty for every unit
  useEffect(() => {
    Promise.all([loadUnit(slug), loadGroups()])
      .then(([u, g]) => {
        setUnit(u)
        setGroups(g)
        document.title = `${u.naziv} · Fiskalna karta`
      })
      .catch((e) =>
        setError(e instanceof HttpError && e.status === 404 ? 'Jedinica nije pronađena.' : 'Podaci se nisu učitali. Provjeri vezu i pokušaj ponovno.'),
      )
  }, [slug])

  if (error)
    return (
      <main className="mx-auto max-w-3xl px-6 py-20 text-center">
        <p className="text-lg">{error}</p>
        <div className="mt-4 flex justify-center gap-4">
          <button type="button" onClick={() => window.location.reload()} className="underline">
            Pokušaj ponovno
          </button>
          <a href="#/" className="underline">
            Natrag na kartu
          </a>
        </div>
      </main>
    )
  if (!unit || !groups) return <main className="mx-auto max-w-[1440px] px-10 py-20 text-muted">Učitavam svjedodžbu…</main>

  const year = String(lastYear)
  const r = unit.godine[year]
  const prev = unit.godine[String(lastYear - 1)]
  const med = groups[unit.skupina]
  const facts = unit.cinjenice?.facts ?? []
  const componentLines = facts.filter((f) => f.label.startsWith('Sastavnica:')).map((f) => f.value)
  const notes = [
    ...r.zastavice.map((z) => ({ kind: 'flag' as const, text: FLAGS[z] ?? z })),
    ...(r.ogranicenje_do
      ? [{ kind: 'rule' as const, text: 'Ocjena je ograničena na najviše 2 jer dospjele obveze dosežu 30 % rashoda poslovanja.' }]
      : []),
    ...r.kvaliteta.map((q) => ({ kind: 'data' as const, text: QUALITY[q] ?? q })),
  ]
  const isCounty = unit.vrsta === 'zupanija'

  return (
    <main className="mx-auto max-w-[1440px] px-6 pt-6 lg:px-10">
      <a href="#/" className="inline-flex items-center gap-1.5 text-sm text-ink-2 hover:text-ink">
        <ArrowLeft className="h-4 w-4" /> Karta
      </a>

      {/* header */}
      <div className="mt-4 grid gap-6 lg:grid-cols-[1fr_420px] lg:items-start">
        <div className="lg:pt-6">
          <Eyebrow>
            Svjedodžba · {VRSTA[unit.vrsta]}
            {!isCounty && ` · ${unit.zupanija}`}
          </Eyebrow>
          <h1 className="mt-2 font-serif text-5xl leading-[1.05] font-semibold tracking-tight">{unit.naziv}</h1>
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-ink-2">
            <span className="tabular">{num(unit.stanovnici_2021)} stanovnika (2021.)</span>
            {unit.povrsina_km2 != null && <span className="tabular">{num(unit.povrsina_km2, 1)} km²</span>}
            {unit.otok && <span>otočna jedinica</span>}
            {unit.razvojna_skupina != null && <span>razvojna skupina {num(unit.razvojna_skupina)} od 8</span>}
            <span>skupina: {unit.skupina}</span>
          </div>
        </div>
        <div className="rounded-2xl border border-hairline bg-card p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Eyebrow>Ocjena za {year}.</Eyebrow>
              <div className="mt-3">
                <GradeChip g={r.ocjena} size="lg" />
              </div>
            </div>
            <div className="text-right">
              <div className="tabular font-serif text-4xl font-semibold">{num(r.bodovi, 1)}</div>
              <div className="text-xs text-muted">od 100 bodova</div>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 border-t border-hairline pt-4 text-sm">
            <div>
              <div className="text-xs text-muted">Mjesto u skupini</div>
              <div className="tabular font-medium">
                {r.rang != null && r.n_skupine != null && r.n_skupine > 1 ? `${num(r.rang)}. od ${num(r.n_skupine)}` : 'bez usporedne skupine'}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted">Prošle godine</div>
              <div className="font-medium">{prev?.ocjena ? `${prev.ocjena} · ${prev.ocjena_rijec}` : '–'}</div>
            </div>
            <div className="col-span-2 flex items-center gap-2 text-ink-2">
              <ShieldCheck className="h-4 w-4 shrink-0" />
              {r.stabilnost === 'stabilna'
                ? 'Ocjena je ista u sva četiri scenarija pondera.'
                : `Ocjena ovisi o ponderima: od ${r.raspon_ocjena?.[0]} do ${r.raspon_ocjena?.[1]} u četiri scenarija.`}
            </div>
          </div>
          <p className="mt-4 border-t border-hairline pt-3 text-xs leading-relaxed text-muted">
            Ocjenjuje se financijska održivost proračuna, a ne kvaliteta upravljanja.{' '}
            <a href="#/metodologija" className="underline underline-offset-2">
              Kako se računa
            </a>
          </p>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_420px]">
        <div className="flex flex-col gap-6">
          {/* explanation */}
          {unit.objasnjenje && (
            <Card>
              <div className="flex items-center justify-between gap-4">
                <Eyebrow>Ukratko</Eyebrow>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-page px-2.5 py-1 text-xs text-ink-2">
                  {unit.objasnjenje.izvor === 'ai' ? <Sparkles className="h-3.5 w-3.5" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                  {unit.objasnjenje.izvor === 'ai'
                    ? `AI tekst${unit.objasnjenje.model ? ` · ${unit.objasnjenje.model}` : ''}`
                    : 'Predložak'}
                  {unit.objasnjenje.provjera &&
                    (unit.objasnjenje.provjera.ok
                      ? ` · ${unit.objasnjenje.provjera.n_brojki}/${unit.objasnjenje.provjera.n_brojki} brojki provjereno`
                      : ` · provjera nije prošla (${unit.objasnjenje.provjera.n_brojki - unit.objasnjenje.provjera.nepoznate.length}/${unit.objasnjenje.provjera.n_brojki})`)}
                </span>
              </div>
              <p className="mt-3 font-serif text-xl leading-relaxed">
                <CheckedText text={unit.objasnjenje.tekst} facts={facts} onOpen={(k) => showSources(k, true)} />
              </p>
              <p className="mt-3 text-xs text-muted">
                Svaka brojka u tekstu je iz paketa činjenica koji je izračunao Python. Prijeđi mišem preko brojke za njezin
                izvor; klik na brojku sastavnice otvara konta i retke u datotekama Ministarstva financija.
              </p>
            </Card>
          )}

          {/* components */}
          <Card>
            <Eyebrow>Pet sastavnica ocjene</Eyebrow>
            <p className="mt-1 text-sm text-muted">Bodovi 0–100 po sastavnici; prosjek zadnjih {r.prozor_godina} godina gdje je navedeno.</p>
            <ul className="mt-5 space-y-5">
              {COMPONENTS.map((c, i) => {
                const score = r[c.score as keyof typeof r] as number | null
                return (
                  <li key={c.key} id={`src-${c.key}`} className="scroll-mt-24">
                    <div className="flex items-baseline justify-between gap-4">
                      <div>
                        <span className="font-medium">{c.name}</span>
                        <span className="ml-2 text-xs text-muted">{c.hint}</span>
                      </div>
                      <span className="tabular shrink-0 text-sm font-semibold">{num(score, 0)}</span>
                    </div>
                    <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-page" role="img" aria-label={`${c.name}: ${num(score, 0)} od 100 bodova`}>
                      <div className="h-full rounded-full bg-ink-2" style={{ width: `${score ?? 0}%` }} />
                    </div>
                    {componentLines[i] && <p className="mt-1.5 text-sm text-ink-2">{capitalize(componentLines[i])}</p>}
                    <button
                      type="button"
                      onClick={() => showSources(c.key)}
                      aria-expanded={openSrc === c.key}
                      className="mt-1 text-xs text-muted underline decoration-axis underline-offset-4 hover:text-ink hover:decoration-ink"
                    >
                      {openSrc === c.key ? 'Sakrij izračun' : 'Kako je izračunato'}
                    </button>
                    {openSrc === c.key &&
                      (src ? (
                        <SourcePanel src={src} k={c.key} />
                      ) : (
                        <p className="mt-2 text-xs text-muted">{srcFailed ? 'Izvor se nije učitao.' : 'Učitavam izvor…'}</p>
                      ))}
                  </li>
                )
              })}
            </ul>
          </Card>

          {/* trend */}
          <Card>
            <Eyebrow>Bodovi kroz godine</Eyebrow>
            <div className="mt-4">
              <TrendChart
                groupName={unit.skupina}
                points={YEARS.map((y) => ({
                  year: y,
                  value: unit.godine[y]?.bodovi ?? null,
                  grade: unit.godine[y]?.ocjena ?? null,
                  median: med?.[y]?.bodovi ?? null,
                }))}
              />
            </div>
          </Card>
        </div>

        <aside className="flex flex-col gap-6">
          <Card>
            <Eyebrow>Upozorenja i napomene</Eyebrow>
            {notes.length === 0 ? (
              <p className="mt-3 flex items-center gap-2 text-sm text-ink-2">
                <CheckCircle2 className="h-4 w-4" /> Nema upozorenja za {year}.
              </p>
            ) : (
              <ul className="mt-3 space-y-3">
                {notes.map((n, i) => (
                  <li key={i} className="flex gap-2.5 text-sm">
                    {n.kind === 'data' ? (
                      <Info className="mt-0.5 h-4 w-4 shrink-0 text-ink-2" aria-label="Napomena o podacima" />
                    ) : (
                      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warn" aria-label="Upozorenje" />
                    )}
                    <span className="text-ink-2">{n.text}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <Eyebrow>Kontekst</Eyebrow>
            <dl className="mt-3 space-y-3 text-sm">
              <Row label="Tekuće pomoći u tekućim prihodima" value={pct(r.udio_tekucih_pomoci)} median={pct(med?.[year]?.udio_tekucih_pomoci)} />
              <Row label="Trošak opće uprave po stanovniku" value={eur(r.uprava_pc)} median={eur(med?.[year]?.uprava_pc)} />
              <Row label="Tekući prihodi po stanovniku" value={eur(r.tekuci_prihodi_pc)} />
              <Row label="Investicijska stopa" value={pct(r.investicijska_stopa)} />
              {r.DO != null && r.DO_iskazano != null && r.DO_iskazano !== r.DO && (
                <>
                  <Row label="Dospjele obveze, kako ih je jedinica iskazala" value={eur(r.DO_iskazano)} />
                  <Row label="Dospjele obveze nakon ispravka kredita" value={eur(r.DO)} />
                </>
              )}
            </dl>
          </Card>

          <Card>
            <Eyebrow>Otvorenost na data.gov.hr</Eyebrow>
            {unit.portal_objavljuje ? (
              <div className="mt-3 space-y-2 text-sm text-ink-2">
                <p>
                  <strong className="tabular text-ink">{num(unit.portal_skupova)}</strong> skupova podataka, zadnje ažuriranje{' '}
                  {unit.portal_zadnje_azuriranje ? new Date(unit.portal_zadnje_azuriranje).toLocaleDateString('hr-HR') : '–'}.
                </p>
                {unit.portal_strojno_citljivo != null && <p>Strojno čitljivo: {pct(unit.portal_strojno_citljivo, 0)} resursa.</p>}
                <div className="flex flex-wrap gap-3 pt-1">
                  {unit.portal_url_org && <ExtLink href={unit.portal_url_org}>Profil na portalu</ExtLink>}
                  {unit.portal_url_proracun && <ExtLink href={unit.portal_url_proracun}>Proračun</ExtLink>}
                </div>
              </div>
            ) : (
              <p className="mt-3 text-sm text-ink-2">Jedinica ne objavljuje skupove podataka na Portalu otvorenih podataka.</p>
            )}
          </Card>

          {unit.susjedi.length > 0 && (
            <Card>
              <Eyebrow>Susjedi</Eyebrow>
              <ul className="mt-3 flex flex-wrap gap-2">
                {unit.susjedi.map((s) => (
                  <li key={s.slug}>
                    <a
                      href={unitHref(s.slug)}
                      className="inline-flex items-center gap-1.5 rounded-full border border-hairline px-3 py-1 text-sm hover:border-ink"
                    >
                      {s.vrsta === 'more' && <MapPin className="h-3.5 w-3.5 text-muted" aria-label="veza preko mora" />}
                      {s.naziv.replace(/^(Općina|Grad) /, '')}
                    </a>
                  </li>
                ))}
              </ul>
              {/* the simulator takes municipalities and towns of one county, not counties or Zagreb */}
              {!isCounty && unit.sifra !== '01333' && (
                <a
                  href={simulatorHref([unit.sifra])}
                  className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium underline decoration-axis underline-offset-4 hover:decoration-ink"
                >
                  Simuliraj spajanje sa susjedima <ArrowRight className="h-4 w-4" aria-hidden />
                </a>
              )}
            </Card>
          )}

          <p className="text-xs leading-relaxed text-muted">
            Izvor: Ministarstvo financija, PR-RAS i Bilanca razine 22, {YEARS[0]}.–{year}.; DZS, Popis 2021. Šifra jedinice{' '}
            {unit.sifra}, OIB {unit.oib}.
          </p>
        </aside>
      </div>
    </main>
  )
}

function Row({ label, value, median }: { label: string; value: string; median?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-hairline pb-2 last:border-0 last:pb-0">
      <dt className="text-ink-2">{label}</dt>
      <dd className="tabular shrink-0 text-right">
        <span className="font-medium whitespace-nowrap">{value}</span>
        {median && <div className="text-xs whitespace-nowrap text-muted">medijan skupine {median}</div>}
      </dd>
    </div>
  )
}

function ExtLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-ink underline decoration-axis underline-offset-4 hover:decoration-ink">
      {children} <ExternalLink className="h-3.5 w-3.5" />
    </a>
  )
}

const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)
