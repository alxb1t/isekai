/* What a render session's record says, read the one way the list and the page
   both read it. */

import type { SessionRecord } from './types'

/* Seconds from `started` to `ended`, or to `now` while it runs; null once ended
   outright. e.g. ("…09:12:00Z", "…09:20:00Z") -> 480 */
export function lasted(
  started: string,
  ended: string | null | undefined,
  running: boolean,
  now: number,
): number | null {
  if (ended) return (Date.parse(ended) - Date.parse(started)) / 1000
  return running ? (now - Date.parse(started)) / 1000 : null
}

/* How many images the session was asked to render, across its flows. */
export function asked(record: SessionRecord): number {
  return Object.values(record.asked).reduce((sum, n) => sum + n, 0)
}

/* The word for how a session ended; a record still reading running whose lifetime
   lock no process holds was ended outright. */
export function outcome(record: SessionRecord): string {
  return record.outcome ?? 'ended, no outcome'
}
