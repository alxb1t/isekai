import { computed, ref } from 'vue'
import { useBatchStore } from '../stores/batch'
import type { BatchInput, HubCell, HubInfo } from '../types'

/* Review walks the batch one flow at a time (design spec J3): with two or more
   flows waiting the operator chooses one, its head opens first, and its rail
   lists what is not yet rendered. */

/** Return whether a cell's sheet waits for review: it has one, not yet approved. */
const unapproved = (cell: HubCell | undefined) =>
  Boolean(cell?.status && cell.status !== 'approved')

/** Return whether a cell's newest approval lacks images. */
const short = (cell: HubCell | undefined) => (cell?.short ?? 0) > 0

/** Return the digests of `flow`'s unapproved sheets, in the hub's order. */
export function queue(info: HubInfo, flow: string): string[] {
  return info.sources.flatMap((source) =>
    source.digest && unapproved(source.cells[flow]) ? [source.digest] : [],
  )
}

/** Another flow's unapproved sheets, and how many. */
export interface Waiting {
  flow: string
  count: number
}

/**
 * Return each flow but `flow` holding unapproved sheets, from the flow after
 * `flow` round to the one before it.
 *
 * e.g. flows [f, g, h] open on g, f 1 and h 2 waiting -> [{h, 2, …}, {f, 1, …}]
 */
export function waiting(info: HubInfo, flow: string): Waiting[] {
  const at = info.flows.indexOf(flow)
  const others = [...info.flows.slice(at + 1), ...info.flows.slice(0, Math.max(at, 0))]
  return others.flatMap((other) => {
    const count = queue(info, other).length
    return count ? [{ flow: other, count }] : []
  })
}

/** A flow holding sheets to review: how many wait to be approved, how many lack
    images, and their sources, in the hub's order. */
export interface FlowWaiting {
  flow: string
  approve: number
  short: number
  sources: { name: string; digest: string }[]
}

/**
 * Return each flow holding a sheet unapproved or short of its images, in the
 * hub's order: the chooser's rows.
 *
 * e.g. f: a unapproved, b short; g: none -> [{f, approve 1, short 1, [a, b]}]
 */
export function flowsWaiting(info: HubInfo): FlowWaiting[] {
  return info.flows.flatMap((flow) => {
    const cells = info.sources.flatMap((source) => {
      const cell = source.cells[flow]
      return source.digest && (unapproved(cell) || short(cell))
        ? [{ name: source.name, digest: source.digest, cell }]
        : []
    })
    if (!cells.length) return []
    return [
      {
        flow,
        approve: cells.filter((one) => unapproved(one.cell)).length,
        short: cells.filter((one) => short(one.cell)).length,
        sources: cells.map(({ name, digest }) => ({ name, digest })),
      },
    ]
  })
}

/** Return whether a batch's Review is the chooser: two or more flows wait. */
export const chooses = (info: HubInfo): boolean => flowsWaiting(info).length > 1

/**
 * Return the sheet Review opens on among `flows`, or null for none.
 *
 * The first unapproved sheet of the first flow that has one, else the first
 * approved sheet whose newest approval lacks images, flow by flow.
 */
export function head(
  info: HubInfo,
  flows: string[] = info.flows,
): { digest: string; flow: string } | null {
  for (const waits of [unapproved, short])
    for (const flow of flows) {
      const source = info.sources.find((one) => one.digest && waits(one.cells[flow]))
      if (source?.digest) return { digest: source.digest, flow }
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
    if (!unapproved(cell) && !short(cell) && source.digest !== current) return []
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
  /* The other flows' unapproved sheets, which the rail's head names. */
  const others = computed(() => (info.value ? waiting(info.value, flow) : []))

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

  return { info, inputs, others, approved, edited, loading, load, markEdited }
}
