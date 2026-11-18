import { onScopeDispose } from 'vue'
import { reporting } from '../confirm'

/** Return a guard for work that must not finish once the view is left: `begin()` hands back a check
    that holds until the next `begin()` or `drop()`. e.g. `const ok = g.begin(); g.drop(); ok()` -> false */
export function latest(): { begin: () => () => boolean; drop: () => void } {
  let current = 0
  return {
    begin: () => {
      const mine = ++current
      return () => mine === current
    },
    drop: () => {
      current += 1
    },
  }
}

/** Return what follows a deletion: `deleted` reads the Hub again, then opens it unless the scope has ended. */
export function useDeletion(after: { reload: () => Promise<unknown>; open: () => void }) {
  const leaving = latest()
  onScopeDispose(leaving.drop)
  /* The Hub is read again first, so it draws without the deleted render; a refusal opens it all the same. */
  async function deleted(): Promise<void> {
    const still = leaving.begin()
    await after.reload().catch(() => undefined)
    if (still()) after.open()
  }
  const through = <T>(remove: () => Promise<T>): (() => Promise<T>) =>
    reporting(remove, () => void deleted())
  return { deleted, through }
}
