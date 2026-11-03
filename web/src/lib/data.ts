// Static API produced by `python -m pipeline.publish` (web/public/api/v1).

export type Vrsta = 'opcina' | 'grad' | 'zupanija'

export interface UnitIndex {
  oib: string
  sifra: string
  slug: string
  naziv: string
  vrsta: Vrsta
  zup_id: number
  zupanija: string
  stanovnici: number
  skupina: string
  ocjena: Record<string, number | null>
  bodovi: Record<string, number | null>
  uprava_pc: number | null
  udio_tekucih_pomoci: number | null
}

export interface IndexFile {
  generirano: string
  zadnja_godina: number
  jedinice: UnitIndex[]
}

export interface YearResult {
  ocjena: number | null
  ocjena_rijec: string | null
  bodovi: number | null
  bodovi_bez_ogranicenja: number | null
  ogranicenje_do: boolean
  stabilnost: string | null
  raspon_ocjena: [number, number] | null
  ocjene_scenarija: Record<string, number | null>
  prozor_godina: number
  rang: number | null
  n_skupine: number | null
  percentil: number | null
  I1: number | null
  I2: number | null
  I3: number | null
  I4: number | null
  I5: number | null
  S1: number | null
  S2: number | null
  S3: number | null
  S4: number | null
  S5: number | null
  DO: number | null
  DO_iskazano: number | null
  zastavice: string[]
  oznake: string[]
  kvaliteta: string[]
  udio_tekucih_pomoci: number | null
  uprava_pc: number | null
  tekuci_prihodi_pc: number | null
  neto_dug_pc: number | null
  investicijska_stopa: number | null
}

export interface Fact {
  label: string
  value: string
}

export interface UnitDetail {
  oib: string
  rkp: string
  sifra: string
  slug: string
  naziv: string
  vrsta: Vrsta
  zupanija: string
  zup_id: number
  skupina: string
  stanovnici_2021: number
  povrsina_km2: number | null
  otok: boolean | null
  indeks_razvijenosti_2024: number | null
  razvojna_skupina: number | null
  portal_objavljuje: boolean
  portal_skupova: number | null
  portal_zadnje_azuriranje: string | null
  portal_strojno_citljivo: number | null
  portal_url_org: string | null
  portal_url_proracun: string | null
  godine: Record<string, YearResult>
  susjedi: { slug: string; naziv: string; vrsta: 'kopno' | 'more'; km: number }[]
  cinjenice: { facts: Fact[]; naziv: { nom: string; gen: string; lok: string } } | null
  objasnjenje: {
    tekst: string
    izvor: 'ai' | 'predlozak'
    provjera?: { ok: boolean; n_brojki: number; nepoznate: string[]; sadrzaj?: string[] }
  } | null
}

export type GroupMedians = Record<string, Record<string, Record<string, number | null>>>

const BASE = `${import.meta.env.BASE_URL}api/v1/`

export class HttpError extends Error {
  status: number
  constructor(path: string, status: number) {
    super(`${path}: HTTP ${status}`)
    this.status = status
  }
}

const cache = new Map<string, Promise<unknown>>()

/** Cached GET; a failed request is dropped from the cache so the next call retries. */
function get<T>(path: string): Promise<T> {
  if (!cache.has(path)) {
    const p = fetch(BASE + path).then((r) => {
      if (!r.ok) throw new HttpError(path, r.status)
      // a static host may answer a missing file with the app's index.html (200, text/html)
      if (!(r.headers.get('content-type') ?? '').includes('json')) throw new HttpError(path, 404)
      return r.json()
    })
    p.catch(() => cache.delete(path))
    cache.set(path, p)
  }
  return cache.get(path) as Promise<T>
}

export const loadIndex = () => get<IndexFile>('jedinice.json')
export const loadUnit = (slug: string) => get<UnitDetail>(`jedinice/${slug}.json`)
export const loadGroups = () => get<GroupMedians>('skupine.json')
export const topoUrl = () => BASE + 'geo/jls.topo.json'
