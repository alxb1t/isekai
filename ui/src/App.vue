<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLive } from './composables/useLive'

/* The shell: the AppBar, the BillingBanner's slot, the route's screen and the
   JobStrip (design spec §3). Review is keyed by batch and flow, so moving to
   another run keeps the view and its autosave; another flow is a new view. */
const route = useRoute()
const router = useRouter()
const { job, billing, alerting, clock, connect } = useLive()
const now = ref(Date.now())
let ticker: ReturnType<typeof setInterval> | undefined

const alert = computed(() => alerting(billing.value))
const running = computed(() => job.value?.state === 'running')
/* `HH:MM` of a UTC time gpunit recorded, on this machine's clock. */
const hour = (at: string | null) =>
  at ? new Date(at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : ''

/* The strip's totals: a render's image n of N and its time against its limit. */
const totals = computed(() => {
  const held = job.value
  if (!held) return ''
  const session = held.session
  if (held.kind === 'render' && session && held.state === 'running') {
    const elapsed = (now.value - Date.parse(session.started)) / 1000
    return `image ${session.images.length} of ${session.of} · ${clock(elapsed)} of ≤${clock(session.limit)}`
  }
  if (held.state === 'running') return [held.stage, held.flow].filter(Boolean).join(' · ')
  return `last: ${held.kind} · ${held.state}`
})

const batch = computed(() => (typeof route.params.batch === 'string' ? route.params.batch : null))
const place = computed(() => batch.value ?? 'library')
const screen = computed(() => route.name)
const key = computed(() =>
  route.name === 'review' ? `${route.params.batch}/${route.params.flow}` : route.path,
)

/* ⌥0 the library and ⌥1 the batch's hub, from anywhere, text fields included.
   Matched on `event.code`: Option types a character on macOS. */
function onKey(event: KeyboardEvent): void {
  if (!event.altKey) return
  if (event.code === 'Digit0') {
    event.preventDefault()
    void router.push({ name: 'home' })
  } else if (event.code === 'Digit1' && batch.value) {
    event.preventDefault()
    void router.push({ name: 'hub', params: { batch: batch.value } })
  } else if (event.code === 'Digit4') {
    event.preventDefault()
    void router.push({ name: 'session' })
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKey)
  connect()
  ticker = setInterval(() => (now.value = Date.now()), 1000)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  clearInterval(ticker)
})
</script>

<template>
  <div class="app">
    <header class="appbar">
      <RouterLink to="/" class="appbar__mark">isekai</RouterLink>
      <span class="appbar__place">{{ place }}</span>
      <template v-if="batch">
        <RouterLink
          :to="{ name: 'hub', params: { batch } }"
          class="appbar__tab"
          :class="{ 'appbar__tab--active': screen === 'hub' }"
          >Hub<span class="appbar__key">⌥1</span></RouterLink
        >
        <span class="appbar__tab" :class="{ 'appbar__tab--active': screen === 'review' }"
          >Review<span class="appbar__key">⌥2</span></span
        >
      </template>
    </header>
    <!-- The BillingBanner: only when something may be billing; esc never closes it. -->
    <div v-if="alert" class="band" role="alert">
      <span v-if="billing?.pod">A pod may still be billing.</span>
      <span v-else
        >Volume gpunit-isekai is still open past its window and is billing.<template
          v-if="billing?.volume?.ends"
        >
          Window ended {{ hour(billing.volume.ends) }}.</template
        ></span
      >
      <RouterLink :to="{ name: 'session' }" class="band__resolve"
        >Resolve<span class="appbar__key">⌥4</span></RouterLink
      >
    </div>
    <main class="app__screen">
      <RouterView :key="key" />
    </main>
    <footer class="jobstrip">
      <span
        class="jobstrip__dot"
        :class="{ 'jobstrip__dot--running': running, 'jobstrip__dot--alert': alert }"
      />
      <span>job · {{ running ? job?.kind : 'idle' }}</span>
      <span class="jobstrip__totals">{{ totals }}</span>
      <span
        v-if="billing?.volume?.state === 'open'"
        class="jobstrip__volume"
        data-volume-item
        >volume open · until {{ hour(billing.volume.ends) }}</span
      >
    </footer>
  </div>
</template>
