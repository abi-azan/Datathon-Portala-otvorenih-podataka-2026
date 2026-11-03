import { Card, Eyebrow } from '../components/Layout'
import { GRADES } from '../lib/format'

// Short version of PLAN §3; the full methodology page comes with the documentation.
export function Methodology() {
  return (
    <main className="mx-auto max-w-3xl px-6 pt-10">
      <Eyebrow>Metodologija i podaci</Eyebrow>
      <h1 className="mt-2 font-serif text-4xl font-semibold tracking-tight">Kako se računa ocjena</h1>
      <p className="mt-4 text-lg leading-relaxed text-ink-2">
        Ocjena mjeri financijsku stabilnost proračuna jedinice: koliko tekući prihodi pokrivaju rashode, koliko je
        dug opterećenje i plaća li jedinica račune na vrijeme. Ne mjeri kvalitetu usluga ni razvijenost.
      </p>
      <Card className="mt-8">
        <Eyebrow>Pet pokazatelja</Eyebrow>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-ink-2">
          <li>Operativni saldo: tekući prihodi minus rashodi poslovanja, prema tekućim prihodima (ponder 20).</li>
          <li>Slobodni saldo: operativni saldo nakon otplate glavnice (ponder 20).</li>
          <li>Godine otplate neto duga iz operativnog viška (ponder 15).</li>
          <li>Servis duga prema zakonskoj osnovici (ponder 15).</li>
          <li>Dospjele neplaćene obveze prema rashodima poslovanja (ponder 30).</li>
        </ol>
        <p className="mt-4 text-sm text-muted">
          Bodovi 0–100 računaju se interpolacijom između pragova iz prakse KDZ-a (Austrija) i INEKO-a (Slovačka).
        </p>
      </Card>
      <Card className="mt-6">
        <Eyebrow>Ljestvica</Eyebrow>
        <ul className="mt-3 space-y-2">
          {GRADES.map((g, i) => (
            <li key={g.value} className="flex items-center gap-3 text-sm">
              <span className="h-4 w-7 rounded" style={{ background: g.color, boxShadow: 'inset 0 0 0 1px rgb(0 0 0 / 0.12)' }} />
              <strong className="w-3">{g.value}</strong>
              <span className="flex-1">{g.word}</span>
              <span className="tabular text-muted">{['80–100', '60–80', '40–60', '20–40', '0–20'][i]} bodova</span>
            </li>
          ))}
        </ul>
      </Card>
    </main>
  )
}
