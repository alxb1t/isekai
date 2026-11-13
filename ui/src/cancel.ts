import { collectionsOf } from './stores/live'
import type { JobSlot } from './types'

/* Whether a render runs for `collection`, as the server's reason for Cancel approve says. */
export function holdsCancel(slot: JobSlot | null, collection: string): boolean {
  return slot?.state === 'running' && collectionsOf(slot).includes(collection)
}

/** What the watcher reads of the open sheet. */
export interface Reading {
  loading: boolean
  readonly: boolean
  detail: unknown
}

/** Read the sheet again `now`, `later` once the read in flight lands, or `no`. */
export type Again = 'now' | 'later' | 'no'

/* Whether an approved sheet is read again: the render slot moved into or out of
   running for its collection. e.g. idle -> running for "a" with "a" open and approved: 'now' */
export function readsAgain(
  before: JobSlot | null,
  after: JobSlot | null,
  collection: string,
  sheet: Reading,
): Again {
  if (holdsCancel(before, collection) === holdsCancel(after, collection)) return 'no'
  if (sheet.loading) return 'later'
  return sheet.readonly && sheet.detail !== null ? 'now' : 'no'
}

/** A value the page holds, as a ref or a computed one is read. */
interface Held<T> {
  readonly value: T
}

/** The sheet's own refs, which `rereads` reads each time. */
export interface Sheet {
  loading: Held<boolean>
  readonly: Held<boolean>
  detail: Held<unknown>
}

export function rereads(collection: () => string, sheet: Sheet, reread: () => void) {
  const reading = (): Reading => ({
    loading: sheet.loading.value,
    readonly: sheet.readonly.value,
    detail: sheet.detail.value,
  })
  let missed = false
  return {
    moved(before: JobSlot | null, after: JobSlot | null): void {
      const again = readsAgain(before, after, collection(), reading())
      if (again === 'later') missed = true
      if (again === 'now') reread()
    },
    landed(): void {
      const now = reading()
      if (now.loading) return
      const owed = missed && now.readonly && now.detail !== null
      missed = false
      if (owed) reread()
    },
  }
}
