import { ref } from 'vue'
import { tags } from '../api'
import type { VocabEntry } from '../types'

/* Debounce. Long enough that a fragment typed at speed costs one request rather
   than five, short enough that the rows are there before the operator has
   decided what they are looking at. The query itself costs about 0.25 ms on the
   server, two orders of magnitude under this. */
const DEBOUNCE = 120

/* How many rows the dropdown draws. The footer states the true match count, so
   narrowing the fragment is the way to see fewer -- there is nothing to scroll. */
const ROWS = 10

/**
 * The tag search, answered by the pipeline's own vocabulary.
 *
 * **This composable ranks nothing.** `vocabulary.search()` orders by post count
 * and the server hands that order over intact; sorting again here would put a
 * second copy of the ranking rule in TypeScript, which is the duplication
 * `GET /api/tags?q=` was introduced to delete. The post count is the reason the
 * surface exists at all -- it predicts how hard a tag lands -- so the decision
 * has to be identical however it is reached.
 */
export function useVocabulary() {
  const matches = ref<VocabEntry[]>([])
  const total = ref(0)

  let timer: ReturnType<typeof setTimeout> | undefined
  // A slow earlier answer must never overwrite a newer one: the operator is
  // typing, and a stale dropdown is worse than an empty one.
  let generation = 0

  function clear(): void {
    if (timer !== undefined) clearTimeout(timer)
    generation += 1
    matches.value = []
    total.value = 0
  }

  function search(fragment: string): void {
    if (timer !== undefined) clearTimeout(timer)
    const asked = (generation += 1)
    if (!fragment.trim()) {
      matches.value = []
      total.value = 0
      return
    }
    timer = setTimeout(() => {
      tags(fragment, ROWS)
        .then((found) => {
          if (asked !== generation) return
          matches.value = found.matches
          total.value = found.total
        })
        .catch(() => {
          if (asked !== generation) return
          matches.value = []
          total.value = 0
        })
    }, DEBOUNCE)
  }

  return { matches, total, search, clear }
}
