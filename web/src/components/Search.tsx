import { Search as SearchIcon } from 'lucide-react'
import { useId, useMemo, useRef, useState } from 'react'
import type { UnitIndex } from '../lib/data'
import { VRSTA, fold, num } from '../lib/format'
import { go, unitHref } from '../lib/router'
import { GradeChip } from './Grade'

/** "Pronađi svoju općinu": accessible combobox, diacritics-insensitive. */
export function Search({ units, year, autoFocus = false }: { units: UnitIndex[]; year: string; autoFocus?: boolean }) {
  const [q, setQ] = useState('')
  const [active, setActive] = useState(0)
  const [open, setOpen] = useState(false)
  const listId = useId()
  const input = useRef<HTMLInputElement>(null)

  const keyed = useMemo(() => units.map((u) => ({ u, k: fold(u.naziv.replace(/^(Općina|Grad) /, '')) })), [units])
  const hits = useMemo(() => {
    const f = fold(q.trim())
    if (!f) return []
    const starts = keyed.filter((x) => x.k.startsWith(f))
    const inside = keyed.filter((x) => !x.k.startsWith(f) && (x.k.includes(f) || fold(x.u.naziv).includes(f)))
    return [...starts, ...inside].slice(0, 8).map((x) => x.u)
  }, [q, keyed])

  const pick = (u: UnitIndex) => {
    setOpen(false)
    setQ('')
    go(unitHref(u.slug))
  }

  return (
    <div className="relative">
      <label htmlFor={`${listId}-input`} className="sr-only">
        Pronađi svoju općinu, grad ili županiju
      </label>
      <div className="flex items-center gap-3 rounded-xl border border-axis bg-card px-4 py-3 shadow-sm transition focus-within:border-ink focus-within:shadow-md">
        <SearchIcon className="h-5 w-5 shrink-0 text-muted" aria-hidden />
        <input
          id={`${listId}-input`}
          ref={input}
          autoFocus={autoFocus}
          value={q}
          onChange={(e) => {
            setQ(e.target.value)
            setActive(0)
            setOpen(true)
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 120)}
          onKeyDown={(e) => {
            if (e.key === 'ArrowDown') {
              e.preventDefault()
              setActive((a) => Math.min(a + 1, hits.length - 1))
            } else if (e.key === 'ArrowUp') {
              e.preventDefault()
              setActive((a) => Math.max(a - 1, 0))
            } else if (e.key === 'Enter' && hits[active]) {
              pick(hits[active])
            } else if (e.key === 'Escape') {
              setOpen(false)
            }
          }}
          placeholder="Pronađi svoju općinu ili grad…"
          className="w-full bg-transparent text-base outline-none placeholder:text-muted focus-visible:outline-none"
          role="combobox"
          aria-expanded={open && hits.length > 0}
          aria-controls={listId}
          aria-activedescendant={hits[active] ? `${listId}-${hits[active].slug}` : undefined}
          autoComplete="off"
        />
      </div>
      {open && hits.length > 0 && (
        <ul
          id={listId}
          role="listbox"
          className="absolute z-20 mt-2 w-full overflow-hidden rounded-xl border border-hairline bg-card py-1 shadow-xl"
        >
          {hits.map((u, i) => (
            <li
              key={u.slug}
              id={`${listId}-${u.slug}`}
              role="option"
              aria-selected={i === active}
              onMouseDown={(e) => {
                e.preventDefault()
                pick(u)
              }}
              onMouseEnter={() => setActive(i)}
              className={`flex cursor-pointer items-center gap-3 px-4 py-2.5 ${i === active ? 'bg-page' : ''}`}
            >
              <div className="min-w-0 flex-1">
                <div className="truncate font-medium">{u.naziv}</div>
                <div className="truncate text-xs text-muted">
                  {VRSTA[u.vrsta]}
                  {u.vrsta !== 'zupanija' && ` · ${u.zupanija}`} · {num(u.stanovnici)} st.
                </div>
              </div>
              <GradeChip g={u.ocjena[year]} />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
