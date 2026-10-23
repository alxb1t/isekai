import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { checkBilling as askBilling, stopJob } from '../api'
import type { Billing, JobSlot } from '../types'
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

/* The job slot and billing, live, for every screen, from the page's one
   `/events` stream: a snapshot on every connect, then each change. */
export const useLiveStore = defineStore('live', () => {
  const job = ref<JobSlot | null>(null)
  const billing = ref<Billing | null>(null)
  /* The first snapshot has arrived: until it does, nothing is known. */
  const loaded = ref(false)
  /* Now, in milliseconds, a second at a time: one clock for every running timer. */
  const now = ref(Date.now())
  /* A render session holds the slot. */
  const renderRunning = computed(
    () => job.value?.kind === 'render' && job.value.state === 'running',
  )
  let stream: EventSource | null = null

  function connect(): void {
    if (stream) return
    setInterval(() => (now.value = Date.now()), 1000)
    stream = new EventSource('/events')
    stream.addEventListener('snapshot', (event) => {
      const data = JSON.parse((event as MessageEvent<string>).data) as {
        job: JobSlot | null
        billing: Billing
      }
      job.value = data.job
      billing.value = data.billing
      loaded.value = true
    })
    stream.addEventListener('job', (event) => {
      job.value = JSON.parse((event as MessageEvent<string>).data) as JobSlot
    })
    stream.addEventListener('billing', (event) => {
      billing.value = JSON.parse((event as MessageEvent<string>).data) as Billing
    })
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
    renderRunning,
    connect,
    stop,
    checkBilling,
    prepareTotals,
    renderTotals,
  }
})
