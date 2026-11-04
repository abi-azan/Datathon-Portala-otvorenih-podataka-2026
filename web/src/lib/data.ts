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
    model?: string | null
    provjera?: { ok: boolean; n_brojki: number; nepoznate: string[]; sadrzaj?: string[] }
  } | null
}

export type GroupMedians = Record<string, Record<string, Record<string, number | null>>>

/** Savings on general administration (01 without 017 and 018), pipeline/merge.py savings(). */
export interface Savings {
  godina: number
  uprava_zbroj: number
  medijan_pc: number | null
  ocekivano: number | null
  strukturni_jaz: number | null
  realno_do: number | null
  iznad_10000: boolean
}

/** Full fiscal equalization under the statutory formula (pipeline/izravnanje.py za_spajanje). */
export interface Equalization {
  godina: number
  puni_po_clanici: number[]
  puni_clanice: number
  puni_spojena: number
  promjena: number
  promjena_udio: number | null
  oznake: string[]
  [k: string]: unknown
}

/** One precomputed group of the merger simulator (api/v1/simulator/zup-<id>.json). */
export interface MergeSummary {
  clanice: string[]
  vrsta: 'grad' | 'opcina'
  skupina: string
  stanovnici: number
  godina: number
  ocjene: Record<string, number | null>
  bodovi: Record<string, number | null>
  zadnja: {
    bodovi: number | null
    bodovi_bez_ogranicenja: number | null
    ogranicenje_do: boolean
    ocjena: number
    ocjena_rijec: string
    zastavice: string[]
    kvaliteta: string[]
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
    ND: number | null
    DO: number | null
    uprava_pc: number | null
    rang: number
    n_skupine: number
  }
  usteda: Savings | null
  izravnanje?: Equalization | null
}

export interface SimulatorFile {
  zup_id: number
  zupanija: string
  skupine: Record<string, MergeSummary>
}

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
/** One unit after the Karta reforme scenario: a merged group or a unit that stayed alone. */
export interface ReformUnit {
  clanice: string[]
  naziv: string
  vrsta: 'grad' | 'opcina'
  zup_id: number
  stanovnici: number
  skupina: string
  ocjene_prije: Record<string, number | null>
  ocjena: number | null
  ocjena_rijec: string | null
  bodovi: number | null
  rang: number | null
  n_skupine: number | null
  usteda: Savings | null
  izravnanje: Equalization | null
}

/** api/v1/reforma/prag-<N>.json (pipeline/reforma.py). */
export interface ReformFile {
  prag: number
  godina: number
  napomena?: string
  n_prije: number
  n_poslije: number
  stanovnika_u_spojenima: number
  n_spojenih_skupina: number
  n_ispod_praga: number
  usteda_realno_do_zbroj: number
  strukturni_jaz_zbroj: number
  izravnanje_promjena_zbroj?: number
  jedinice: ReformUnit[]
}

export const REFORM_THRESHOLDS = [2500, 5000, 10000] as const
export const loadReform = (prag: number) => get<ReformFile>(`reforma/prag-${prag}.json`)
export const loadSimulator =(zupId: number) => get<SimulatorFile>(`simulator/zup-${String(zupId).padStart(2, '0')}.json`)
export const topoUrl = () => BASE + 'geo/jls.topo.json'
