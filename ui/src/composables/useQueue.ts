import { computed, ref } from 'vue'
import { hub } from '../api'
import type { BatchInput, HubInfo } from '../types'

/* The queue is the batch, one flow at a time: that flow's sheets not yet
   approved, in the hub's order (design spec J3). Approving is the only step
   between them; after the last, the hub. */

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
 * Return the sheet Review opens after `digest` is approved, or null for the hub.
 *
 * The next unapproved sheet after it in the hub's order, else the first one
 * left before it. e.g. order a b c, approved b, a and c unapproved -> c
 */
export function after(info: HubInfo, flow: string, digest: string): string | null {
  const left = queue(info, flow).filter((one) => one !== digest)
  const order = info.sources.map((source) => source.digest)
  const at = order.indexOf(digest)
  return left.find((one) => order.indexOf(one) > at) ?? left[0] ?? null
}

/**
 * One batch in one flow, as Review's rail shows it: the queue, and the sheet
 * open now if it has left the queue by being approved.
 *
 * Read from `/api/b/{batch}/hub`, which lists the run directories on every
 * request, so the rail follows a verb run in the terminal.
 */
export function useQueue(batch: string, flow: string, current: () => string) {
  const info = ref<HubInfo | null>(null)
  const edited = ref(new Set<string>())
  const loading = ref(true)

  const inputs = computed<BatchInput[]>(() => {
    const held = info.value
    if (!held) return []
    const waiting = new Set(queue(held, flow))
    return held.sources.flatMap((source) => {
      const status = source.cells[flow]?.status
      if (!source.digest || !status) return []
      if (!waiting.has(source.digest) && source.digest !== current()) return []
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
  })

  /* Every sheet in the flow holding an approved artifact, re-opened ones
     included: what the directory holds, not what the rail shows. */
  const approved = computed(() =>
    (info.value?.sources ?? []).filter((source) => {
      const status = source.cells[flow]?.status
      return status === 'approved' || status === 're-opened'
    }).length,
  )

  /* Every sheet in the flow, the population `approved` is counted from: the
     rail's length leaves the approved ones out. */
  const sheets = computed(
    () => (info.value?.sources ?? []).filter((source) => source.cells[flow]?.status).length,
  )

  /** Re-read the hub; a refusal is thrown to the caller, who decides where it shows. */
  async function load(): Promise<HubInfo> {
    try {
      info.value = await hub(batch)
      return info.value
    } finally {
      loading.value = false
    }
  }

  function markEdited(id: string): void {
    if (edited.value.has(id)) return
    edited.value = new Set(edited.value).add(id)
  }

  return { info, inputs, approved, sheets, edited, loading, load, markEdited }
}
