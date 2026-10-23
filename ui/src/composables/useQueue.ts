import { computed, ref } from 'vue'
import { useBatchStore } from '../stores/batch'
import type { BatchInput, HubInfo } from '../types'

/* Review walks the batch one flow at a time (design spec J3): its head opens
   first, and its rail lists what is not yet rendered. */

/** Return the digests of `flow`'s unapproved sheets, in the hub's order. */
export function queue(info: HubInfo, flow: string): string[] {
  return info.sources.flatMap((source) => {
    const status = source.cells[flow]?.status
    return source.digest && status && status !== 'approved' ? [source.digest] : []
  })
}

/** Return the first flow, in the hub's order, that has an unapproved sheet. */
export function firstFlow(info: HubInfo): string | null {
  return info.flows.find((flow) => queue(info, flow).length > 0) ?? null
}

/**
 * Return the sheet a batch's Review opens on, or null for none.
 *
 * The first unapproved sheet of the first flow that has one, else the first
 * approved sheet whose newest approval lacks images, flow by flow.
 */
export function head(info: HubInfo): { digest: string; flow: string } | null {
  const flow = firstFlow(info)
  if (flow) return { digest: queue(info, flow)[0], flow }
  for (const one of info.flows) {
    const source = info.sources.find((held) => held.digest && (held.cells[one]?.short ?? 0) > 0)
    if (source?.digest) return { digest: source.digest, flow: one }
  }
  return null
}

/**
 * Return `flow`'s sheets Review's rail lists, in the hub's order: every one
 * unapproved or short of its images, and the one open now.
 *
 * e.g. a unapproved, b approved and short, c approved and rendered -> [a, b]
 */
export function rail(info: HubInfo, flow: string, current: string): BatchInput[] {
  return info.sources.flatMap((source) => {
    const cell = source.cells[flow]
    const status = cell?.status
    if (!source.digest || !status) return []
    const waiting = status !== 'approved' || (cell.short ?? 0) > 0
    if (!waiting && source.digest !== current) return []
    return [
      {
        id: source.digest,
        name: source.name,
        width: source.width ?? 1,
        height: source.height ?? 1,
        status,
      },
    ]
  })
}

/**
 * One batch in one flow, as Review's rail shows it.
 *
 * Read from the batch store's hub, which `load` reads again from the run
 * directories, so the rail follows a verb run in the terminal.
 */
export function useQueue(batch: string, flow: string, current: () => string) {
  const store = useBatchStore()
  store.open(batch)
  const info = computed(() => store.hub)
  const edited = ref(new Set<string>())
  const loading = ref(true)

  const inputs = computed<BatchInput[]>(() =>
    info.value ? rail(info.value, flow, current()) : [],
  )

  /* The rail's sheets holding an approved artifact, re-opened ones included:
     what the directory holds, not what the sheet shows. */
  const approved = computed(
    () => inputs.value.filter((input) => input.status !== 'draft').length,
  )

  /** Re-read the hub; a refusal is thrown to the caller, who decides where it shows. */
  async function load(): Promise<HubInfo> {
    try {
      return await store.reloadHub()
    } finally {
      loading.value = false
    }
  }

  function markEdited(id: string): void {
    if (edited.value.has(id)) return
    edited.value = new Set(edited.value).add(id)
  }

  return { info, inputs, approved, edited, loading, load, markEdited }
}
