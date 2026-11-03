import type { ReactNode } from 'react'

export function Header({ current }: { current: 'home' | 'unit' | 'methodology' }) {
  const link = (href: string, label: string, active: boolean) => (
    <a
      href={href}
      aria-current={active ? 'page' : undefined}
      className={`rounded-lg px-3 py-1.5 text-sm transition ${active ? 'bg-ink text-white' : 'text-ink-2 hover:bg-hairline/60 hover:text-ink'}`}
    >
      {label}
    </a>
  )
  return (
    <header className="border-b border-hairline bg-page/90 backdrop-blur supports-[backdrop-filter]:bg-page/75 sticky top-0 z-30">
      <div className="mx-auto flex h-16 max-w-[1440px] items-center gap-6 px-6 lg:px-10">
        <a href="#/" className="flex items-center gap-2.5">
          <img src="./favicon.svg" alt="" className="h-7 w-7" />
          <span className="font-serif text-xl font-semibold tracking-tight">Fiskalna karta</span>
        </a>
        <nav className="ml-auto flex items-center gap-1" aria-label="Glavna navigacija">
          {link('#/', 'Karta', current === 'home')}
          <span className="cursor-not-allowed rounded-lg px-3 py-1.5 text-sm text-muted" title="Uskoro">
            Simulator spajanja
          </span>
          <span className="cursor-not-allowed rounded-lg px-3 py-1.5 text-sm text-muted" title="Uskoro">
            Karta reforme
          </span>
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
          <p className="mt-2">
            Ministarstvo financija (PR-RAS, Bilanca), DZS (Popis 2021., granice, INSPIRE WFS), data.gov.hr (CKAN API).
            Granice: © DZS / DGU, Otvorena dozvola. Podloga: © OpenStreetMap, OpenFreeMap.
          </p>
        </div>
        <div>
          <div className="font-medium text-ink">Otvoreno</div>
          <p className="mt-2">
            Kod: EUPL-1.2 · Podaci: CC BY 4.0
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
