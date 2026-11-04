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
  uprava_pc_po_godini?: Record<string, number | null>
  udio_tekucih_pomoci_po_godini?: Record<string, number | null>
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
  /** Z5, the 10 % criterion (methodology.criterion_10): deficit without EU sources / revenue without EU sources. */
  z5_manjak_udio?: number | null
  z5_zadovoljava?: boolean | null
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
  /** Latest financial audit of the State Audit Office since 2019 (pipeline/dur.py); null: none. */
  revizija?: {
    objavljeno: number
    revidirana_godina: number | null
    misljenje: 'bezuvjetno' | 'uvjetno' | 'nepovoljno' | 'suzdržano' | null
    url: string
  } | null
  objasnjenje: {
    tekst: string
    izvor: 'ai' | 'predlozak'
    model?: string | null
    provjera?: { ok: boolean; n_brojki: number; nepoznate: string[]; sadrzaj?: string[] }
  } | null
  /** Population and economy (pipeline/kontekst.py; DZS PxWeb, Porezna uprava). Not in the score. */
  stanovnistvo_gospodarstvo?: PopulationEconomy
  /** Fiscal equalization of the unit (pipeline/kontekst.py, MF table). */
  izravnanje?: UnitEqualization | null
  /** Local tax rates by year (Porezna uprava); null for counties. */
  porezne_stope?: Record<string, TaxRates> | null
}

/** One context indicator with its peer-group median. oznaka: DZS symbol, "-" none (counted as 0), "z" confidential (null). */
/** Where a demographic year comes from: the DZS PxWeb API, or the DZS publication "Gradovi i općine u
 * statistici" for the years PxWeb does not have yet (pipeline/dzs_xlsx.py; izvor_po_godini). */
export type DzsSource = 'pxweb' | 'xlsx'

export interface ContextIndicator {
  godina: number
  od_godine?: number
  /** only the three demographic indicators: the source of the last year */
  izvor?: DzsSource | null
  vrijednost: number | null
  oznaka: '-' | 'z' | null
  broj: number | null
  medijan: number | null
  n_medijan: number
}

export type ContextKey =
  | 'promjena_stanovnistva'
  | 'prirodni_prirast'
  | 'neto_migracija'
  | 'nocenja_po_stanovniku'
  | 'dozvole_na_1000'
  | 'neto_dohodak_pc'
  | 'udio_mirovina'

/** The PxWeb request the browser sends to DZS for the population series (POST, json-stat2). */
export interface LiveQuery {
  tablica: string
  kod: string
  /** DZS's label for kod in the table's metadata; the browser rejects an answer with another label */
  naziv?: string | null
  url: string
  upit: { query: unknown[]; response: { format: string } }
}

export interface PopulationEconomy {
  skupina: string | null
  pokazatelji: Record<ContextKey, ContextIndicator>
  /** Population estimate at 31.12. by year (SP31_2): only for the trend. */
  procjene: Record<string, number | null>
  /** Source of the demographic numbers per year: PxWeb, or the DZS publication for the years PxWeb lacks. */
  izvor_po_godini?: Record<string, DzsSource>
  uzivo: LiveQuery | null
  izvori: {
    izdavatelj: string
    naziv: string | null
    tablica: string | null
    url: string
    azurirano: string | null
    preuzeto?: string | null
    /** only for the DZS publication: the years taken from it */
    godine?: number[]
  }[]
}

export interface UnitEqualization {
  godina: number
  proracun_godina: number
  iznos_proracuna: number
  vrsta_reference: 'opcina' | 'grad' | 'zupanija'
  kapacitet_pc: number
  referentna_pc: number
  /** Full amount by the formula; the UI shows only the payout. */
  puni_iznos: number
  udio: number
  isplata: number
  stopa: {
    godina: number
    niza: number | null
    visa?: number | null
    niza_max: number | null
    visa_max?: number | null
    ispod_maksimuma: boolean | null
  } | null
  /** Decision S1: what the unit's own budget would collect more a year at the highest rates; only below the maximum. */
  uz_najvise_stope?: {
    godina_stopa: number
    godina_poreza: number
    procjena: number
    od: number
    do: number
    niza: number
    visa: number
    niza_max: number
    visa_max: number
  } | null
}

export interface TaxRates {
  niza: number | null
  visa: number | null
  niza_max: number | null
  ispod_maksimuma: boolean | null
  potrosnja_min: number | null
  potrosnja_max: number | null
  nekretnine_min: number | null
  nekretnine_max: number | null
  nekretnine_naplata: string | null
}

/** jedinice/<slug>/izvor.json (pipeline/provenance.py): formula and inputs behind I1-I5. */
export interface SourceFile {
  godina: number
  prozor: { godine: number[]; ponderi: number[] }
  pokazatelji: Record<string, { naziv: string; formula: string; vrijednost: number | null; bodovi: number | null; velicine: string[] }>
  velicine: Record<
    string,
    {
      formula: string
      godine: Record<string, number | null>
      iskazano?: number | null
      pravilo1_iskljuceno?: number | null
      refinanciranje?: Record<string, boolean>
      prag_refinanciranja?: number
      /** FI only: odluka | konto_6353 | porez_na_dohodak, per year */
      izvor?: Record<string, string>
    }
  >
  izvori: Record<string, { datoteka: string | null; list: string | null }>
  konta: Record<string, { naziv: string | null; izvor: 'PR-RAS' | 'Bilanca' | 'Odluka MF-a'; za: string[] }>
  /** datoteka, list, udio and proracun: the fiscal equalization input (izvor 'Odluka MF-a') */
  ulazi: {
    konto: string
    godina: number
    iznos: number
    redak: number | null
    stupac?: string | null
    datoteka?: string
    list?: string
    udio?: number
    proracun?: number
  }[]
  napomena?: string
}

export type GroupMedians = Record<string, Record<string, Record<string, number | null>>>

/** Savings on general administration (01 without 017 and 018), pipeline/merge.py savings():
 * only the economy of scale within the merged unit's type (research/08 §7.1). */
export interface Savings {
  godina: number
  uprava_zbroj: number
  medijan_pc: number | null
  ocekivano: number | null
  ocekivano_clanice: number | null
  razmjer: number | null
  realno_do: number | null
  jaz_bez_spajanja: number | null
  iznad_10000: boolean
}

/** Incentive for an actual merger under NN 88/2022 t. IX., pipeline/merge.py incentive(). */
export interface Incentive {
  pripaja: string
  s_pravom: string[]
  izravnanje_isplata: number | null
  godisnje: number | null
  ukupno: number | null
  kapitalni_do: number
  omjer_isplate: number | null
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
  /** Payout estimate (pipeline/merge.py payout): share of all full amounts x the budget line. */
  iznos_proracuna?: number
  omjer_prije?: number
  omjer_poslije?: number | null
  isplata_po_clanici?: number[]
  isplata_clanice?: number
  isplata_spojena?: number
  isplata_promjena?: number
  [k: string]: unknown
}

/** Population trend of a merged group or a unit, pipeline/merge.py demography() (decision P4).
 * Shown next to the result, never part of the grade, which uses Popis 2021. */
export interface GroupDemography {
  od: number
  do: number
  /** Summed yearly estimates, od..do; only for the trend, never shown next to Popis 2021. */
  stanovnici: (number | null)[]
  promjena: number | null
  /** Live births − deaths and in − out migration in the year `do`, summed over the members. */
  prirodna: number | null
  migracije: number | null
  /** Each member's population change, in the order of `clanice`. */
  clanice: (number | null)[]
  oznake?: string[]
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
    z5_manjak_udio?: number | null
    z5_zadovoljava?: boolean | null
    oznake?: string[]
    rang: number
    n_skupine: number
  }
  usteda: Savings | null
  izravnanje?: Equalization | null
  poticaj?: Incentive | null
  demografija?: GroupDemography | null
}

export interface SimulatorFile {
  zup_id: number
  zupanija: string
  /** Source of the demographic numbers per year (pipeline/merge.py load_demography). */
  demografija_izvor_po_godini?: Record<string, DzsSource> | null
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
/** api/v1/metodologija.json (pipeline/metodologija.py). */
export interface MethodologyDoc {
  godina: number
  prozor: { ponderi: number[]; opis: string }
  velicine: { oznaka: string; formula: string }[]
  pokazatelji: { oznaka: string; naziv: string; formula: string; ponder: number; pragovi: { vrijednost: number; bodovi: number }[] }[]
  ocjene: { ocjena: number; rijec: string; od_bodova: number }[]
  scenariji: Record<string, Record<string, number>>
  pravila: { oznaka: string; tekst: string }[]
  zastavice: { oznaka: string; tekst: string }[]
  skupine: { razredi: string[]; opis: string }
  ai: {
    opis: string
    model: string
    sustav: string
    pravila: string
    primjer: string
    prompt_sha256: string
    kod: Record<string, string>
    batch: {
      modeli: string[]
      jedinica: number
      tekstova: number
      uvezeno_ai: number
      prikazano_ai: number | null
      uvezeno: string
      llama_cpp_commit: string | null
    } | null
    prompt_jednak_batchu: boolean | null
  }
  simulator: Record<string, string>
  kriterij_10?: string
  revizija?: string
  /** Profile cards that do not enter the score (pipeline/metodologija.py). */
  stanovnistvo_gospodarstvo?: string
  izravnanje_jedinice?: string
  ogranicenja: string[]
}

/** api/v1/skupovi.json: every dataset the project uses (data/reference/skupovi.csv + download log). */
export interface Dataset {
  kljuc: string
  naziv: string
  izdavatelj: string
  url: string
  portal_url: string | null
  licenca: string
  licenca_url: string | null
  pristup: string
  uloga: string
  koristi_se: boolean
  zadnja_izmjena: string | null
  zadnje_preuzimanje?: string | null
}

/** DGU code of Grad Zagreb: a city and a county at once, so it is left out of mergers. */
export const ZAGREB_SIFRA = '01333'
/** Can the simulator and Karta reforme merge this unit (no counties, no Zagreb; merge.Data.eligible)? */
export const canMerge = (u: { vrsta: Vrsta; sifra: string }) => u.vrsta !== 'zupanija' && u.sifra !== ZAGREB_SIFRA

export const loadMethodology = () => get<MethodologyDoc>('metodologija.json')
export const loadDatasets = () => get<Dataset[]>('skupovi.json')
export const loadSource = (slug: string) => get<SourceFile>(`jedinice/${slug}/izvor.json`)
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
  poticaj?: Incentive | null
  demografija?: GroupDemography | null
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
  razmjer_zbroj: number
  jaz_bez_spajanja_zbroj: number
  poticaj_godisnje_zbroj: number
  izravnanje_promjena_zbroj?: number
  izravnanje_isplata_spojene_promjena?: number
  izravnanje_isplata_ostale_promjena?: number
  /** Population change od→do for all merged groups and for the units that stay alone (reforma.demography_all). */
  demografija?: {
    od: number
    do: number
    izvor_po_godini?: Record<string, DzsSource>
    spojene: { stanovnici_od: number; stanovnici_do: number; promjena: number | null } | null
    ostale: { stanovnici_od: number; stanovnici_do: number; promjena: number | null } | null
  } | null
  jedinice: ReformUnit[]
}

export const REFORM_THRESHOLDS = [2500, 5000, 10000] as const
export const loadReform = (prag: number) => get<ReformFile>(`reforma/prag-${prag}.json`)
export const loadSimulator =(zupId: number) => get<SimulatorFile>(`simulator/zup-${String(zupId).padStart(2, '0')}.json`)
export const topoUrl = () => BASE + 'geo/jls.topo.json'
