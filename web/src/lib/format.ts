// Croatian number formats and the grade scale shared by every view.

const nf = (digits: number) =>
  new Intl.NumberFormat('hr-HR', { minimumFractionDigits: digits, maximumFractionDigits: digits })

export const num = (x: number | null | undefined, digits = 0) => (x == null ? '–' : nf(digits).format(x))
export const pct = (share: number | null | undefined, digits = 1) =>
  share == null ? '–' : `${nf(digits).format(share * 100)} %`
export const eur = (x: number | null | undefined, digits = 0) => (x == null ? '–' : `${nf(digits).format(x)} €`)

export interface GradeMeta {
  value: number
  word: string
  color: string
  ink: string // text colour on the grade fill
}

export const GRADES: GradeMeta[] = [
  { value: 5, word: 'vrlo stabilno', color: '#1c5cab', ink: '#ffffff' },
  { value: 4, word: 'stabilno', color: '#86b6ef', ink: '#0b0b0b' },
  { value: 3, word: 'umjereno stabilno', color: '#e6e4dd', ink: '#0b0b0b' },
  { value: 2, word: 'pod pritiskom', color: '#f5938c', ink: '#0b0b0b' },
  { value: 1, word: 'pod velikim pritiskom', color: '#9e3432', ink: '#ffffff' },
]

export const grade = (g: number | null | undefined) => GRADES.find((x) => x.value === g)

/** Display-only terminology; stored AI texts and their verification stay unchanged. */
export const normalizeGradeLabels = (text: string) =>
  text.replace(/\bumjereno\b(?!\s+stabilno)/g, 'umjereno stabilno').replaceAll('ozbiljan pritisak', 'pod velikim pritiskom')

export const VRSTA: Record<string, string> = { opcina: 'općina', grad: 'grad', zupanija: 'županija' }

/** Case- and diacritics-insensitive key for search ("Kloštar" matches "klostar"). */
export const fold = (s: string) =>
  s
    .toLowerCase()
    .replace(/đ/g, 'dj')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')

export const COMPONENTS = [
  { key: 'I1', score: 'S1', name: 'Operativni saldo', hint: 'Koliko tekući prihodi premašuju rashode poslovanja.' },
  { key: 'I2', score: 'S2', name: 'Slobodni saldo', hint: 'Što ostaje nakon otplate glavnice kredita.' },
  { key: 'I3', score: 'S3', name: 'Godine otplate duga', hint: 'Za koliko bi se godina neto dug otplatio iz operativnog viška.' },
  { key: 'I4', score: 'S4', name: 'Servis duga', hint: 'Otplata kredita i kamata prema zakonskoj osnovici.' },
  { key: 'I5', score: 'S5', name: 'Dospjele obveze', hint: 'Neplaćene obveze kojima je prošao rok, prema rashodima.' },
] as const

export const FLAGS: Record<string, string> = {
  Z1: 'Preneseni manjak veći od 5 % tekućih prihoda',
  Z2: 'Otplata duga i dospjele obveze blizu zakonskog limita',
  Z3: 'Operativni manjak dvije godine zaredom',
  Z4: 'Novca na računu manje nego za mjesec dana rashoda',
}

export const QUALITY: Record<string, string> = {
  kredit_iskazan_kao_dospio:
    'U Bilanci je cijeli kredit iskazan kao dospio, ali se redovno otplaćuje, pa se ne broji u dospjele obveze.',
  funkcije_ne_odgovaraju_rashodima: 'Zbroj rashoda po funkcijama ne odgovara ukupnim rashodima.',
}
