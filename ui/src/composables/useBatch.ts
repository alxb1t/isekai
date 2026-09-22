import { computed, ref } from 'vue'
import { batch as readBatch } from '../api'
import type { BatchInfo } from '../types'

/**
 * The batch: which inputs, which one is open, and how many are approved.
 *
 * It is the invocation's argument list and it lives in memory -- nothing on disk
 * says ten photographs belong together, and writing one down would add an
 * artifact to a layout whose own rules make a shape change a hand migration. A
 * restart loses the rail; one retyped command restores it; the sheets are
 * independent of it either way.
 *
 * `useBatch`, not `useRun`: *run* already means one input's directory in this
 * repository, and a composable that took the other meaning would be the first
 * place the two words drifted apart.
 */
export function useBatch() {
  const info = ref<BatchInfo | null>(null)
  const current = ref('')
  const edited = ref(new Set<string>())
  const loading = ref(true)
  const failure = ref<string | null>(null)

  const inputs = computed(() => info.value?.inputs ?? [])

  const index = computed(() => inputs.value.findIndex((i) => i.id === current.value))

  async function load(): Promise<void> {
    try {
      const body = await readBatch()
      info.value = body
      if (body.inputs.length) current.value = body.inputs[0].id
      loading.value = false
    } catch (reason) {
      failure.value = (reason as Error).message
      loading.value = false
    }
  }

  /** Re-read the batch, so the approved count follows the directory. */
  async function refresh(): Promise<void> {
    const body = await readBatch()
    info.value = body
  }

  function select(id: string): void {
    current.value = id
  }

  function step(direction: -1 | 1): void {
    const at = index.value
    if (at < 0 || inputs.value.length === 0) return
    const next = (at + direction + inputs.value.length) % inputs.value.length
    current.value = inputs.value[next].id
  }

  function markEdited(id: string): void {
    if (edited.value.has(id)) return
    edited.value = new Set(edited.value).add(id)
  }

  /* `=== 'approved'` deliberately, and not `!== 'draft'` like the manifest's
     filter. This gates "nothing left to review" -- the closing banner and the
     auto-open of the manifest -- and a re-opened input demonstrably has
     something left: the server accepts a draft update for it. The two
     comparisons are two different questions, not an inconsistency. */
  const allApproved = computed(
    () => inputs.value.length > 0 && inputs.value.every((i) => i.status === 'approved'),
  )

  return {
    info,
    inputs,
    current,
    index,
    edited,
    loading,
    failure,
    allApproved,
    load,
    refresh,
    select,
    step,
    markEdited,
  }
}
