import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  /** Shown in place of the children once one of them has thrown while rendering or in an effect. */
  fallback: ReactNode
  children: ReactNode
}

/** Without a boundary React removes the whole page when one component throws, and the visitor is
 *  left with an empty screen (a MapLibre map without WebGL 2 did exactly that). */
export class ErrorBoundary extends Component<Props, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  componentDidCatch(error: unknown, info: ErrorInfo) {
    console.warn('Dio stranice se nije mogao prikazati:', error, info.componentStack)
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children
  }
}

/** The last resort for a whole page: a sentence and two ways out instead of an empty screen. */
export function PageFailed() {
  return (
    <p className="mx-auto max-w-3xl px-6 py-20 text-center">
      Ova se stranica nije mogla prikazati.{' '}
      <button type="button" onClick={() => window.location.reload()} className="underline">
        Pokušaj ponovno
      </button>{' '}
      ili se vrati na{' '}
      <a href="#/" className="underline">
        početnu stranicu
      </a>
      .
    </p>
  )
}
