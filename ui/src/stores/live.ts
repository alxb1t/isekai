import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { checkBilling as askBilling, stopJob } from '../api'
import type { Billing, FileState, JobSlot } from '../types'
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

/* What the stream names: the batch the screen shows and the import it has open. */
export interface Target {
  batch: string | null
  staging: string | null
}

/* The kinds of event the stream sends. */
const KINDS = ['snapshot', 'job', 'billing', 'cell', 'file'] as const
export type Kind = (typeof KINDS)[number]
type Handler = (data: unknown) => void

interface Snapshot {
  job: JobSlot | null
  billing: Billing
  files?: Record<string, FileState>
}

/* The job slot, billing and the open import's files, live, for every screen,
   from the page's one stream. Every connect brings a snapshot, so opening it
   again for another batch or import loses nothing. */
export const useLiveStore = defineStore('live', () => {
  const job = ref<JobSlot | null>(null)
  const billing = ref<Billing | null>(null)
  /* The first snapshot has arrived: until it does, nothing is known. */
  const loaded = ref(false)
  /* Now, in milliseconds, a second at a time: one clock for every running timer. */
  const now = ref(Date.now())
  /* The followed import's files, by name. */
  const files = ref<Record<string, FileState>>({})
  /* A render session holds the slot. */
  const renderRunning = computed(
    () => job.value?.kind === 'render' && job.value.state === 'running',
  )
  const target: Target = { batch: null, staging: null }
  const handlers = new Map<Kind, Set<Handler>>()
  let stream: EventSource | null = null
  let ticking = false

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

  /* Name a batch, an import, or both; the stream opens again only when either changes. */
  function follow(next: Partial<Target>): void {
    const batch = next.batch !== undefined ? next.batch : target.batch
    const staging = next.staging !== undefined ? next.staging : target.staging
    if (stream && batch === target.batch && staging === target.staging) return
    if (staging !== target.staging) files.value = {}
    target.batch = batch
    target.staging = staging
    open()
  }

  function open(): void {
    stream?.close()
    if (!ticking) {
      ticking = true
      setInterval(() => (now.value = Date.now()), 1000)
    }
    const query = new URLSearchParams()
    if (target.batch !== null) query.set('batch', target.batch)
    if (target.staging !== null) query.set('staging', target.staging)
    const named = query.toString()
    const opened = new EventSource(named ? `/events?${named}` : '/events')
    stream = opened
    for (const kind of KINDS)
      opened.addEventListener(kind, (event) => {
        const data: unknown = JSON.parse((event as MessageEvent<string>).data)
        take(kind, data)
        emit(kind, data)
      })
  }

  /* Keep what this store holds of an event. */
  function take(kind: Kind, data: unknown): void {
    if (kind === 'snapshot') {
      const found = data as Snapshot
      job.value = found.job
      billing.value = found.billing
      files.value = found.files ?? {}
      loaded.value = true
    } else if (kind === 'job') {
      job.value = data as JobSlot
    } else if (kind === 'billing') {
      billing.value = data as Billing
    } else if (kind === 'file') {
      const { file, ...state } = data as FileState & { file: string }
      files.value = { ...files.value, [file]: state }
    }
  }

  /* Stop the running job; a refusal is thrown for the screen to show. */
  async function stop(): Promise<void> {
    await stopJob()
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
    job,
    billing,
    loaded,
    now,
    files,
    renderRunning,
    follow,
    listen,
    stop,
    checkBilling,
    prepareTotals,
    renderTotals,
  }
})
