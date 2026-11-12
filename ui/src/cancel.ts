import { collectionsOf } from './stores/live'
import type { JobSlot } from './types'

/* Whether a render runs for `collection`, as the server's reason for Cancel approve says. */
export function holdsCancel(slot: JobSlot | null, collection: string): boolean {
  return slot?.state === 'running' && collectionsOf(slot).includes(collection)
}

/* Whether an approved sheet is read again: the render slot moved into or out of
   running for its collection. e.g. idle -> running for "a" with "a" open: true */
export function readsAgain(
  before: JobSlot | null,
  after: JobSlot | null,
  collection: string,
  approved: boolean,
): boolean {
  return approved && holdsCancel(before, collection) !== holdsCancel(after, collection)
}
