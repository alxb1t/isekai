import { computed, ref } from 'vue'
import { useBatchStore } from '../stores/batch'
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

/** Return the queue's head: the first unapproved sheet of the first flow that has any. */
export function head(info: HubInfo): { digest: string; flow: string } | null {
  const flow = firstFlow(info)
  const digest = flow ? queue(info, flow)[0] : undefined
  return flow && digest ? { digest, flow } : null
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
 * Read from the batch store's hub, which `load` reads again from the run
 * directories, so the rail follows a verb run in the terminal.
 */
export function useQueue(batch: string, flow: string, current: () => string) {
  const store = useBatchStore()
  store.open(batch)
  const info = computed(() => store.hub)
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
      return await store.reloadHub()
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

/* Revise's queue rides in Review's `queue` query: the drafts left after the one
   open, each `digest:flow`. Present, even empty, it ends at the hub. */
export interface Queued {
  digest: string
  flow: string
}

/** Return the query that carries `drafts`. e.g. [{a, f}, {b, f}] -> "a:f,b:f" */
export function reviewQueue(drafts: Queued[]): string {
  return drafts.map((one) => `${one.digest}:${one.flow}`).join(',')
}

/** Return the drafts a `queue` query carries. e.g. "a:f,b:f" -> [{a, f}, {b, f}] */
export function queued(query: string): Queued[] {
  return query
    ? query.split(',').map((one) => {
        const [digest, flow] = one.split(':')
        return { digest, flow }
      })
    : []
}
