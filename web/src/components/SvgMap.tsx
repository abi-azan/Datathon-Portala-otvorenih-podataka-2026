import { Minus, Plus } from 'lucide-react'
import { useMemo, useRef, useState, type MouseEvent as ReactMouseEvent, type PointerEvent as ReactPointerEvent, type ReactNode } from 'react'
import { VIEW_H, VIEW_W, type Box } from '../lib/geo'

/** A filled shape of the map: a unit, or a group of merged units. */
export interface SvgArea {
  key: string
  d: string
  fill: string
  /** Fill opacity; 1 when left out. */
  opacity?: number
}

/** A line over the fills: county borders, the outline of a selected or merged unit. */
export interface SvgLine {
  key: string
  d: string
  stroke: string
  /** Width in screen pixels, at every zoom. */
  width: number
  opacity?: number
}

interface Props {
  areas: SvgArea[]
  lines?: SvgLine[]
  /** The box to show; the whole country when missing. */
  focus?: Box | null
  label: string
  /** What the tooltip of an area says; no tooltip when it returns nothing. */
  tooltip?: (key: string) => ReactNode
  /** Whether a click on the area does something (the pointer becomes a hand). */
  clickable?: (key: string) => boolean
  onClick?: (key: string) => void
  tooltipWidth?: number
  tooltipHeight?: number
}

const PAD = 14
const FULL: Box = [-PAD, -PAD, VIEW_W + 2 * PAD, VIEW_H + 2 * PAD]
const ZOOM_STEP = 1.6
const MIN_W = VIEW_W / 14 // closest zoom: about 40 km across
const DRAG_PX = 5 // a press that moves less than this is a click, not a pan

const keyAt = (target: EventTarget | null) => (target as Element | null)?.closest?.('[data-k]')?.getAttribute('data-k') ?? null

/** The view for a focus box ("x,y,w,h"): a square around it with some air, or the whole country. */
function fit(focusKey: string): Box {
  if (!focusKey) return FULL
  const [x, y, w, h] = focusKey.split(',').map(Number)
  const side = Math.max(w, h, MIN_W) * 1.3
  return [x + w / 2 - side / 2, y + h / 2 - side / 2, side, side]
}

/** The map without WebGL: the same shapes as SVG paths, with a tooltip, clicks, two zoom buttons and
 *  panning by dragging once zoomed in. No basemap, so it needs neither tiles nor a graphics card. */
export function SvgMap({ areas, lines = [], focus, label, tooltip, clickable, onClick, tooltipWidth = 256, tooltipHeight = 132 }: Props) {
  const wrap = useRef<HTMLDivElement>(null)
  const svg = useRef<SVGSVGElement>(null)
  // the view follows the focus box whenever that changes; in between, the buttons and dragging move it
  const focusKey = focus ? focus.map((v) => v.toFixed(1)).join(',') : ''
  const [view, setView] = useState<Box>(() => fit(focusKey))
  const [fitted, setFitted] = useState(focusKey)
  if (fitted !== focusKey) {
    setFitted(focusKey)
    setView(fit(focusKey))
  }
  const [hover, setHover] = useState<{ key: string; left: number; top: number } | null>(null)
  const drag = useRef<{ x: number; y: number; view: Box; moved: boolean } | null>(null)

  const zoomed = view[2] < FULL[2] - 0.5
  const zoom = (factor: number) => {
    setHover(null)
    setView(([x, y, w, h]) => {
      const nw = Math.min(FULL[2], Math.max(MIN_W, w / factor))
      if (nw >= FULL[2] - 0.5) return FULL
      const nh = (h / w) * nw
      return [x + (w - nw) / 2, y + (h - nh) / 2, nw, nh]
    })
  }

  /** Screen pixels per map unit, as `preserveAspectRatio="xMidYMid meet"` scales the view box. */
  const scale = (v: Box) => {
    const r = svg.current?.getBoundingClientRect()
    return r ? Math.min(r.width / v[2], r.height / v[3]) : 1
  }

  const onPointerDown = (e: ReactPointerEvent) => {
    if (e.button !== 0) return
    drag.current = { x: e.clientX, y: e.clientY, view, moved: false }
  }
  const onPointerMove = (e: ReactPointerEvent) => {
    const d = drag.current
    if (d && e.buttons & 1) {
      const [dx, dy] = [e.clientX - d.x, e.clientY - d.y]
      if (!d.moved && Math.hypot(dx, dy) < DRAG_PX) return
      d.moved = true
      setHover(null)
      if (!zoomed) return
      const s = scale(d.view)
      // the centre of the view stays inside the country's box
      const cx = Math.min(FULL[0] + FULL[2], Math.max(FULL[0], d.view[0] + d.view[2] / 2 - dx / s))
      const cy = Math.min(FULL[1] + FULL[3], Math.max(FULL[1], d.view[1] + d.view[3] / 2 - dy / s))
      setView([cx - d.view[2] / 2, cy - d.view[3] / 2, d.view[2], d.view[3]])
      return
    }
    if (e.pointerType === 'touch') return
    const key = keyAt(e.target)
    const box = wrap.current?.getBoundingClientRect()
    if (!key || !box) return setHover(null)
    const [px, py] = [e.clientX - box.left, e.clientY - box.top]
    // right of the pointer, or left of it near the right edge; above it near the bottom edge
    const left = px + 16 + tooltipWidth > box.width - 8 ? px - 16 - tooltipWidth : px + 16
    const top = py + tooltipHeight > box.height - 8 ? py - tooltipHeight - 12 : py - 12
    setHover({ key, left: Math.max(8, left), top: Math.max(8, top) })
  }
  const onClickMap = (e: ReactMouseEvent) => {
    if (drag.current?.moved) return
    const key = keyAt(e.target)
    if (key && (clickable?.(key) ?? true)) onClick?.(key)
  }

  // the fills are kept between renders, so a moving tooltip does not touch 556 paths
  const fills = useMemo(
    () =>
      areas.map((a) => (
        <path
          key={a.key}
          data-k={a.key}
          d={a.d}
          fill={a.fill}
          fillOpacity={a.opacity ?? 1}
          fillRule="evenodd"
          stroke="#ffffff"
          strokeWidth={0.5}
          vectorEffect="non-scaling-stroke"
          className="transition-[fill,fill-opacity] duration-[650ms] motion-reduce:transition-none"
        />
      )),
    [areas],
  )
  const shapes = useMemo(() => new Map(areas.map((a) => [a.key, a.d])), [areas])
  const tip = hover ? tooltip?.(hover.key) : null
  const hand = hover != null && (clickable?.(hover.key) ?? true)
  const button = 'grid h-[29px] w-[29px] place-items-center text-ink hover:bg-hairline/50 disabled:text-axis disabled:hover:bg-transparent'

  return (
    <div ref={wrap} className="relative h-full w-full overflow-hidden">
      <svg
        ref={svg}
        viewBox={view.map((v) => v.toFixed(2)).join(' ')}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={label}
        className="h-full w-full select-none"
        style={{ cursor: hand ? 'pointer' : zoomed ? 'grab' : 'default', touchAction: zoomed ? 'none' : 'auto' }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerLeave={() => setHover(null)}
        onClick={onClickMap}
      >
        {fills}
        <g fill="none" strokeLinejoin="round" pointerEvents="none">
          {lines.map((l) => (
            <path key={l.key} d={l.d} stroke={l.stroke} strokeWidth={l.width} strokeOpacity={l.opacity ?? 1} vectorEffect="non-scaling-stroke" />
          ))}
          {hover && shapes.has(hover.key) && (
            <path d={shapes.get(hover.key)} stroke="#0b0b0b" strokeWidth={2.2} vectorEffect="non-scaling-stroke" />
          )}
        </g>
      </svg>
      <div className="absolute top-2.5 right-2.5 flex flex-col divide-y divide-hairline overflow-hidden rounded-md border border-hairline bg-card shadow-sm">
        <button type="button" className={button} aria-label="Približi" title="Približi" disabled={view[2] <= MIN_W + 0.5} onClick={() => zoom(ZOOM_STEP)}>
          <Plus className="h-4 w-4" aria-hidden />
        </button>
        <button type="button" className={button} aria-label="Udalji" title="Udalji" disabled={!zoomed} onClick={() => zoom(1 / ZOOM_STEP)}>
          <Minus className="h-4 w-4" aria-hidden />
        </button>
      </div>
      {hover && tip && (
        <div
          className="pointer-events-none absolute z-10 rounded-xl border border-hairline bg-card/95 p-3 shadow-lg backdrop-blur"
          style={{ left: hover.left, top: hover.top, width: tooltipWidth }}
        >
          {tip}
        </div>
      )}
    </div>
  )
}
