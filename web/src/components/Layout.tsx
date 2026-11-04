import type { ReactNode } from 'react'
import type { Page } from '../lib/router'

export function Header({ current }: { current: Page }) {
  const link = (href: string, label: string, active: boolean) => (
    <a
      href={href}
      aria-current={active ? 'page' : undefined}
      className={`shrink-0 rounded-lg px-3 py-1.5 text-sm whitespace-nowrap transition ${active ? 'bg-ink text-white' : 'text-ink-2 hover:bg-hairline/60 hover:text-ink'}`}
    >
      {label}
    </a>
  )
  // Below lg the logo and the menu (about 760 px with padding) do not fit one row: the menu becomes a
  // second row that scrolls sideways on its own, edge to edge, padded so focus rings are not clipped.
  return (
    <header className="border-b border-hairline bg-page/90 backdrop-blur supports-[backdrop-filter]:bg-page/75 sticky top-0 z-30">
      <div className="mx-auto flex max-w-[1440px] flex-wrap items-center gap-x-6 px-6 lg:h-16 lg:flex-nowrap lg:px-10">
        <a href="#/" className="flex h-12 items-center gap-2.5 lg:h-auto">
          <img src="./favicon.svg" alt="" className="h-7 w-7" />
          <span className="font-serif text-xl font-semibold tracking-tight">Fiskalna karta</span>
        </a>
        <nav
          className="-mx-6 flex w-[calc(100%+3rem)] items-center gap-1 overflow-x-auto px-6 pt-1 pb-2.5 lg:mr-0 lg:ml-auto lg:w-auto lg:overflow-visible lg:p-0"
          aria-label="Glavna navigacija"
        >
          {link('#/', 'Karta', current === 'home')}
          {link('#/simulator', 'Simulator spajanja', current === 'simulator')}
          {link('#/reforma', 'Karta reforme', current === 'reform')}
          {link('#/metodologija', 'Metodologija i podaci', current === 'methodology')}
        </nav>
      </div>
    </header>
  )
}

export function Footer({ generated }: { generated?: string }) {
  return (
    <footer className="mt-16 border-t border-hairline">
      <div className="mx-auto grid max-w-[1440px] gap-6 px-6 py-10 text-sm text-ink-2 md:grid-cols-3 lg:px-10">
        <div>
          <div className="font-serif text-base font-semibold text-ink">Fiskalna karta</div>
          <p className="mt-2 max-w-sm">
            Ocjena financijske stabilnosti svih 576 općina, gradova i županija iz otvorenih podataka. Datathon Portala
            otvorenih podataka 2026.
          </p>
        </div>
        <div>
          <div className="font-medium text-ink">Izvori</div>
          {/* Source statement required by the Otvorena dozvola (t. II-III): bodies, link to the licence, link to
              the datasets with their last-change dates, and a note that the data were changed. */}
          <p className="mt-2">
            Sadrži informacije tijela javne vlasti u skladu s{' '}
            <a href="https://data.gov.hr/otvorena-dozvola" className="underline decoration-axis underline-offset-4 hover:decoration-ink">
              Otvorenom dozvolom
            </a>
            : Ministarstvo financija (PR-RAS, Bilanca, fiskalno izravnanje), DZS (Popis 2021. i granice, INSPIRE WFS), DGU
            (upravne jedinice), Državni ured za reviziju (izvješća o reviziji) i data.gov.hr (CKAN API). Indeks razvijenosti:
            MRRFEU.
          </p>
          <p className="mt-2">
            Podaci su preračunati u pokazatelje i ocjene, a granice pojednostavljene.{' '}
            <a
              href="https://github.com/abi-azan/Datathon-Portala-otvorenih-podataka-2026/blob/main/docs/skupovi-podataka.md"
              className="underline decoration-axis underline-offset-4 hover:decoration-ink"
            >
              Skupovi, poveznice i datumi izmjene
            </a>
          </p>
          <p className="mt-2">
            Podloga karte: ©{' '}
            <a href="https://www.openstreetmap.org/copyright" className="underline decoration-axis underline-offset-4 hover:decoration-ink">
              OpenStreetMap
            </a>{' '}
            suradnici, © OpenMapTiles, OpenFreeMap.
          </p>
        </div>
        <div>
          <div className="font-medium text-ink">Otvoreno</div>
          <ul className="mt-2 space-y-1">
            <li>
              <a href="./api/v1/openapi.json" className="underline decoration-axis underline-offset-4 hover:decoration-ink">
                Otvoreni API (OpenAPI 3.1)
              </a>
            </li>
            <li>
              <a href="./api/v1/rezultati.csv" className="underline decoration-axis underline-offset-4 hover:decoration-ink">
                Svi rezultati (CSV)
              </a>{' '}
              ·{' '}
              <a href="./api/v1/sifrarnik.csv" className="underline decoration-axis underline-offset-4 hover:decoration-ink">
                Šifrarnik (CSV)
              </a>
            </li>
            <li>
              <a href="./api/v1/izvori.json" className="underline decoration-axis underline-offset-4 hover:decoration-ink">
                Zapis izvora i preuzimanja
              </a>
            </li>
            <li>
              <a href="./api/v1/dcat.jsonld" className="underline decoration-axis underline-offset-4 hover:decoration-ink">
                Katalog skupova (DCAT-AP)
              </a>
            </li>
          </ul>
          <p className="mt-2">
            Kod: EUPL-1.2 · Podaci: CC BY 4.0 ·{' '}
            <a href="./licence-trecih-strana.txt" className="underline decoration-axis underline-offset-4 hover:decoration-ink">
              Licence softvera
            </a>
            {generated && (
              <>
                <br />
                Podaci obrađeni {new Date(generated).toLocaleDateString('hr-HR')}
              </>
            )}
          </p>
        </div>
      </div>
    </footer>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-2xl border border-hairline bg-card p-6 ${className}`}>{children}</section>
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="text-xs font-semibold tracking-[0.08em] text-muted uppercase">{children}</div>
}
