import { useEffect, useState } from 'react'
import type { Topology } from 'topojson-specification'
import { topoUrl } from './data'

let pending: Promise<Topology> | null = null

/** geo/jls.topo.json, fetched once for all SVG maps; a failed fetch is tried again by the next map. */
function loadTopology(): Promise<Topology> {
  pending ??= fetch(topoUrl())
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      return r.json() as Promise<Topology>
    })
    .catch((e: unknown) => {
      pending = null
      throw e
    })
  return pending
}

/** The boundaries for an SVG map: null while loading, `failed` when they could not be fetched. */
export function useTopology() {
  const [state, setState] = useState<{ topo: Topology | null; failed: boolean }>({ topo: null, failed: false })
  useEffect(() => {
    let off = false
    loadTopology()
      .then((topo) => !off && setState({ topo, failed: false }))
      .catch(() => !off && setState({ topo: null, failed: true }))
    return () => {
      off = true
    }
  }, [])
  return state
}
