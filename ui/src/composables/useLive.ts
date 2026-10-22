import { ref } from 'vue'
import type { Billing, JobSlot } from '../types'
import { noun } from '../words'

/* The job slot and billing, live, for every screen: one `/events` stream the
   shell opens once. A snapshot on every connect, then each change. */
const job = ref<JobSlot | null>(null)
const billing = ref<Billing | null>(null)
/* The first snapshot has arrived: until it does, nothing is known. */
const loaded = ref(false)
/* Now, in milliseconds, a second at a time: one clock for every running timer. */
const now = ref(Date.now())
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

/* Whether a pod may be billing or the window is past its end. */
function alerting(found: Billing | null): boolean {
  return Boolean(found && (found.pod || found.volume?.state === 'band'))
}

/* `mm:ss` of a span in seconds. e.g. 401 -> "06:41" */
function clock(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds))
  const minutes = String(Math.floor(whole / 60)).padStart(2, '0')
  return `${minutes}:${String(whole % 60).padStart(2, '0')}`
}

function prepareTotals(held: JobSlot | null): string {
  const progress = held?.progress
  if (!progress) return ''
  const elapsed = (now.value - Date.parse(progress.started)) / 1000
  return `${progress.done} of ${progress.of} ${noun(progress.of, 'cell')} done · ${clock(elapsed)}`
}

export function useLive() {
  return { job, billing, loaded, now, connect, alerting, clock, prepareTotals }
}
