// MapLibre GL 6 draws on WebGL 2 only and throws when the browser cannot give it one (remote desktop,
// hardware acceleration switched off, old graphics drivers). The pages ask here first and draw the SVG
// map instead (components/GradeMapSvg, ReformMapSvg).
let known: boolean | null = null

/** Whether this browser gives out a WebGL 2 context. `?webgl=0` before the hash answers no, so the
 *  SVG maps can be checked on any machine: .../?webgl=0#/ */
export function webgl2Available(): boolean {
  if (known != null) return known
  known = false
  try {
    if (new URLSearchParams(window.location.search).get('webgl') === '0') return known
    const gl = document.createElement('canvas').getContext('webgl2')
    known = gl != null
    // give the test context back at once: browsers allow only a handful per page
    gl?.getExtension('WEBGL_lose_context')?.loseContext()
  } catch {
    known = false
  }
  return known
}
