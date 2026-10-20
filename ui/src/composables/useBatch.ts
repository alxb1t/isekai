import { computed, ref } from 'vue'
import { hub } from '../api'
import type { BatchInput, HubInfo } from '../types'

/**
 * One batch in one flow, as Review's rail shows it: the sources with a sheet in
 * that flow, in the hub's order, each with where stage ③ stands.
 *
 * Read from `/api/b/{batch}/hub`, which lists the run directories on every
 * request, so the rail follows a verb run in the terminal.
 */
export function useBatch(batch: string, flow: string) {
  const info = ref<HubInfo | null>(null)
  const edited = ref(new Set<string>())
  const loading = ref(true)
  const failure = ref<string | null>(null)

  const inputs = computed<BatchInput[]>(() =>
    (info.value?.sources ?? []).flatMap((source) => {
      const status = source.cells[flow]?.status
      if (!source.digest || !status) return []
      return [
        {
          id: source.digest,
          name: source.name,
          width: source.width ?? 1,
          height: source.height ?? 1,
          status,
        },
      ]
    }),
  )

  /* The server's count of inputs holding an approved artifact, re-opened ones
     included: what the directory holds, not what the rail calls it. */
  const approved = computed(() => inputs.value.filter((i) => i.status !== 'draft').length)

  async function load(): Promise<void> {
    try {
      info.value = await hub(batch)
      failure.value = null
    } catch (reason) {
      failure.value = (reason as Error).message
    } finally {
      loading.value = false
    }
  }

  function markEdited(id: string): void {
    if (edited.value.has(id)) return
    edited.value = new Set(edited.value).add(id)
  }

  /* `=== 'approved'` deliberately: a re-opened input has something left. */
  const allApproved = computed(
    () => inputs.value.length > 0 && inputs.value.every((i) => i.status === 'approved'),
  )

  return { info, inputs, approved, edited, loading, failure, allApproved, load, markEdited }
}
