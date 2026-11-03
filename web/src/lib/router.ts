import { useEffect, useState } from 'react'

// Hash routes work on GitHub Pages without a server: #/, #/jedinica/<slug>, #/metodologija
export type Route = { page: 'home' } | { page: 'unit'; slug: string } | { page: 'methodology' }

function parse(hash: string): Route {
  const path = hash.replace(/^#/, '')
  const unit = path.match(/^\/jedinica\/([a-z0-9-]+)/)
  if (unit) return { page: 'unit', slug: unit[1] }
  if (path.startsWith('/metodologija')) return { page: 'methodology' }
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
export const go = (href: string) => {
  window.location.hash = href.replace(/^#/, '')
}
