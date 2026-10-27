import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { checkBilling as askBilling, runningSessions, stopJob } from '../api'
import type {
  Billing,
  FileState,
  HubInfo,
  JobKind,
  JobSlot,
  JobSlots,
  RunningRender,
  RunningSession,
} from '../types'
import { noun } from '../words'

/* Whether a pod may be billing or the window is past its end. */
export function alerting(found: Billing | null): boolean {
  return Boolean(found && (found.pod || found.volume?.state === 'band'))
}

/* `mm:ss` of a span in seconds. e.g. 401 -> "06:41" */
export function clock(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds))
  const minutes = String(Math.floor(whole / 60)).padStart(2, '0')
  return `${minutes}:${String(whole % 60).padStart(2, '0')}`
}

/* Every collection a job renders, its own first. */
export function collectionsOf(slot: JobSlot): string[] {
  return slot.collections ?? [slot.collection]
}

/* The disk's running records, one render per id, in the order first read.
   e.g. [{b, s}, {c, s}] -> [{collections: [b, c], id: s}] */
export function grouped(found: RunningSession[]): RunningRender[] {
  const renders = new Map<string, RunningRender>()
  for (const one of found) {
    const held = renders.get(one.id)
    if (held) held.collections.push(one.collection)
    else renders.set(one.id, { collections: [one.collection], id: one.id, started: one.started })
  }
  return [...renders.values()]
}

/* What the stream names: the collection the screen shows and the import it has open. */
interface Target {
  collection: string | null
  staging: string | null
}

/* The kinds of event the stream sends. */
const KINDS = ['snapshot', 'job', 'billing', 'cell', 'file'] as const
type Kind = (typeof KINDS)[number]
type Handler = (data: unknown) => void

/* What every connect sends first: both slots, billing, and the hub and files it names. */
export interface Snapshot {
  jobs: JobSlots
  billing: Billing
  hub?: HubInfo
  files?: Record<string, FileState>
}

/* Both job slots, billing and the open import's files, live, for every screen,
   from the page's one stream. Every connect brings a snapshot, so opening it
   again for another collection or import loses nothing. */
export const useLiveStore = defineStore('live', () => {
  /* Each kind's job, running or ended; a job event replaces its own kind's alone. */
  const jobs = ref<JobSlots>({ prepare: null, render: null })
  const billing = ref<Billing | null>(null)
  /* The first snapshot has arrived: until it does, nothing is known. */
  const loaded = ref(false)
  /* Now, in milliseconds, a second at a time: one clock for every running timer. */
  const now = ref(Date.now())
  /* The followed import's files, by upload id. */
  const files = ref<Record<string, FileState>>({})
  /* Disk liveness also sees renders started outside this surface. */
  const activeSessions = ref<RunningSession[]>([])
  /* Why the last read of them failed; while set, their last answer may be stale. */
  const sessionsRefusal = ref<string | null>(null)
  const slotRender = computed(() => {
    const held = jobs.value.render
    return held?.state === 'running' && held.session ? held : null
  })
  const activeRender = computed<RunningRender | null>(() => {
    const held = slotRender.value
    if (held?.session)
      return { collections: collectionsOf(held), id: held.session.id, started: held.session.started }
    return grouped(activeSessions.value)[0] ?? null
  })
  const renderRunning = computed(() => activeRender.value !== null)
  /* Whether what `renderRunning` says is current: the slot's, or a read that answered. */
  const renderConfirmed = computed(() => slotRender.value !== null || sessionsRefusal.value === null)
  const target: Target = { collection: null, staging: null }
  const handlers = new Map<Kind, Set<Handler>>()
  let stream: EventSource | null = null
  setInterval(() => (now.value = Date.now()), 1000)
  let readingSessions = false
  async function refreshSessions(): Promise<void> {
    if (readingSessions) return
    readingSessions = true
    try {
      activeSessions.value = (await runningSessions()).sessions
      sessionsRefusal.value = null
    } catch (reason) {
      // A failed read is no evidence a render ended, so the last answer stays,
      // named as unconfirmed rather than shown as fact.
      sessionsRefusal.value = (reason as Error).message
    } finally {
      readingSessions = false
    }
  }
  setInterval(() => {
    if (stream) void refreshSessions()
  }, 2000)

  /* Each event of `kind`, on every stream this page opens; returns the way to stop. */
  function listen(kind: Kind, handler: Handler): () => void {
    const found = handlers.get(kind) ?? new Set<Handler>()
    handlers.set(kind, found)
    found.add(handler)
    return () => found.delete(handler)
  }

  function emit(kind: Kind, data: unknown): void {
    for (const handler of handlers.get(kind) ?? []) handler(data)
  }

  /* Name a collection, an import, or both; the stream opens again only when either changes. */
  function follow(next: Partial<Target>): void {
    const collection = next.collection !== undefined ? next.collection : target.collection
    const staging = next.staging !== undefined ? next.staging : target.staging
    if (stream && collection === target.collection && staging === target.staging) return
    if (staging !== target.staging) files.value = {}
    target.collection = collection
    target.staging = staging
    open()
    void refreshSessions()
  }

  function open(): void {
    stream?.close()
    const query = new URLSearchParams()
    if (target.collection !== null) query.set('collection', target.collection)
    if (target.staging !== null) query.set('staging', target.staging)
    const named = query.toString()
    const opened = new EventSource(named ? `/events?${named}` : '/events')
    stream = opened
    for (const kind of KINDS)
      opened.addEventListener(kind, (event) => {
        emit(kind, JSON.parse((event as MessageEvent<string>).data))
      })
  }

  /* This store's own handlers, registered first, so every other one reads what they keep. */
  listen('snapshot', (data) => {
    const found = data as Snapshot
    jobs.value = found.jobs
    billing.value = found.billing
    files.value = found.files ?? {}
    loaded.value = true
  })
  listen('job', (data) => hold(data as JobSlot))
  listen('billing', (data) => (billing.value = data as Billing))
  listen('file', (data) => {
    const { upload, ...state } = data as FileState & { upload: string }
    files.value = { ...files.value, [upload]: state }
  })

  /* Put `slot` in its kind's slot, leaving the other kind's as it is. */
  function hold(slot: JobSlot): void {
    jobs.value = { ...jobs.value, [slot.kind]: slot }
  }

  /* Stop `kind`'s running job; a refusal is thrown for the screen to show. */
  async function stop(kind: JobKind): Promise<void> {
    await stopJob(kind)
  }

  /* Ask gpunit again what may be billing; a refusal is thrown for the screen to show. */
  async function checkBilling(): Promise<void> {
    billing.value = (await askBilling()).billing
  }

  function prepareTotals(held: JobSlot | null): string {
    const progress = held?.progress
    if (!progress) return ''
    const elapsed = (now.value - Date.parse(progress.started)) / 1000
    return `${progress.done} of ${progress.of} ${noun(progress.of, 'cell')} done · ${clock(elapsed)}`
  }

  /* A running render's images against its total, and its clock against its limit.
     e.g. "image 1 of 2 · 06:41 of ≤10:30" */
  function renderTotals(held: JobSlot | null): string {
    const session = held?.session
    if (held?.kind !== 'render' || held.state !== 'running' || !session) return ''
    const elapsed = (now.value - Date.parse(session.started)) / 1000
    return `image ${session.images.length} of ${session.of} · ${clock(elapsed)} of ≤${clock(session.limit)}`
  }

  return {
    jobs,
    billing,
    loaded,
    now,
    files,
    renderRunning,
    activeRender,
    activeSessions,
    sessionsRefusal,
    renderConfirmed,
    follow,
    listen,
    hold,
    stop,
    checkBilling,
    prepareTotals,
    renderTotals,
  }
})

/** The billing page's state, from what is known and whether a render runs.
    A running render that is not `confirmed` never hides an alert. */
export function billingState(found: Billing | null, running: boolean, confirmed = true): string {
  if (!found) return 'pending'
  if (running && confirmed) return 'running'
  if (alerting(found)) return 'alert'
  if (running) return 'running'
  return found.volume ? 'open' : 'quiet'
}
