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
  { value: 2, word: 'nestabilno', color: '#f5938c', ink: '#0b0b0b' },
  { value: 1, word: 'vrlo nestabilno', color: '#9e3432', ink: '#ffffff' },
]

export const grade = (g: number | null | undefined) => GRADES.find((x) => x.value === g)

/** The grade a number of points falls in (80 / 60 / 40 / 20, PLAN §3.2); used to colour a component's points. */
export const gradeOfPoints = (p: number) => (p >= 80 ? 5 : p >= 60 ? 4 : p >= 40 ? 3 : p >= 20 ? 2 : 1)

/** A row of a map legend: colour, an optional grade number, the label and an optional unit count. */
export interface LegendRow {
  key: string | number
  color: string
  value?: number
  label: string
  /** How many units fall in the row; omitted when the page shows the counts elsewhere. */
  n?: number
}

/** The grade rows of a map legend, with the unit counts when given. */
export const gradeRows = (counts?: Record<number, number>): LegendRow[] =>
  GRADES.map((g) => ({ key: g.value, color: g.color, value: g.value, label: g.word, n: counts ? (counts[g.value] ?? 0) : undefined }))

/** Display-only: texts stored before the grade words changed (5.11.) use the old words
 *  ("umjereno", "pod pritiskom", "ozbiljan pritisak"); their verification stays unchanged. */
export const normalizeGradeLabels = (text: string) =>
  text
    .replace(/\bumjereno\b(?!\s+stabilno)/g, 'umjereno stabilno')
    .replaceAll('ozbiljan pritisak', 'vrlo nestabilno')
    .replaceAll('pod velikim pritiskom', 'vrlo nestabilno')
    .replaceAll('pod pritiskom', 'nestabilno')

export const VRSTA: Record<string, string> = { opcina: 'općina', grad: 'grad', zupanija: 'županija' }

/** Peer-group name for reading (same rule as facts.group_label): "općine do 2.000" -> "općine do
 *  2.000 stanovnika", with an en dash in a range. The group key itself stays as it is. */
export const groupLabel = (skupina: string) => {
  const s = skupina.replace(/(?<=\d)-(?=\d)/g, '–')
  return /\d$/.test(s) ? `${s} stanovnika` : s
}

/** Roman numeral for the development groups I–VIII. */
export const roman = (n: number) => ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'][n] ?? String(n)

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
  { key: 'I4', score: 'S4', name: 'Servis duga', hint: 'Otplata kredita i kamata kao udio zakonske osnovice (prihoda od kojih zakon računa granicu zaduživanja).' },
  { key: 'I5', score: 'S5', name: 'Dospjele obveze', hint: 'Neplaćene obveze kojima je prošao rok, kao udio rashoda poslovanja.' },
] as const

export const FLAGS: Record<string, string> = {
  // the same wording as pipeline/facts.py FLAGS, which the fact packs and the AI text use
  Z1: 'Preneseni manjak iz prethodnih godina veći od 5 % tekućih prihoda',
  Z2: 'Otplata duga i dospjele obveze iznad 20 % zakonske osnovice',
  Z3: 'Rashodi poslovanja veći od tekućih prihoda dvije godine zaredom',
  Z4: 'Novca na računu manje nego za mjesec dana rashoda poslovanja',
}

/** Z5, the 10 % criterion of the Government conclusion of 16.4.2026 (methodology.criterion_10).
 * Approximate when EU projects are large, because PR-RAS does not split spending by source.
 * Shown as an additional indicator, never among the warnings: in 2025 about half of the units do
 * not meet it on this approximate calculation (decided 5.11.). */
export function criterion10(udio: number | null | undefined, ok: boolean | null | undefined, oznake?: string[]) {
  if (udio == null || ok == null) return null
  const approx = oznake?.includes('eu_projekt') ?? false
  return {
    ok,
    approx,
    value: ok ? 'zadovoljava' : 'ne zadovoljava',
    hint: `manjak ${pct(udio)} prihoda bez EU izvora${approx ? '; približno zbog velikih EU projekata' : ''}`,
  }
}

export const QUALITY: Record<string, string> = {
  kredit_iskazan_kao_dospio:
    'U Bilanci je kredit iskazan u cijelosti kao dospio, ali se redovno otplaćuje ili se još povlači, pa se ne broji u dospjele obveze.',
  funkcije_ne_odgovaraju_rashodima: 'Zbroj rashoda po funkcijama ne odgovara ukupnim rashodima.',
  izravnanje_na_drugom_kontu:
    'Fiskalno izravnanje nije knjiženo na kontu 6353, nego na drugom kontu pomoći, pa se za zakonsku osnovicu uzima iznos iz odluke Ministarstva financija.',
  izravnanje_nije_medu_pomocima:
    'Dio fiskalnog izravnanja iz odluke Ministarstva financija nije knjižen među pomoćima (vjerojatno među porezima), pa se u zakonsku osnovicu ne dodaje dvaput.',
  konto_6353_vise_od_odluke:
    'Na kontu 6353 knjiženo je više od fiskalnog izravnanja iz odluke Ministarstva financija; razlika se računa kao ostala pomoć.',
}
