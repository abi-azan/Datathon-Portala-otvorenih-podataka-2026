// Live calls from the browser to the public APIs the build reads: the open data portal's CKAN API
// (data.gov.hr), the DZS PxWeb API and the DZS/NIPP INSPIRE WFS.
//
// data.gov.hr sends no Access-Control-Allow-Origin header, so fetch() cannot read its answers. CKAN
// answers JSONP when the call carries a `callback` parameter: the answer is a script that calls that
// function with the JSON. That script comes from data.gov.hr, the national portal; nothing else is
// loaded this way. PxWeb and the WFS send the CORS header and are read with fetch().
//
// Every failing case (timeout, network, an answer of another shape) gives null, and the caller keeps
// the copy from the build. Answers are kept in sessionStorage, so a tab asks each question once.

const CKAN = 'https://data.gov.hr/ckan/api/3/action/'
const TIMEOUT_MS = 4000

function read<T>(k: string): T | null {
  try {
    const s = sessionStorage.getItem(k)
    return s ? (JSON.parse(s) as T) : null
  } catch {
    return null
  }
}

function write(k: string, v: unknown) {
  try {
    sessionStorage.setItem(k, JSON.stringify(v))
  } catch {
    // private mode or full storage: the question is just asked again next time
  }
}

const inFlight = new Map<string, Promise<unknown>>()

/** One answer per key: from this tab's storage, else from `ask` (shared while it is under way). */
function once<T>(key: string, ask: () => Promise<T | null>): Promise<T | null> {
  const cached = read<T>(key)
  if (cached != null) return Promise.resolve(cached)
  let p = inFlight.get(key) as Promise<T | null> | undefined
  if (!p) {
    p = ask()
      .then((v) => {
        if (v != null) write(key, v)
        return v
      })
      .catch(() => null)
      .finally(() => inFlight.delete(key))
    inFlight.set(key, p)
  }
  return p
}

let seq = 0

/** A CKAN call as JSONP; null on timeout or when the script does not load. */
function jsonp<T>(url: string): Promise<T | null> {
  return new Promise((resolve) => {
    const name = `__ckan${Date.now().toString(36)}${seq++}`
    const globals = window as unknown as Record<string, unknown>
    const script = document.createElement('script')
    let done = false
    const finish = (v: T | null, late = false) => {
      if (done) return
      done = true
      clearTimeout(timer)
      script.remove()
      // after a timeout the answer may still arrive; leave a function for it to call, then remove it
      if (late) globals[name] = () => delete globals[name]
      else delete globals[name]
      resolve(v)
    }
    globals[name] = (data: T) => finish(data)
    const timer = setTimeout(() => finish(null, true), TIMEOUT_MS)
    script.onerror = () => finish(null)
    script.async = true
    script.referrerPolicy = 'no-referrer'
    script.src = `${url}&callback=${name}`
    document.head.appendChild(script)
  })
}

/** The address of a CKAN call, as the page links to it ("otvori poziv"). */
export const ckanUrl = (action: string, params: Record<string, string>) => `${CKAN}${action}?${new URLSearchParams(params)}`

interface SearchAnswer {
  success?: boolean
  result?: { count?: unknown; results?: { metadata_modified?: unknown }[] }
}

/** Count and newest change from a package_search answer; null when it is not one. */
export function parseSearch(a: SearchAnswer | null): { count: number; modified: string | null } | null {
  const count = a?.success === true ? a.result?.count : null
  if (typeof count !== 'number' || !Number.isInteger(count) || count < 0) return null
  const m = a?.result?.results?.[0]?.metadata_modified
  return { count, modified: typeof m === 'string' && /^\d{4}-\d{2}-\d{2}/.test(m) ? m.slice(0, 10) : null }
}

export interface PortalLive {
  /** datasets the publisher has on the portal right now */
  count: number
  /** day of its newest change (YYYY-MM-DD), null when it has no datasets */
  modified: string | null
  /** when the portal answered (ISO time) */
  fetched: string
}

/** The publisher account in a portal address: ".../organization/grad-rijeka" gives "grad-rijeka". */
export const orgSlug = (url?: string | null) => url?.match(/\/organization\/([a-z0-9_-]+)\/?$/i)?.[1] ?? null

/** The call that counts one publisher's datasets, newest first. */
export const orgSearchUrl = (org: string) =>
  ckanUrl('package_search', { fq: `organization:${org}`, rows: '1', sort: 'metadata_modified desc', fl: 'name,metadata_modified' })

/** While the portal rebuilds its search index it can answer with no or few datasets (pipeline/openness.py
 *  retries such an answer). A live count under 80 % of the stored one is taken as that and not shown. */
export const plausible = (count: number, stored: number | null | undefined) => !stored || count >= 0.8 * stored

/** One publisher's datasets straight from the portal; null on any failure or an implausible count. */
export function liveOrg(org: string, stored?: number | null): Promise<PortalLive | null> {
  return once<PortalLive>(`portal:v1:org:${org}`, async () => {
    const a = parseSearch(await jsonp<SearchAnswer>(orgSearchUrl(org)))
    return a && plausible(a.count, stored) ? { ...a, fetched: new Date().toISOString() } : null
  })
}

/** What a live check of one API found, in the words shown on the page. */
export interface ApiCheck {
  ok: true
  /** the number the API answered with (datasets, units, last year) */
  value: number
  fetched: string
}

export const CATALOGUE_URL = ckanUrl('package_search', { rows: '0' })

/** All datasets in the portal's catalogue right now. */
export function liveCatalogue(): Promise<ApiCheck | null> {
  return once<ApiCheck>('portal:v1:katalog', async () => {
    const a = parseSearch(await jsonp<SearchAnswer>(CATALOGUE_URL))
    return a && a.count > 0 ? { ok: true, value: a.count, fetched: new Date().toISOString() } : null
  })
}

async function fetchText(url: string): Promise<string | null> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS)
  try {
    const r = await fetch(url, { signal: ctrl.signal })
    return r.ok ? await r.text() : null
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

/** The last year a PxWeb table holds, from its metadata (variable "Godina"); null when it is not there. */
export function parsePxLastYear(meta: unknown): number | null {
  const vars = (meta as { variables?: { code?: string; valueTexts?: unknown[] }[] } | null)?.variables
  const years = (Array.isArray(vars) ? vars.find((v) => v.code === 'Godina')?.valueTexts ?? [] : [])
    .map(Number)
    .filter((y) => Number.isInteger(y) && y > 1900 && y < 2200)
  return years.length ? Math.max(...years) : null
}

/** The last year in a DZS PxWeb table, asked from the table's own address (GET gives its metadata). */
export function livePxTable(url: string): Promise<ApiCheck | null> {
  return once<ApiCheck>(`portal:v1:px:${url}`, async () => {
    const text = await fetchText(url)
    let year: number | null = null
    try {
      year = text ? parsePxLastYear(JSON.parse(text)) : null
    } catch {
      year = null
    }
    return year ? { ok: true, value: year, fetched: new Date().toISOString() } : null
  })
}

/** numberMatched of a WFS "hits" answer; null when the answer is not one. */
export function parseWfsHits(xml: string | null): number | null {
  const m = xml?.match(/<wfs:FeatureCollection\b[^>]*\bnumberMatched="(\d+)"/)
  return m ? Number(m[1]) : null
}

/** A WFS GetFeature address turned into a count-only request (RESULTTYPE=hits, no features sent). */
export function wfsHitsUrl(url: string): string {
  const [base, query = ''] = url.split('?')
  const keep = new URLSearchParams()
  for (const [k, v] of new URLSearchParams(query)) {
    if (['SERVICE', 'VERSION', 'REQUEST', 'TYPENAMES'].includes(k.toUpperCase())) keep.set(k.toUpperCase(), v)
  }
  keep.set('RESULTTYPE', 'hits')
  // the service reads a literal colon in TYPENAMES
  return `${base}?${keep.toString().replace(/%3A/gi, ':')}`
}

/** How many features a WFS layer holds right now. */
export function liveWfsCount(url: string): Promise<ApiCheck | null> {
  return once<ApiCheck>(`portal:v1:wfs:${url}`, async () => {
    const n = parseWfsHits(await fetchText(wfsHitsUrl(url)))
    return n ? { ok: true, value: n, fetched: new Date().toISOString() } : null
  })
}
