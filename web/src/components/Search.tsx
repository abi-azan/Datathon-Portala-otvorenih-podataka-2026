import { Search as SearchIcon } from 'lucide-react'
import { useId, useMemo, useRef, useState, type RefObject } from 'react'
import type { UnitIndex } from '../lib/data'
import { VRSTA, fold, num } from '../lib/format'
import { go, unitHref } from '../lib/router'
import { GradeChip } from './Grade'

interface Props {
  units: UnitIndex[]
  year: string
  autoFocus?: boolean
  /** Called with the picked unit instead of opening its profile (the simulator). */
  onPick?: (u: UnitIndex) => void
  /** Why a unit cannot be picked; such options are shown but disabled. */
  disabledReason?: (u: UnitIndex) => string | undefined
  label?: string
  placeholder?: string
  /** The text input, for a parent that moves focus back to it (the simulator after a removal). */
  inputRef?: RefObject<HTMLInputElement | null>
}

/** "Pronađi svoju općinu": accessible combobox, diacritics-insensitive. */
export function Search({
  units,
  year,
  autoFocus = false,
  onPick,
  disabledReason,
  label = 'Pronađi svoju općinu, grad ili županiju',
  placeholder = 'Pronađi svoju općinu ili grad…',
  inputRef,
}: Props) {
  const [q, setQ] = useState('')
  const [active, setActive] = useState(0)
  const [open, setOpen] = useState(false)
  const listId = useId()
  const own = useRef<HTMLInputElement>(null)
  const input = inputRef ?? own

  const keyed = useMemo(() => units.map((u) => ({ u, k: fold(u.naziv.replace(/^(Općina|Grad) /, '')) })), [units])
  const hits = useMemo(() => {
    const f = fold(q.trim())
    if (!f) return []
    const starts = keyed.filter((x) => x.k.startsWith(f))
    const inside = keyed.filter((x) => !x.k.startsWith(f) && (x.k.includes(f) || fold(x.u.naziv).includes(f)))
    return [...starts, ...inside].slice(0, 8).map((x) => x.u)
  }, [q, keyed])

  const pick = (u: UnitIndex) => {
    if (disabledReason?.(u)) return
    setOpen(false)
    setQ('')
    if (onPick) {
      onPick(u)
      input.current?.focus()
    } else go(unitHref(u.slug))
  }

  return (
    <div className="relative">
      <label htmlFor={`${listId}-input`} className="sr-only">
        {label}
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
          placeholder={placeholder}
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
          {hits.map((u, i) => {
            const reason = disabledReason?.(u)
            return (
              <li
                key={u.slug}
                id={`${listId}-${u.slug}`}
                role="option"
                aria-selected={i === active}
                aria-disabled={reason ? true : undefined}
                onMouseDown={(e) => {
                  e.preventDefault()
                  pick(u)
                }}
                onMouseEnter={() => setActive(i)}
                className={`flex items-center gap-3 px-4 py-2.5 ${reason ? 'cursor-not-allowed' : 'cursor-pointer'} ${i === active ? 'bg-page' : ''}`}
              >
                <div className={`min-w-0 flex-1 ${reason ? 'opacity-55' : ''}`}>
                  <div className="truncate font-medium">{u.naziv}</div>
                  <div className="truncate text-xs text-muted">
                    {reason ??
                      `${VRSTA[u.vrsta]}${u.vrsta !== 'zupanija' ? ` · ${u.zupanija}` : ''} · ${num(u.stanovnici)} stanovnika`}
                  </div>
                </div>
                <GradeChip g={u.ocjena[year]} />
              </li>
            )
          })}
        </ul>
      )}
      {/* live region stays mounted so screen readers announce the empty result */}
      <p
        role="status"
        className={
          open && q.trim() !== '' && hits.length === 0
            ? 'absolute z-20 mt-2 w-full rounded-xl border border-hairline bg-card px-4 py-3 text-sm text-ink-2 shadow-xl'
            : 'sr-only'
        }
      >
        {open && q.trim() !== '' && hits.length === 0
          ? `Nema jedinice s nazivom „${q.trim()}”. Provjerite pravopis ili upišite početak naziva, npr. „povlj”.`
          : ''}
      </p>
    </div>
  )
}
