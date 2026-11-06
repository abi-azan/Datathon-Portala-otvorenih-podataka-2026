import { ExternalLink, Radio } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import type { UnitDetail } from '../lib/data'
import { num, pct } from '../lib/format'
import { liveOrg, orgSearchUrl, orgSlug, type PortalLive } from '../lib/portal'
import { Card, Eyebrow } from './Layout'

function Out({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1 text-ink underline decoration-axis underline-offset-4 hover:decoration-ink"
    >
      {children} <ExternalLink className="h-3.5 w-3.5" aria-hidden />
    </a>
  )
}

/** The unit's datasets on the open data portal. The count and the day of the newest change are asked
 *  from the portal's CKAN API while the page is open (lib/portal.ts). Until it answers, and whenever it
 *  does not, the card shows the copy from the build. The machine-readable share is always the build's:
 *  it needs every dataset of the unit, not one call. */
export function PortalCard({ unit, className = '' }: { unit: UnitDetail; className?: string }) {
  const org = unit.portal_objavljuje ? orgSlug(unit.portal_url_org) : null
  const [live, setLive] = useState<PortalLive | null>(null)
  useEffect(() => {
    setLive(null)
    if (!org) return
    let alive = true
    liveOrg(org, unit.portal_skupova).then((a) => alive && setLive(a))
    return () => {
      alive = false
    }
  }, [org, unit.portal_skupova])

  const count = live?.count ?? unit.portal_skupova
  const updated = live?.modified ?? unit.portal_zadnje_azuriranje
  return (
    <Card className={className}>
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <Eyebrow>Otvoreni podaci jedinice</Eyebrow>
        {live && (
          <span
            title="Broj skupova i dan zadnjeg ažuriranja stigli su upravo s API-ja Portala otvorenih podataka (CKAN, package_search). Udio strojno čitljivih je iz zadnje obrade podataka."
            className="inline-flex items-center gap-1.5 rounded-full bg-page px-2.5 py-1 text-xs whitespace-nowrap text-ink-2"
          >
            <Radio className="h-3.5 w-3.5 shrink-0" aria-hidden />
            uživo s API-ja Portala
          </span>
        )}
      </div>
      {unit.portal_objavljuje ? (
        <div className="mt-3 space-y-2 text-sm text-ink-2">
          <p>
            <strong className="tabular text-ink">{num(count)}</strong> skupova podataka, zadnje ažuriranje{' '}
            {/* the Croatian date ends with a full stop of its own */}
            {updated ? new Date(updated).toLocaleDateString('hr-HR') : 'nepoznato.'}
          </p>
          {unit.portal_strojno_citljivo != null && <p>Strojno čitljivo: {pct(unit.portal_strojno_citljivo, 0)} resursa.</p>}
          <div className="flex flex-wrap gap-x-3 gap-y-1 pt-1">
            {unit.portal_url_org && <Out href={unit.portal_url_org}>Profil na portalu</Out>}
            {unit.portal_url_proracun && <Out href={unit.portal_url_proracun}>Proračun</Out>}
            {org && <Out href={orgSearchUrl(org)}>Poziv API-ju</Out>}
          </div>
        </div>
      ) : (
        <p className="mt-3 text-sm text-ink-2">Jedinica ne objavljuje skupove podataka na Portalu otvorenih podataka.</p>
      )}
    </Card>
  )
}
