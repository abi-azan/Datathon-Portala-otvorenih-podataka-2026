import { useEffect, useState } from 'react'

// Hash routes work on GitHub Pages without a server:
// #/, #/jedinica/<slug>, #/metodologija, #/simulator?j=<sifra>,<sifra>, #/reforma?prag=<N>&s=<skupina>
export type Route =
  | { page: 'home' }
  | { page: 'unit'; slug: string }
  | { page: 'methodology' }
  | { page: 'simulator' }
  | { page: 'reform' }

export type Page = Route['page']

/** DGU codes from the simulator's ?j= parameter (5 digits each, at most 4, no repeats).
 *  The simulator reads it itself and keeps it in sync with replaceState, so the route has no copy. */
export function parseSelection(hash: string): string[] {
  const q = hash.split('?')[1] ?? ''
  const j = new URLSearchParams(q).get('j') ?? ''
  return [...new Set(j.split(',').filter((s) => /^\d{5}$/.test(s)))].slice(0, 4)
}

function parse(hash: string): Route {
  const path = hash.replace(/^#/, '')
  const unit = path.match(/^\/jedinica\/([a-z0-9-]+)/)
  if (unit) return { page: 'unit', slug: unit[1] }
  if (path.startsWith('/metodologija')) return { page: 'methodology' }
  if (path.startsWith('/simulator')) return { page: 'simulator' }
  if (path.startsWith('/reforma')) return { page: 'reform' }
  return { page: 'home' }
}

export function useRoute(): Route {
  const [route, setRoute] = useState(() => parse(window.location.hash))
  useEffect(() => {
    const on = () => {
      setRoute(parse(window.location.hash))
      window.scrollTo({ top: 0 })
    }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return route
}

export const unitHref = (slug: string) => `#/jedinica/${slug}`
export const simulatorHref = (sifre: string[] = []) => (sifre.length ? `#/simulator?j=${sifre.join(',')}` : '#/simulator')
export const go = (href: string) => {
  window.location.hash = href.replace(/^#/, '')
}
